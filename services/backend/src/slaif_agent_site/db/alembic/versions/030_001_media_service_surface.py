# ruff: noqa: E501
"""Add the narrow Media service auth, COW metadata, and idempotency surface."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "030_001"
down_revision: str | Sequence[str] | None = "029_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_CONTROL_FUNCTIONS = (
    ("control.slaif_media_authorize", "text,bytea,bytea,uuid,text,boolean"),
    ("control.slaif_media_workspace_assert", "uuid,uuid,uuid,uuid,text,uuid"),
    (
        "control.slaif_media_idempotency_begin",
        "uuid,uuid,uuid,uuid,text,text,text,uuid",
    ),
    (
        "control.slaif_media_idempotency_complete",
        "uuid,uuid,uuid,uuid,text,text,text,uuid,integer,jsonb,text,text,uuid",
    ),
)
_CONTENT_FUNCTIONS = (
    (
        "content.slaif_media_asset_register",
        "uuid,uuid,uuid,text,text,text,bigint,text,text,text,jsonb,uuid,uuid",
    ),
    ("content.slaif_media_asset_get", "uuid,uuid,uuid,uuid,text,uuid"),
)


def _secure(function: str, signature: str) -> None:
    qualified = f"{function}({signature})"
    op.execute(f"ALTER FUNCTION {qualified} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {qualified} FROM PUBLIC")


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE control.media_idempotency (
            workspace_id UUID NOT NULL REFERENCES control.workspace(id),
            human_user_id UUID NOT NULL REFERENCES control.user_account(id),
            site_id UUID NOT NULL REFERENCES control.site(id),
            idempotency_key TEXT NOT NULL,
            request_digest TEXT NOT NULL,
            operation_id UUID NOT NULL UNIQUE,
            status_code INTEGER,
            response_body JSONB,
            resource_type TEXT,
            resource_id UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,
            PRIMARY KEY (workspace_id, idempotency_key),
            CONSTRAINT media_idempotency_digest_shape
                CHECK (request_digest ~ '^[0-9a-f]{64}$'),
            CONSTRAINT media_idempotency_completion_shape CHECK (
                (status_code IS NULL AND response_body IS NULL
                    AND resource_type IS NULL AND resource_id IS NULL
                    AND completed_at IS NULL)
                OR (status_code BETWEEN 200 AND 299
                    AND response_body IS NOT NULL AND resource_type = 'media_asset'
                    AND resource_id IS NOT NULL AND completed_at IS NOT NULL)
            )
        )
        """
    )
    op.execute(
        """
        CREATE TABLE audit.media_mutation (
            operation_id UUID PRIMARY KEY,
            human_user_id UUID NOT NULL REFERENCES control.user_account(id),
            workspace_id UUID NOT NULL REFERENCES control.workspace(id),
            site_id UUID NOT NULL REFERENCES control.site(id),
            action TEXT NOT NULL,
            resource_id UUID NOT NULL,
            request_digest TEXT NOT NULL,
            response_status INTEGER NOT NULL,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT media_mutation_digest_shape CHECK (request_digest ~ '^[0-9a-f]{64}$'),
            CONSTRAINT media_mutation_status_shape CHECK (response_status BETWEEN 200 AND 299)
        )
        """
    )
    op.execute("ALTER TABLE control.media_idempotency OWNER TO slaif_owner")
    op.execute("ALTER TABLE audit.media_mutation OWNER TO slaif_owner")
    op.execute("REVOKE ALL ON TABLE control.media_idempotency FROM PUBLIC")
    op.execute("REVOKE ALL ON TABLE audit.media_mutation FROM PUBLIC")

    op.execute(
        """
        CREATE FUNCTION control.slaif_media_authorize(
            p_public_id text, p_session_digest bytea, p_csrf_digest bytea,
            p_site_id uuid, p_permission text, p_state_changing boolean
        ) RETURNS TABLE (
            session_id uuid, human_user_id uuid, site_id uuid, workspace_id uuid
        ) LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog AS $fn$
            SELECT session.id, session.user_account_id, site.id, workspace.id
            FROM control.user_session AS session
            JOIN control.user_account AS account ON account.id = session.user_account_id
            JOIN control.site AS site ON site.id = p_site_id
            JOIN control.workspace AS workspace
              ON workspace.site_id = site.id
             AND workspace.created_by = account.id
             AND workspace.actor_type = 'HUMAN'
             AND workspace.status = 'ACTIVE'
             AND workspace.expires_at > CURRENT_TIMESTAMP
            WHERE session.public_id = p_public_id
              AND session.secret_digest = p_session_digest
              AND session.revoked_at IS NULL
              AND session.absolute_expires_at > CURRENT_TIMESTAMP
              AND account.status = 'ACTIVE'
              AND site.status = 'ACTIVE'
              AND (NOT p_state_changing OR session.csrf_secret_digest = p_csrf_digest)
              AND (
                  EXISTS (
                      SELECT 1 FROM control.platform_administrator AS administrator
                      WHERE administrator.user_account_id = account.id
                  )
                  OR EXISTS (
                      SELECT 1
                      FROM control.slaif_effective_human_membership(account.id, site.id) AS membership
                      WHERE p_permission = ANY(membership.effective_permissions)
                  )
              )
            ORDER BY workspace.created_at DESC, workspace.id DESC
            LIMIT 1
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_media_workspace_assert(
            p_workspace_id uuid, p_human_user_id uuid, p_site_id uuid,
            p_human_session_id uuid, p_permission text, p_operation_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE session_text text;
        DECLARE operation_text text;
        BEGIN
            session_text := NULLIF(current_setting('app.session_id', true), '');
            operation_text := NULLIF(current_setting('app.operation_id', true), '');
            IF session_text IS NULL OR operation_text IS NULL
               OR session_text::uuid IS DISTINCT FROM p_workspace_id
               OR operation_text::uuid IS DISTINCT FROM p_operation_id
            THEN
                RAISE EXCEPTION 'MEDIA_COW_CONTEXT_INVALID' USING ERRCODE = '22023';
            END IF;
            IF NOT EXISTS (
                SELECT 1
                FROM control.workspace AS workspace
                JOIN control.site AS site ON site.id = workspace.site_id
                JOIN control.user_account AS account ON account.id = workspace.created_by
                JOIN control.user_session AS session
                  ON session.id = p_human_session_id
                 AND session.user_account_id = p_human_user_id
                WHERE workspace.id = p_workspace_id
                  AND workspace.site_id = p_site_id
                  AND workspace.created_by = p_human_user_id
                  AND workspace.actor_type = 'HUMAN'
                  AND workspace.status = 'ACTIVE'
                  AND workspace.expires_at > CURRENT_TIMESTAMP
                  AND site.status = 'ACTIVE'
                  AND account.status = 'ACTIVE'
                  AND session.revoked_at IS NULL
                  AND session.absolute_expires_at > CURRENT_TIMESTAMP
                  AND (
                      EXISTS (
                          SELECT 1 FROM control.platform_administrator AS administrator
                          WHERE administrator.user_account_id = p_human_user_id
                      )
                      OR EXISTS (
                          SELECT 1
                          FROM control.slaif_effective_human_membership(p_human_user_id, p_site_id) AS membership
                          WHERE p_permission = ANY(membership.effective_permissions)
                      )
                  )
            ) THEN
                RAISE EXCEPTION 'MEDIA_WORKSPACE_NOT_AUTHORIZED' USING ERRCODE = 'P0002';
            END IF;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_media_idempotency_begin(
            p_workspace_id uuid, p_human_user_id uuid, p_site_id uuid,
            p_human_session_id uuid, p_permission text, p_key text,
            p_digest text, p_operation_id uuid
        ) RETURNS TABLE (state text, operation_id uuid, status_code integer, response_body jsonb)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE existing control.media_idempotency%ROWTYPE;
        BEGIN
            PERFORM control.slaif_media_workspace_assert(
                p_workspace_id, p_human_user_id, p_site_id, p_human_session_id,
                p_permission, p_operation_id
            );
            IF p_key IS NULL OR p_key !~ '^[A-Za-z0-9._~-]{1,128}$'
               OR p_digest IS NULL OR p_digest !~ '^[0-9a-f]{64}$'
            THEN
                RAISE EXCEPTION 'MEDIA_IDEMPOTENCY_INPUT' USING ERRCODE = 'P0001';
            END IF;
            INSERT INTO control.media_idempotency(
                workspace_id, human_user_id, site_id, idempotency_key,
                request_digest, operation_id
            ) VALUES (
                p_workspace_id, p_human_user_id, p_site_id, p_key,
                p_digest, p_operation_id
            ) ON CONFLICT (workspace_id, idempotency_key) DO NOTHING;
            IF FOUND THEN
                RETURN QUERY SELECT 'STARTED'::text, p_operation_id, NULL::integer, NULL::jsonb;
                RETURN;
            END IF;
            SELECT * INTO existing FROM control.media_idempotency
            WHERE workspace_id = p_workspace_id AND idempotency_key = p_key FOR UPDATE;
            IF existing.request_digest <> p_digest THEN
                RETURN QUERY SELECT 'MISMATCH'::text, existing.operation_id, NULL::integer, NULL::jsonb;
                RETURN;
            END IF;
            IF existing.status_code IS NULL THEN
                RAISE EXCEPTION 'MEDIA_IDEMPOTENCY_IN_PROGRESS' USING ERRCODE = 'P0001';
            END IF;
            RETURN QUERY SELECT 'REPLAY'::text, existing.operation_id,
                existing.status_code, existing.response_body;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_media_idempotency_complete(
            p_workspace_id uuid, p_human_user_id uuid, p_site_id uuid,
            p_human_session_id uuid, p_permission text, p_key text,
            p_digest text, p_operation_id uuid, p_status integer,
            p_body jsonb, p_action text, p_resource_type text, p_resource_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            PERFORM control.slaif_media_workspace_assert(
                p_workspace_id, p_human_user_id, p_site_id, p_human_session_id,
                p_permission, p_operation_id
            );
            IF p_status NOT BETWEEN 200 AND 299 OR p_resource_type <> 'media_asset'
               OR p_resource_id IS NULL OR p_body IS NULL
            THEN
                RAISE EXCEPTION 'MEDIA_IDEMPOTENCY_COMPLETION_INPUT' USING ERRCODE = 'P0001';
            END IF;
            INSERT INTO audit.media_mutation(
                operation_id, human_user_id, workspace_id, site_id, action,
                resource_id, request_digest, response_status
            ) VALUES (
                p_operation_id, p_human_user_id, p_workspace_id, p_site_id,
                p_action, p_resource_id, p_digest, p_status
            );
            UPDATE control.media_idempotency SET status_code = p_status,
                response_body = p_body, resource_type = p_resource_type,
                resource_id = p_resource_id, completed_at = CURRENT_TIMESTAMP
            WHERE workspace_id = p_workspace_id AND idempotency_key = p_key
              AND request_digest = p_digest AND operation_id = p_operation_id
              AND status_code IS NULL;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'MEDIA_IDEMPOTENCY_NOT_STARTED' USING ERRCODE = 'P0002';
            END IF;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_media_asset_register(
            p_site_id uuid, p_uploaded_by uuid, p_session_id uuid, p_permission text,
            p_filename text, p_mime_type text, p_size bigint, p_hash text,
            p_storage_key text, p_alt_text text, p_metadata jsonb,
            p_workspace_id uuid, p_human_user_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, uploaded_by uuid, filename text,
            mime_type text, size_bytes bigint, content_hash text,
            storage_key text, alt_text text, metadata jsonb,
            created_at timestamptz, updated_at timestamptz
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
               OR p_size < 1 OR p_hash !~ '^[0-9a-f]{64}$'
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
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_media_asset_get(
            p_site_id uuid, p_media_id uuid, p_human_user_id uuid,
            p_session_id uuid, p_permission text, p_workspace_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, uploaded_by uuid, filename text,
            mime_type text, size_bytes bigint, content_hash text,
            storage_key text, alt_text text, metadata jsonb,
            created_at timestamptz, updated_at timestamptz
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
        $fn$
        """
    )

    for function, signature in (*_CONTROL_FUNCTIONS, *_CONTENT_FUNCTIONS):
        _secure(function, signature)
    for function, signature in _CONTROL_FUNCTIONS:
        op.execute(f"GRANT EXECUTE ON FUNCTION {function}({signature}) TO slaif_media")
    for function, signature in _CONTENT_FUNCTIONS:
        op.execute(f"GRANT EXECUTE ON FUNCTION {function}({signature}) TO slaif_media")
    op.execute("GRANT USAGE ON SCHEMA control TO slaif_media")
    op.execute("GRANT USAGE ON SCHEMA content TO slaif_media")


def downgrade() -> None:
    for function, signature in (*_CONTENT_FUNCTIONS, *_CONTROL_FUNCTIONS):
        op.execute(f"DROP FUNCTION IF EXISTS {function}({signature}) CASCADE")
    op.execute("DROP TABLE IF EXISTS audit.media_mutation CASCADE")
    op.execute("DROP TABLE IF EXISTS control.media_idempotency CASCADE")
