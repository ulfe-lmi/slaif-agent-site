"""Public whole-session promotion qualification for the frozen foundation.

Qualifies, through the public agent-cow-postgresql 0.2.0 API only, whether a
whole mixed-FK COW session can be committed after promotion has made
uncommitted effects, and rolled back completely when the terminal window
fails. This is GENERIC MECHANISM PROOF on an owned disposable cluster:
it does NOT qualify the actual public Agent/Editor/Media HTTP surface,
the freeze/accept worker, or the audit/revision/outbox product families.

Fixture geometry is source-backed actual-product-equivalent: single-UUID
primary keys with composite site-scoped UNIQUE constraints, matching the
shipped content tables (PK-vs-composite-UK shapes preserved, not collapsed
into composite PKs):

  fixture table               product table (migration)
  site                        control.site (kept OUTSIDE the COW set)
  site_locale                 content.site_locale (042_001 lines 25..36)
  content_type                content.content_type (016_001, 040_001)
  field_definition            content.field_definition (016_001, 040_001)
  content_item                content.content_item (016_001, 040_001)
  content_item_translation    content.content_item_translation (040_001)
  item_relation               content.item_relation (040_001)
  page                        content.page (021_001, 042_001 line 228)
  page_composition            content.page_composition (022_001)
  media_asset                 content.media_asset (023_001)
  navigation                  content.navigation (020_001, 042_001 line 18)
  navigation_item             content.navigation_item (042_001 lines 45..73)
  redirect                    content.redirect (042_001 lines 68..84, 234)
  cycle_a / cycle_b           explicitly SYNTHETIC physical FK cycle pair (P5)
  txn_probe                   generic app-owned transaction probe (P6); plain
                              table kept OUTSIDE the COW set so the reviewer
                              writes ordinary application state, not COW rows

Representative P2 families covered: page, model (content_type), field
(field_definition), item (content_item), translation, relation,
navigation (navigation/navigation_item), composition (page_composition),
media-reference (media_asset). Mixed reference shapes carried: composite
UUID+TEXT (site_id, locale) -> site_locale(site_id, tag) exactly as 042
lines 228/231/234 add them; composite UUID+UUID references including
self-references (page.parent_id, page_composition.parent_id,
navigation_item.parent_id); the DEFERRABLE INITIALLY IMMEDIATE composite
FKs of 040/042 plus plain FKs that the public
enable_cow_schema(allow_deferred_fks=True) call flips, mirroring the
product bootstrap. pg_constraint deferrability is captured and asserted
before/after enable on every COW base table.

Deliberately omitted (disclosed): CHECK bounds, row_version/audit/created
columns, JSON metadata bounds, column DEFAULTs, the uploaded_by identity
reference, functions/triggers, the control schema. None of these changes
the transaction boundary under qualification.

Known operation IDs are assigned explicitly (uuid4 named variables) and
passed via operation_id=/set_operation(); no auto-generated operation ID
is relied on for a pass/fail assertion. The returned
committed_operations is a PRE-promotion locked tuple: every pass/fail
conclusion below is also proven by independent canonical row/value
oracles and public pending-operation inspection after scope exit.

P6 terminal-window lifecycle semantics are source-backed: the deferred
whole-session commit (commit_session(..., defer_fk_constraints=True), the
same qualified mode as P2) makes uncommitted promotion effects inside the
reviewer transaction; a window failure after that point must roll the
promotion back without leaking a transaction, locks, or COW context. The
cancellation outcome is a positive proof: the exact owned asyncio task
actually cancels (CancelledError observed, task.cancelled() is True). An
escaped refusal or a cancel may legally leave the healthy pooled backend
alive and idle, or the pool may have replaced it; only an
"idle in transaction" state or a live lock for the window pid would be a
leak, while the termination outcome expects the backend to be gone.
Frozen 0.2.0 context cleanness is public semantics, not literal
representation: safe_session._normalize_context normalizes both None and
'' to clean, so the leak assertion rejects only nonempty stale app.*
settings.

P7 (composite-FK dependencies() characterization) is a SEPARATE
SCRATCH-ONLY diagnostic and is not part of this module or its CI
selection; whole-session promotion does not call the dependencies SQL, so
dependencies() is deliberately kept out of these pass/fail assertions.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.metadata
import os
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import asyncpg
import pytest
import pytest_asyncio
from conftest import FoundationDatabase
from slaif_agent_site.agent_state.foundation import (
    FOUNDATION_DISTRIBUTION,
    FOUNDATION_VERSION,
    QUALIFIED_PUBLIC_API,
    CowConflictError,
    asyncpg_cow_reviewer,
    asyncpg_cow_session,
    deploy_cow_functions,
    enable_cow_schema,
    harden_cow_schema,
    validate_cow_schema_privileges,
)
from slaif_agent_site.db.executor import AsyncpgExecutor

SITE_A = uuid.UUID("11111111-1111-4111-8111-111111111111")
SITE_B = uuid.UUID("22222222-2222-4222-8222-222222222222")
# SITE_C holds seeded untouched canonical facts (session-isolation control).
SITE_C = uuid.UUID("33333333-3333-4333-8333-333333333333")

SEED_LOCALE_C = uuid.UUID("33333333-0001-4000-8000-000000000001")
SEED_PAGE_C = uuid.UUID("33333333-0002-4000-8000-000000000002")
LOCALE_EN_A = uuid.UUID("33333333-0003-4000-8000-000000000003")
SEED_PAGE_P3 = uuid.UUID("33333333-0004-4000-8000-000000000004")
SEED_PAGE_P4 = uuid.UUID("33333333-0005-4000-8000-000000000005")
TYPE_P6 = uuid.UUID("33333333-0006-4000-8000-000000000006")

# COW-enabled tables: actual-product content geometry plus the synthetic
# physical cycle pair. `site` and `txn_probe` stay outside the COW set.
COW_TABLES = (
    "content_item",
    "content_item_translation",
    "content_type",
    "cycle_a",
    "cycle_b",
    "field_definition",
    "item_relation",
    "media_asset",
    "navigation",
    "navigation_item",
    "page",
    "page_composition",
    "redirect",
    "site_locale",
)
EXCLUDED_TABLES = frozenset({"site", "txn_probe"})

# Frozen P1 anchors (registry pypi.org; retained wheel 106280B).
WHEEL_SHA256 = "c469d24700fabb93a58f464d3539a32e936097f93035a95f193062859546f5b1"
WHEEL_SIZE = 106280
SDIST_SHA256 = "eae8d434d2fc03c4faa08b44b4863fc8f8efb44ee33eaad3adc22e7eb96a062c"
SDIST_SIZE = 107970
REPO_ROOT = Path(__file__).resolve().parents[4]

ORACLE_COLUMNS = {
    "site_locale": "id, site_id, tag, enabled, is_default",
    "page": "id, site_id, slug, title, locale, parent_id",
    "content_type": "id, site_id, key",
    "field_definition": "id, site_id, type_id, key",
    "content_item": "id, site_id, type_id, slug, values",
    "content_item_translation": "id, site_id, item_id, locale, localized_values",
    "item_relation": (
        "id, site_id, source_item_id, field_definition_id, target_item_id, position"
    ),
    "navigation": "id, site_id, key, label",
    "navigation_item": (
        "id, site_id, navigation_id, parent_id, page_id, target_kind, "
        "target_value, locale, position"
    ),
    "page_composition": (
        "id, site_id, page_id, component_type, slot_key, order_key, parent_id, props"
    ),
    "media_asset": "id, site_id, filename, mime_type, size_bytes, content_hash, "
    "storage_key",
    "redirect": "id, site_id, source_route, target, status_code, locale",
    "cycle_a": "id, site_id, partner_id, note",
    "cycle_b": "id, site_id, partner_id, note",
}


def _q(ident: str) -> str:
    return '"' + ident.replace('"', '""') + '"'


def _ddl(schema: str, reviewer_role: str) -> tuple[str, ...]:
    s = _q(schema)
    return (
        f"CREATE TABLE {s}.site (id uuid PRIMARY KEY)",
        f"INSERT INTO {s}.site (id) VALUES ('{SITE_A}'), ('{SITE_B}'), ('{SITE_C}')",
        f"""CREATE TABLE {s}.site_locale (
          id uuid PRIMARY KEY,
          site_id uuid NOT NULL REFERENCES {s}.site(id),
          tag text NOT NULL,
          enabled boolean NOT NULL,
          is_default boolean NOT NULL,
          UNIQUE (site_id, tag)
        )""",
        f"""CREATE TABLE {s}.content_type (
          id uuid PRIMARY KEY,
          site_id uuid NOT NULL REFERENCES {s}.site(id),
          key text NOT NULL,
          UNIQUE (site_id, key),
          UNIQUE (site_id, id)
        )""",
        f"""CREATE TABLE {s}.field_definition (
          id uuid PRIMARY KEY,
          site_id uuid NOT NULL REFERENCES {s}.site(id),
          type_id uuid NOT NULL,
          key text NOT NULL,
          CONSTRAINT field_definition_site_type_fk FOREIGN KEY (site_id, type_id)
            REFERENCES {s}.content_type(site_id, id) DEFERRABLE INITIALLY IMMEDIATE,
          UNIQUE (site_id, type_id, key),
          UNIQUE (site_id, id)
        )""",
        f"""CREATE TABLE {s}.content_item (
          id uuid PRIMARY KEY,
          site_id uuid NOT NULL REFERENCES {s}.site(id),
          type_id uuid NOT NULL REFERENCES {s}.content_type(id),
          slug text NOT NULL,
          values jsonb NOT NULL,
          UNIQUE (site_id, id),
          UNIQUE (site_id, type_id, slug)
        )""",
        f"""CREATE TABLE {s}.content_item_translation (
          id uuid PRIMARY KEY,
          site_id uuid NOT NULL,
          item_id uuid NOT NULL,
          locale text NOT NULL,
          localized_values jsonb NOT NULL,
          CONSTRAINT translation_site_item_fk FOREIGN KEY (site_id, item_id)
            REFERENCES {s}.content_item(site_id, id) DEFERRABLE INITIALLY IMMEDIATE,
          UNIQUE (site_id, item_id, locale)
        )""",
        f"""CREATE TABLE {s}.item_relation (
          id uuid PRIMARY KEY,
          site_id uuid NOT NULL,
          source_item_id uuid NOT NULL,
          field_definition_id uuid NOT NULL,
          target_item_id uuid NOT NULL,
          position integer NOT NULL,
          CONSTRAINT relation_source_fk FOREIGN KEY (site_id, source_item_id)
            REFERENCES {s}.content_item(site_id, id) DEFERRABLE INITIALLY IMMEDIATE,
          CONSTRAINT relation_target_fk FOREIGN KEY (site_id, target_item_id)
            REFERENCES {s}.content_item(site_id, id) DEFERRABLE INITIALLY IMMEDIATE,
          CONSTRAINT relation_field_fk FOREIGN KEY (site_id, field_definition_id)
            REFERENCES {s}.field_definition(site_id, id) DEFERRABLE INITIALLY IMMEDIATE,
          UNIQUE (site_id, source_item_id, field_definition_id, position)
        )""",
        f"""CREATE TABLE {s}.page (
          id uuid PRIMARY KEY,
          site_id uuid NOT NULL REFERENCES {s}.site(id),
          slug text NOT NULL,
          title text NOT NULL,
          locale text NOT NULL,
          parent_id uuid REFERENCES {s}.page(id),
          UNIQUE (site_id, id),
          UNIQUE (site_id, locale, slug),
          CONSTRAINT page_site_locale_fk FOREIGN KEY (site_id, locale)
            REFERENCES {s}.site_locale(site_id, tag)
        )""",
        f"""CREATE TABLE {s}.page_composition (
          id uuid PRIMARY KEY,
          site_id uuid NOT NULL REFERENCES {s}.site(id),
          page_id uuid NOT NULL REFERENCES {s}.page(id),
          component_type text NOT NULL,
          slot_key text NOT NULL,
          order_key integer NOT NULL,
          parent_id uuid REFERENCES {s}.page_composition(id),
          props jsonb NOT NULL
        )""",
        f"""CREATE TABLE {s}.media_asset (
          id uuid PRIMARY KEY,
          site_id uuid NOT NULL REFERENCES {s}.site(id),
          filename text NOT NULL,
          mime_type text NOT NULL,
          size_bytes bigint NOT NULL,
          content_hash text NOT NULL,
          storage_key text NOT NULL,
          UNIQUE (site_id, content_hash)
        )""",
        f"""CREATE TABLE {s}.navigation (
          id uuid PRIMARY KEY,
          site_id uuid NOT NULL REFERENCES {s}.site(id),
          key text NOT NULL,
          label text NOT NULL,
          UNIQUE (site_id, key),
          UNIQUE (site_id, id)
        )""",
        f"""CREATE TABLE {s}.navigation_item (
          id uuid PRIMARY KEY,
          site_id uuid NOT NULL,
          navigation_id uuid NOT NULL,
          parent_id uuid,
          page_id uuid,
          target_kind text NOT NULL,
          target_value text NOT NULL,
          locale text,
          position integer NOT NULL,
          UNIQUE (site_id, id),
          CONSTRAINT navigation_item_site_fk FOREIGN KEY (site_id, navigation_id)
            REFERENCES {s}.navigation(site_id, id) DEFERRABLE INITIALLY IMMEDIATE,
          CONSTRAINT navigation_item_parent_fk FOREIGN KEY (site_id, parent_id)
            REFERENCES {s}.navigation_item(site_id, id) DEFERRABLE INITIALLY IMMEDIATE,
          CONSTRAINT navigation_item_page_fk FOREIGN KEY (site_id, page_id)
            REFERENCES {s}.page(site_id, id) DEFERRABLE INITIALLY IMMEDIATE,
          CONSTRAINT navigation_item_site_locale_fk FOREIGN KEY (site_id, locale)
            REFERENCES {s}.site_locale(site_id, tag)
        )""",
        f"""CREATE TABLE {s}.redirect (
          id uuid PRIMARY KEY,
          site_id uuid NOT NULL REFERENCES {s}.site(id),
          source_route text NOT NULL,
          target text NOT NULL,
          status_code integer NOT NULL,
          locale text,
          CONSTRAINT redirect_site_locale_fk FOREIGN KEY (site_id, locale)
            REFERENCES {s}.site_locale(site_id, tag)
        )""",
        f"CREATE UNIQUE INDEX redirect_site_source_locale_idx "
        f"ON {s}.redirect (site_id, source_route, coalesce(locale, ''))",
        # Explicitly synthetic physical two-table deferred-FK cycle (P5).
        f"CREATE TABLE {s}.cycle_a (id uuid PRIMARY KEY, "
        f"site_id uuid NOT NULL REFERENCES {s}.site(id), "
        "partner_id uuid, note text)",
        f"CREATE TABLE {s}.cycle_b (id uuid PRIMARY KEY, "
        f"site_id uuid NOT NULL REFERENCES {s}.site(id), "
        "partner_id uuid, note text)",
        f"ALTER TABLE {s}.cycle_a ADD CONSTRAINT cycle_a_b_fk "
        f"FOREIGN KEY (partner_id) REFERENCES {s}.cycle_b(id) "
        "DEFERRABLE INITIALLY IMMEDIATE",
        f"ALTER TABLE {s}.cycle_b ADD CONSTRAINT cycle_b_a_fk "
        f"FOREIGN KEY (partner_id) REFERENCES {s}.cycle_a(id) "
        "DEFERRABLE INITIALLY IMMEDIATE",
        # Generic application-owned transaction probe (P6); plain table,
        # outside the COW set, so the reviewer writes ordinary app state.
        f"CREATE TABLE {s}.txn_probe (id bigserial PRIMARY KEY, note text NOT NULL)",
        f"GRANT SELECT, INSERT ON {s}.txn_probe TO {_q(reviewer_role)}",
        f"GRANT USAGE, SELECT ON SEQUENCE {s}.txn_probe_id_seq TO {_q(reviewer_role)}",
        # Seeded pre-enable canonical facts (written directly to the base
        # tables with no COW context, mirroring fixture seeding practice).
        f"INSERT INTO {s}.site_locale (id, site_id, tag, enabled, is_default) "
        f"VALUES ('{SEED_LOCALE_C}', '{SITE_C}', 'en', true, true), "
        f"('{LOCALE_EN_A}', '{SITE_A}', 'en', true, true)",
        f"INSERT INTO {s}.page (id, site_id, slug, title, locale) "
        f"VALUES ('{SEED_PAGE_C}', '{SITE_C}', 'seed-slug', 'seed-title', 'en'), "
        f"('{SEED_PAGE_P3}', '{SITE_A}', 'p3-slug', 'p3-title', 'en'), "
        f"('{SEED_PAGE_P4}', '{SITE_A}', 'p4-slug', 'p4-title', 'en')",
        f"INSERT INTO {s}.content_type (id, site_id, key) "
        f"VALUES ('{TYPE_P6}', '{SITE_A}', 'p6type')",
    )


_FK_STATE_SQL = """
SELECT c.conname, c.condeferrable, c.condeferred
FROM pg_catalog.pg_constraint c
JOIN pg_catalog.pg_class t ON t.oid = c.conrelid
JOIN pg_catalog.pg_namespace n ON n.oid = t.relnamespace
WHERE n.nspname = $1 AND t.relname = $2 AND c.contype = 'f'
ORDER BY c.conname
"""


async def _fk_state(
    conn: asyncpg.Connection[Any], schema: str, table: str
) -> dict[str, tuple[bool, bool]]:
    rows = await conn.fetch(_FK_STATE_SQL, schema, table)
    return {row[0]: (row[1], row[2]) for row in rows}


@dataclass(frozen=True, slots=True)
class WholeSessionDatabase:
    """Owned disposable multi-table COW qualification fixture.

    The fixture creates its OWN disposable database so that the setup role
    is the first (and only) deployer of the shared agentcow control objects
    in that database; foreign/shared schemas, functions and owners on other
    databases are preserved untouched.
    """

    schema: str
    admin: asyncpg.Connection[Any]
    setup: asyncpg.Connection[Any]
    runtime_pool: asyncpg.Pool[Any]
    reviewer_pool: asyncpg.Pool[Any]
    runtime_role: str
    reviewer_role: str
    enabled: tuple[str, ...]
    fk_state_before: dict[str, dict[str, tuple[bool, bool]]]
    fk_state_after: dict[str, dict[str, tuple[bool, bool]]]

    def tbl(self, table: str) -> str:
        return f"{_q(self.schema)}.{_q(table)}"

    def view(self, table: str) -> str:
        return f"{_q(self.schema)}.{_q(table)}"

    def base(self, table: str) -> str:
        return f"{_q(self.schema)}.{_q(table + '_base')}"


@pytest_asyncio.fixture(scope="session")
async def db() -> AsyncIterator[WholeSessionDatabase]:
    """Owned disposable database/schema/roles; product-mirroring enable.

    allow_deferred_fks=True and fail-closed writes mirror the actual
    product bootstrap (bootstrap/service.py enable_cow_schema(content,
    allow_deferred_fks=True, allow_unsafe_canonical_writes=False)).
    """

    cluster = {
        "host": os.environ.get("PGHOST", "127.0.0.1"),
        "port": int(os.environ.get("PGPORT", "5432")),
    }
    admin = await asyncpg.connect(
        **cluster,
        database=os.environ.get("PGDATABASE", "postgres"),
        user=os.environ.get("PGUSER", "postgres"),
        password=os.environ.get("PGPASSWORD", "qualification-admin"),
    )
    suffix = uuid.uuid4().hex[:12]
    database = f"qw8_qual_{suffix}"
    schema = f"qw8_{suffix}"
    setup_role = f"qw8_setup_{suffix}"
    runtime_role = f"qw8_runtime_{suffix}"
    reviewer_role = f"qw8_reviewer_{suffix}"
    passwords = {
        "setup": f"qw8-setup-{suffix}",
        "runtime": f"qw8-runtime-{suffix}",
        "reviewer": f"qw8-reviewer-{suffix}",
    }
    setup: asyncpg.Connection[Any] | None = None
    runtime_pool: asyncpg.Pool[Any] | None = None
    reviewer_pool: asyncpg.Pool[Any] | None = None
    try:
        await admin.execute(f"CREATE DATABASE {_q(database)}")
        for role, password in (
            (setup_role, passwords["setup"]),
            (runtime_role, passwords["runtime"]),
            (reviewer_role, passwords["reviewer"]),
        ):
            await admin.execute(
                f"CREATE ROLE {_q(role)} LOGIN PASSWORD '{password}' "
                "NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT"
            )
        await admin.execute(
            f"GRANT CREATE ON DATABASE {_q(database)} TO {_q(setup_role)}"
        )
        db_params = {**cluster, "database": database}
        setup = await asyncpg.connect(
            **db_params, user=setup_role, password=passwords["setup"]
        )
        ex = AsyncpgExecutor(setup)
        fk_state_before: dict[str, dict[str, tuple[bool, bool]]] = {}
        fk_state_after: dict[str, dict[str, tuple[bool, bool]]] = {}
        enabled: list[str] = []
        async with setup.transaction():
            await setup.execute(
                f"CREATE SCHEMA {_q(schema)} AUTHORIZATION {_q(setup_role)}"
            )
            for statement in _ddl(schema, reviewer_role):
                await setup.execute(statement)
            for table in COW_TABLES:
                fk_state_before[table] = await _fk_state(setup, schema, table)
            await deploy_cow_functions(ex)
            enabled = await enable_cow_schema(
                ex,
                schema=schema,
                exclude=EXCLUDED_TABLES,
                allow_deferred_fks=True,
                allow_unsafe_canonical_writes=False,
            )
            assert sorted(enabled) == sorted(COW_TABLES), enabled
            hardened = await harden_cow_schema(
                ex,
                schema=schema,
                runtime_roles=[runtime_role],
                reviewer_roles=[reviewer_role],
            )
            assert hardened["safe"], hardened["violations"]
            validation = await validate_cow_schema_privileges(
                ex,
                schema=schema,
                runtime_roles=[runtime_role],
                reviewer_roles=[reviewer_role],
            )
            assert validation["safe"], validation["violations"]
        for table in COW_TABLES:
            fk_state_after[table] = await _fk_state(setup, schema, table + "_base")
        # Every FK on a COW base table must be DEFERRABLE INITIALLY
        # IMMEDIATE after enable (product bootstrap parity), including the
        # composite UUID+TEXT and UUID+UUID constraints and the plain FKs
        # that enable flipped.
        for table in COW_TABLES:
            for name, (deferrable, initially_immediate) in fk_state_after[
                table
            ].items():
                assert (deferrable, initially_immediate) == (True, False), (
                    table,
                    name,
                )
        # The before-state must contain genuinely non-deferrable FKs so the
        # enable flip is a real mutation, not a no-op record.
        non_deferrable_before = [
            (table, name)
            for table in COW_TABLES
            for name, (deferrable, _) in fk_state_before[table].items()
            if not deferrable
        ]
        assert non_deferrable_before, (
            "expected plain FKs pre-enable to prove the deferrability flip"
        )
        runtime_pool = await asyncpg.create_pool(
            **db_params,
            user=runtime_role,
            password=passwords["runtime"],
            min_size=1,
            max_size=2,
        )
        reviewer_pool = await asyncpg.create_pool(
            **db_params,
            user=reviewer_role,
            password=passwords["reviewer"],
            min_size=1,
            max_size=1,
        )
        yield WholeSessionDatabase(
            schema=schema,
            admin=admin,
            setup=setup,
            runtime_pool=runtime_pool,
            reviewer_pool=reviewer_pool,
            runtime_role=runtime_role,
            reviewer_role=reviewer_role,
            enabled=tuple(sorted(enabled)),
            fk_state_before=fk_state_before,
            fk_state_after=fk_state_after,
        )
    finally:
        for pool in (runtime_pool, reviewer_pool):
            if pool is not None:
                await pool.close()
        if setup is not None:
            await setup.close()
        # DROP OWNED is database-local: the schema/agentcow objects live in
        # the owned new database, so clean them there via an owned admin
        # connection before the roles can be dropped cluster-wide.
        db_admin = await asyncpg.connect(
            **db_params,
            user=os.environ.get("PGUSER", "postgres"),
            password=os.environ.get("PGPASSWORD", "qualification-admin"),
        )
        try:
            for role in (reviewer_role, runtime_role, setup_role):
                await db_admin.execute(f"DROP OWNED BY {_q(role)} CASCADE")
        finally:
            await db_admin.close()
        for role in (reviewer_role, runtime_role, setup_role):
            await admin.execute(f"DROP ROLE IF EXISTS {_q(role)}")
        await admin.execute(f"DROP DATABASE IF EXISTS {_q(database)}")
        await admin.close()


async def _assert_rows(
    db: WholeSessionDatabase,
    table: str,
    ids: list[uuid.UUID],
    expected: list[tuple[Any, ...]],
) -> None:
    """Exact canonical row/value oracle on the owned base table."""
    placeholders = ", ".join(f"${index}" for index in range(1, len(ids) + 1))
    rows = await db.setup.fetch(
        f"SELECT {ORACLE_COLUMNS[table]} FROM {db.base(table)} "
        f"WHERE id IN ({placeholders}) ORDER BY id",
        *ids,
    )
    assert [tuple(row) for row in rows] == sorted(expected, key=lambda item: item[0]), (
        table
    )


async def _assert_absent(
    db: WholeSessionDatabase, table: str, ids: list[uuid.UUID]
) -> None:
    placeholders = ", ".join(f"${index}" for index in range(1, len(ids) + 1))
    count = await db.setup.fetchval(
        f"SELECT count(*) FROM {db.base(table)} WHERE id IN ({placeholders})",
        *ids,
    )
    assert count == 0, table


def _lock_package_block(lock_text: str, package_name: str) -> str:
    lines = lock_text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line.startswith("[[package]]"):
            start = index
        elif start is not None and line.startswith("name = "):
            if line.strip() == f'name = "{package_name}"':
                end = len(lines)
                for follow in range(index + 1, len(lines)):
                    if lines[follow].startswith("[[package]]"):
                        end = follow
                        break
                return "\n".join(lines[start:end])
            start = None
    raise AssertionError(f"package {package_name!r} not found in uv.lock")


async def _seeded_controls(db: WholeSessionDatabase) -> dict[str, Any]:
    locale_c = await db.setup.fetchrow(
        f"SELECT id, site_id, tag, enabled, is_default "
        f"FROM {db.tbl('site_locale')} WHERE id = '{SEED_LOCALE_C}'"
    )
    page_c = await db.setup.fetchrow(
        f"SELECT id, site_id, slug, title, locale, parent_id "
        f"FROM {db.tbl('page')} WHERE id = '{SEED_PAGE_C}'"
    )
    return {
        "site_count": await db.setup.fetchval(f"SELECT count(*) FROM {db.tbl('site')}"),
        "locale_c": tuple(locale_c) if locale_c is not None else None,
        "page_c": tuple(page_c) if page_c is not None else None,
        "probe_count": await db.setup.fetchval(
            f"SELECT count(*) FROM {db.tbl('txn_probe')}"
        ),
    }


def test_p1_frozen_020_anchors_are_public_and_uv_lock_pinned() -> None:
    assert FOUNDATION_VERSION == "0.2.0"
    assert importlib.metadata.version(FOUNDATION_DISTRIBUTION) == FOUNDATION_VERSION
    metadata = importlib.metadata.metadata(FOUNDATION_DISTRIBUTION)
    assert metadata["Name"] == "agent-cow-postgresql"
    assert metadata["Version"] == "0.2.0"
    # The installed 0.2.0 distribution exposes MIT as the SPDX license
    # expression; the legacy `License` field is unset (honestly recorded).
    assert metadata.get("License-Expression") == "MIT"
    assert metadata.get("License") is None
    # Every qualified public API name is present and usable on the
    # product's re-export surface (no wrapper, no private surface).
    product = importlib.import_module("slaif_agent_site.agent_state.foundation")
    for name in QUALIFIED_PUBLIC_API:
        target = getattr(product, name)
        assert callable(target) or isinstance(target, type), name
    block = _lock_package_block(
        (REPO_ROOT / "uv.lock").read_text(encoding="utf-8"),
        FOUNDATION_DISTRIBUTION,
    )
    assert 'version = "0.2.0"' in block
    assert 'source = { registry = "https://pypi.org/simple" }' in block
    assert f'hash = "sha256:{WHEEL_SHA256}", size = {WHEEL_SIZE}' in block
    assert f'hash = "sha256:{SDIST_SHA256}", size = {SDIST_SIZE}' in block
    assert "git" not in block
    assert "editable" not in block
    assert "directory" not in block


async def test_p2_mixed_table_whole_session_promotion(
    db: WholeSessionDatabase,
) -> None:
    # Explicitly known operation IDs; one operation (op_multi_table)
    # touches four tables.
    op_locale_page = uuid.uuid4()
    op_model_field_item = uuid.uuid4()
    op_translation_relation = uuid.uuid4()
    op_nav_composition = uuid.uuid4()
    op_multi_table = uuid.uuid4()
    expected_ops = {
        op_locale_page,
        op_model_field_item,
        op_translation_relation,
        op_nav_composition,
        op_multi_table,
    }
    session_a = uuid.uuid4()
    session_b = uuid.uuid4()
    op_b = uuid.uuid4()
    locale_a, page_a = uuid.uuid4(), uuid.uuid4()
    type_b, field_b = uuid.uuid4(), uuid.uuid4()
    item_b1, item_b2 = uuid.uuid4(), uuid.uuid4()
    trans_b, rel_b = uuid.uuid4(), uuid.uuid4()
    nav_a, nav_a1, nav_a2 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    comp_a1, comp_a2 = uuid.uuid4(), uuid.uuid4()
    media_a, redirect_a = uuid.uuid4(), uuid.uuid4()
    locale_b, page_b = uuid.uuid4(), uuid.uuid4()
    type_b4, item_b3, trans_b3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    view = db.view

    untouched_before = await _seeded_controls(db)

    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session_a, operation_id=op_locale_page
    ) as cow:
        await cow.execute(
            f"INSERT INTO {view('site_locale')} "
            f"(id, site_id, tag, enabled, is_default) "
            f"VALUES ('{locale_a}', '{SITE_A}', 'de', true, false)"
        )
        await cow.execute(
            f"INSERT INTO {view('page')} (id, site_id, slug, title, locale) "
            f"VALUES ('{page_a}', '{SITE_A}', 'a-slug', 'A', 'de')"
        )
        await cow.set_operation(op_model_field_item)
        await cow.execute(
            f"INSERT INTO {view('content_type')} (id, site_id, key) "
            f"VALUES ('{type_b}', '{SITE_B}', 'article')"
        )
        await cow.execute(
            f"INSERT INTO {view('field_definition')} "
            f"(id, site_id, type_id, key) "
            f"VALUES ('{field_b}', '{SITE_B}', '{type_b}', 'body')"
        )
        await cow.execute(
            f"INSERT INTO {view('content_item')} "
            f"(id, site_id, type_id, slug, values) "
            f"VALUES ('{item_b1}', '{SITE_B}', '{type_b}', 'item-1', '{{}}')"
        )
        await cow.execute(
            f"INSERT INTO {view('content_item')} "
            f"(id, site_id, type_id, slug, values) "
            f"VALUES ('{item_b2}', '{SITE_B}', '{type_b}', 'item-2', '{{}}')"
        )
        await cow.set_operation(op_translation_relation)
        await cow.execute(
            f"INSERT INTO {view('content_item_translation')} "
            f"(id, site_id, item_id, locale, localized_values) "
            f"VALUES ('{trans_b}', '{SITE_B}', '{item_b1}', 'en', '{{}}')"
        )
        await cow.execute(
            f"INSERT INTO {view('item_relation')} "
            f"(id, site_id, source_item_id, field_definition_id, "
            f"target_item_id, position) "
            f"VALUES ('{rel_b}', '{SITE_B}', '{item_b1}', '{field_b}', "
            f"'{item_b2}', 0)"
        )
        await cow.set_operation(op_nav_composition)
        await cow.execute(
            f"INSERT INTO {view('navigation')} (id, site_id, key, label) "
            f"VALUES ('{nav_a}', '{SITE_A}', 'main', 'Main')"
        )
        await cow.execute(
            f"INSERT INTO {view('navigation_item')} "
            f"(id, site_id, navigation_id, parent_id, page_id, target_kind, "
            f"target_value, locale, position) "
            f"VALUES ('{nav_a1}', '{SITE_A}', '{nav_a}', NULL, '{page_a}', "
            f"'PAGE', '{page_a}', 'de', 0)"
        )
        await cow.execute(
            f"INSERT INTO {view('navigation_item')} "
            f"(id, site_id, navigation_id, parent_id, page_id, target_kind, "
            f"target_value, locale, position) "
            f"VALUES ('{nav_a2}', '{SITE_A}', '{nav_a}', '{nav_a1}', "
            f"'{page_a}', 'PAGE', '{page_a}', 'de', 1)"
        )
        await cow.execute(
            f"INSERT INTO {view('page_composition')} "
            f"(id, site_id, page_id, component_type, slot_key, order_key, "
            f"parent_id, props) "
            f"VALUES ('{comp_a1}', '{SITE_A}', '{page_a}', 'hero', 'default', "
            f"0, NULL, '{{}}')"
        )
        await cow.execute(
            f"INSERT INTO {view('page_composition')} "
            f"(id, site_id, page_id, component_type, slot_key, order_key, "
            f"parent_id, props) "
            f"VALUES ('{comp_a2}', '{SITE_A}', '{page_a}', 'body', 'default', "
            f"1, '{comp_a1}', '{{}}')"
        )
        await cow.set_operation(op_multi_table)
        await cow.execute(
            f"INSERT INTO {view('media_asset')} "
            f"(id, site_id, filename, mime_type, size_bytes, content_hash, "
            f"storage_key) "
            f"VALUES ('{media_a}', '{SITE_A}', 'a.bin', "
            f"'application/octet-stream', 3, 'hash-a', 'key-a')"
        )
        await cow.execute(
            f"INSERT INTO {view('redirect')} "
            f"(id, site_id, source_route, target, status_code, locale) "
            f"VALUES ('{redirect_a}', '{SITE_A}', '/a-old', '/a-new', 302, 'de')"
        )
        await cow.execute(
            f"INSERT INTO {view('site_locale')} "
            f"(id, site_id, tag, enabled, is_default) "
            f"VALUES ('{locale_b}', '{SITE_B}', 'fr', true, false)"
        )
        await cow.execute(
            f"INSERT INTO {view('page')} (id, site_id, slug, title, locale) "
            f"VALUES ('{page_b}', '{SITE_B}', 'b-slug', 'B', 'fr')"
        )

    # Independent second session while A is pending: A's rows are invisible
    # to B, and B's own multi-table operation stays independent.
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session_b, operation_id=op_b
    ) as cow_b:
        assert (
            await cow_b.execute(
                f"SELECT count(*) FROM {view('page')} WHERE id = '{page_a}'"
            )
        ) == [(0,)]
        assert (
            await cow_b.execute(
                f"SELECT count(*) FROM {view('content_item')} WHERE id = '{item_b1}'"
            )
        ) == [(0,)]
        await cow_b.execute(
            f"INSERT INTO {view('content_type')} (id, site_id, key) "
            f"VALUES ('{type_b4}', '{SITE_B}', 'btype')"
        )
        await cow_b.execute(
            f"INSERT INTO {view('content_item')} "
            f"(id, site_id, type_id, slug, values) "
            f"VALUES ('{item_b3}', '{SITE_B}', '{type_b4}', 'b-item', '{{}}')"
        )
        await cow_b.execute(
            f"INSERT INTO {view('content_item_translation')} "
            f"(id, site_id, item_id, locale, localized_values) "
            f"VALUES ('{trans_b3}', '{SITE_B}', '{item_b3}', 'en', '{{}}')"
        )

    # Pre-approval: NONE of the known pending inserts (A's or B's) exists
    # in canonical state yet, and the untouched controls are unchanged.
    await _assert_absent(db, "site_locale", [locale_a, locale_b])
    await _assert_absent(db, "page", [page_a, page_b])
    await _assert_absent(db, "content_type", [type_b, type_b4])
    await _assert_absent(db, "field_definition", [field_b])
    await _assert_absent(db, "content_item", [item_b1, item_b2, item_b3])
    await _assert_absent(db, "content_item_translation", [trans_b, trans_b3])
    await _assert_absent(db, "item_relation", [rel_b])
    await _assert_absent(db, "navigation", [nav_a])
    await _assert_absent(db, "navigation_item", [nav_a1, nav_a2])
    await _assert_absent(db, "page_composition", [comp_a1, comp_a2])
    await _assert_absent(db, "media_asset", [media_a])
    await _assert_absent(db, "redirect", [redirect_a])
    assert await _seeded_controls(db) == untouched_before

    # A's pending operation set is exactly the five known unique IDs.
    expected_tables = tuple(
        sorted(
            (
                "site_locale",
                "page",
                "content_type",
                "field_definition",
                "content_item",
                "content_item_translation",
                "item_relation",
                "navigation",
                "navigation_item",
                "page_composition",
                "media_asset",
                "redirect",
            ),
            key=lambda table: f"{table}_changes",
        )
    )
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        ops_a = await reviewer.operations(session_a, schema=db.schema)
        assert set(ops_a) == expected_ops
        assert len(ops_a) == len(expected_ops) == 5
        result_a = await reviewer.commit_session(
            session_a, schema=db.schema, defer_fk_constraints=True
        )
        # In-scope proof: after promotion returns, the SAME reviewer body
        # still sees no pending operations for A.
        assert await reviewer.operations(session_a, schema=db.schema) == []
    assert result_a.session_id == session_a
    assert result_a.schema == db.schema
    assert result_a.no_op is False
    assert result_a.has_pending_operations is False
    assert result_a.conflict_policy == "error"
    assert set(result_a.committed_operations) == expected_ops
    assert len(result_a.committed_operations) == 5
    assert result_a.committed_tables == expected_tables

    # Independent canonical row/value oracles after scope exit.
    await _assert_rows(
        db, "site_locale", [locale_a], [(locale_a, SITE_A, "de", True, False)]
    )
    await _assert_rows(
        db, "page", [page_a], [(page_a, SITE_A, "a-slug", "A", "de", None)]
    )
    await _assert_rows(db, "content_type", [type_b], [(type_b, SITE_B, "article")])
    await _assert_rows(
        db, "field_definition", [field_b], [(field_b, SITE_B, type_b, "body")]
    )
    await _assert_rows(
        db,
        "content_item",
        [item_b1, item_b2],
        [
            (item_b1, SITE_B, type_b, "item-1", {}),
            (item_b2, SITE_B, type_b, "item-2", {}),
        ],
    )
    await _assert_rows(
        db,
        "content_item_translation",
        [trans_b],
        [
            (trans_b, SITE_B, item_b1, "en", {}),
        ],
    )
    await _assert_rows(
        db,
        "item_relation",
        [rel_b],
        [
            (rel_b, SITE_B, item_b1, field_b, item_b2, 0),
        ],
    )
    await _assert_rows(db, "navigation", [nav_a], [(nav_a, SITE_A, "main", "Main")])
    await _assert_rows(
        db,
        "navigation_item",
        [nav_a1, nav_a2],
        [
            (nav_a1, SITE_A, nav_a, None, page_a, "PAGE", str(page_a), "de", 0),
            (nav_a2, SITE_A, nav_a, nav_a1, page_a, "PAGE", str(page_a), "de", 1),
        ],
    )
    await _assert_rows(
        db,
        "page_composition",
        [comp_a1, comp_a2],
        [
            (comp_a1, SITE_A, page_a, "hero", "default", 0, None, {}),
            (comp_a2, SITE_A, page_a, "body", "default", 1, comp_a1, {}),
        ],
    )
    await _assert_rows(
        db,
        "media_asset",
        [media_a],
        [
            (
                media_a,
                SITE_A,
                "a.bin",
                "application/octet-stream",
                3,
                "hash-a",
                "key-a",
            ),
        ],
    )
    await _assert_rows(
        db,
        "redirect",
        [redirect_a],
        [
            (redirect_a, SITE_A, "/a-old", "/a-new", 302, "de"),
        ],
    )
    await _assert_rows(
        db, "site_locale", [locale_b], [(locale_b, SITE_B, "fr", True, False)]
    )
    await _assert_rows(
        db, "page", [page_b], [(page_b, SITE_B, "b-slug", "B", "fr", None)]
    )
    # B's rows are NOT promoted by A's whole-session commit:
    await _assert_absent(db, "content_type", [type_b4])
    await _assert_absent(db, "content_item", [item_b3])
    await _assert_absent(db, "content_item_translation", [trans_b3])
    # Untouched canonical/other-site facts unchanged:
    assert await _seeded_controls(db) == untouched_before

    # Fresh public reviewer: A has no pending operations; B's pending set
    # is preserved untouched by A's promotion.
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        assert await reviewer.operations(session_a, schema=db.schema) == []
        assert set(await reviewer.operations(session_b, schema=db.schema)) == {op_b}

    # B promotes on top of A's committed base.
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        result_b = await reviewer.commit_session(
            session_b, schema=db.schema, defer_fk_constraints=True
        )
        # In-scope proof for B as well, before scope exit.
        assert await reviewer.operations(session_b, schema=db.schema) == []
    assert result_b.no_op is False
    assert result_b.has_pending_operations is False
    assert set(result_b.committed_operations) == {op_b}
    await _assert_rows(db, "content_type", [type_b4], [(type_b4, SITE_B, "btype")])
    await _assert_rows(
        db,
        "content_item",
        [item_b3],
        [
            (item_b3, SITE_B, type_b4, "b-item", {}),
        ],
    )
    await _assert_rows(
        db,
        "content_item_translation",
        [trans_b3],
        [
            (trans_b3, SITE_B, item_b3, "en", {}),
        ],
    )
    assert await _seeded_controls(db) == untouched_before
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        assert await reviewer.operations(session_b, schema=db.schema) == []


async def test_p3_empty_session_is_no_op(db: WholeSessionDatabase) -> None:
    session = uuid.uuid4()
    async with asyncpg_cow_session(db.runtime_pool, session_id=session) as cow:
        assert (await cow.execute("SELECT 1")) == [(1,)]
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        assert await reviewer.operations(session, schema=db.schema) == []
        result = await reviewer.commit_session(session, schema=db.schema)
    assert result.no_op is True
    assert result.committed_tables == ()
    assert result.committed_operations == ()
    assert result.has_pending_operations is False


async def test_p3_same_value_update_preserves_canonical(
    db: WholeSessionDatabase,
) -> None:
    session, op = uuid.uuid4(), uuid.uuid4()
    before = await db.setup.fetchrow(
        f"SELECT id, site_id, slug, title, locale, parent_id "
        f"FROM {db.tbl('page')} WHERE id = '{SEED_PAGE_P3}'"
    )
    assert before is not None
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session, operation_id=op
    ) as cow:
        await cow.execute(
            f"UPDATE {db.view('page')} SET slug = 'p3-slug' WHERE id = '{SEED_PAGE_P3}'"
        )
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        # A same-value write still records a pending operation (the row is
        # touched), but promotion must leave the canonical row identical.
        assert set(await reviewer.operations(session, schema=db.schema)) == {op}
        result = await reviewer.commit_session(session, schema=db.schema)
    assert result.no_op is False
    assert result.has_pending_operations is False
    after = await db.setup.fetchrow(
        f"SELECT id, site_id, slug, title, locale, parent_id "
        f"FROM {db.tbl('page')} WHERE id = '{SEED_PAGE_P3}'"
    )
    assert tuple(after) == tuple(before)
    await _assert_rows(db, "page", [SEED_PAGE_P3], [tuple(before)])


async def test_p3_repeated_writes_coalesce_to_last_value(
    db: WholeSessionDatabase,
) -> None:
    session, op1, op2 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session, operation_id=op1
    ) as cow:
        await cow.execute(
            f"UPDATE {db.view('page')} SET slug = 'p3-first' "
            f"WHERE id = '{SEED_PAGE_P3}'"
        )
        await cow.set_operation(op2)
        await cow.execute(
            f"UPDATE {db.view('page')} SET slug = 'p3-second' "
            f"WHERE id = '{SEED_PAGE_P3}'"
        )
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        # Both operations stay in the exact public pending set; the row
        # semantics are last-write-wins through the overlay.
        assert set(await reviewer.operations(session, schema=db.schema)) == {op1, op2}
        result = await reviewer.commit_session(session, schema=db.schema)
    assert result.no_op is False
    assert result.has_pending_operations is False
    await _assert_rows(
        db,
        "page",
        [SEED_PAGE_P3],
        [(SEED_PAGE_P3, SITE_A, "p3-second", "p3-title", "en", None)],
    )
    # Positive control: a different row promoted in the same session.
    session2, op3, keep_page = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session2, operation_id=op3
    ) as cow:
        await cow.execute(
            f"INSERT INTO {db.view('page')} (id, site_id, slug, title, locale) "
            f"VALUES ('{keep_page}', '{SITE_A}', 'p3-control', 'P3C', 'en')"
        )
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        result2 = await reviewer.commit_session(session2, schema=db.schema)
    assert result2.no_op is False
    await _assert_rows(
        db,
        "page",
        [keep_page],
        [(keep_page, SITE_A, "p3-control", "P3C", "en", None)],
    )


async def test_p3_insert_delete_net_zero(db: WholeSessionDatabase) -> None:
    session, op1, op2, op3 = (
        uuid.uuid4(),
        uuid.uuid4(),
        uuid.uuid4(),
        uuid.uuid4(),
    )
    gone_page, kept_page = uuid.uuid4(), uuid.uuid4()
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session, operation_id=op1
    ) as cow:
        await cow.execute(
            f"INSERT INTO {db.view('page')} (id, site_id, slug, title, locale) "
            f"VALUES ('{gone_page}', '{SITE_A}', 'p3d-gone', 'Gone', 'en')"
        )
        await cow.set_operation(op2)
        await cow.execute(f"DELETE FROM {db.view('page')} WHERE id = '{gone_page}'")
        await cow.set_operation(op3)
        await cow.execute(
            f"INSERT INTO {db.view('page')} (id, site_id, slug, title, locale) "
            f"VALUES ('{kept_page}', '{SITE_A}', 'p3d-kept', 'Kept', 'en')"
        )
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        # Insert + delete of the same row still record both operations.
        assert set(await reviewer.operations(session, schema=db.schema)) == {
            op1,
            op2,
            op3,
        }
        result = await reviewer.commit_session(session, schema=db.schema)
    assert result.no_op is False
    assert result.has_pending_operations is False
    await _assert_absent(db, "page", [gone_page])
    await _assert_rows(
        db,
        "page",
        [kept_page],
        [(kept_page, SITE_A, "p3d-kept", "Kept", "en", None)],
    )


async def test_p4_row_conflict_refusal_preserves_pending(
    db: WholeSessionDatabase,
) -> None:
    page = SEED_PAGE_P4
    sess_a, sess_b = uuid.uuid4(), uuid.uuid4()
    op_a, op_b = uuid.uuid4(), uuid.uuid4()
    # BOTH competing sessions first-touch the same original row BEFORE A
    # commits.
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=sess_a, operation_id=op_a
    ) as cow:
        await cow.execute(
            f"UPDATE {db.view('page')} SET title = 'title-A' WHERE id = '{page}'"
        )
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=sess_b, operation_id=op_b
    ) as cow:
        await cow.execute(
            f"UPDATE {db.view('page')} SET title = 'title-B' WHERE id = '{page}'"
        )
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        assert set(await reviewer.operations(sess_a, schema=db.schema)) == {op_a}
        result_a = await reviewer.commit_session(sess_a, schema=db.schema)
    assert result_a.no_op is False
    await _assert_rows(
        db, "page", [page], [(page, SITE_A, "p4-slug", "title-A", "en", None)]
    )
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        conflicts = await reviewer.conflicts(sess_b, schema=db.schema)
        assert len(conflicts) == 1
        conflict = conflicts[0]
        assert conflict["conflict_kind"] == "BASE_ROW_CHANGED"
        assert conflict["table_name"] == "page"
        assert conflict["primary_key"] == {"id": page}
        assert conflict["operation_id"] == op_b
        # `order` is the frozen foundation's authoritative operation order:
        # a per-schema _cow_operation_order_seq sequence value (1-based
        # bigint). This shared session schema has already consumed sequence
        # values in earlier tests, so pin the public 1-based invariant
        # rather than an execution-order-dependent absolute position.
        assert isinstance(conflict["order"], int)
        assert conflict["order"] >= 1
        with pytest.raises(CowConflictError) as exc_info:
            await reviewer.commit_session(sess_b, schema=db.schema)
    assert exc_info.value.session_id == sess_b
    assert exc_info.value.schema == db.schema
    assert exc_info.value.conflicts == tuple(conflicts)
    assert exc_info.value.sqlstate == "40001"
    # Zero B effects promoted; B's pending change is retained.
    await _assert_rows(
        db, "page", [page], [(page, SITE_A, "p4-slug", "title-A", "en", None)]
    )
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        assert set(await reviewer.operations(sess_b, schema=db.schema)) == {op_b}


async def test_p4_schema_conflict_refusal_restores_and_promotes(
    foundation_database: FoundationDatabase,
) -> None:
    session, op = uuid.uuid4(), uuid.uuid4()
    schema = foundation_database.schema
    relation = foundation_database.relation
    canonical = foundation_database.canonical_relation
    before = await foundation_database.setup.fetchrow(
        f"SELECT id, title FROM {canonical} WHERE id = 1"
    )
    assert before is not None
    async with asyncpg_cow_session(
        foundation_database.runtime_pool, session_id=session, operation_id=op
    ) as cow:
        await cow.execute(f"UPDATE {relation} SET title = 'qw8-probe' WHERE id = 1")
    index = "qw8_probe_idx"
    try:
        # Index-only DDL is the benign positive control: it must NOT drift
        # the base fingerprint.
        async with foundation_database.setup.transaction():
            await foundation_database.setup.execute(
                f"CREATE INDEX {index} ON {canonical} (title)"
            )
        async with asyncpg_cow_reviewer(foundation_database.reviewer_pool) as reviewer:
            assert await reviewer.conflicts(session, schema=schema) == []
        # Genuine column-default fingerprint drift on the OWNED canonical
        # base (the frozen signature includes pg_get_expr(column default)).
        await foundation_database.setup.execute(
            f"ALTER TABLE {canonical} "
            f"ALTER COLUMN title SET DEFAULT 'qw8_probe_default'"
        )
        async with asyncpg_cow_reviewer(foundation_database.reviewer_pool) as reviewer:
            conflicts = await reviewer.conflicts(session, schema=schema)
            assert len(conflicts) == 1
            conflict = conflicts[0]
            assert conflict["conflict_kind"] == "BASE_SCHEMA_CHANGED"
            assert conflict["table_name"] == "items"
            assert conflict["primary_key"] == {"id": 1}
            assert conflict["operation_id"] == op
            # Fresh function-scoped database/schema: this is the first COW
            # operation, so the 1-based _cow_operation_order_seq value is
            # exactly 1.
            assert conflict["order"] == 1
            with pytest.raises(CowConflictError) as exc_info:
                await reviewer.commit_session(session, schema=schema)
        assert exc_info.value.session_id == session
        assert exc_info.value.conflicts == tuple(conflicts)
    finally:
        # Restore the original real fingerprint exactly.
        await foundation_database.setup.execute(
            f"ALTER TABLE {canonical} ALTER COLUMN title DROP DEFAULT"
        )
        await foundation_database.setup.execute(f"DROP INDEX IF EXISTS {index}")
    # Zero promoted effects while refused:
    after = await foundation_database.setup.fetchrow(
        f"SELECT id, title FROM {canonical} WHERE id = 1"
    )
    assert tuple(after) == tuple(before)
    # Pending retained; after restoration the same pending operation
    # promotes cleanly.
    async with asyncpg_cow_reviewer(foundation_database.reviewer_pool) as reviewer:
        assert set(await reviewer.operations(session, schema=schema)) == {op}
        result = await reviewer.commit_session(session, schema=schema)
    assert result.no_op is False
    assert result.has_pending_operations is False
    assert (
        await foundation_database.setup.fetchval(
            f"SELECT title FROM {canonical} WHERE id = 1"
        )
        == "qw8-probe"
    )


async def test_p5_deferred_cycle_commit_succeeds(db: WholeSessionDatabase) -> None:
    # The explicitly synthetic physical two-table deferred-FK cycle:
    # row-level cross-references that are valid only in the FINAL state.
    session, op = uuid.uuid4(), uuid.uuid4()
    a_id, b_id = uuid.uuid4(), uuid.uuid4()
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session, operation_id=op
    ) as cow:
        await cow.execute(
            f"INSERT INTO {db.view('cycle_a')} "
            f"(id, site_id, partner_id, note) "
            f"VALUES ('{a_id}', '{SITE_A}', '{b_id}', 'a')"
        )
        await cow.execute(
            f"INSERT INTO {db.view('cycle_b')} "
            f"(id, site_id, partner_id, note) "
            f"VALUES ('{b_id}', '{SITE_A}', '{a_id}', 'b')"
        )
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        result = await reviewer.commit_session(
            session, schema=db.schema, defer_fk_constraints=True
        )
    assert result.no_op is False
    assert result.has_pending_operations is False
    assert result.committed_tables == ("cycle_a", "cycle_b")
    assert set(result.committed_operations) == {op}
    await _assert_rows(db, "cycle_a", [a_id], [(a_id, SITE_A, b_id, "a")])
    await _assert_rows(db, "cycle_b", [b_id], [(b_id, SITE_A, a_id, "b")])


async def test_p5_nondeferred_cycle_refused_before_promotion(
    db: WholeSessionDatabase,
) -> None:
    session, op = uuid.uuid4(), uuid.uuid4()
    a_id, b_id = uuid.uuid4(), uuid.uuid4()
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session, operation_id=op
    ) as cow:
        await cow.execute(
            f"INSERT INTO {db.view('cycle_a')} "
            f"(id, site_id, partner_id, note) "
            f"VALUES ('{a_id}', '{SITE_A}', '{b_id}', 'a')"
        )
        await cow.execute(
            f"INSERT INTO {db.view('cycle_b')} "
            f"(id, site_id, partner_id, note) "
            f"VALUES ('{b_id}', '{SITE_A}', '{a_id}', 'b')"
        )
    # The frozen SDK raises its public CowPromotionRequestError (a
    # ValueError) for an unorderable FK cycle; the class is recorded by
    # exact name because it is intentionally NOT part of the product's
    # qualified re-export boundary, which this module must not widen.
    with pytest.raises(ValueError) as exc_info:
        async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
            await reviewer.commit_session(session, schema=db.schema)
    assert type(exc_info.value).__name__ == "CowPromotionRequestError"
    assert not isinstance(exc_info.value, CowConflictError)
    assert "Cycle detected" in str(exc_info.value)
    assert "defer_fk_constraints=True" in str(exc_info.value)
    # Nothing was promoted; the pending operation is retained.
    await _assert_absent(db, "cycle_a", [a_id])
    await _assert_absent(db, "cycle_b", [b_id])
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        assert set(await reviewer.operations(session, schema=db.schema)) == {op}


async def test_p5_dangling_deferred_state_refused_at_immediate_stage(
    db: WholeSessionDatabase,
) -> None:
    # defer_fk_constraints=True with a genuinely invalid FINAL FK state:
    # the refusal surfaces at the promotion's deferred final-state check
    # (SET CONSTRAINTS ALL IMMEDIATE inside commit_session, BEFORE the
    # reviewer COMMIT) and the whole promotion rolls back.
    session, op = uuid.uuid4(), uuid.uuid4()
    a_id, b_id, missing = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session, operation_id=op
    ) as cow:
        await cow.execute(
            f"INSERT INTO {db.view('cycle_a')} "
            f"(id, site_id, partner_id, note) "
            f"VALUES ('{a_id}', '{SITE_A}', '{b_id}', 'a')"
        )
        await cow.execute(
            f"INSERT INTO {db.view('cycle_b')} "
            f"(id, site_id, partner_id, note) "
            f"VALUES ('{b_id}', '{SITE_A}', '{missing}', 'b')"
        )
    with pytest.raises(asyncpg.ForeignKeyViolationError) as exc_info:
        async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
            await reviewer.commit_session(
                session, schema=db.schema, defer_fk_constraints=True
            )
    assert exc_info.value.sqlstate == "23503"
    await _assert_absent(db, "cycle_a", [a_id])
    await _assert_absent(db, "cycle_b", [b_id])
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        assert set(await reviewer.operations(session, schema=db.schema)) == {op}


async def test_p5_dangling_composite_fk_deferred_refused(
    db: WholeSessionDatabase,
) -> None:
    # Same final-state refusal on ACTUAL product geometry: a page whose
    # composite (site_id, locale) reference has no site_locale row.
    session, op = uuid.uuid4(), uuid.uuid4()
    page_x = uuid.uuid4()
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session, operation_id=op
    ) as cow:
        await cow.execute(
            f"INSERT INTO {db.view('page')} (id, site_id, slug, title, locale) "
            f"VALUES ('{page_x}', '{SITE_A}', 'zz-slug', 'ZZ', 'zz')"
        )
    with pytest.raises(asyncpg.ForeignKeyViolationError) as exc_info:
        async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
            await reviewer.commit_session(
                session, schema=db.schema, defer_fk_constraints=True
            )
    assert exc_info.value.sqlstate == "23503"
    await _assert_absent(db, "page", [page_x])
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        assert set(await reviewer.operations(session, schema=db.schema)) == {op}


async def test_p5_write_time_refusal_is_distinct(db: WholeSessionDatabase) -> None:
    # WRITE-time refusal: a canonical write WITHOUT the COW context is
    # refused immediately at the write statement (fail-closed trigger,
    # sqlstate 22023). This is distinct from the promotion-time refusals
    # above; a rejected write does not qualify the promotion path.
    async with db.runtime_pool.acquire() as raw:
        with pytest.raises(asyncpg.PostgresError) as exc_info:
            await raw.execute(
                f"INSERT INTO {db.view('site_locale')} "
                f"(id, site_id, tag, enabled, is_default) "
                f"VALUES ('{uuid.uuid4()}', '{SITE_A}', 'xx', true, false)"
            )
    assert exc_info.value.sqlstate == "22023"


async def _run_p6_window(
    db: WholeSessionDatabase,
    outcome: str,
    session: uuid.UUID,
    op: uuid.UUID,
    item: uuid.UUID,
) -> None:
    entered = asyncio.Event()
    release = asyncio.Event()
    window: dict[str, Any] = {"pid": None}

    async def reviewer_body() -> None:
        async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
            # Same qualified deferred whole-session mechanism as P2:
            result = await reviewer.commit_session(
                session, schema=db.schema, defer_fk_constraints=True
            )
            assert result.no_op is False
            assert result.has_pending_operations is False
            window["pid"] = await reviewer.native.fetchval("SELECT pg_backend_pid()")
            # Ordinary application state written INSIDE the reviewer
            # transaction (generic probe table, not a COW table):
            await reviewer.native.execute(
                f"INSERT INTO {db.tbl('txn_probe')} (note) VALUES ($1)",
                f"qw8-{outcome}",
            )
            # Real uncommitted promotion effect, proven in-transaction on
            # the owned reviewer connection (view SELECT is granted):
            assert (
                await reviewer.native.fetchval(
                    f"SELECT count(*) FROM {db.view('content_item')} "
                    f"WHERE id = '{item}'"
                )
            ) == 1
            # Independent owned connection: the effect is NOT committed.
            assert (
                await db.setup.fetchval(
                    f"SELECT count(*) FROM {db.tbl('content_item')} WHERE id = '{item}'"
                )
            ) == 0
            entered.set()
            await release.wait()
            if outcome == "postcondition":
                raise RuntimeError("qw8 postcondition refusal after promotion")
            await reviewer.native.fetchval("SELECT 1")

    task = asyncio.create_task(reviewer_body())
    try:
        await asyncio.wait_for(entered.wait(), timeout=30)
    except BaseException:
        # Barrier failure/timeout before the window opened: unconditionally
        # cancel and await the exact owned task so no reviewer task or
        # transaction can outlive the window, then preserve the first
        # failure (the child's exception when the child failed first,
        # otherwise the barrier failure itself).
        task.cancel()
        child_failure: BaseException | None = None
        try:
            await task
        except BaseException as child_exc:
            child_failure = child_exc
        if child_failure is not None and not task.cancelled():
            # The child failed before the barrier; its exception is the
            # original first failure (the timeout is derivative):
            raise child_failure from None
        raise
    try:
        pid = window["pid"]
        assert pid is not None
        # In-window observation from the separate owned admin connection:
        state = await db.admin.fetchval(
            "SELECT state FROM pg_stat_activity WHERE pid = $1", pid
        )
        assert state == "idle in transaction"
        locks = await db.admin.fetchval(
            "SELECT count(*) FROM pg_locks WHERE pid = $1", pid
        )
        assert locks > 0
        if outcome == "postcondition":
            release.set()
            with pytest.raises(RuntimeError, match="qw8 postcondition refusal"):
                await task
        elif outcome == "cancel":
            # Positive cancellation proof: the exact owned task must
            # actually raise CancelledError and end in the cancelled state.
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert task.cancelled() is True
        else:
            assert (
                await db.admin.fetchval("SELECT pg_terminate_backend($1)", pid) is True
            )
            release.set()
            with pytest.raises(
                (asyncpg.InterfaceError, asyncpg.PostgresConnectionError)
            ):
                await task
    finally:
        # No window-phase failure (driver assertion, admin query, or
        # outcome handling) may leave the exact owned task running or
        # pending; the barrier path above already cleaned up and this is
        # a no-op whenever the task reached a terminal state.
        if not task.done():
            task.cancel()
            try:
                await task
            except BaseException:
                pass
    await _p6_restored(db, session, op, item, pid, outcome)


async def _p6_restored(
    db: WholeSessionDatabase,
    session: uuid.UUID,
    op: uuid.UUID,
    item: uuid.UUID,
    pid: int,
    outcome: str,
) -> None:
    # Canonical and application probe state fully restored:
    assert (
        await db.setup.fetchval(
            f"SELECT count(*) FROM {db.tbl('content_item')} WHERE id = '{item}'"
        )
        == 0
    )
    assert await db.setup.fetchval(f"SELECT count(*) FROM {db.tbl('txn_probe')}") == 0
    # Pending operation retained for a fresh public reviewer:
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        assert await reviewer.operations(session, schema=db.schema) == [op]
    # No leaked transaction or locks for the window pid. Termination kills
    # the backend outright; an escaped refusal or cancel may legally leave
    # the healthy pooled backend alive and idle, or the pool may have
    # replaced it, and neither is a leak:
    if outcome == "terminate":
        assert (
            await db.admin.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE pid = $1", pid
            )
            == 0
        )
    else:
        state = await db.admin.fetchval(
            "SELECT state FROM pg_stat_activity WHERE pid = $1", pid
        )
        assert state in (None, "idle"), f"leaked activity {state!r} for pid {pid}"
        assert (
            await db.admin.fetchval("SELECT count(*) FROM pg_locks WHERE pid = $1", pid)
            == 0
        )
    # The pools are reusable end-to-end on replacement connections, under
    # the same qualified deferred mechanism:
    session2, op2, item2 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    # Unique per-test slug: (site_id, type_id, slug) is UNIQUE and the
    # session-scoped fixture database is shared across the three P6 tests.
    replace_slug = f"p6-replace-{uuid.uuid4().hex[:12]}"
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session2, operation_id=op2
    ) as cow:
        await cow.execute(
            f"INSERT INTO {db.view('content_item')} "
            f"(id, site_id, type_id, slug, values) "
            f"VALUES ('{item2}', '{SITE_A}', '{TYPE_P6}', '{replace_slug}', '{{}}')"
        )
    async with asyncpg_cow_reviewer(db.reviewer_pool) as reviewer:
        result2 = await reviewer.commit_session(
            session2, schema=db.schema, defer_fk_constraints=True
        )
    assert result2.no_op is False
    assert result2.has_pending_operations is False
    assert (
        await db.setup.fetchval(
            f"SELECT count(*) FROM {db.tbl('content_item')} WHERE id = '{item2}'"
        )
        == 1
    )
    # No COW GUC leaks on fresh pooled connections. Frozen 0.2.0 public
    # semantics (safe_session._normalize_context, values or None; SQL side
    # NULLIF(current_setting(..., true), '')) treat BOTH NULL and empty
    # string as clean, so only a nonempty stale value is a leak:
    async with db.runtime_pool.acquire() as conn:
        for guc in ("app.session_id", "app.operation_id", "app.visible_operations"):
            value = await conn.fetchval("SELECT current_setting($1, true)", guc)
            assert value in (None, "")
    async with db.reviewer_pool.acquire() as conn:
        for guc in ("app.session_id", "app.operation_id", "app.visible_operations"):
            value = await conn.fetchval("SELECT current_setting($1, true)", guc)
            assert value in (None, "")


async def test_p6_escaped_postcondition_rolls_back_promotion(
    db: WholeSessionDatabase,
) -> None:
    session, op, item = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session, operation_id=op
    ) as cow:
        await cow.execute(
            f"INSERT INTO {db.view('content_item')} "
            f"(id, site_id, type_id, slug, values) "
            f"VALUES ('{item}', '{SITE_A}', '{TYPE_P6}', 'p6-item', '{{}}')"
        )
    await _run_p6_window(db, "postcondition", session, op, item)


async def test_p6_task_cancel_rolls_back_promotion(db: WholeSessionDatabase) -> None:
    session, op, item = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session, operation_id=op
    ) as cow:
        await cow.execute(
            f"INSERT INTO {db.view('content_item')} "
            f"(id, site_id, type_id, slug, values) "
            f"VALUES ('{item}', '{SITE_A}', '{TYPE_P6}', 'p6-item', '{{}}')"
        )
    await _run_p6_window(db, "cancel", session, op, item)


async def test_p6_reviewer_termination_rolls_back_promotion(
    db: WholeSessionDatabase,
) -> None:
    session, op, item = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    async with asyncpg_cow_session(
        db.runtime_pool, session_id=session, operation_id=op
    ) as cow:
        await cow.execute(
            f"INSERT INTO {db.view('content_item')} "
            f"(id, site_id, type_id, slug, values) "
            f"VALUES ('{item}', '{SITE_A}', '{TYPE_P6}', 'p6-item', '{{}}')"
        )
    await _run_p6_window(db, "terminate", session, op, item)
