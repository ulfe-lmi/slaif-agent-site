# ruff: noqa: E501
"""Complete Agent session authority propagation, quotas, listing, and audit."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "039_001"
down_revision: str | Sequence[str] | None = "038_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for column in ("request_used", "mutation_used", "delete_used", "upload_used"):
        op.execute(
            f"ALTER TABLE control.capability ADD COLUMN IF NOT EXISTS {column} integer NOT NULL DEFAULT 0"
        )
    op.execute(
        "ALTER TABLE control.workspace ALTER COLUMN request_quota SET DEFAULT 1000"
    )
    op.execute(
        "ALTER TABLE control.workspace ALTER COLUMN mutation_quota SET DEFAULT 500"
    )
    op.execute("UPDATE control.workspace SET request_quota=1000 WHERE request_quota=0")
    op.execute("UPDATE control.workspace SET mutation_quota=500 WHERE mutation_quota=0")
    op.execute(
        "ALTER TABLE control.capability ALTER COLUMN request_quota SET DEFAULT 1000"
    )
    op.execute(
        "ALTER TABLE control.capability ALTER COLUMN mutation_quota SET DEFAULT 500"
    )
    op.execute("UPDATE control.capability SET request_quota=1000 WHERE request_quota=0")
    op.execute(
        "UPDATE control.capability SET mutation_quota=500 WHERE mutation_quota=0"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS audit.human_agent_session (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            action text NOT NULL CHECK (action IN ('WORKSPACE_CREATED','CAPABILITY_ISSUED','CAPABILITY_REVOKED')),
            actor_user_id uuid NOT NULL REFERENCES control.user_account(id),
            site_id uuid NOT NULL REFERENCES control.site(id),
            workspace_id uuid NOT NULL REFERENCES control.workspace(id),
            capability_public_id text,
            details jsonb NOT NULL DEFAULT '{}'::jsonb,
            occurred_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT human_agent_session_details_bounded CHECK (jsonb_typeof(details)='object' AND octet_length(details::text) <= 4096)
        )
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_human_agent_audit_trigger()
        RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE actor uuid;
        BEGIN
            actor := NULLIF(current_setting('app.human_user_id', true), '')::uuid;
            IF pg_has_role(session_user, 'slaif_control', 'MEMBER') AND TG_TABLE_NAME = 'workspace' AND TG_OP = 'INSERT'
              AND (to_jsonb(NEW)->>'actor_type') = 'AGENT' THEN
                IF actor IS NULL THEN actor := COALESCE(NEW.delegator_id, NEW.created_by); END IF;
                INSERT INTO audit.human_agent_session(action,actor_user_id,site_id,workspace_id,details)
                VALUES ('WORKSPACE_CREATED',actor,NEW.site_id,NEW.id,jsonb_build_object('preset',NEW.delegation_preset,'scopes',NEW.effective_scopes,'source_origins',NEW.source_origins,'request_quota',NEW.request_quota,'mutation_quota',NEW.mutation_quota,'delete_quota',NEW.delete_quota,'upload_quota',NEW.upload_quota,'browser_quota',NEW.browser_quota));
            ELSIF pg_has_role(session_user, 'slaif_control', 'MEMBER') AND TG_TABLE_NAME = 'capability' AND TG_OP = 'INSERT' THEN
                INSERT INTO audit.human_agent_session(action,actor_user_id,site_id,workspace_id,capability_public_id,details)
                SELECT 'CAPABILITY_ISSUED',COALESCE(w.delegator_id,w.created_by),w.site_id,NEW.workspace_id,NEW.public_id,'{}'::jsonb FROM control.workspace w WHERE w.id=NEW.workspace_id;
            ELSIF pg_has_role(session_user, 'slaif_control', 'MEMBER') AND TG_TABLE_NAME = 'capability' AND TG_OP = 'UPDATE'
              AND (to_jsonb(OLD)->>'revoked_at') IS NULL
              AND (to_jsonb(NEW)->>'revoked_at') IS NOT NULL THEN
                INSERT INTO audit.human_agent_session(action,actor_user_id,site_id,workspace_id,capability_public_id,details)
                SELECT 'CAPABILITY_REVOKED',COALESCE(w.delegator_id,w.created_by),w.site_id,NEW.workspace_id,NEW.public_id,'{}'::jsonb FROM control.workspace w WHERE w.id=NEW.workspace_id;
            END IF;
            IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
            RETURN NEW;
        END; $fn$
        """
    )
    op.execute(
        "DROP TRIGGER IF EXISTS human_agent_workspace_audit ON control.workspace"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS human_agent_capability_audit ON control.capability"
    )
    op.execute(
        "CREATE TRIGGER human_agent_workspace_audit AFTER INSERT ON control.workspace FOR EACH ROW EXECUTE FUNCTION control.slaif_human_agent_audit_trigger()"
    )
    op.execute(
        "CREATE TRIGGER human_agent_capability_audit AFTER INSERT OR UPDATE OF revoked_at ON control.capability FOR EACH ROW EXECUTE FUNCTION control.slaif_human_agent_audit_trigger()"
    )

    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_capability_context(p_public_id text)
        RETURNS TABLE(id uuid, public_id text, secret_digest text, workspace_id uuid,
            site_id uuid, created_by uuid, scopes jsonb, created_at timestamptz,
            expires_at timestamptz, revoked_at timestamptz,
            browser_max_runs integer, browser_max_concurrent_runs integer,
            browser_max_screenshots integer, browser_max_artifact_bytes bigint,
            browser_max_routes_per_run integer, browser_max_evidence_per_run integer,
            browser_max_duration_seconds integer, browser_max_attempts integer,
            browser_allowed_targets text[], resource_constraints jsonb,
            source_origins text[], request_quota integer, mutation_quota integer,
            delete_quota integer, upload_quota integer, request_used integer,
            mutation_used integer, delete_used integer, upload_used integer)
        LANGUAGE sql SECURITY DEFINER STABLE SET search_path = pg_catalog AS $fn$
            SELECT c.id,c.public_id,c.secret_digest,w.id,w.site_id,COALESCE(w.delegator_id,w.created_by),c.scopes,
                c.created_at,c.expires_at,c.revoked_at,c.browser_max_runs,c.browser_max_concurrent_runs,
                c.browser_max_screenshots,c.browser_max_artifact_bytes,c.browser_max_routes_per_run,
                c.browser_max_evidence_per_run,c.browser_max_duration_seconds,c.browser_max_attempts,
                c.browser_allowed_targets,c.resource_constraints,c.source_origins,c.request_quota,
                c.mutation_quota,c.delete_quota,c.upload_quota,c.request_used,c.mutation_used,
                c.delete_used,c.upload_used
            FROM control.capability c JOIN control.workspace w ON w.id=c.workspace_id
            JOIN control.site s ON s.id=w.site_id JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
            WHERE c.public_id=p_public_id AND c.revoked_at IS NULL AND c.expires_at>CURRENT_TIMESTAMP
              AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE' AND a.status='ACTIVE'
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_quota_consume(
            p_capability_id uuid, p_workspace_id uuid, p_kind text
        ) RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE consumed boolean := false;
        BEGIN
            IF p_kind NOT IN ('request','mutation','delete','upload') THEN RETURN false; END IF;
            IF p_kind='request' THEN
                UPDATE control.capability c SET request_used=c.request_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL AND c.expires_at>CURRENT_TIMESTAMP
                  AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE' AND a.status='ACTIVE' AND c.request_used<c.request_quota
                RETURNING true INTO consumed;
            ELSIF p_kind='mutation' THEN
                UPDATE control.capability c SET mutation_used=c.mutation_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL AND c.expires_at>CURRENT_TIMESTAMP
                  AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE' AND a.status='ACTIVE' AND c.mutation_used<c.mutation_quota
                RETURNING true INTO consumed;
            ELSIF p_kind='delete' THEN
                UPDATE control.capability c SET delete_used=c.delete_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL AND c.expires_at>CURRENT_TIMESTAMP
                  AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE' AND a.status='ACTIVE' AND c.delete_used<c.delete_quota
                RETURNING true INTO consumed;
            ELSE
                UPDATE control.capability c SET upload_used=c.upload_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL AND c.expires_at>CURRENT_TIMESTAMP
                  AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE' AND a.status='ACTIVE' AND c.upload_used<c.upload_quota
                RETURNING true INTO consumed;
            END IF;
            RETURN COALESCE(consumed,false);
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_human_agent_workspace_list(
            p_site_id uuid, p_user_id uuid
        ) RETURNS TABLE(id uuid, site_id uuid, created_by uuid, delegator_id uuid, title text,
            task_description text, status text, delegation_preset text, effective_scopes jsonb,
            resource_constraints jsonb, source_origins text[], request_quota integer,
            mutation_quota integer, delete_quota integer, upload_quota integer, browser_quota integer,
            base_site_revision bigint, created_at timestamptz, expires_at timestamptz)
        LANGUAGE sql SECURITY DEFINER STABLE SET search_path = pg_catalog AS $fn$
            SELECT w.id,w.site_id,w.created_by,w.delegator_id,w.title,w.task_description,w.status,
                w.delegation_preset,w.effective_scopes,w.resource_constraints,w.source_origins,
                w.request_quota,w.mutation_quota,w.delete_quota,w.upload_quota,w.browser_quota,
                w.base_site_revision,w.created_at,w.expires_at FROM control.workspace w
            JOIN control.site s ON s.id=w.site_id JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
            WHERE w.site_id=p_site_id
              AND (COALESCE(w.delegator_id,w.created_by)=p_user_id OR EXISTS (SELECT 1 FROM control.platform_administrator WHERE user_account_id=p_user_id))
              AND w.actor_type='AGENT' AND s.status='ACTIVE' AND a.status='ACTIVE'
            ORDER BY w.created_at DESC,w.id DESC
        $fn$
        """
    )
    for name, signature, role in (
        ("slaif_agent_capability_context", "text", "slaif_agent_runtime"),
        ("slaif_agent_quota_consume", "uuid,uuid,text", "slaif_agent_runtime"),
        ("slaif_human_agent_workspace_list", "uuid,uuid", "slaif_control"),
    ):
        op.execute(f'ALTER FUNCTION control.{name}({signature}) OWNER TO "slaif_owner"')
        op.execute(f"REVOKE ALL ON FUNCTION control.{name}({signature}) FROM PUBLIC")
        op.execute(f'GRANT EXECUTE ON FUNCTION control.{name}({signature}) TO "{role}"')
    op.execute(
        'GRANT EXECUTE ON FUNCTION control.slaif_agent_capability_context(text) TO "slaif_control"'
    )


def downgrade() -> None:
    op.execute(
        "DROP TRIGGER IF EXISTS human_agent_workspace_audit ON control.workspace"
    )
    op.execute(
        "DROP TRIGGER IF EXISTS human_agent_capability_audit ON control.capability"
    )
    for name, signature in (
        ("slaif_agent_capability_context", "text"),
        ("slaif_agent_quota_consume", "uuid,uuid,text"),
        ("slaif_human_agent_workspace_list", "uuid,uuid"),
        ("slaif_human_agent_audit_trigger", ""),
    ):
        op.execute(f"DROP FUNCTION IF EXISTS control.{name}({signature}) CASCADE")
    op.execute("DROP TABLE IF EXISTS audit.human_agent_session")
