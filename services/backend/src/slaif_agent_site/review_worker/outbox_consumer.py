"""Durable cache-outbox consumer (083/3): verify-and-consume, no listener.

The accept reviewer transaction emits exactly one durable
``WORKSPACE_ACCEPTED`` row per accepted workspace (072_001). This
module is the consumer: one bounded round claims a batch of pending
rows through ``control.slaif_cache_outbox_claim`` (id order,
``FOR UPDATE SKIP LOCKED``, 25-attempt budget), reads the site's
current ``canonical_revision``, evaluates the payload, and closes the
row through the idempotent ``control.slaif_cache_outbox_consume``.

Crash semantics (the normative contract): the claim commits the
``attempt_count`` increment, so death between claim and consume leaves
the row re-claimable with the attempt already counted; consume is
idempotent, so the row is processed exactly once in effect (a single
``consumed_at``). At the 25-attempt budget the row stops being claimed
and is abandoned, operator-visible via ``last_attempt_at``/
``attempt_count``.

Accept race: a concurrent acceptance may advance
``control.site.canonical_revision`` past the row's
``new_canonical_revision`` between the revision read and the consume.
The row is then recorded ``SUBSUMED`` — harmless by construction,
because the later acceptance has already superseded this row's effect
on the canonical surface; the outbox row's only product consequence is
marking that revision transition as seen.

In the current deployment the consume action is an explicit no-op
against the (nonexistent) public edge cache: public HTML is
``private, no-store`` and public media is content-addressed and
immutable, so there is nothing to invalidate. If a public edge cache is
added later, this consumed/outbox contract is the hook point.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import asyncpg

LOGGER = logging.getLogger(__name__)

# Stable terminal codes written to ``control.cache_outbox.last_error``.
PAYLOAD_INVALID = "PAYLOAD_INVALID"
SUBSUMED = "SUBSUMED"
REVISION_AHEAD = "REVISION_AHEAD"

_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_DIGEST_RE = re.compile(r"[0-9a-f]{64}")
_PUBLIC_KEY_RE = re.compile(r"public/sha256/[0-9a-f]{2}/[0-9a-f]{2}/[0-9a-f]{64}")

_PAYLOAD_KEYS = frozenset(
    {
        "snapshot_id",
        "digest",
        "base_site_revision",
        "new_canonical_revision",
        "media_manifest",
    }
)
_MANIFEST_KEYS = frozenset({"media_id", "digest", "public_key"})


class OutboxOutcome(StrEnum):
    """Exactly one terminal outcome per outbox row."""

    CONSUMED = "CONSUMED"
    SUBSUMED = "SUBSUMED"
    DEAD_LETTER = "DEAD_LETTER"


@dataclass(frozen=True, slots=True)
class OutboxEvaluation:
    """One evaluation result: the outcome plus the stable code if any."""

    outcome: OutboxOutcome
    code: str | None = None


def _is_uuid_str(value: Any) -> bool:
    return isinstance(value, str) and _UUID_RE.fullmatch(value) is not None


def _is_int(value: Any) -> bool:
    # bool is an int subclass; a JSON boolean is never a revision.
    return isinstance(value, int) and not isinstance(value, bool)


def _payload_is_valid(payload: Any) -> bool:
    """True iff the payload is exactly one WORKSPACE_ACCEPTED document.

    The accept job emits ``{snapshot_id, digest, base_site_revision,
    new_canonical_revision, media_manifest}`` (sort_keys, compact
    JSONB); every field is checked for exact shape. A JSONB cell can
    hold any JSON document, so "missing JSON" is observed here as "not
    a JSON object" and is dead-lettered like any other shape failure.
    """
    if not isinstance(payload, dict) or set(payload) != _PAYLOAD_KEYS:
        return False
    if not _is_uuid_str(payload["snapshot_id"]):
        return False
    if not (
        isinstance(payload["digest"], str)
        and _DIGEST_RE.fullmatch(payload["digest"]) is not None
    ):
        return False
    if not _is_int(payload["base_site_revision"]):
        return False
    if not _is_int(payload["new_canonical_revision"]):
        return False
    manifest = payload["media_manifest"]
    if not isinstance(manifest, list):
        return False
    for entry in manifest:
        if not isinstance(entry, dict) or set(entry) != _MANIFEST_KEYS:
            return False
        if not _is_uuid_str(entry["media_id"]):
            return False
        if not (
            isinstance(entry["digest"], str)
            and _DIGEST_RE.fullmatch(entry["digest"]) is not None
        ):
            return False
        if not (
            isinstance(entry["public_key"], str)
            and _PUBLIC_KEY_RE.fullmatch(entry["public_key"]) is not None
        ):
            return False
    return True


def evaluate_outbox_row(payload: Any, current_revision: int) -> OutboxEvaluation:
    """Pure evaluation of one claimed row against the current canonical.

    Exactly one of: ``CONSUMED`` (valid payload AND
    ``new_canonical_revision == current_revision``), ``SUBSUMED``
    (valid payload AND ``new_canonical_revision < current_revision``;
    terminal, not a failure), or ``DEAD_LETTER`` with the stable code
    ``PAYLOAD_INVALID`` (any shape failure) or ``REVISION_AHEAD``
    (``new_canonical_revision > current_revision``; impossible under
    the accept invariants; terminal).
    """
    if not _payload_is_valid(payload):
        return OutboxEvaluation(OutboxOutcome.DEAD_LETTER, PAYLOAD_INVALID)
    new_revision = int(payload["new_canonical_revision"])
    if new_revision == current_revision:
        return OutboxEvaluation(OutboxOutcome.CONSUMED)
    if new_revision < current_revision:
        return OutboxEvaluation(OutboxOutcome.SUBSUMED)
    return OutboxEvaluation(OutboxOutcome.DEAD_LETTER, REVISION_AHEAD)


def _consume_error_for(evaluation: OutboxEvaluation) -> str | None:
    """The ``p_error`` to record: NULL consumed, SUBSUMED, or the code."""
    if evaluation.outcome is OutboxOutcome.CONSUMED:
        return None
    if evaluation.outcome is OutboxOutcome.SUBSUMED:
        return SUBSUMED
    return evaluation.code


def _decode_payload(raw: Any) -> Any:
    """Decode one JSONB cell into its JSON document.

    asyncpg delivers ``jsonb`` as the JSON text, so a stored object
    arrives as a string; a stored string/array/null document arrives
    as its JSON encoding. ``json.loads`` normalizes both to the
    document itself. A cell that cannot be decoded (defensive; a JSONB
    cell is always valid JSON) is dead-lettered as the null document.
    """
    if not isinstance(raw, str):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def outbox_round_due(
    last_run_monotonic: float | None,
    now_monotonic: float,
    interval_seconds: float,
) -> bool:
    """Pure last-run gating: ``None`` means the first run is due."""
    if last_run_monotonic is None:
        return True
    return (now_monotonic - last_run_monotonic) >= interval_seconds


async def consume_outbox_round(pool: Any, settings: Any) -> int:
    """Run one bounded outbox round; return the processed row count.

    One claim of up to ``settings.outbox_batch_size`` rows. Per row:
    read ``canonical_revision`` for the row's site, evaluate, consume
    with the exact ``p_error`` (NULL / ``SUBSUMED`` / stable code). A
    missing site row or a transient database failure skips the row:
    the claim already committed the attempt increment, so the row
    stays re-claimable and the round returns the count of the rows it
    actually closed.
    """
    try:
        async with pool.acquire() as connection:
            rows = await connection.fetch(
                "SELECT * FROM control.slaif_cache_outbox_claim($1)",
                settings.outbox_batch_size,
            )
    except (asyncpg.PostgresError, TimeoutError, OSError):
        LOGGER.warning(
            "outbox claim unavailable",
            extra={"event_fields": {"event": "outbox_claim_unavailable"}},
        )
        return 0
    if not rows:
        return 0
    processed = 0
    for row in rows:
        outbox_id = int(row["id"])
        attempt_count = int(row["attempt_count"])
        try:
            async with pool.acquire() as connection:
                revision_row = await connection.fetchrow(
                    "SELECT canonical_revision FROM control.site WHERE id = $1",
                    row["site_id"],
                )
            if revision_row is None:
                LOGGER.warning(
                    "outbox row site missing, left re-claimable",
                    extra={
                        "event_fields": {
                            "outbox_id": outbox_id,
                            "attempt_count": attempt_count,
                        }
                    },
                )
                continue
            evaluation = evaluate_outbox_row(
                _decode_payload(row["payload"]),
                int(revision_row["canonical_revision"]),
            )
            async with pool.acquire() as connection:
                await connection.fetch(
                    "SELECT control.slaif_cache_outbox_consume($1, $2)",
                    outbox_id,
                    _consume_error_for(evaluation),
                )
        except (asyncpg.PostgresError, TimeoutError, OSError):
            LOGGER.warning(
                "outbox row skipped after transient failure",
                extra={
                    "event_fields": {
                        "outbox_id": outbox_id,
                        "attempt_count": attempt_count,
                    }
                },
            )
            continue
        processed += 1
        LOGGER.info(
            "outbox row consumed",
            extra={
                "event_fields": {
                    "outbox_id": outbox_id,
                    "outcome": evaluation.outcome.value,
                    "code": evaluation.code,
                    "attempt_count": attempt_count,
                }
            },
        )
    return processed


__all__ = [
    "PAYLOAD_INVALID",
    "REVISION_AHEAD",
    "SUBSUMED",
    "OutboxEvaluation",
    "OutboxOutcome",
    "consume_outbox_round",
    "evaluate_outbox_row",
    "outbox_round_due",
]
