# ruff: noqa: E501
"""Bind durable browser artifacts to the authenticated worker request."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "037_001"
down_revision: str | Sequence[str] | None = "036_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_REGISTER_OLD = "control.slaif_agent_browser_artifact_register(uuid,uuid,uuid,text,text,text,bigint,text,text,timestamptz)"
_REGISTER_NEW = "control.slaif_agent_browser_artifact_register(uuid,uuid,uuid,text,uuid,text,text,bigint,text,text,timestamptz)"
_RETRIEVE = (
    "control.slaif_agent_browser_artifact_retrieve(uuid,uuid,uuid,uuid,uuid,uuid)"
)
_ROLES = (
    "slaif_control",
    "slaif_editor_runtime",
    "slaif_agent_runtime",
    "slaif_public_reader",
    "slaif_preview_reader",
    "slaif_reviewer",
    "slaif_scheduler",
    "slaif_media",
    "slaif_gc",
)


def _secure(functions: tuple[str, ...]) -> None:
    for function in functions:
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        for role in _ROLES:
            op.execute(f"REVOKE ALL ON FUNCTION {function} FROM {role}")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_REGISTER_NEW} TO slaif_agent_runtime")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_RETRIEVE} TO slaif_agent_runtime")


def upgrade() -> None:
    # Existing artifacts cannot be truthfully backfilled with a worker request.
    # Fresh-install state is authoritative; a non-empty legacy table fails safe.
    op.execute(
        """
        DO $check$
        BEGIN
            IF EXISTS (SELECT 1 FROM control.browser_artifact LIMIT 1) THEN
                RAISE EXCEPTION 'BROWSER_ARTIFACT_WORKER_BINDING_REQUIRES_EMPTY_TABLE';
            END IF;
        END
        $check$
        """
    )
    op.execute(
        """
        ALTER TABLE control.browser_artifact
            ADD COLUMN worker_request_id UUID NOT NULL,
            ADD CONSTRAINT browser_artifact_worker_request_kind_unique
                UNIQUE (worker_request_id, kind)
        """
    )
    op.execute(
        """
        CREATE INDEX browser_artifact_worker_request
            ON control.browser_artifact(worker_request_id, run_id, id)
        """
    )
    op.execute(f"DROP FUNCTION {_REGISTER_OLD}")
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_browser_artifact_register(
            p_run_id uuid, p_lease_id uuid, p_artifact_id uuid, p_kind text,
            p_worker_request_id uuid, p_mime_type text, p_sha256 text,
            p_size_bytes bigint, p_target text, p_route_digest text,
            p_expires_at timestamptz
        ) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER VOLATILE
        SET search_path = pg_catalog AS $fn$
        DECLARE
            selected_run record;
            existing record;
            used_bytes numeric;
        BEGIN
            IF p_artifact_id IS NULL OR p_worker_request_id IS NULL
               OR p_kind NOT IN (
                    'screenshot','accessibility-summary','structure-summary',
                    'heading-summary','link-summary','media-summary',
                    'overflow-summary','console-summary','failed-request-summary'
               )
               OR p_mime_type NOT IN ('image/png','application/json','text/plain')
               OR (p_kind = 'screenshot' AND p_mime_type <> 'image/png')
               OR p_sha256 !~ '^[0-9a-f]{64}$'
               OR p_route_digest !~ '^[0-9a-f]{64}$'
               OR p_size_bytes NOT BETWEEN 1 AND 1073741824
               OR p_expires_at IS NULL OR p_expires_at <= CURRENT_TIMESTAMP
            THEN
                RAISE EXCEPTION 'INVALID_BROWSER_ARTIFACT' USING ERRCODE = '22023';
            END IF;
            SELECT run.* INTO selected_run FROM control.browser_run AS run
            WHERE run.id = p_run_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'BROWSER_LEASE_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            PERFORM pg_advisory_xact_lock_shared(
                hashtextextended(selected_run.workspace_id::text, 280)
            );
            IF NOT control.slaif_agent_browser_authorized(
                selected_run.capability_id, selected_run.site_id,
                selected_run.workspace_id, selected_run.delegator_id
            ) OR selected_run.state <> 'RUNNING'
               OR selected_run.lease_id IS DISTINCT FROM p_lease_id
               OR selected_run.lease_expires_at <= CURRENT_TIMESTAMP
            THEN
                RAISE EXCEPTION 'BROWSER_LEASE_NOT_CURRENT' USING ERRCODE = 'P0002';
            END IF;
            IF p_target <> selected_run.target
               OR p_route_digest <> selected_run.route_digest
               OR NOT p_kind = ANY(selected_run.evidence)
               OR p_expires_at > selected_run.expires_at
            THEN
                RAISE EXCEPTION 'BROWSER_ARTIFACT_RUN_MISMATCH' USING ERRCODE = 'P0001';
            END IF;
            SELECT artifact.* INTO existing
            FROM control.browser_artifact AS artifact
            WHERE artifact.worker_request_id = p_worker_request_id
            ORDER BY artifact.id
            LIMIT 1 FOR UPDATE;
            IF FOUND AND existing.run_id IS DISTINCT FROM p_run_id THEN
                RAISE EXCEPTION 'BROWSER_ARTIFACT_MISMATCH' USING ERRCODE = 'P0001';
            END IF;
            SELECT artifact.* INTO existing FROM control.browser_artifact AS artifact
            WHERE artifact.id = p_artifact_id FOR UPDATE;
            IF FOUND THEN
                IF existing.run_id = p_run_id
                   AND existing.worker_request_id = p_worker_request_id
                   AND existing.kind = p_kind
                   AND existing.mime_type = p_mime_type
                   AND existing.sha256 = p_sha256
                   AND existing.size_bytes = p_size_bytes
                   AND existing.target = p_target
                   AND existing.route_digest = p_route_digest
                   AND existing.expires_at = p_expires_at
                THEN
                    RETURN existing.id;
                END IF;
                RAISE EXCEPTION 'BROWSER_ARTIFACT_MISMATCH' USING ERRCODE = 'P0001';
            END IF;
            SELECT artifact.* INTO existing FROM control.browser_artifact AS artifact
            WHERE artifact.worker_request_id = p_worker_request_id
              AND artifact.kind = p_kind FOR UPDATE;
            IF FOUND THEN
                RAISE EXCEPTION 'BROWSER_ARTIFACT_MISMATCH' USING ERRCODE = 'P0001';
            END IF;
            SELECT COALESCE(sum(size_bytes), 0) INTO used_bytes
            FROM control.browser_artifact WHERE run_id = p_run_id;
            IF used_bytes + p_size_bytes > selected_run.reserved_artifact_bytes
               OR EXISTS (
                    SELECT 1 FROM control.browser_artifact
                    WHERE run_id = p_run_id AND kind = p_kind
               )
            THEN
                RAISE EXCEPTION 'BROWSER_ARTIFACT_QUOTA_EXCEEDED' USING ERRCODE = 'P0001';
            END IF;
            INSERT INTO control.browser_artifact (
                id, run_id, site_id, workspace_id, capability_id,
                delegator_id, kind, worker_request_id, mime_type, sha256,
                size_bytes, target, route_digest, expires_at
            ) VALUES (
                p_artifact_id, p_run_id, selected_run.site_id,
                selected_run.workspace_id, selected_run.capability_id,
                selected_run.delegator_id, p_kind, p_worker_request_id,
                p_mime_type, p_sha256, p_size_bytes, p_target, p_route_digest,
                p_expires_at
            );
            INSERT INTO audit.browser_event (
                run_id, operation_id, capability_id, workspace_id, site_id,
                delegator_id, event_type, attempt, lease_id, artifact_id,
                details
            ) VALUES (
                selected_run.id, selected_run.operation_id,
                selected_run.capability_id, selected_run.workspace_id,
                selected_run.site_id, selected_run.delegator_id,
                'ARTIFACT_REGISTERED', selected_run.attempt_count, p_lease_id,
                p_artifact_id,
                jsonb_build_object('kind', p_kind, 'size_bytes', p_size_bytes)
            );
            RETURN p_artifact_id;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_browser_artifact_retrieve(
            p_capability_id uuid, p_site_id uuid, p_workspace_id uuid,
            p_delegator_id uuid, p_run_id uuid, p_artifact_id uuid
        ) RETURNS TABLE (
            worker_request_id uuid, run_id uuid, site_id uuid, workspace_id uuid,
            artifact_id uuid, kind text, mime_type text, sha256 text,
            size_bytes bigint, target text, route_digest text,
            created_at timestamptz, expires_at timestamptz, visibility text
        ) LANGUAGE sql SECURITY DEFINER STABLE
        SET search_path = pg_catalog ROWS 1 AS $fn$
            SELECT artifact.worker_request_id, artifact.run_id, artifact.site_id,
                artifact.workspace_id, artifact.id, artifact.kind,
                artifact.mime_type, artifact.sha256, artifact.size_bytes,
                artifact.target, artifact.route_digest, artifact.created_at,
                artifact.expires_at, artifact.visibility
            FROM control.browser_artifact AS artifact
            JOIN control.browser_run AS run ON run.id = artifact.run_id
            WHERE artifact.id = p_artifact_id
              AND run.id = p_run_id
              AND artifact.run_id = p_run_id
              AND artifact.capability_id = p_capability_id
              AND artifact.site_id = p_site_id
              AND artifact.workspace_id = p_workspace_id
              AND artifact.delegator_id = p_delegator_id
              AND run.capability_id = p_capability_id
              AND run.site_id = p_site_id
              AND run.workspace_id = p_workspace_id
              AND run.delegator_id = p_delegator_id
              AND run.state = 'COMPLETED'
              AND run.expires_at > CURRENT_TIMESTAMP
              AND artifact.expires_at > CURRENT_TIMESTAMP
              AND artifact.visibility = 'PRIVATE'
              AND control.slaif_agent_browser_authorized(
                    p_capability_id, p_site_id, p_workspace_id, p_delegator_id
              )
        $fn$
        """
    )
    _secure((_REGISTER_NEW, _RETRIEVE))


def downgrade() -> None:
    for function in (_RETRIEVE, _REGISTER_NEW):
        op.execute(f"DROP FUNCTION IF EXISTS {function}")
    op.execute("DROP INDEX IF EXISTS control.browser_artifact_worker_request")
    op.execute(
        "ALTER TABLE control.browser_artifact "
        "DROP CONSTRAINT IF EXISTS browser_artifact_worker_request_kind_unique, "
        "DROP COLUMN IF EXISTS worker_request_id"
    )
    # Restore the 036-compatible function signature/body.
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_browser_artifact_register(
            p_run_id uuid, p_lease_id uuid, p_artifact_id uuid, p_kind text,
            p_mime_type text, p_sha256 text, p_size_bytes bigint,
            p_target text, p_route_digest text, p_expires_at timestamptz
        ) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER VOLATILE
        SET search_path = pg_catalog AS $fn$
        DECLARE selected_run record; existing record; used_bytes numeric;
        BEGIN
            IF p_artifact_id IS NULL OR p_kind NOT IN (
                'screenshot','accessibility-summary','structure-summary',
                'heading-summary','link-summary','media-summary',
                'overflow-summary','console-summary','failed-request-summary'
            ) OR p_mime_type NOT IN ('image/png','application/json','text/plain')
               OR (p_kind = 'screenshot' AND p_mime_type <> 'image/png')
               OR p_sha256 !~ '^[0-9a-f]{64}$'
               OR p_route_digest !~ '^[0-9a-f]{64}$'
               OR p_size_bytes NOT BETWEEN 1 AND 1073741824
               OR p_expires_at IS NULL OR p_expires_at <= CURRENT_TIMESTAMP THEN
                RAISE EXCEPTION 'INVALID_BROWSER_ARTIFACT' USING ERRCODE = '22023';
            END IF;
            SELECT run.* INTO selected_run FROM control.browser_run AS run
            WHERE run.id = p_run_id FOR UPDATE;
            IF NOT FOUND THEN RAISE EXCEPTION 'BROWSER_LEASE_NOT_FOUND' USING ERRCODE = 'P0002'; END IF;
            PERFORM pg_advisory_xact_lock_shared(hashtextextended(selected_run.workspace_id::text, 280));
            IF NOT control.slaif_agent_browser_authorized(selected_run.capability_id, selected_run.site_id, selected_run.workspace_id, selected_run.delegator_id)
               OR selected_run.state <> 'RUNNING' OR selected_run.lease_id IS DISTINCT FROM p_lease_id
               OR selected_run.lease_expires_at <= CURRENT_TIMESTAMP THEN
                RAISE EXCEPTION 'BROWSER_LEASE_NOT_CURRENT' USING ERRCODE = 'P0002';
            END IF;
            IF p_target <> selected_run.target OR p_route_digest <> selected_run.route_digest
               OR NOT p_kind = ANY(selected_run.evidence) OR p_expires_at > selected_run.expires_at THEN
                RAISE EXCEPTION 'BROWSER_ARTIFACT_RUN_MISMATCH' USING ERRCODE = 'P0001';
            END IF;
            SELECT artifact.* INTO existing FROM control.browser_artifact AS artifact WHERE artifact.id = p_artifact_id FOR UPDATE;
            IF FOUND THEN
                IF existing.run_id = p_run_id AND existing.kind = p_kind AND existing.mime_type = p_mime_type
                   AND existing.sha256 = p_sha256 AND existing.size_bytes = p_size_bytes
                   AND existing.target = p_target AND existing.route_digest = p_route_digest
                   AND existing.expires_at = p_expires_at THEN RETURN existing.id; END IF;
                RAISE EXCEPTION 'BROWSER_ARTIFACT_MISMATCH' USING ERRCODE = 'P0001';
            END IF;
            SELECT COALESCE(sum(size_bytes), 0) INTO used_bytes FROM control.browser_artifact WHERE run_id = p_run_id;
            IF used_bytes + p_size_bytes > selected_run.reserved_artifact_bytes OR EXISTS (
                SELECT 1 FROM control.browser_artifact WHERE run_id = p_run_id AND kind = p_kind
            ) THEN RAISE EXCEPTION 'BROWSER_ARTIFACT_QUOTA_EXCEEDED' USING ERRCODE = 'P0001'; END IF;
            INSERT INTO control.browser_artifact (id, run_id, site_id, workspace_id, capability_id, delegator_id, kind, mime_type, sha256, size_bytes, target, route_digest, expires_at)
            VALUES (p_artifact_id, p_run_id, selected_run.site_id, selected_run.workspace_id, selected_run.capability_id, selected_run.delegator_id, p_kind, p_mime_type, p_sha256, p_size_bytes, p_target, p_route_digest, p_expires_at);
            INSERT INTO audit.browser_event (run_id, operation_id, capability_id, workspace_id, site_id, delegator_id, event_type, attempt, lease_id, artifact_id, details)
            VALUES (selected_run.id, selected_run.operation_id, selected_run.capability_id, selected_run.workspace_id, selected_run.site_id, selected_run.delegator_id, 'ARTIFACT_REGISTERED', selected_run.attempt_count, p_lease_id, p_artifact_id, jsonb_build_object('kind', p_kind, 'size_bytes', p_size_bytes));
            RETURN p_artifact_id;
        END;
        $fn$
        """
    )
    op.execute(f"ALTER FUNCTION {_REGISTER_OLD} OWNER TO slaif_owner")
    op.execute(f"REVOKE ALL ON FUNCTION {_REGISTER_OLD} FROM PUBLIC")
    op.execute(f"GRANT EXECUTE ON FUNCTION {_REGISTER_OLD} TO slaif_agent_runtime")
