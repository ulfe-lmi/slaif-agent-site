"""Canonical JSON serialization at the review snapshot boundary.

Shared by the review-worker capture path and the trusted renderer
projection path: the snapshot digest is the SHA-256 of
``canonical_json(payload)``, and byte lengths measured through
``canonical_json`` are the exact serialized bytes of the stored jsonb.
The form is byte-identical to the SQL canonical form
``control.slaif_canonical_jsonb_text`` for every value reachable through
the supported write path (sorted keys, compact separators, ASCII
escapes, PG jsonb canonical numeric text).  ``canonical_json_bounded``
produces those same bytes under a hard byte budget for the read-side
admission seam: every output byte is charged exactly once and every
allocation is pre-bounded by an exact cost (R8 bounded-work ordering).
"""

from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal
from typing import Any


def _decimal_text(value: Decimal) -> str:
    """Render a Decimal in PostgreSQL jsonb canonical numeric text.

    Fixed-point, exact retained digits, no exponent; a negative zero keeps
    its scale but drops the sign (``-0.00`` -> ``0.00``), matching the
    verified PG 18.6 probe (jsonb normalizes ``-0`` -> ``0`` while
    preserving ``1.50`` scale).
    """

    if value == 0:
        value = abs(value)
    return format(value, "f")


def canonical_json(value: Any) -> str:
    """Canonical JSON serialization (sorted, compact, ensure_ascii).

    Byte-identical to the SQL canonical form
    ``control.slaif_canonical_jsonb_text`` for every value reachable
    through the supported write path:

    * ``int``/``Decimal`` render in PG jsonb canonical numeric text (exact
      retained digits, no exponent, negative zero normalized to 0 while
      keeping scale);
    * finite ``float`` renders the same text PG derives from the exact
      shortest-repr token ``json.dumps`` writes (``repr`` -> Decimal ->
      fixed-point), so the Python digest recomputes from the stored jsonb
      for exponent-form and ``-0.0`` values; non-finite floats are
      rejected (they cannot be stored in jsonb);
    * ``str``/``bool``/``None`` retain the legacy ``json.dumps``
      rendering.

    Every successfully stored v1 snapshot was accepted only because its
    numbers already satisfy old-repr == PG-text; for exactly that set the
    float branch above yields the identical bytes, so legacy digests stay
    recomputable (see test_snapshot_v2_canonical).
    """

    if isinstance(value, dict):
        if not value:
            return "{}"
        entries = [
            json.dumps(key, ensure_ascii=True) + ":" + canonical_json(value[key])
            for key in sorted(value)
        ]
        return "{" + ",".join(entries) + "}"
    if isinstance(value, (list, tuple)):
        if not value:
            return "[]"
        return "[" + ",".join(canonical_json(item) for item in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, Decimal):
        return _decimal_text(value)
    if value is None:
        return "null"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("non-finite values cannot be retained in PG jsonb")
        # The exact token json.dumps writes for this float; PG jsonb
        # parses that token and canonical numeric_out is its fixed-point
        # Decimal text (probe-qualified, incl. exponent/-0.0 forms).
        return _decimal_text(Decimal(repr(value)))
    raise TypeError(f"unsupported canonical value type: {type(value).__name__}")


def parse_snapshot_text(text: str) -> Any:
    """Parse trusted materializer JSON text with exact numeric retention.

    ``parse_float=Decimal`` keeps every written digit/scale (raw-retention
    boundary of the v2 capture); integers arrive as ``int``.
    """

    return json.loads(text, parse_float=Decimal, parse_int=int)


def canonical_digest(payload: dict[str, Any]) -> str:
    """SHA-256 hex over the canonical serialization of the payload."""

    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class CanonicalBudgetExceeded(ValueError):
    """The canonical serialization exceeds its byte budget.

    Raised by ``canonical_json_bounded``; the read-side admission seam maps
    it to the stable refusal.  The budget is the capture canonical payload
    budget (8 MiB), so no allocation can exceed it.
    """


def _string_cost(text: str) -> int:
    """Exact ``json.dumps(text, ensure_ascii=True)`` output length.

    Counted character-by-character before any allocation: ASCII 0x20..0x7E
    passes through (1 byte), ``"``/``\\`` double (2), ``\\b \\t \\n
    \\f \\r`` keep their two-byte escapes, every other control character
    (including 0x7F), every BMP non-ASCII character becomes ``\\uXXXX``
    (6), and a non-BMP character becomes a surrogate pair
    ``\\uXXXX\\uXXXX`` (12).
    """

    total = 2  # the two quotes
    for char in text:
        code = ord(char)
        if code == 0x22 or code == 0x5C:
            total += 2
        elif code < 0x20:
            total += 2 if code in (0x08, 0x09, 0x0A, 0x0C, 0x0D) else 6
        elif code <= 0x7E:
            total += 1
        elif code <= 0xFFFF:
            total += 6
        else:
            total += 12
    return total


def _int_text(value: int) -> str:
    """Exact decimal text of an arbitrary-magnitude int.

    ``str`` within the runtime's integer-string digit limit; beyond it, the
    C decimal module formats the identical digits (no read restriction -
    PostgreSQL jsonb numbers are unconstrained numeric, not the 1000-digit
    declared-precision column default).
    """

    if value == 0:
        return "0"
    try:
        return str(value)
    except ValueError:
        text = format(Decimal(abs(value)), "f")
        return "-" + text if value < 0 else text


def _decimal_f_text_length(value: Decimal) -> int:
    """Exact ``len(format(value, "f"))`` computed from ``as_tuple``.

    Tuple form ``value = digits-integral x 10**exponent``: a non-negative
    exponent appends zeros (``len(digits) + exponent``); a negative exponent
    renders ``-exponent`` decimal places (``len(digits) + 1`` when the
    coefficient already spans them, else ``2 + scale``); zero renders ``0``
    for a non-negative exponent and ``0`` plus scale zeros below it.
    """

    parts = value.as_tuple()
    exponent = parts.exponent
    if not isinstance(exponent, int):
        raise ValueError("non-finite decimals cannot be retained in PG jsonb")
    if value == 0:
        return 1 if exponent >= 0 else 2 + (-exponent)
    digit_count = len(parts.digits)
    if exponent >= 0:
        return digit_count + exponent
    scale = -exponent
    return digit_count + 1 if digit_count > scale else 2 + scale


def canonical_json_bounded(value: Any, max_bytes: int) -> str:
    """Byte-exact canonical serialization with a hard byte budget.

    Produces exactly the text ``canonical_json`` produces for every value it
    renders (str/bool/None, arbitrary-magnitude int and Decimal, finite
    float, str-keyed objects and arrays) and raises
    :class:`CanonicalBudgetExceeded` the moment the serialized form would
    exceed ``max_bytes``.

    Accounting: every output byte is charged exactly once, in order of
    production.  A scalar (including each object key) is charged its own
    text; a container is charged only its own bytes - braces or brackets,
    one separator between parts, and one colon per entry (objects) - at the
    instant it joins its already-charged parts.  The sum of all charges is
    exactly the final text length, so a document at or below its actual
    budget is never refused merely for being nested, and a document one
    byte over always refuses.  Each allocation (escaped strings, int
    conversion, joins) is pre-bounded by an exact cost computed before it,
    so no allocation exceeds the budget.  Non-finite floats and unsupported
    value/key types raise ``ValueError``/``TypeError`` exactly as
    ``canonical_json`` does for unsupported types, so a caller's existing
    refusal mapping covers both failure kinds.

    The caller must first bound the document's container depth: this
    serializer recurses to it.  The admission seam runs its bounded
    whole-document raw-depth probe before calling here, so no unbounded
    recursion or allocation can occur.
    """

    remaining = [max_bytes]

    def charged(text: str) -> str:
        if len(text) > remaining[0]:
            raise CanonicalBudgetExceeded()
        remaining[0] -= len(text)
        return text

    def scalar(item: Any) -> str:
        if isinstance(item, bool):
            return "true" if item else "false"
        if isinstance(item, int):
            try:
                return str(item)
            except ValueError:
                magnitude = Decimal(abs(item))
                length = _decimal_f_text_length(magnitude)
                if item < 0:
                    length += 1
                if length > remaining[0]:
                    raise CanonicalBudgetExceeded() from None
                text = format(magnitude, "f")
                return "-" + text if item < 0 else text
        if isinstance(item, Decimal):
            length = _decimal_f_text_length(abs(item) if item == 0 else item)
            if item < 0:
                length += 1
            if length > remaining[0]:
                raise CanonicalBudgetExceeded()
            return _decimal_text(item)
        if item is None:
            return "null"
        if isinstance(item, str):
            if _string_cost(item) > remaining[0]:
                raise CanonicalBudgetExceeded()
            return json.dumps(item, ensure_ascii=True)
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ValueError("non-finite values cannot be retained in PG jsonb")
            # A finite float's PG canonical text is short (its repr carries a
            # bounded exponent); the render-level charge bounds the joins.
            return _decimal_text(Decimal(repr(item)))
        raise TypeError(f"unsupported canonical value type: {type(item).__name__}")

    def key_text(key: Any) -> str:
        # A trusted jsonb object key is a string; anything else is not a
        # jsonb-representable capture value.
        if not isinstance(key, str):
            raise TypeError(f"unsupported canonical key type: {type(key).__name__}")
        if _string_cost(key) > remaining[0]:
            raise CanonicalBudgetExceeded()
        return json.dumps(key, ensure_ascii=True)

    def render(item: Any) -> str:
        if isinstance(item, dict):
            if not item:
                return charged("{}")
            parts: list[str] = []
            for key in sorted(item):
                # The key is charged exactly once (here); the child was
                # charged by its own render call; the container's own bytes
                # (braces, separators, one colon per entry) are charged in
                # the overhead below.  Parts are never re-charged.
                parts.append(charged(key_text(key)) + ":" + render(item[key]))
            overhead = 2 + (len(parts) - 1) + len(parts)
            if overhead > remaining[0]:
                raise CanonicalBudgetExceeded()
            remaining[0] -= overhead
            return "{" + ",".join(parts) + "}"
        if isinstance(item, (list, tuple)):
            if not item:
                return charged("[]")
            parts = [render(child) for child in item]
            overhead = 2 + (len(parts) - 1)
            if overhead > remaining[0]:
                raise CanonicalBudgetExceeded()
            remaining[0] -= overhead
            return "[" + ",".join(parts) + "]"
        return charged(scalar(item))

    return render(value)


__all__ = [
    "CanonicalBudgetExceeded",
    "canonical_digest",
    "canonical_json",
    "canonical_json_bounded",
    "parse_snapshot_text",
]
