# ruff: noqa: E501
"""Media publication core: public visibility state, finalization mark, agent media surface.

Media assets are site-scoped, content-addressed, immutable records: every
product media write path (human/agent registration, legacy create/update,
finalization mark) targets the physical ``media_asset_base`` relation
directly, so a registered asset is visible to every site session from the
commit moment and is what the sessionless public digest route reads.  The
foundation COW structure on ``media_asset`` is preserved (bootstrap
reconcile keeps re-enabling it), but no product write path uses the media
overlay; in any session the COW view therefore resolves to exactly the base
rows.
"""

from __future__ import annotations

from collections.abc import Sequence
from importlib import import_module
from typing import Any

from alembic import op

revision: str = "068_001"
down_revision: str | Sequence[str] | None = "067_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_M060: Any = import_module(
    "slaif_agent_site.db.alembic.versions.060_001_agent_component_semantics"
)
_M067: Any = import_module(
    "slaif_agent_site.db.alembic.versions.067_001_global_region_data_plane"
)

# The 14-column media record shape used by every SELECT media_asset.* surface
# after this revision (the two publication columns are appended in table
# column order).
MEDIA_RECORD_COLUMNS = """
        id uuid, site_id uuid, uploaded_by uuid, filename text,
        mime_type text, size_bytes bigint, content_hash text,
        storage_key text, alt_text text, metadata jsonb,
        created_at timestamptz, updated_at timestamptz,
        public_status content.media_public_status, published_at timestamptz
"""

# The pre-068 12-column shape, used only by the downgrade to restore the
# historical function signatures.
MEDIA_RECORD_COLUMNS_LEGACY = """
        id uuid, site_id uuid, uploaded_by uuid, filename text,
        mime_type text, size_bytes bigint, content_hash text,
        storage_key text, alt_text text, metadata jsonb,
        created_at timestamptz, updated_at timestamptz
"""


def _execute_block(sql: str) -> None:
    statement: list[str] = []
    in_function_body = False
    for line in sql.splitlines(keepends=True):
        statement.append(line)
        if line.count("$fn$") % 2:
            in_function_body = not in_function_body
        if line.rstrip().endswith(";") and not in_function_body:
            op.execute("".join(statement))
            statement = []
    if "".join(statement).strip():
        op.execute("".join(statement))


def _secure(function: str, signature: str) -> None:
    qualified = f"{function}({signature})"
    op.execute(f"ALTER FUNCTION {qualified} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {qualified} FROM PUBLIC")


# The seven pre-068 media functions keep their exact argument signatures;
# only their returned row shape grows by the two publication columns.
# PostgreSQL cannot change a function's return type via CREATE OR REPLACE,
# so each is dropped (no SQL object depends on them) and recreated.
_LEGACY_MEDIA_FUNCTIONS: tuple[tuple[str, str], ...] = (
    (
        "content.slaif_media_create",
        "uuid,uuid,text,text,bigint,text,text,text,jsonb",
    ),
    ("content.slaif_media_list", "uuid"),
    ("content.slaif_media_get", "uuid"),
    ("content.slaif_media_update", "uuid,text,jsonb"),
    ("content.slaif_agent_media_list", "uuid"),
    (
        "content.slaif_media_asset_register",
        "uuid,uuid,uuid,text,text,text,bigint,text,text,text,jsonb,uuid,uuid",
    ),
    ("content.slaif_media_asset_get", "uuid,uuid,uuid,uuid,text,uuid"),
)


def _drop_cow_for_media_change() -> None:
    """Refuse to discard pending workspace state before changing media columns.

    ``content.media_asset`` is a COW-enabled content table: bootstrap
    reconcile renames it to ``media_asset_base`` and installs the overlay
    view (and re-enables it after this guard tears it down).  Column DDL is
    only possible on the physical relation, so the guard tears the COW down
    first, failing closed on unreviewed workspace overlay rows or a missing
    foundation, exactly like the 065/066/067 data-plane migrations.  Product
    media writes target the base relation directly (site-scoped immutable
    media, see module docstring), so the overlay is expected to stay empty.
    """

    op.execute(
        """
        DO $guard$
        DECLARE relation_kind char; pending boolean;
        BEGIN
            SELECT c.relkind INTO relation_kind
            FROM pg_catalog.pg_class c
            JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='content' AND c.relname='media_asset';
            IF relation_kind='v' THEN
                SELECT EXISTS (
                    SELECT 1 FROM pg_catalog.pg_class c
                    JOIN pg_catalog.pg_namespace n ON n.oid=c.relnamespace
                    WHERE n.nspname='content' AND c.relname='media_asset_changes'
                ) INTO pending;
                IF pending THEN
                    EXECUTE 'SELECT EXISTS (SELECT 1 FROM content.media_asset_changes)'
                        INTO pending;
                    IF pending THEN
                        RAISE EXCEPTION 'MEDIA_PUBLICATION_MIGRATION_PENDING_COW'
                            USING ERRCODE='P0001';
                    END IF;
                END IF;
                IF pg_catalog.to_regprocedure('agentcow.teardown_cow(text,text)') IS NULL THEN
                    RAISE EXCEPTION 'MEDIA_PUBLICATION_MIGRATION_REQUIRES_FOUNDATION'
                        USING ERRCODE='P0001';
                END IF;
                PERFORM agentcow.teardown_cow('content','media_asset');
                EXECUTE 'ALTER TABLE content.media_asset_base RENAME TO media_asset';
            END IF;
        END $guard$;
        """
    )


def _drop_legacy_media_functions() -> None:
    for function, signature in _LEGACY_MEDIA_FUNCTIONS:
        op.execute(f"DROP FUNCTION IF EXISTS {function}({signature}) CASCADE")


# The base-state execute grants (023/029/030) travel with the function ACL, so
# the drop-then-recreate must restore them exactly; hardening never re-grants
# role-specific execute beyond its own whitelists.
_LEGACY_MEDIA_GRANTS: tuple[tuple[str, str, str], ...] = (
    (
        "content.slaif_media_create",
        "uuid,uuid,text,text,bigint,text,text,text,jsonb",
        "slaif_editor_runtime, slaif_control",
    ),
    (
        "content.slaif_media_list",
        "uuid",
        "slaif_editor_runtime, slaif_control",
    ),
    (
        "content.slaif_media_get",
        "uuid",
        "slaif_editor_runtime, slaif_control",
    ),
    (
        "content.slaif_media_update",
        "uuid,text,jsonb",
        "slaif_editor_runtime, slaif_control",
    ),
    (
        "content.slaif_agent_media_list",
        "uuid",
        "slaif_agent_runtime",
    ),
    (
        "content.slaif_media_asset_register",
        "uuid,uuid,uuid,text,text,text,bigint,text,text,text,jsonb,uuid,uuid",
        "slaif_media",
    ),
    (
        "content.slaif_media_asset_get",
        "uuid,uuid,uuid,uuid,text,uuid",
        "slaif_media",
    ),
)


def _grant_legacy_media_functions() -> None:
    for function, signature, grantees in _LEGACY_MEDIA_GRANTS:
        op.execute(f"GRANT EXECUTE ON FUNCTION {function}({signature}) TO {grantees}")


def _replace_validator_prefix(sql: str) -> str:
    # The validator body changes (media MIME branch) while its signature and
    # void return type stay fixed, so CREATE OR REPLACE is the only valid
    # form: it preserves the OID, the dependent composition functions, the
    # owner, and the existing grants.
    prefix = "CREATE FUNCTION content.slaif_agent_component_validate("
    if not sql.lstrip().startswith(prefix):
        raise RuntimeError("060 validator definition drift")
    return sql.replace(
        prefix,
        "CREATE OR REPLACE FUNCTION content.slaif_agent_component_validate(",
        1,
    )


def _media_create_sql(*, columns: str) -> str:
    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_media_create(
            p_site_id uuid, p_uploaded_by uuid, p_filename text,
            p_mime_type text, p_size_bytes bigint, p_content_hash text,
            p_storage_key text, p_alt_text text, p_metadata jsonb
        ) RETURNS TABLE (
{columns}
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            INSERT INTO content.media_asset_base
                (site_id, uploaded_by, filename, mime_type, size_bytes,
                 content_hash, storage_key, alt_text, metadata)
            VALUES (p_site_id, p_uploaded_by, p_filename, p_mime_type,
                    p_size_bytes, p_content_hash, p_storage_key, p_alt_text, p_metadata);
            RETURN QUERY SELECT * FROM content.media_asset_base
            WHERE site_id = p_site_id AND content_hash = p_content_hash LIMIT 1;
        END;
        $fn$;
    """


def _media_list_sql(*, columns: str) -> str:
    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_media_list(
            p_site_id uuid
        ) RETURNS TABLE (
{columns}
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.media_asset WHERE site_id = p_site_id
            ORDER BY created_at DESC
        $fn$;
    """


def _media_get_sql(*, columns: str) -> str:
    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_media_get(
            p_media_id uuid
        ) RETURNS TABLE (
{columns}
        ) LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog STABLE AS $fn$
            SELECT * FROM content.media_asset WHERE id = p_media_id
        $fn$;
    """


def _media_update_sql(*, columns: str) -> str:
    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_media_update(
            p_media_id uuid, p_alt_text text, p_metadata jsonb
        ) RETURNS TABLE (
{columns}
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.media_asset_base AS media_asset SET
                alt_text = COALESCE(p_alt_text, media_asset.alt_text),
                metadata = COALESCE(p_metadata, media_asset.metadata),
                updated_at = CURRENT_TIMESTAMP
            WHERE media_asset.id = p_media_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT media_asset.* FROM content.media_asset_base AS media_asset
            WHERE media_asset.id = p_media_id;
        END;
        $fn$;
    """


def _agent_media_list_sql(*, columns: str) -> str:
    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_agent_media_list(
            p_site_id uuid
        ) RETURNS TABLE (
{columns}
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY
            SELECT media_asset.*
            FROM content.media_asset AS media_asset
            WHERE media_asset.site_id = p_site_id
            ORDER BY media_asset.created_at DESC;
        END;
        $fn$;
    """


def _media_asset_register_sql(*, columns: str) -> str:
    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_media_asset_register(
            p_site_id uuid, p_uploaded_by uuid, p_session_id uuid, p_permission text,
            p_filename text, p_mime_type text, p_size bigint, p_hash text,
            p_storage_key text, p_alt_text text, p_metadata jsonb,
            p_workspace_id uuid, p_human_user_id uuid
        ) RETURNS TABLE (
{columns}
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE operation_uuid uuid;
        BEGIN
            operation_uuid := NULLIF(current_setting('app.operation_id', true), '')::uuid;
            PERFORM control.slaif_media_workspace_assert(
                p_workspace_id, p_human_user_id, p_site_id, p_session_id,
                p_permission, operation_uuid
            );
            IF p_uploaded_by IS DISTINCT FROM p_human_user_id
               OR p_mime_type NOT IN ('image/png', 'image/jpeg')
               OR p_size < 1 OR p_hash !~ '^[0-9a-f]{{64}}$'
               OR p_storage_key <> 'sha256/' || substr(p_hash, 1, 2) || '/' || substr(p_hash, 3, 2) || '/' || p_hash
               OR length(p_filename) NOT BETWEEN 1 AND 255
            THEN
                RAISE EXCEPTION 'MEDIA_REGISTRATION_INPUT' USING ERRCODE = 'P0001';
            END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(p_site_id::text || ':' || p_hash, 702));
            RETURN QUERY SELECT media_asset.* FROM content.media_asset_base AS media_asset
            WHERE media_asset.site_id = p_site_id AND media_asset.content_hash = p_hash
            ORDER BY media_asset.created_at LIMIT 1;
            IF FOUND THEN RETURN; END IF;
            INSERT INTO content.media_asset_base(
                site_id, uploaded_by, filename, mime_type, size_bytes,
                content_hash, storage_key, alt_text, metadata
            ) VALUES (
                p_site_id, p_uploaded_by, p_filename, p_mime_type, p_size,
                p_hash, p_storage_key, p_alt_text, p_metadata
            );
            RETURN QUERY SELECT media_asset.* FROM content.media_asset_base AS media_asset
            WHERE media_asset.site_id = p_site_id AND media_asset.content_hash = p_hash
            ORDER BY media_asset.created_at DESC LIMIT 1;
        END;
        $fn$;
    """


def _media_asset_get_sql(*, columns: str) -> str:
    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_media_asset_get(
            p_site_id uuid, p_media_id uuid, p_human_user_id uuid,
            p_session_id uuid, p_permission text, p_workspace_id uuid
        ) RETURNS TABLE (
{columns}
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE operation_uuid uuid;
        BEGIN
            operation_uuid := NULLIF(current_setting('app.operation_id', true), '')::uuid;
            PERFORM control.slaif_media_workspace_assert(
                p_workspace_id, p_human_user_id, p_site_id, p_session_id,
                p_permission, operation_uuid
            );
            RETURN QUERY SELECT media_asset.* FROM content.media_asset AS media_asset
            WHERE media_asset.id = p_media_id AND media_asset.site_id = p_site_id;
        END;
        $fn$;
    """


def _agent_media_register_sql() -> str:
    return f"""
        CREATE FUNCTION content.slaif_agent_media_register(
            p_site_id uuid, p_uploaded_by uuid, p_filename text,
            p_mime_type text, p_size bigint, p_hash text,
            p_storage_key text, p_alt_text text, p_metadata jsonb,
            p_workspace_id uuid, p_operation_id uuid
        ) RETURNS TABLE (
{MEDIA_RECORD_COLUMNS}
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id, 'media:upload');
            IF NULLIF(current_setting('app.session_id', true), '') IS DISTINCT FROM p_workspace_id::text
               OR NULLIF(current_setting('app.operation_id', true), '') IS DISTINCT FROM p_operation_id::text
            THEN
                RAISE EXCEPTION 'AGENT_MEDIA_CONTEXT_INVALID' USING ERRCODE = '22023';
            END IF;
            IF p_uploaded_by IS NULL
               OR p_mime_type NOT IN ('image/png', 'image/jpeg')
               OR p_size < 1 OR p_hash !~ '^[0-9a-f]{{64}}$'
               OR p_storage_key <> 'sha256/' || substr(p_hash, 1, 2) || '/' || substr(p_hash, 3, 2) || '/' || p_hash
               OR length(p_filename) NOT BETWEEN 1 AND 255
               OR p_metadata IS NULL OR jsonb_typeof(p_metadata) <> 'object'
            THEN
                RAISE EXCEPTION 'AGENT_MEDIA_INPUT_INVALID' USING ERRCODE = 'P0001';
            END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(p_site_id::text || ':' || p_hash, 702));
            RETURN QUERY SELECT media_asset.* FROM content.media_asset_base AS media_asset
            WHERE media_asset.site_id = p_site_id AND media_asset.content_hash = p_hash
            ORDER BY media_asset.created_at LIMIT 1;
            IF FOUND THEN RETURN; END IF;
            INSERT INTO content.media_asset_base(
                site_id, uploaded_by, filename, mime_type, size_bytes,
                content_hash, storage_key, alt_text, metadata
            ) VALUES (
                p_site_id, p_uploaded_by, p_filename, p_mime_type, p_size,
                p_hash, p_storage_key, p_alt_text, p_metadata
            );
            RETURN QUERY SELECT media_asset.* FROM content.media_asset_base AS media_asset
            WHERE media_asset.site_id = p_site_id AND media_asset.content_hash = p_hash
            ORDER BY media_asset.created_at DESC LIMIT 1;
        END;
        $fn$;
    """


def _agent_media_get_sql() -> str:
    return f"""
        CREATE FUNCTION content.slaif_agent_media_get(
            p_site_id uuid, p_media_id uuid
        ) RETURNS TABLE (
{MEDIA_RECORD_COLUMNS}
        ) LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_cow_site(p_site_id);
            RETURN QUERY SELECT media_asset.* FROM content.media_asset AS media_asset
            WHERE media_asset.id = p_media_id AND media_asset.site_id = p_site_id;
        END;
        $fn$;
    """


def _media_public_get_sql() -> str:
    return """
        CREATE FUNCTION content.slaif_media_public_get(
            p_hash text
        ) RETURNS TABLE (
            content_hash text, mime_type text, size_bytes bigint,
            public_status text
        ) LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
            SELECT m.content_hash, m.mime_type, m.size_bytes, m.public_status
            FROM content.media_asset AS m
            WHERE m.content_hash = p_hash
              AND m.public_status = 'public'
        $fn$;
    """


def _media_public_fetch_sql() -> str:
    return f"""
        CREATE FUNCTION content.slaif_media_public_fetch(
            p_site_id uuid, p_media_id uuid
        ) RETURNS TABLE (
{MEDIA_RECORD_COLUMNS}
        ) LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
            SELECT m.*
            FROM content.media_asset AS m
            WHERE m.id = p_media_id AND m.site_id = p_site_id
        $fn$;
    """


def _media_public_mark_sql() -> str:
    return f"""
        CREATE FUNCTION content.slaif_media_public_mark(
            p_site_id uuid, p_media_id uuid,
            p_workspace_id uuid, p_operation_id uuid
        ) RETURNS TABLE (
{MEDIA_RECORD_COLUMNS}
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            IF NULLIF(current_setting('app.session_id', true), '') IS DISTINCT FROM p_workspace_id::text
               OR NULLIF(current_setting('app.operation_id', true), '') IS DISTINCT FROM p_operation_id::text
            THEN
                RAISE EXCEPTION 'MEDIA_FINALIZATION_CONTEXT_INVALID' USING ERRCODE = '22023';
            END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(p_site_id::text || ':' || p_media_id::text, 913));
            IF NOT EXISTS (
                SELECT 1 FROM content.media_asset_base AS m
                WHERE m.id = p_media_id AND m.site_id = p_site_id
            ) THEN
                RAISE EXCEPTION 'MEDIA_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM content.page_composition AS c
                WHERE c.site_id = p_site_id
                  AND c.props ->> 'mediaId' = p_media_id::text
            ) THEN
                RAISE EXCEPTION 'MEDIA_NOT_WORKSPACE_REFERENCED' USING ERRCODE = 'P0003';
            END IF;
            UPDATE content.media_asset_base AS m
            SET public_status = 'public',
                published_at = COALESCE(m.published_at, CURRENT_TIMESTAMP)
            WHERE m.id = p_media_id AND m.site_id = p_site_id;
            RETURN QUERY SELECT media_asset.* FROM content.media_asset_base AS media_asset
            WHERE media_asset.id = p_media_id AND media_asset.site_id = p_site_id;
        END;
        $fn$;
    """


def _render_media_resolve_sql() -> str:
    return """
        CREATE FUNCTION content.slaif_render_media_resolve(
            p_site_id uuid, p_media_id uuid
        ) RETURNS TABLE (
            mime_type text, size_bytes bigint,
            content_hash text, public_status text
        ) LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
            SELECT m.mime_type, m.size_bytes, m.content_hash, m.public_status
            FROM content.media_asset AS m
            WHERE m.id = p_media_id AND m.site_id = p_site_id
        $fn$;
    """


def _component_validator_sql() -> str:
    # The 060 validator body with the media_asset binding branch extended to
    # the MIME class the immutable store accepts (R5).  Everything else is
    # byte-identical to the 060_001 definition.
    validator_sql = str(_M060._component_validator_sql())
    old_branch = (
        "                IF NOT EXISTS (\n"
        "                    SELECT 1 FROM content.media_asset m\n"
        "                    WHERE m.id=binding_id AND m.site_id=p_site_id\n"
        "                ) THEN RAISE EXCEPTION 'COMPONENT_BINDING_INVALID' USING ERRCODE='P0003'; END IF;\n"
    )
    new_branch = (
        "                IF NOT EXISTS (\n"
        "                    SELECT 1 FROM content.media_asset m\n"
        "                    WHERE m.id=binding_id AND m.site_id=p_site_id\n"
        "                      AND m.mime_type IN ('image/png','image/jpeg')\n"
        "                ) THEN RAISE EXCEPTION 'COMPONENT_BINDING_INVALID' USING ERRCODE='P0003'; END IF;\n"
    )
    if old_branch not in validator_sql:
        raise RuntimeError("060 validator media branch drift")
    return validator_sql.replace(old_branch, new_branch, 1)


def _semantic_completion_sql() -> str:
    # The 067 completion whitelist plus the one bounded media upload row.
    completion_sql = str(_M067._semantic_completion_sql(include_region=True))
    anchor = "                       ('CONTENT_TYPE_DELETED','content_type','DELETE',200,'delete'),\n"
    media_row = (
        "                       ('MEDIA_UPLOADED','media_asset','POST',201,'upload'),\n"
    )
    if media_row.strip() in completion_sql or anchor not in completion_sql:
        raise RuntimeError("067 completion whitelist drift")
    return completion_sql.replace(anchor, media_row + anchor, 1)


def _semantic_constraint_sql() -> str:
    # The 067 audit semantic shape plus the one bounded media upload clause.
    constraint_sql = str(_M067._semantic_constraint_sql(include_region=True))
    anchor = "            OR (action IN ('PAGE_MOVED','PAGE_RESTORED','NAVIGATION_ITEM_MOVED','COMPONENT_MOVED') AND http_method='POST' AND response_status=200 AND quota_kind='mutation')\n"
    media_clause = "            OR (action='MEDIA_UPLOADED' AND resource_type='media_asset' AND http_method='POST' AND response_status=201 AND quota_kind='upload')\n"
    if "MEDIA_UPLOADED" in constraint_sql or anchor not in constraint_sql:
        raise RuntimeError("067 audit semantic constraint drift")
    return constraint_sql.replace(anchor, media_clause + anchor, 1)


def upgrade() -> None:
    _drop_cow_for_media_change()
    op.execute("CREATE TYPE content.media_public_status AS ENUM ('private', 'public')")
    op.execute(
        "ALTER TABLE content.media_asset "
        "ADD COLUMN public_status content.media_public_status "
        "NOT NULL DEFAULT 'private'"
    )
    op.execute("ALTER TABLE content.media_asset ADD COLUMN published_at timestamptz")
    _drop_legacy_media_functions()
    _execute_block(_media_create_sql(columns=MEDIA_RECORD_COLUMNS))
    _execute_block(_media_list_sql(columns=MEDIA_RECORD_COLUMNS))
    _execute_block(_media_get_sql(columns=MEDIA_RECORD_COLUMNS))
    _execute_block(_media_update_sql(columns=MEDIA_RECORD_COLUMNS))
    _execute_block(_agent_media_list_sql(columns=MEDIA_RECORD_COLUMNS))
    _execute_block(_media_asset_register_sql(columns=MEDIA_RECORD_COLUMNS))
    _execute_block(_media_asset_get_sql(columns=MEDIA_RECORD_COLUMNS))
    _grant_legacy_media_functions()
    _execute_block(_replace_validator_prefix(_component_validator_sql()))
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(_semantic_constraint_sql())
    _execute_block(_semantic_completion_sql())
    _execute_block(_agent_media_register_sql())
    _execute_block(_agent_media_get_sql())
    _execute_block(_media_public_get_sql())
    _execute_block(_media_public_fetch_sql())
    _execute_block(_media_public_mark_sql())
    _execute_block(_render_media_resolve_sql())
    _secure(
        "content.slaif_agent_media_register",
        "uuid,uuid,text,text,bigint,text,text,text,jsonb,uuid,uuid",
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_agent_media_register(uuid,uuid,text,text,bigint,text,text,text,jsonb,uuid,uuid) TO slaif_agent_runtime"
    )
    _secure("content.slaif_agent_media_get", "uuid,uuid")
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_agent_media_get(uuid,uuid) TO slaif_agent_runtime"
    )
    _secure("content.slaif_media_public_get", "text")
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_media_public_get(text) TO slaif_media"
    )
    _secure("content.slaif_media_public_fetch", "uuid,uuid")
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_media_public_fetch(uuid,uuid) TO slaif_media"
    )
    _secure("content.slaif_media_public_mark", "uuid,uuid,uuid,uuid")
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_media_public_mark(uuid,uuid,uuid,uuid) TO slaif_media"
    )
    _secure("content.slaif_render_media_resolve", "uuid,uuid")
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_render_media_resolve(uuid,uuid) TO slaif_public_reader, slaif_preview_reader"
    )


def downgrade() -> None:
    _drop_cow_for_media_change()
    for function, signature in (
        ("content.slaif_render_media_resolve", "uuid,uuid"),
        ("content.slaif_media_public_fetch", "uuid,uuid"),
        ("content.slaif_media_public_mark", "uuid,uuid,uuid,uuid"),
        ("content.slaif_media_public_get", "text"),
        ("content.slaif_agent_media_get", "uuid,uuid"),
        (
            "content.slaif_agent_media_register",
            "uuid,uuid,text,text,bigint,text,text,text,jsonb,uuid,uuid",
        ),
    ):
        op.execute(f"DROP FUNCTION IF EXISTS {function}({signature}) CASCADE")
    _execute_block(_replace_validator_prefix(_M060._component_validator_sql()))
    op.execute(
        "ALTER TABLE audit.agent_mutation DROP CONSTRAINT agent_mutation_semantic_shape"
    )
    op.execute(_M067._semantic_constraint_sql(include_region=True))
    _execute_block(_M067._semantic_completion_sql(include_region=True))
    _drop_legacy_media_functions()
    # The 068-added columns must go before the legacy 12-column media
    # functions are recreated: they SELECT * from content.media_asset, so
    # the table must already have the pre-068 shape when they are defined.
    op.execute("ALTER TABLE content.media_asset DROP COLUMN published_at")
    op.execute("ALTER TABLE content.media_asset DROP COLUMN public_status")
    op.execute("DROP TYPE IF EXISTS content.media_public_status")
    _execute_block(_media_create_sql(columns=MEDIA_RECORD_COLUMNS_LEGACY))
    _execute_block(_media_list_sql(columns=MEDIA_RECORD_COLUMNS_LEGACY))
    _execute_block(_media_get_sql(columns=MEDIA_RECORD_COLUMNS_LEGACY))
    _execute_block(_media_update_sql(columns=MEDIA_RECORD_COLUMNS_LEGACY))
    _execute_block(_agent_media_list_sql(columns=MEDIA_RECORD_COLUMNS_LEGACY))
    _execute_block(_media_asset_register_sql(columns=MEDIA_RECORD_COLUMNS_LEGACY))
    _execute_block(_media_asset_get_sql(columns=MEDIA_RECORD_COLUMNS_LEGACY))
    _grant_legacy_media_functions()
