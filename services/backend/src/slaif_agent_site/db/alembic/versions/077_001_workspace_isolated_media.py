# ruff: noqa: E501
"""Workspace-isolated media: pending editorial writes through the COW view.

068 pointed the online human/agent registration and metadata update
functions at the physical ``media_asset_base`` relation, so a registered
asset was visible to every site session from the commit moment and was
what the sessionless public digest route could read.  This migration
restores the existing COW MediaAsset view as the target of every online
workspace write, without changing function signatures, return shapes,
grants, idempotency, audit, validation or locking:

- ``slaif_media_asset_register`` and ``slaif_agent_media_register``
  dedupe against, and insert into, the COW view: a fresh upload is a
  pending change row visible only to the registered workspace's
  session; a canonical same-hash asset is an honest no-op dedupe (no
  COW change row, same returned record/identity).
- ``slaif_media_update`` targets the view: an editorial PATCH is a
  workspace-pending change (first-touch baseline, like every other
  content COW write), never a canonical base mutation.
- the unwired legacy canonical creator ``slaif_media_create`` and the
  pre-transaction finalization marker ``slaif_media_public_mark`` are
  dropped: the creator had no product callers (its editor/control
  grants vanish with the object), and the mark is superseded by
  ``slaif_media_publicize_promoted``.
- ``slaif_media_publicize_promoted`` is the publication-derived
  helper the accept job calls INSIDE the single reviewer transaction,
  after the foundation promotion: least-authority (EXECUTE granted to
  ``slaif_review_worker`` only), site-bound, base-existence and
  promoted-base typed-closure reference checked (page composition or
  media/document field reference, same-site, compared by UUID
  identity), idempotent for public rows.

No table DDL and no COW teardown: the media COW stays exactly as the
bootstrap reconcile established it (requirement: never re-COW an
enabled table).  The downgrade is an explicit fail-closed refusal: the
pre-077 media functions wrote ``media_asset_base`` directly, so
restoring them would silently reinstate the unsafe canonical media
write path and its editor/control/media publication grants.  No
database at this head has a supported downgrade below it; the
bootstrap operator path refuses before any PENDING marker, COW disable
or migration step, and the Alembic body raises unconditionally as the
second line of defense.
"""

from __future__ import annotations

from collections.abc import Sequence
from importlib import import_module
from typing import Any

from alembic import op

revision: str = "077_001"
down_revision: str | Sequence[str] | None = "076_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_M068: Any = import_module(
    "slaif_agent_site.db.alembic.versions.068_001_media_publication_core"
)

_MEDIA_COLUMNS = _M068.MEDIA_RECORD_COLUMNS


def _register_sql() -> str:
    """068 body with the dedupe select and insert on the COW view.

    The view resolves to base rows plus this session's own change rows,
    so the same-hash dedupe is workspace-visible only: two workspaces
    proposing identical fresh bytes keep separate pending rows, and a
    canonical asset is reused with its stable id (no COW change row).
    """

    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_media_asset_register(
            p_site_id uuid, p_uploaded_by uuid, p_session_id uuid, p_permission text,
            p_filename text, p_mime_type text, p_size bigint, p_hash text,
            p_storage_key text, p_alt_text text, p_metadata jsonb,
            p_workspace_id uuid, p_human_user_id uuid
        ) RETURNS TABLE (
{_MEDIA_COLUMNS}
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE operation_uuid uuid;
        BEGIN
            operation_uuid := NULLIF(current_setting('app.operation_id', true), '')::uuid;
            PERFORM control.slaif_media_workspace_assert(
                p_workspace_id, p_human_user_id, p_site_id, p_session_id,
                p_permission, operation_uuid
            );
            IF p_uploaded_by IS DISTINCT FROM p_human_user_id
               OR p_mime_type NOT IN ('image/png', 'image/jpeg', 'application/pdf')
               OR p_size < 1 OR p_hash !~ '^[0-9a-f]{{64}}$'
               OR p_storage_key <> 'sha256/' || substr(p_hash, 1, 2) || '/' || substr(p_hash, 3, 2) || '/' || p_hash
               OR length(p_filename) NOT BETWEEN 1 AND 255
            THEN
                RAISE EXCEPTION 'MEDIA_REGISTRATION_INPUT' USING ERRCODE = 'P0001';
            END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(p_site_id::text || ':' || p_hash, 702));
            RETURN QUERY SELECT media_asset.* FROM content.media_asset AS media_asset
            WHERE media_asset.site_id = p_site_id AND media_asset.content_hash = p_hash
            ORDER BY media_asset.created_at LIMIT 1;
            IF FOUND THEN RETURN; END IF;
            INSERT INTO content.media_asset(
                site_id, uploaded_by, filename, mime_type, size_bytes,
                content_hash, storage_key, alt_text, metadata
            ) VALUES (
                p_site_id, p_uploaded_by, p_filename, p_mime_type, p_size,
                p_hash, p_storage_key, p_alt_text, p_metadata
            );
            RETURN QUERY SELECT media_asset.* FROM content.media_asset AS media_asset
            WHERE media_asset.site_id = p_site_id AND media_asset.content_hash = p_hash
            ORDER BY media_asset.created_at DESC LIMIT 1;
        END;
        $fn$;
    """


def _agent_register_sql() -> str:
    """068 agent body with the dedupe select and insert on the COW view."""

    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_agent_media_register(
            p_site_id uuid, p_uploaded_by uuid, p_filename text,
            p_mime_type text, p_size bigint, p_hash text,
            p_storage_key text, p_alt_text text, p_metadata jsonb,
            p_workspace_id uuid, p_operation_id uuid
        ) RETURNS TABLE (
{_MEDIA_COLUMNS}
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_agent_require_capability(p_site_id, 'media:upload');
            IF NULLIF(current_setting('app.session_id', true), '') IS DISTINCT FROM p_workspace_id::text
               OR NULLIF(current_setting('app.operation_id', true), '') IS DISTINCT FROM p_operation_id::text
            THEN
                RAISE EXCEPTION 'AGENT_MEDIA_CONTEXT_INVALID' USING ERRCODE = '22023';
            END IF;
            IF p_uploaded_by IS NULL
               OR p_mime_type NOT IN ('image/png', 'image/jpeg', 'application/pdf')
               OR p_size < 1 OR p_hash !~ '^[0-9a-f]{{64}}$'
               OR p_storage_key <> 'sha256/' || substr(p_hash, 1, 2) || '/' || substr(p_hash, 3, 2) || '/' || p_hash
               OR length(p_filename) NOT BETWEEN 1 AND 255
               OR p_metadata IS NULL OR jsonb_typeof(p_metadata) <> 'object'
            THEN
                RAISE EXCEPTION 'AGENT_MEDIA_INPUT_INVALID' USING ERRCODE = 'P0001';
            END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(p_site_id::text || ':' || p_hash, 702));
            RETURN QUERY SELECT media_asset.* FROM content.media_asset AS media_asset
            WHERE media_asset.site_id = p_site_id AND media_asset.content_hash = p_hash
            ORDER BY media_asset.created_at LIMIT 1;
            IF FOUND THEN RETURN; END IF;
            INSERT INTO content.media_asset(
                site_id, uploaded_by, filename, mime_type, size_bytes,
                content_hash, storage_key, alt_text, metadata
            ) VALUES (
                p_site_id, p_uploaded_by, p_filename, p_mime_type, p_size,
                p_hash, p_storage_key, p_alt_text, p_metadata
            );
            RETURN QUERY SELECT media_asset.* FROM content.media_asset AS media_asset
            WHERE media_asset.site_id = p_site_id AND media_asset.content_hash = p_hash
            ORDER BY media_asset.created_at DESC LIMIT 1;
        END;
        $fn$;
    """


def _update_sql() -> str:
    """068 update body targeting the COW view (workspace-pending edit)."""

    return f"""
        CREATE OR REPLACE FUNCTION content.slaif_media_update(
            p_media_id uuid, p_alt_text text, p_metadata jsonb
        ) RETURNS TABLE (
{_MEDIA_COLUMNS}
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE content.media_asset AS media_asset SET
                alt_text = COALESCE(p_alt_text, media_asset.alt_text),
                metadata = COALESCE(p_metadata, media_asset.metadata),
                updated_at = CURRENT_TIMESTAMP
            WHERE media_asset.id = p_media_id;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            RETURN QUERY SELECT media_asset.* FROM content.media_asset AS media_asset
            WHERE media_asset.id = p_media_id;
        END;
        $fn$;
    """


def _publicize_sql() -> str:
    """Reviewer-transaction publication helper (accept job, step 5).

    Called by the accept job inside the single ``asyncpg_cow_reviewer``
    transaction, after the foundation promotion has committed the
    session's pending rows to the base: every promoted media row
    referenced by the promoted base state is marked public atomically
    with the promotion, the site revision, the promotion audit, the
    workspace/job success and the cache outbox.  Any failure aborts the
    whole transaction (no separately committed mark exists any more).

    The reference check mirrors the 076 v2 typed media closure over the
    BASE tables (the promoted state): page composition
    ``props.mediaId``/``items[*].mediaId``, plus the ``media``/
    ``document`` ``field_definition`` values in ``content_item`` base
    values and in ``content_item_translation`` localized values, for
    both scalar and array cardinality.  Declared references are
    compared by UUID identity (the 076 materializer casts them to
    UUID, so accepted non-canonical spellings of the same UUID match);
    a declared value that is not a UUID aborts the transaction
    fail-closed (P0002).
    """

    return """
        CREATE FUNCTION content.slaif_media_publicize_promoted(
            p_site_id uuid, p_media_ids uuid[]
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            media_id uuid;
            referenced boolean;
        BEGIN
            FOREACH media_id IN ARRAY COALESCE(p_media_ids, ARRAY[]::uuid[])
            LOOP
                PERFORM pg_advisory_xact_lock(
                    hashtextextended(p_site_id::text || ':' || media_id::text, 913)
                );
                IF NOT EXISTS (
                    SELECT 1 FROM content.media_asset_base AS m
                    WHERE m.id = media_id AND m.site_id = p_site_id
                ) THEN
                    RAISE EXCEPTION 'MEDIA_PUBLICIZE_NOT_FOUND' USING ERRCODE = 'P0002';
                END IF;
                BEGIN
                    referenced := EXISTS (
                        SELECT 1 FROM content.page_composition_base AS c
                        WHERE c.site_id = p_site_id
                          AND (
                              (c.props ->> 'mediaId')::uuid = media_id
                              OR EXISTS (
                                  SELECT 1
                                  FROM jsonb_array_elements(c.props -> 'items') AS item
                                  WHERE (item ->> 'mediaId')::uuid = media_id
                              )
                          )
                    ) OR EXISTS (
                        SELECT 1
                        FROM content.field_definition_base AS f
                        JOIN content.content_item_base AS i
                            ON i.site_id = f.site_id
                           AND i.type_id = f.type_id
                        WHERE f.site_id = p_site_id
                          AND f.field_type IN ('media', 'document')
                          AND i.values -> f.key IS NOT NULL
                          AND (
                              (f.cardinality = 1
                               AND (i.values ->> f.key)::uuid = media_id)
                              OR (f.cardinality <> 1
                                  AND EXISTS (
                                      SELECT 1
                                      FROM jsonb_array_elements(i.values -> f.key) AS e
                                      WHERE (e.value #>> '{}')::uuid = media_id
                                  ))
                          )
                    ) OR EXISTS (
                        SELECT 1
                        FROM content.field_definition_base AS f
                        JOIN content.content_item_translation_base AS t
                            ON t.site_id = f.site_id
                           AND t.item_id IN (
                               SELECT i2.id
                               FROM content.content_item_base AS i2
                               WHERE i2.site_id = f.site_id
                                 AND i2.type_id = f.type_id
                           )
                        WHERE f.site_id = p_site_id
                          AND f.field_type IN ('media', 'document')
                          AND t.localized_values -> f.key IS NOT NULL
                          AND (
                              (f.cardinality = 1
                               AND (t.localized_values ->> f.key)::uuid = media_id)
                              OR (f.cardinality <> 1
                                  AND EXISTS (
                                      SELECT 1
                                      FROM jsonb_array_elements(t.localized_values -> f.key) AS e
                                      WHERE (e.value #>> '{}')::uuid = media_id
                                  ))
                          )
                    );
                EXCEPTION WHEN invalid_text_representation THEN
                    RAISE EXCEPTION 'MEDIA_PUBLICIZE_REFERENCE_INVALID'
                        USING ERRCODE = 'P0002';
                END;
                IF NOT referenced THEN
                    RAISE EXCEPTION 'MEDIA_PUBLICIZE_NOT_REFERENCED'
                        USING ERRCODE = 'P0003';
                END IF;
                UPDATE content.media_asset_base AS m
                SET public_status = 'public',
                    published_at = COALESCE(m.published_at, CURRENT_TIMESTAMP)
                WHERE m.id = media_id AND m.site_id = p_site_id;
            END LOOP;
        END;
        $fn$;
    """


def upgrade() -> None:
    # No COW teardown: no media table DDL in this revision, so the
    # enabled media COW (view + changes + triggers) is untouched and the
    # bootstrap reconcile never has to re-enable it.
    op.execute(_register_sql())
    op.execute(_agent_register_sql())
    op.execute(_update_sql())
    # Scoped drops without CASCADE: no other object in the migration
    # graph depends on either legacy helper, and an undetected dependent
    # must fail the migration loudly rather than be silently removed.
    op.execute(
        "DROP FUNCTION IF EXISTS content.slaif_media_create"
        "(uuid,uuid,text,text,bigint,text,text,text,jsonb)"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS content.slaif_media_public_mark(uuid,uuid,uuid,uuid)"
    )
    op.execute(_publicize_sql())
    op.execute(
        "ALTER FUNCTION content.slaif_media_publicize_promoted(uuid,uuid[])"
        " OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_media_publicize_promoted(uuid,uuid[])"
        " FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_media_publicize_promoted(uuid,uuid[])"
        " TO slaif_review_worker"
    )
    # The worker's effective role carries NOINHERIT membership in the
    # reviewer role, so it cannot inherit the reviewer's content USAGE;
    # resolving the helper inside the reviewer transaction needs direct
    # schema USAGE (resolution only: no CREATE, no table access).
    op.execute("GRANT USAGE ON SCHEMA content TO slaif_review_worker")


def downgrade() -> None:
    # Explicit fail-closed refusal (no conditional path): a downgrade
    # below this revision would have to recreate the base-writing
    # registration/update/mark bodies and their grants - the exact
    # unsafe canonical media write path this revision removes.  The
    # refusal raises before any restoration, touches no canonical media
    # or retained snapshot state, and leaves the safe authority set
    # exactly as found.  The bootstrap operator path refuses this
    # rollback earlier still (before the PENDING marker and the content
    # COW disable); this body is the defense for direct migration
    # invocations.
    op.execute(
        """
        DO $guard$
        BEGIN
            RAISE EXCEPTION
                'MEDIA_WORKSPACE_ISOLATION_DOWNGRADE_UNSUPPORTED'
                USING ERRCODE = 'P0001';
        END $guard$;
        """
    )
