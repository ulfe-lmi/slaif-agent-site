"""077_001 data preservation: canonical media + a genuine v2 snapshot.

The A7 preservation slice of 083-10-a: a real released 076_001 baseline
carries NONEMPTY canonical media (meaningful metadata + verified immutable
bytes in the private and public store namespaces) and a GENUINE COMPLETE
review-snapshot/v2 captured by the actual freeze worker over a meaningful
site/composition/media.  The pending COW work is cleared by the REAL
supported discard lifecycle (snapshot/media/evidence retained) BEFORE the
normal physical 076 -> 077 upgrade, which must preserve:

- every canonical media row byte-for-byte (all columns, ids, status,
  timestamps, metadata, digests, storage keys);
- the immutable store bytes (private namespace for both assets, public
  namespace for the public asset);
- the full retained snapshot row, payload, siblings, digest and bindings
  byte-exact; and
- the canonical site revision.

The positive 076 -> 077 stage runs the ACTUAL production operator
upgrade (bootstrap.service.upgrade), whose admission preflight refuses
any workspace with pending COW operations - which is exactly why the
supported discard lifecycle runs first - then the normal reconcile
(actual head 077_001, valid normal hardening/roles).  After it, the
actual supported downgrade refusal from 077 is exercised through BOTH
paths: the bootstrap operator path (typed BootstrapStateError before
any PENDING marker / COW disable / migration effect) and the documented
direct Alembic path (the 077 migration body's P0001 ratchet).  After
each refusal the head, media rows, snapshot row,
store bytes, canonical revision and the media-function authority set are
asserted unchanged.

Provenance and limits:
- the canonical media rows and bytes are seeded by an explicit trusted
  OWNER fixture through the real store staging/publish interface plus one
  owner INSERT (bootstrap-grade setup data); the seed is never
  reviewer-publication proof;
- the v2 snapshot is real worker-generated (real freeze constructor,
  claim, run_freeze_job; real digest verified through the product
  canonical-digest function; nonempty selected media closure) - no
  hand-inserted snapshot rows or f*64 placeholder hashes;
- the pending COW edits (one Heading + two canonical Image references)
  are real agent COW operations through the public agentcow session +
  the real product component function;
- raw-DB/worker only: the product TEST app locators reject the peer
  endpoint, so HTTP/NGINX behavior, all PG versions and the remaining
  A8 proofs stay with PRIMARY;
- the initial 076 stage uses the already-reviewed narrow TEST-only
  expected-head metadata seam (test_agent_mutations._expected_head_
  override); the normal current 077 production gate stays unchanged for
  the real upgrade/reconcile.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import pytest
from conftest import AgentSiteDatabase, AsyncpgExecutor
from slaif_agent_site.agent_state.foundation import (
    asyncpg_cow_session,
    get_session_operations,
)
from slaif_agent_site.bootstrap.service import (
    BootstrapStateError,
    downgrade,
    reconcile,
    upgrade,
)
from slaif_agent_site.db.connections import owner_connection
from slaif_agent_site.db.migrations import run_migration
from slaif_agent_site.media_service.store import MediaStore, StagedMedia
from slaif_agent_site.review_worker.discard_job import run_discard_job
from test_agent_mutations import _expected_head_override
from test_freeze_review_snapshot import (
    _control_call,
    _create_workspace,
    _digest_is_valid,
    _freeze_claim_run,
    _rt_seed_baseline,
    _snapshot_row,
    _worker_call,
    _worker_pool,
    _worker_settings,
)

_PRIVATE_PNG = b"\x89PNG\r\n\x1a\na7-preserve-canonical-private"
_PUBLIC_PNG = b"\x89PNG\r\n\x1a\na7-preserve-canonical-public"
_ORIGINAL_ALT = "A7 preserve canonical alt"
_ORIGINAL_METADATA = {"origin": "canonical-a7"}

_ALEMBIC_SQL = "SELECT version_num::text FROM control.alembic_version"
_REVISION_SQL = "SELECT canonical_revision FROM control.site WHERE id = $1"
_MARKER_SQL = (
    "SELECT row_to_json(b)::text FROM control.bootstrap_readiness b WHERE b.singleton"
)
_MEDIA_ROW_SQL = (
    "SELECT row_to_json(m)::text FROM content.media_asset_base m WHERE m.id = $1"
)
_SNAP_ROW_SQL = (
    "SELECT row_to_json(r)::text FROM control.review_snapshot r "
    "WHERE r.workspace_id = $1"
)
_WORKSPACE_SQL = "SELECT row_to_json(w)::text FROM control.workspace w WHERE w.id = $1"
# The 077 media contract's authority surface: exact EXECUTE grantee sets
# for the four live media functions (no legacy helper remains at 077).
_AUTH_SQL = (
    "SELECT p.proname || pg_get_function_identity_arguments(p.oid) AS fn, "
    "g.grantee::regrole::text AS role, g.privilege_type "
    "FROM pg_proc p "
    "JOIN pg_namespace n ON n.oid = p.pronamespace "
    "CROSS JOIN LATERAL aclexplode(p.proacl) g "
    "WHERE n.nspname = 'content' AND p.proname IN "
    "('slaif_media_asset_register', 'slaif_agent_media_register', "
    "'slaif_media_update', 'slaif_media_publicize_promoted') "
    "ORDER BY fn, role, privilege_type"
)


def _storage_key(content_hash: str) -> str:
    return f"sha256/{content_hash[:2]}/{content_hash[2:4]}/{content_hash}"


async def _seed_preservation_media(
    database: AgentSiteDatabase,
    store: MediaStore,
    *,
    site_id: UUID,
    uploaded_by: UUID,
    asset_id: UUID,
    content_bytes: bytes,
    public_status: str,
) -> str:
    """Explicit trusted OWNER fixture: canonical base row + immutable bytes.

    The bytes go through the real store staging/publish interface (the
    same interface the upload path uses), then one owner INSERT places the
    canonical record.  Fixture data only: this is not a reviewer
    publication and proves nothing about the accept path.
    """
    content_hash = hashlib.sha256(content_bytes).hexdigest()
    writer = store.create_staging_writer()
    try:
        writer.stream.write(content_bytes)
        writer.stream.close()
        storage_key = store.publish(
            StagedMedia(
                staging_path=writer.path,
                digest=content_hash,
                size_bytes=len(content_bytes),
                mime_type="image/png",
                stream=None,
            )
        )
    except BaseException:
        store.discard_staged(
            StagedMedia(
                staging_path=writer.path,
                digest=content_hash,
                size_bytes=len(content_bytes),
                mime_type="image/png",
                stream=None,
            )
        )
        raise
    assert storage_key == _storage_key(content_hash)
    assert store.object_path(storage_key).read_bytes() == content_bytes
    if public_status == "public":
        # The public digest route serves the separate verified public
        # namespace (the same store method finalization phase 1 uses).
        # Fixture preparation only, still not reviewer-publication proof.
        public_key = store.publish_public(storage_key, content_hash, len(content_bytes))
        assert public_key == f"public/{storage_key}"
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        await owner.execute(
            "INSERT INTO content.media_asset_base "
            "(id, site_id, uploaded_by, filename, mime_type, size_bytes, "
            "content_hash, storage_key, alt_text, metadata, public_status, "
            "published_at) "
            "VALUES ($1,$2,$3,'preserve.png','image/png',$4,$5,$6,"
            f"'{_ORIGINAL_ALT}',$7::jsonb,$8, "
            "CASE WHEN $9 = 'public' THEN now() ELSE NULL END)",
            asset_id,
            site_id,
            uploaded_by,
            len(content_bytes),
            content_hash,
            storage_key,
            json.dumps(_ORIGINAL_METADATA, sort_keys=True),
            public_status,
            public_status,
        )
    return storage_key


async def _cow_component_create(
    database: AgentSiteDatabase,
    *,
    workspace_id: UUID,
    capability_id: UUID,
    site_id: UUID,
    page_id: UUID,
    parent_id: UUID,
    component_type: str,
    props: dict[str, Any],
) -> UUID:
    """One real agent COW component create on the given workspace."""

    agent_pool = await database.role_pool("slaif_agent_runtime")
    try:
        async with asyncpg_cow_session(
            agent_pool, session_id=workspace_id, operation_id=uuid4()
        ) as cow:
            await cow.native.execute(
                "SELECT set_config('app.capability_id', $1, true)",
                str(capability_id),
            )
            created = await cow.native.fetchrow(
                "SELECT * FROM content.slaif_agent_component_create("
                " $1, $2, $3, $4, 'default', NULL, NULL, $5::jsonb)",
                site_id,
                page_id,
                component_type,
                parent_id,
                json.dumps(props),
            )
            assert created is not None
            return UUID(str(created["id"]))
    finally:
        await agent_pool.close()


async def _content_operations(database: AgentSiteDatabase, workspace_id: UUID) -> Any:
    """Public foundation session-operation probe (supported SDK surface)."""
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        return await get_session_operations(
            AsyncpgExecutor(owner), workspace_id, schema="content"
        )


async def _state_oracle(
    database: AgentSiteDatabase,
    *,
    site_id: UUID,
    workspace_id: UUID,
    asset_ids: tuple[UUID, ...],
) -> dict[str, Any]:
    """Exact no-effects capture at a refusal boundary."""
    async with owner_connection(
        database.settings.resolved_owner_dsn(), expected_database=database.name
    ) as owner:
        media_rows = {
            str(aid): await owner.fetchval(_MEDIA_ROW_SQL, aid) for aid in asset_ids
        }
        return {
            "alembic": await owner.fetchval(_ALEMBIC_SQL),
            "revision": int(await owner.fetchval(_REVISION_SQL, site_id)),
            "marker": await owner.fetchval(_MARKER_SQL),
            "media": media_rows,
            "snapshot": await owner.fetchval(_SNAP_ROW_SQL, workspace_id),
            "workspace": await owner.fetchval(_WORKSPACE_SQL, workspace_id),
            "authority": [
                (row["fn"], row["role"], row["privilege_type"])
                for row in await owner.fetch(_AUTH_SQL)
            ],
        }


def _store_bytes(
    store: MediaStore,
    storage_private: str,
    storage_public: str,
) -> dict[str, bytes]:
    return {
        "private_private": store.object_path(storage_private).read_bytes(),
        "private_public": store.object_path(storage_public).read_bytes(),
        "public_public": store.object_path(f"public/{storage_public}").read_bytes(),
    }


def _exception_sqlstates(error: BaseException) -> list[str]:
    sqlstates: list[str] = []
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        sqlstate = getattr(current, "sqlstate", None)
        if isinstance(sqlstate, str):
            sqlstates.append(sqlstate)
        orig = getattr(current, "orig", None)
        current = current.__cause__ or current.__context__ or orig
    return sqlstates


@pytest.mark.asyncio
async def test_077_media_and_v2_snapshot_preservation_and_downgrade_refusal(
    agent_site_database: AgentSiteDatabase,
    tmp_path: Path,
) -> None:
    database = agent_site_database
    dsn = database.settings.resolved_owner_dsn()
    db_name = database.name
    store = MediaStore(tmp_path / "media")

    # --- released 076_001 stage (the current head is 077_001) -----------
    await run_migration(
        dsn, expected_database=db_name, operation="upgrade", revision="076_001"
    )
    with _expected_head_override("076_001"):
        await reconcile(database.settings)
    async with owner_connection(dsn, expected_database=db_name) as owner:
        assert await owner.fetchval(_ALEMBIC_SQL) == "076_001"
        assert (
            await owner.fetchval(
                "SELECT readiness_state::text FROM control.bootstrap_readiness "
                "WHERE singleton"
            )
            == "HARDENED"
        )

    # --- meaningful site + NONEMPTY canonical media (trusted owner data)
    private_id = uuid4()
    public_id = uuid4()
    async with owner_connection(dsn, expected_database=db_name) as owner:
        seed = await _rt_seed_baseline(owner)
        site_id = UUID(seed["site_id"])
        user_id = UUID(seed["user_id"])
        page_id = uuid4()
        section_id = uuid4()
        await owner.execute(
            "INSERT INTO content.page_base (id, site_id, slug, title, status,"
            " locale) VALUES ($1,$2,'home','A7 Preserve Home','PUBLISHED',"
            " 'en-US')",
            page_id,
            site_id,
        )
        await owner.execute(
            "INSERT INTO content.page_composition_base (id, site_id, page_id,"
            " component_type, schema_version, parent_id, slot_key, order_key,"
            " props) VALUES ($1,$2,$3,'Section','1',NULL,'default',0,"
            " '{}'::jsonb)",
            section_id,
            site_id,
            page_id,
        )
    private_hash = hashlib.sha256(_PRIVATE_PNG).hexdigest()
    public_hash = hashlib.sha256(_PUBLIC_PNG).hexdigest()
    storage_private = await _seed_preservation_media(
        database,
        store,
        site_id=site_id,
        uploaded_by=user_id,
        asset_id=private_id,
        content_bytes=_PRIVATE_PNG,
        public_status="private",
    )
    storage_public = await _seed_preservation_media(
        database,
        store,
        site_id=site_id,
        uploaded_by=user_id,
        asset_id=public_id,
        content_bytes=_PUBLIC_PNG,
        public_status="public",
    )

    # --- v2 workspace + genuine pending COW work (real agent session) ---
    async with owner_connection(dsn, expected_database=db_name) as owner:
        ws, cap = await _create_workspace(
            owner, site_id, user_id, "083/10-a A7 Preservation"
        )
    await _cow_component_create(
        database,
        workspace_id=ws,
        capability_id=cap,
        site_id=site_id,
        page_id=page_id,
        parent_id=section_id,
        component_type="Heading",
        props={"level": 1, "text": "083/10-a A7 preservation marker"},
    )
    await _cow_component_create(
        database,
        workspace_id=ws,
        capability_id=cap,
        site_id=site_id,
        page_id=page_id,
        parent_id=section_id,
        component_type="Image",
        props={"mediaId": str(private_id), "alt": "preserve private"},
    )
    await _cow_component_create(
        database,
        workspace_id=ws,
        capability_id=cap,
        site_id=site_id,
        page_id=page_id,
        parent_id=section_id,
        component_type="Image",
        props={"mediaId": str(public_id), "alt": "preserve public"},
    )
    pending_before = await _content_operations(database, ws)
    assert pending_before, "the pending COW work must be genuine and nonempty"

    pool = await _worker_pool(database)
    try:
        # --- GENUINE COMPLETE v2 snapshot from the real freeze worker ---
        freeze_result, _freeze_job = await _freeze_claim_run(
            database,
            workspace_id=ws,
            site_id=site_id,
            delegator_id=user_id,
            pool=pool,
            claimant="a7-preserve-freeze",
        )
        assert freeze_result.status == "SUCCEEDED", freeze_result.error
        snap = await _snapshot_row(database, ws)
        assert snap is not None
        assert str(snap["status"]) == "COMPLETE"
        payload_text = (
            snap["payload"]
            if isinstance(snap["payload"], str)
            else json.dumps(snap["payload"])
        )
        payload = json.loads(payload_text)
        assert payload["state_version"] == "review-snapshot/v2"
        assert set(payload["media"]) == {str(private_id), str(public_id)}
        inventory = {
            str(doc["id"]): (str(doc["content_hash"]), str(doc["public_status"]))
            for doc in payload["media_inventory"]
        }
        assert inventory == {
            str(private_id): (private_hash, "private"),
            str(public_id): (public_hash, "public"),
        }
        references = snap["media_references"]
        if isinstance(references, str):
            references = json.loads(references)
        assert {str(ref["id"]) for ref in references} == {
            str(private_id),
            str(public_id),
        }
        assert await _digest_is_valid(database, UUID(str(snap["id"])))
        assert snap["versions"] is not None
        assert snap["normalized_state"] is not None
        assert snap["validation_report"] is not None

        # --- data oracles captured at the reconciled 076 stage ----------
        pre = await _state_oracle(
            database,
            site_id=site_id,
            workspace_id=ws,
            asset_ids=(private_id, public_id),
        )
        bytes_pre = _store_bytes(store, storage_private, storage_public)
        assert bytes_pre["private_private"] == _PRIVATE_PNG
        assert bytes_pre["private_public"] == _PUBLIC_PNG
        assert bytes_pre["public_public"] == _PUBLIC_PNG

        # --- real supported discard: pending COW cleared, retained -----
        discard_result = await _discard_claim_run(
            database,
            pool,
            workspace_id=ws,
            site_id=site_id,
            user_id=user_id,
        )
        assert discard_result.status == "SUCCEEDED", discard_result.error
        pending_after = await _content_operations(database, ws)
        assert not pending_after, (
            "the supported discard lifecycle must clear the pending COW work"
        )
        mid = await _state_oracle(
            database,
            site_id=site_id,
            workspace_id=ws,
            asset_ids=(private_id, public_id),
        )
        assert mid["snapshot"] == pre["snapshot"]
        assert mid["media"] == pre["media"]
        assert mid["revision"] == pre["revision"]
        assert _store_bytes(store, storage_private, storage_public) == bytes_pre
        workspace_row = json.loads(mid["workspace"])
        assert workspace_row["status"] == "DISCARDED"
        assert workspace_row["discarded_at"] is not None

        # --- ACTUAL normal operator upgrade + real current reconcile ---
        # bootstrap.service.upgrade proves the production operator
        # admission path end to end: the pending-COW preflight (empty
        # after the real discard above), the COW disable, then the head
        # migration.
        await upgrade(database.settings)
        await reconcile(database.settings)
        post = await _state_oracle(
            database,
            site_id=site_id,
            workspace_id=ws,
            asset_ids=(private_id, public_id),
        )
        assert post["alembic"] == "077_001"
        marker = json.loads(post["marker"])
        assert marker["readiness_state"] == "HARDENED"
        assert marker["migration_revision"] == "077_001"
        assert marker["safe"] is True
        assert marker["product_privileges_validated"] is True
        assert marker["foundation_hardened"] is True
        # Byte-exact preservation through the 077 migration.
        assert post["media"] == pre["media"]
        assert post["snapshot"] == pre["snapshot"]
        assert post["revision"] == pre["revision"]
        assert post["workspace"] == mid["workspace"]
        assert _store_bytes(store, storage_private, storage_public) == bytes_pre

        # --- actual supported downgrade refusal from 077: bootstrap -----
        with pytest.raises(
            BootstrapStateError, match="workspace-isolated media contract"
        ):
            await downgrade(database.settings)
        refused_bootstrap = await _state_oracle(
            database,
            site_id=site_id,
            workspace_id=ws,
            asset_ids=(private_id, public_id),
        )
        assert refused_bootstrap == post
        assert _store_bytes(store, storage_private, storage_public) == bytes_pre

        # --- 077 migration-body ratchet: documented direct Alembic path -
        try:
            await run_migration(
                dsn,
                expected_database=db_name,
                operation="downgrade",
                revision="base",
            )
            raise AssertionError("077 downgrade did not refuse")
        except Exception as error:  # noqa: BLE001 - exact text asserted below
            assert "MEDIA_WORKSPACE_ISOLATION_DOWNGRADE_UNSUPPORTED" in str(error)
            assert "P0001" in _exception_sqlstates(error), str(error)[:300]
        refused_direct = await _state_oracle(
            database,
            site_id=site_id,
            workspace_id=ws,
            asset_ids=(private_id, public_id),
        )
        assert refused_direct == post
        assert _store_bytes(store, storage_private, storage_public) == bytes_pre
    finally:
        await pool.close()


async def _discard_claim_run(
    database: AgentSiteDatabase,
    pool: Any,
    *,
    workspace_id: UUID,
    site_id: UUID,
    user_id: UUID,
) -> Any:
    """Real discard enqueue (control authority) + worker claim + run."""
    rows = await _control_call(
        database,
        "SELECT * FROM control.slaif_human_agent_workspace_discard($1,$2,$3)",
        workspace_id,
        site_id,
        user_id,
    )
    assert len(rows) == 1
    claimed = await _worker_call(
        database,
        "SELECT * FROM control.slaif_review_job_claim($1, $2)",
        "a7-preserve-discard",
        ["DISCARD"],
    )
    assert len(claimed) == 1 and str(claimed[0]["id"]) == str(rows[0]["job_id"])
    return await run_discard_job(pool, _worker_settings(database), dict(claimed[0]))
