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
        "ALTER TABLE control.workspace ADD COLUMN IF NOT EXISTS create_idempotency_key text"
    )
    op.execute(
        "ALTER TABLE control.workspace ADD COLUMN IF NOT EXISTS create_request_digest text"
    )
    op.execute(
        "ALTER TABLE control.capability ADD COLUMN IF NOT EXISTS issue_idempotency_key text"
    )
    op.execute(
        "ALTER TABLE control.capability ADD COLUMN IF NOT EXISTS issue_request_digest text"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS workspace_agent_create_idempotency ON control.workspace(site_id,created_by,create_idempotency_key) WHERE create_idempotency_key IS NOT NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS capability_agent_issue_idempotency ON control.capability(workspace_id,issue_idempotency_key) WHERE issue_idempotency_key IS NOT NULL"
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
                SELECT 'CAPABILITY_ISSUED',COALESCE(actor,w.delegator_id,w.created_by),w.site_id,NEW.workspace_id,NEW.public_id,'{}'::jsonb FROM control.workspace w WHERE w.id=NEW.workspace_id;
            ELSIF pg_has_role(session_user, 'slaif_control', 'MEMBER') AND TG_TABLE_NAME = 'capability' AND TG_OP = 'UPDATE'
              AND (to_jsonb(OLD)->>'revoked_at') IS NULL
              AND (to_jsonb(NEW)->>'revoked_at') IS NOT NULL THEN
                INSERT INTO audit.human_agent_session(action,actor_user_id,site_id,workspace_id,capability_public_id,details)
                SELECT 'CAPABILITY_REVOKED',COALESCE(actor,w.delegator_id,w.created_by),w.site_id,NEW.workspace_id,NEW.public_id,'{}'::jsonb FROM control.workspace w WHERE w.id=NEW.workspace_id;
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
        CREATE FUNCTION control.slaif_human_agent_workspace_create_idempotent(
            p_site_id uuid, p_user_id uuid, p_title text, p_description text,
            p_preset text, p_requested_scopes text[], p_constraints jsonb,
            p_origins text[], p_request_quota integer, p_mutation_quota integer,
            p_delete_quota integer, p_upload_quota integer, p_browser_quota integer,
            p_duration_hours integer, p_idempotency_key text, p_request_digest text
        ) RETURNS TABLE (id uuid, site_id uuid, created_by uuid, delegator_id uuid,
            title text, task_description text, status text, delegation_preset text,
            effective_scopes jsonb, resource_constraints jsonb, source_origins text[],
            request_quota integer, mutation_quota integer, delete_quota integer,
            upload_quota integer, browser_quota integer, base_site_revision bigint,
            created_at timestamptz, expires_at timestamptz, replayed boolean)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE existing record; created_id uuid;
        BEGIN
            PERFORM set_config('app.human_user_id', p_user_id::text, true);
            IF p_idempotency_key !~ '^[A-Za-z0-9._~-]{1,128}$'
               OR p_request_digest !~ '^[0-9a-f]{64}$'
            THEN RAISE EXCEPTION 'AGENT_CONTROL_INPUT_INVALID' USING ERRCODE='P0001'; END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(p_site_id::text || ':' || p_user_id::text || ':' || p_idempotency_key, 992));
            SELECT w.* INTO existing FROM control.workspace w
            WHERE w.site_id=p_site_id AND w.created_by=p_user_id AND w.create_idempotency_key=p_idempotency_key
            FOR UPDATE;
            IF FOUND THEN
                IF existing.create_request_digest <> p_request_digest THEN RAISE EXCEPTION 'AGENT_CONTROL_IDEMPOTENCY_MISMATCH' USING ERRCODE='P0001'; END IF;
                RETURN QUERY SELECT existing.id,existing.site_id,existing.created_by,existing.delegator_id,existing.title,existing.task_description,existing.status,existing.delegation_preset,existing.effective_scopes,existing.resource_constraints,existing.source_origins,existing.request_quota,existing.mutation_quota,existing.delete_quota,existing.upload_quota,existing.browser_quota,existing.base_site_revision,existing.created_at,existing.expires_at,TRUE;
                RETURN;
            END IF;
            SELECT created.id INTO created_id FROM control.slaif_human_agent_workspace_create(p_site_id,p_user_id,p_title,p_description,p_preset,p_requested_scopes,p_constraints,p_origins,p_request_quota,p_mutation_quota,p_delete_quota,p_upload_quota,p_browser_quota,p_duration_hours) AS created;
            UPDATE control.workspace AS ws SET create_idempotency_key=p_idempotency_key, create_request_digest=p_request_digest WHERE ws.id=created_id;
            RETURN QUERY SELECT w.id,w.site_id,w.created_by,w.delegator_id,w.title,w.task_description,w.status,w.delegation_preset,w.effective_scopes,w.resource_constraints,w.source_origins,w.request_quota,w.mutation_quota,w.delete_quota,w.upload_quota,w.browser_quota,w.base_site_revision,w.created_at,w.expires_at,FALSE FROM control.workspace w WHERE w.id=created_id;
        END; $fn$
        """
    )

    op.execute(
        """
        CREATE FUNCTION control.slaif_human_agent_capability_create_idempotent(
            p_workspace_id uuid, p_site_id uuid, p_user_id uuid, p_public_id text,
            p_secret_digest text, p_idempotency_key text, p_request_digest text
        ) RETURNS TABLE (id uuid, public_id text, workspace_id uuid, site_id uuid,
            scopes jsonb, created_at timestamptz, expires_at timestamptz,
            resource_constraints jsonb, source_origins text[], request_quota integer,
            mutation_quota integer, delete_quota integer, upload_quota integer,
            replayed boolean)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE existing record; created_id uuid;
        BEGIN
            PERFORM set_config('app.human_user_id', p_user_id::text, true);
            IF p_idempotency_key !~ '^[A-Za-z0-9._~-]{1,128}$' OR p_request_digest !~ '^[0-9a-f]{64}$'
            THEN RAISE EXCEPTION 'AGENT_CONTROL_INPUT_INVALID' USING ERRCODE='P0001'; END IF;
            PERFORM pg_advisory_xact_lock(hashtextextended(p_workspace_id::text || ':' || p_idempotency_key, 993));
            SELECT c.* INTO existing FROM control.capability c WHERE c.workspace_id=p_workspace_id AND c.issue_idempotency_key=p_idempotency_key FOR UPDATE;
            IF FOUND THEN
                IF existing.issue_request_digest <> p_request_digest THEN RAISE EXCEPTION 'AGENT_CONTROL_IDEMPOTENCY_MISMATCH' USING ERRCODE='P0001'; END IF;
                RETURN QUERY SELECT existing.id,existing.public_id,existing.workspace_id,w.site_id,existing.scopes,existing.created_at,existing.expires_at,existing.resource_constraints,existing.source_origins,existing.request_quota,existing.mutation_quota,existing.delete_quota,existing.upload_quota,TRUE FROM control.workspace w WHERE w.id=existing.workspace_id;
                RETURN;
            END IF;
            SELECT created.id INTO created_id FROM control.slaif_human_agent_capability_create(p_workspace_id,p_site_id,p_user_id,p_public_id,p_secret_digest) AS created;
            UPDATE control.capability AS cap SET issue_idempotency_key=p_idempotency_key, issue_request_digest=p_request_digest WHERE cap.id=created_id;
            RETURN QUERY SELECT c.id,c.public_id,c.workspace_id,w.site_id,c.scopes,c.created_at,c.expires_at,c.resource_constraints,c.source_origins,c.request_quota,c.mutation_quota,c.delete_quota,c.upload_quota,FALSE FROM control.capability c JOIN control.workspace w ON w.id=c.workspace_id WHERE c.id=created_id;
        END; $fn$
        """
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
              AND (
                EXISTS (SELECT 1 FROM control.platform_administrator pa WHERE pa.user_account_id=COALESCE(w.delegator_id,w.created_by))
                OR EXISTS (
                    SELECT 1 FROM control.slaif_effective_human_membership(COALESCE(w.delegator_id,w.created_by),w.site_id) m
                    WHERE m.effective_ceiling >= CASE w.delegation_preset
                        WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1
                        WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2
                        WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3
                        WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END
                )
              )
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
                  AND (
                    EXISTS (SELECT 1 FROM control.platform_administrator pa WHERE pa.user_account_id=COALESCE(w.delegator_id,w.created_by))
                    OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(COALESCE(w.delegator_id,w.created_by),w.site_id) m WHERE m.effective_ceiling >= CASE w.delegation_preset WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1 WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2 WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3 WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END)
                  )
                RETURNING true INTO consumed;
            ELSIF p_kind='mutation' THEN
                UPDATE control.capability c SET mutation_used=c.mutation_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL AND c.expires_at>CURRENT_TIMESTAMP
                  AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE' AND a.status='ACTIVE' AND c.mutation_used<c.mutation_quota
                  AND (
                    EXISTS (SELECT 1 FROM control.platform_administrator pa WHERE pa.user_account_id=COALESCE(w.delegator_id,w.created_by))
                    OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(COALESCE(w.delegator_id,w.created_by),w.site_id) m WHERE m.effective_ceiling >= CASE w.delegation_preset WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1 WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2 WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3 WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END)
                  )
                RETURNING true INTO consumed;
            ELSIF p_kind='delete' THEN
                UPDATE control.capability c SET delete_used=c.delete_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL AND c.expires_at>CURRENT_TIMESTAMP
                  AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE' AND a.status='ACTIVE' AND c.delete_used<c.delete_quota
                  AND (
                    EXISTS (SELECT 1 FROM control.platform_administrator pa WHERE pa.user_account_id=COALESCE(w.delegator_id,w.created_by))
                    OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(COALESCE(w.delegator_id,w.created_by),w.site_id) m WHERE m.effective_ceiling >= CASE w.delegation_preset WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1 WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2 WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3 WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END)
                  )
                RETURNING true INTO consumed;
            ELSE
                UPDATE control.capability c SET upload_used=c.upload_used+1
                FROM control.workspace w JOIN control.site s ON s.id=w.site_id JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
                WHERE c.id=p_capability_id AND c.workspace_id=p_workspace_id
                  AND w.id=c.workspace_id AND c.revoked_at IS NULL AND c.expires_at>CURRENT_TIMESTAMP
                  AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP AND s.status='ACTIVE' AND a.status='ACTIVE' AND c.upload_used<c.upload_quota
                  AND (
                    EXISTS (SELECT 1 FROM control.platform_administrator pa WHERE pa.user_account_id=COALESCE(w.delegator_id,w.created_by))
                    OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(COALESCE(w.delegator_id,w.created_by),w.site_id) m WHERE m.effective_ceiling >= CASE w.delegation_preset WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1 WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2 WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3 WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END)
                  )
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
              AND (COALESCE(w.delegator_id,w.created_by)=p_user_id
                   OR EXISTS (SELECT 1 FROM control.platform_administrator WHERE user_account_id=p_user_id)
                   OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(p_user_id,p_site_id) m WHERE 'workspace:read-all'=ANY(m.effective_permissions)))
              AND w.actor_type='AGENT' AND s.status='ACTIVE' AND a.status='ACTIVE'
            ORDER BY w.created_at DESC,w.id DESC
        $fn$
        """
    )
    # Recheck the delegator's current membership before reserving an Agent
    # mutation.  This closes the deactivate/lower-ceiling race between HTTP
    # authentication and the shared COW transaction.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_idempotency_begin(
            p_capability_id uuid, p_workspace_id uuid, p_idempotency_key text,
            p_request_digest text, p_operation_id uuid
        ) RETURNS TABLE (state text, operation_id uuid, status_code integer, response_body jsonb)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE expected_workspace uuid; inserted_count integer; existing control.agent_idempotency%ROWTYPE;
        BEGIN
            IF length(p_idempotency_key) NOT BETWEEN 1 AND 128 OR p_idempotency_key !~ '^[A-Za-z0-9._~-]+$' OR p_request_digest !~ '^[0-9a-f]{64}$'
            THEN RAISE EXCEPTION 'INVALID_IDEMPOTENCY_INPUT' USING ERRCODE='P0001'; END IF;
            SELECT capability.workspace_id INTO expected_workspace
            FROM control.capability capability JOIN control.workspace workspace ON workspace.id=capability.workspace_id
            JOIN control.site site ON site.id=workspace.site_id
            JOIN control.user_account account ON account.id=COALESCE(workspace.delegator_id,workspace.created_by)
            WHERE capability.id=p_capability_id AND capability.workspace_id=p_workspace_id
              AND capability.revoked_at IS NULL AND (capability.expires_at IS NULL OR capability.expires_at>CURRENT_TIMESTAMP)
              AND workspace.status='ACTIVE' AND workspace.expires_at>CURRENT_TIMESTAMP
              AND site.status='ACTIVE' AND account.status='ACTIVE'
              AND (EXISTS (SELECT 1 FROM control.platform_administrator pa WHERE pa.user_account_id=account.id)
                   OR EXISTS (SELECT 1 FROM control.slaif_effective_human_membership(account.id,workspace.site_id) m WHERE m.effective_ceiling >= CASE workspace.delegation_preset WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1 WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2 WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3 WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END));
            IF expected_workspace IS NULL THEN RAISE EXCEPTION 'CAPABILITY_WORKSPACE_NOT_ACTIVE' USING ERRCODE='P0002'; END IF;
            INSERT INTO control.agent_idempotency(capability_id,workspace_id,idempotency_key,request_digest,operation_id)
            VALUES (p_capability_id,p_workspace_id,p_idempotency_key,p_request_digest,p_operation_id)
            ON CONFLICT (capability_id,idempotency_key) DO NOTHING;
            GET DIAGNOSTICS inserted_count=ROW_COUNT;
            IF inserted_count=1 THEN RETURN QUERY SELECT 'STARTED'::text,p_operation_id,NULL::integer,NULL::jsonb; RETURN; END IF;
            SELECT * INTO existing FROM control.agent_idempotency WHERE capability_id=p_capability_id AND idempotency_key=p_idempotency_key FOR UPDATE;
            IF existing.request_digest<>p_request_digest THEN RETURN QUERY SELECT 'MISMATCH'::text,existing.operation_id,NULL::integer,NULL::jsonb; RETURN; END IF;
            IF existing.status_code IS NULL THEN RAISE EXCEPTION 'IDEMPOTENCY_IN_PROGRESS' USING ERRCODE='P0001'; END IF;
            RETURN QUERY SELECT 'REPLAY'::text,existing.operation_id,existing.status_code,existing.response_body;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_require_cow_site(
            p_site_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            session_text text;
            operation_text text;
            session_uuid uuid;
            operation_uuid uuid;
            workspace_record record;
            membership_record record;
            membership_found boolean;
            platform_admin boolean;
            required_level smallint;
        BEGIN
            session_text := NULLIF(current_setting('app.session_id', true), '');
            operation_text := NULLIF(current_setting('app.operation_id', true), '');
            IF session_text IS NULL OR operation_text IS NULL THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END IF;
            BEGIN
                session_uuid := session_text::uuid;
                operation_uuid := operation_text::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END;
            IF session_uuid IS NULL OR operation_uuid IS NULL THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END IF;
            SELECT w.site_id,w.delegator_id,w.created_by,w.delegation_preset,w.status,
                   w.expires_at,s.status AS site_status,a.status AS account_status
            INTO workspace_record
            FROM control.workspace w
            JOIN control.site s ON s.id=w.site_id
            JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
            WHERE w.id=session_uuid
            FOR SHARE;
            IF NOT FOUND OR workspace_record.site_id IS DISTINCT FROM p_site_id
               OR workspace_record.status <> 'ACTIVE'
               OR workspace_record.expires_at <= CURRENT_TIMESTAMP
               OR workspace_record.site_status <> 'ACTIVE'
               OR workspace_record.account_status <> 'ACTIVE'
            THEN
                RAISE EXCEPTION 'COW_SITE_MISMATCH' USING ERRCODE='P0002';
            END IF;
            required_level := CASE workspace_record.delegation_preset
                WHEN 'L1' THEN 1 WHEN 'L1_CONTENT_EDITOR' THEN 1
                WHEN 'L2' THEN 2 WHEN 'L2_SITE_EDITOR' THEN 2
                WHEN 'L3' THEN 3 WHEN 'L3_SITE_DESIGNER' THEN 3
                WHEN 'L4' THEN 4 WHEN 'L4_SITE_ARCHITECT' THEN 4 ELSE 99 END;
            SELECT m.delegation_ceiling,r.default_delegation_ceiling
            INTO membership_record
            FROM control.site_membership m
            JOIN control.human_role r ON r.role_key=m.role_key
            WHERE m.site_id=workspace_record.site_id
              AND m.user_account_id=COALESCE(workspace_record.delegator_id,workspace_record.created_by)
              AND m.status='ACTIVE'
            FOR SHARE;
            membership_found := FOUND;
            SELECT EXISTS (
                SELECT 1 FROM control.platform_administrator pa
                JOIN control.user_account ua ON ua.id=pa.user_account_id
                WHERE pa.user_account_id=COALESCE(workspace_record.delegator_id,workspace_record.created_by)
                  AND ua.status='ACTIVE'
            ) INTO platform_admin;
            IF NOT platform_admin AND (NOT membership_found
               OR LEAST(membership_record.delegation_ceiling,membership_record.default_delegation_ceiling) < required_level)
            THEN
                RAISE EXCEPTION 'COW_AUTHORITY_REVOKED' USING ERRCODE='P0002';
            END IF;
        END;
        $fn$
        """
    )
    for name, signature, role in (
        ("slaif_agent_capability_context", "text", "slaif_agent_runtime"),
        ("slaif_agent_quota_consume", "uuid,uuid,text", "slaif_agent_runtime"),
        ("slaif_human_agent_workspace_list", "uuid,uuid", "slaif_control"),
        (
            "slaif_human_agent_workspace_create_idempotent",
            "uuid,uuid,text,text,text,text[],jsonb,text[],integer,integer,integer,integer,integer,integer,text,text",
            "slaif_control",
        ),
        (
            "slaif_human_agent_capability_create_idempotent",
            "uuid,uuid,uuid,text,text,text,text",
            "slaif_control",
        ),
    ):
        op.execute(f'ALTER FUNCTION control.{name}({signature}) OWNER TO "slaif_owner"')
        op.execute(f"REVOKE ALL ON FUNCTION control.{name}({signature}) FROM PUBLIC")
        op.execute(f'GRANT EXECUTE ON FUNCTION control.{name}({signature}) TO "{role}"')
    op.execute(
        'GRANT EXECUTE ON FUNCTION control.slaif_agent_capability_context(text) TO "slaif_control"'
    )


def downgrade() -> None:
    # Restore the 026 guard before removing 039 objects. The stronger
    # membership/ceiling check must not survive under an older revision.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_require_cow_site(
            p_site_id uuid
        ) RETURNS void LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE session_text text; operation_text text; session_uuid uuid;
            operation_uuid uuid; workspace_site uuid;
        BEGIN
            session_text := NULLIF(current_setting('app.session_id', true), '');
            operation_text := NULLIF(current_setting('app.operation_id', true), '');
            IF session_text IS NULL OR operation_text IS NULL THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END IF;
            BEGIN
                session_uuid := session_text::uuid;
                operation_uuid := operation_text::uuid;
            EXCEPTION WHEN invalid_text_representation THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END;
            IF session_uuid IS NULL OR operation_uuid IS NULL THEN
                RAISE EXCEPTION 'COW_CONTEXT_REQUIRED' USING ERRCODE='22023';
            END IF;
            SELECT workspace.site_id INTO workspace_site
            FROM control.workspace AS workspace
            WHERE workspace.id=session_uuid AND workspace.status='ACTIVE'
              AND workspace.expires_at>CURRENT_TIMESTAMP;
            IF workspace_site IS NULL OR workspace_site IS DISTINCT FROM p_site_id THEN
                RAISE EXCEPTION 'COW_SITE_MISMATCH' USING ERRCODE='P0002';
            END IF;
        END;
        $fn$
        """
    )
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
        (
            "slaif_human_agent_workspace_create_idempotent",
            "uuid,uuid,text,text,text,text[],jsonb,text[],integer,integer,integer,integer,integer,integer,text,text",
        ),
        (
            "slaif_human_agent_capability_create_idempotent",
            "uuid,uuid,uuid,text,text,text,text",
        ),
        ("slaif_human_agent_audit_trigger", ""),
    ):
        op.execute(f"DROP FUNCTION IF EXISTS control.{name}({signature}) CASCADE")
    op.execute("DROP TABLE IF EXISTS audit.human_agent_session")
    op.execute("DROP INDEX IF EXISTS control.workspace_agent_create_idempotency")
    op.execute("DROP INDEX IF EXISTS control.capability_agent_issue_idempotency")
    op.execute(
        "ALTER TABLE control.workspace DROP COLUMN IF EXISTS create_idempotency_key, DROP COLUMN IF EXISTS create_request_digest"
    )
    op.execute(
        "ALTER TABLE control.capability DROP COLUMN IF EXISTS issue_idempotency_key, DROP COLUMN IF EXISTS issue_request_digest"
    )
    for table in ("workspace", "capability"):
        op.execute(
            f"ALTER TABLE control.{table} ALTER COLUMN request_quota SET DEFAULT 0"
        )
        op.execute(
            f"ALTER TABLE control.{table} ALTER COLUMN mutation_quota SET DEFAULT 0"
        )
    for column in ("request_used", "mutation_used", "delete_used", "upload_used"):
        op.execute(f"ALTER TABLE control.capability DROP COLUMN IF EXISTS {column}")
    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_idempotency_begin(
            p_capability_id uuid, p_workspace_id uuid, p_idempotency_key text,
            p_request_digest text, p_operation_id uuid
        ) RETURNS TABLE (state text, operation_id uuid, status_code integer, response_body jsonb)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE expected_workspace uuid; inserted_count integer; existing control.agent_idempotency%ROWTYPE;
        BEGIN
            IF length(p_idempotency_key) NOT BETWEEN 1 AND 128 OR p_idempotency_key !~ '^[A-Za-z0-9._~-]+$' OR p_request_digest !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'INVALID_IDEMPOTENCY_INPUT' USING ERRCODE='P0001'; END IF;
            SELECT capability.workspace_id INTO expected_workspace FROM control.capability capability JOIN control.workspace workspace ON workspace.id=capability.workspace_id WHERE capability.id=p_capability_id AND capability.workspace_id=p_workspace_id AND capability.revoked_at IS NULL AND (capability.expires_at IS NULL OR capability.expires_at>CURRENT_TIMESTAMP) AND workspace.status='ACTIVE' AND workspace.expires_at>CURRENT_TIMESTAMP;
            IF expected_workspace IS NULL THEN RAISE EXCEPTION 'CAPABILITY_WORKSPACE_NOT_ACTIVE' USING ERRCODE='P0002'; END IF;
            INSERT INTO control.agent_idempotency(capability_id,workspace_id,idempotency_key,request_digest,operation_id) VALUES (p_capability_id,p_workspace_id,p_idempotency_key,p_request_digest,p_operation_id) ON CONFLICT (capability_id,idempotency_key) DO NOTHING;
            GET DIAGNOSTICS inserted_count=ROW_COUNT;
            IF inserted_count=1 THEN RETURN QUERY SELECT 'STARTED'::text,p_operation_id,NULL::integer,NULL::jsonb; RETURN; END IF;
            SELECT * INTO existing FROM control.agent_idempotency WHERE capability_id=p_capability_id AND idempotency_key=p_idempotency_key FOR UPDATE;
            IF existing.request_digest<>p_request_digest THEN RETURN QUERY SELECT 'MISMATCH'::text,existing.operation_id,NULL::integer,NULL::jsonb; RETURN; END IF;
            IF existing.status_code IS NULL THEN RAISE EXCEPTION 'IDEMPOTENCY_IN_PROGRESS' USING ERRCODE='P0001'; END IF;
            RETURN QUERY SELECT 'REPLAY'::text,existing.operation_id,existing.status_code,existing.response_body;
        END; $fn$
        """
    )
