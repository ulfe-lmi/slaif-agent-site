# ruff: noqa: E501
"""Install the authenticated human Agent-session Control surface."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "038_001"
down_revision: str | Sequence[str] | None = "037_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE control.workspace ADD COLUMN IF NOT EXISTS delegator_id uuid"
    )
    op.execute(
        "ALTER TABLE control.workspace ADD COLUMN IF NOT EXISTS resource_constraints jsonb NOT NULL DEFAULT '{}'::jsonb"
    )
    op.execute(
        "ALTER TABLE control.workspace ADD COLUMN IF NOT EXISTS source_origins text[] NOT NULL DEFAULT ARRAY[]::text[]"
    )
    for column in (
        "request_quota",
        "mutation_quota",
        "delete_quota",
        "upload_quota",
        "browser_quota",
    ):
        op.execute(
            f"ALTER TABLE control.workspace ADD COLUMN IF NOT EXISTS {column} integer NOT NULL DEFAULT 0"
        )
    op.execute(
        "UPDATE control.workspace SET delegator_id = created_by WHERE delegator_id IS NULL"
    )
    op.execute(
        "ALTER TABLE control.capability ADD COLUMN IF NOT EXISTS resource_constraints jsonb NOT NULL DEFAULT '{}'::jsonb"
    )
    op.execute(
        "ALTER TABLE control.capability ADD COLUMN IF NOT EXISTS source_origins text[] NOT NULL DEFAULT ARRAY[]::text[]"
    )
    for column in ("request_quota", "mutation_quota", "delete_quota", "upload_quota"):
        op.execute(
            f"ALTER TABLE control.capability ADD COLUMN IF NOT EXISTS {column} integer NOT NULL DEFAULT 0"
        )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_agent_capability_authenticate(
            p_public_id text
        ) RETURNS TABLE (
            id uuid, public_id text, secret_digest text, workspace_id uuid,
            site_id uuid, created_by uuid, scopes jsonb, created_at timestamptz,
            expires_at timestamptz, revoked_at timestamptz,
            browser_max_runs integer, browser_max_concurrent_runs integer,
            browser_max_screenshots integer, browser_max_artifact_bytes bigint,
            browser_max_routes_per_run integer, browser_max_evidence_per_run integer,
            browser_max_duration_seconds integer, browser_max_attempts integer,
            browser_allowed_targets text[]
        ) LANGUAGE sql SECURITY DEFINER STABLE SET search_path = pg_catalog AS $fn$
            SELECT c.id,c.public_id,c.secret_digest,w.id,w.site_id,COALESCE(w.delegator_id,w.created_by),c.scopes,
                c.created_at,c.expires_at,c.revoked_at,c.browser_max_runs,
                c.browser_max_concurrent_runs,c.browser_max_screenshots,c.browser_max_artifact_bytes,
                c.browser_max_routes_per_run,c.browser_max_evidence_per_run,c.browser_max_duration_seconds,
                c.browser_max_attempts,c.browser_allowed_targets
            FROM control.capability c JOIN control.workspace w ON w.id=c.workspace_id
            JOIN control.site s ON s.id=w.site_id JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
            WHERE c.public_id=p_public_id AND c.revoked_at IS NULL AND c.expires_at>CURRENT_TIMESTAMP
              AND w.status='ACTIVE' AND w.expires_at>CURRENT_TIMESTAMP
              AND s.status='ACTIVE' AND a.status='ACTIVE'
        $fn$
        """
    )

    op.execute(
        """
        CREATE OR REPLACE FUNCTION control.slaif_human_agent_workspace_create(
            p_site_id uuid, p_user_id uuid, p_title text, p_description text,
            p_preset text, p_requested_scopes text[], p_constraints jsonb,
            p_origins text[], p_request_quota integer, p_mutation_quota integer,
            p_delete_quota integer, p_upload_quota integer, p_browser_quota integer,
            p_duration_hours integer
        ) RETURNS TABLE (
            id uuid, site_id uuid, created_by uuid, delegator_id uuid,
            title text, task_description text, status text,
            delegation_preset text, effective_scopes jsonb,
            resource_constraints jsonb, source_origins text[],
            request_quota integer, mutation_quota integer, delete_quota integer,
            upload_quota integer, browser_quota integer,
            base_site_revision bigint, created_at timestamptz, expires_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE
            authority record;
            level smallint;
            effective text[];
            workspace_id uuid;
        BEGIN
            IF p_duration_hours NOT BETWEEN 1 AND 8
               OR p_request_quota NOT BETWEEN 1 AND 10000
               OR p_mutation_quota NOT BETWEEN 0 AND 5000
               OR p_delete_quota NOT BETWEEN 0 AND 5000
               OR p_upload_quota NOT BETWEEN 0 AND 1000
               OR p_browser_quota NOT BETWEEN 0 AND 1000
               OR jsonb_typeof(p_constraints) <> 'object'
               OR octet_length(p_constraints::text) > 8192
               OR cardinality(p_origins) > 16
               OR EXISTS (SELECT 1 FROM unnest(p_origins) origin WHERE length(origin) > 2048)
            THEN RAISE EXCEPTION 'AGENT_WORKSPACE_INPUT_INVALID' USING ERRCODE = 'P0001'; END IF;
            level := CASE p_preset
                WHEN 'L1_CONTENT_EDITOR' THEN 1 WHEN 'L2_SITE_EDITOR' THEN 2
                WHEN 'L3_SITE_DESIGNER' THEN 3 WHEN 'L4_SITE_ARCHITECT' THEN 4
                ELSE 0 END;
            IF level = 0 THEN RAISE EXCEPTION 'AGENT_WORKSPACE_INPUT_INVALID' USING ERRCODE = 'P0001'; END IF;
            SELECT * INTO authority FROM control.slaif_effective_human_membership(p_user_id, p_site_id);
            IF (authority IS NULL AND NOT EXISTS (SELECT 1 FROM control.platform_administrator WHERE user_account_id=p_user_id))
               OR (authority IS NOT NULL AND (authority.effective_ceiling < level
               OR NOT ('workspace:create' = ANY(authority.effective_permissions))))
            THEN RAISE EXCEPTION 'AGENT_WORKSPACE_DENIED' USING ERRCODE = 'P0002'; END IF;
            SELECT COALESCE(array_agg(scope ORDER BY scope), ARRAY[]::text[]) INTO effective
            FROM unnest(COALESCE(p_requested_scopes, ARRAY[]::text[])) scope
            JOIN control.permission permission ON permission.permission_key = scope
            WHERE scope = ANY(COALESCE(authority.effective_permissions, ARRAY(SELECT permission_key FROM control.permission WHERE site_assignable)))
              AND permission.site_assignable
              AND permission.agent_delegation_level IS NOT NULL
              AND permission.agent_delegation_level <= level;
            IF cardinality(effective) <> cardinality(COALESCE(p_requested_scopes, ARRAY[]::text[]))
            THEN RAISE EXCEPTION 'AGENT_WORKSPACE_SCOPE_DENIED' USING ERRCODE = 'P0002'; END IF;
            INSERT INTO control.workspace(
                site_id, created_by, delegator_id, actor_type, title, task_description,
                delegation_preset, effective_scopes, resource_constraints, source_origins,
                request_quota, mutation_quota, delete_quota, upload_quota, browser_quota,
                status, base_site_revision, expires_at
            ) SELECT p_site_id, p_user_id, p_user_id, 'AGENT', p_title, p_description,
                p_preset, to_jsonb(effective), p_constraints, COALESCE(p_origins, ARRAY[]::text[]),
                p_request_quota, p_mutation_quota, p_delete_quota, p_upload_quota, p_browser_quota,
                'ACTIVE', site.canonical_revision, CURRENT_TIMESTAMP + make_interval(hours => p_duration_hours)
            FROM control.site site WHERE site.id = p_site_id AND site.status = 'ACTIVE'
            RETURNING workspace.id INTO workspace_id;
            IF workspace_id IS NULL THEN RAISE EXCEPTION 'AGENT_WORKSPACE_NOT_FOUND' USING ERRCODE = 'P0002'; END IF;
            RETURN QUERY SELECT w.id,w.site_id,w.created_by,w.delegator_id,w.title,w.task_description,
                w.status,w.delegation_preset,w.effective_scopes,w.resource_constraints,w.source_origins,
                w.request_quota,w.mutation_quota,w.delete_quota,w.upload_quota,w.browser_quota,
                w.base_site_revision,w.created_at,w.expires_at FROM control.workspace w WHERE w.id = workspace_id;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_human_agent_workspace_get(
            p_workspace_id uuid, p_site_id uuid, p_user_id uuid
        ) RETURNS TABLE (
            id uuid, site_id uuid, created_by uuid, delegator_id uuid, title text,
            task_description text, status text, delegation_preset text,
            effective_scopes jsonb, resource_constraints jsonb, source_origins text[],
            request_quota integer, mutation_quota integer, delete_quota integer,
            upload_quota integer, browser_quota integer, base_site_revision bigint,
            created_at timestamptz, expires_at timestamptz
        ) LANGUAGE sql SECURITY DEFINER STABLE SET search_path = pg_catalog AS $fn$
            SELECT w.id,w.site_id,w.created_by,w.delegator_id,w.title,w.task_description,w.status,
                w.delegation_preset,w.effective_scopes,w.resource_constraints,w.source_origins,
                w.request_quota,w.mutation_quota,w.delete_quota,w.upload_quota,w.browser_quota,
                w.base_site_revision,w.created_at,w.expires_at
            FROM control.workspace w JOIN control.user_account a ON a.id=COALESCE(w.delegator_id,w.created_by)
            JOIN control.site s ON s.id=w.site_id
            WHERE w.id=p_workspace_id AND w.site_id=p_site_id
              AND (COALESCE(w.delegator_id,w.created_by)=p_user_id OR EXISTS (SELECT 1 FROM control.platform_administrator WHERE user_account_id=p_user_id))
              AND w.actor_type='AGENT' AND a.status='ACTIVE' AND s.status='ACTIVE'
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_human_agent_capability_create(
            p_workspace_id uuid, p_site_id uuid, p_user_id uuid, p_public_id text,
            p_secret_digest text
        ) RETURNS TABLE (id uuid, public_id text, workspace_id uuid, site_id uuid,
            scopes jsonb, created_at timestamptz, expires_at timestamptz,
            resource_constraints jsonb, source_origins text[], request_quota integer,
            mutation_quota integer, delete_quota integer, upload_quota integer)
        LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        DECLARE w record; capability_id uuid;
        BEGIN
            SELECT * INTO w FROM control.workspace WHERE workspace.id=p_workspace_id
              AND workspace.site_id=p_site_id
              AND (COALESCE(workspace.delegator_id,workspace.created_by)=p_user_id OR EXISTS (SELECT 1 FROM control.platform_administrator WHERE user_account_id=p_user_id))
              AND workspace.actor_type='AGENT' AND workspace.status='ACTIVE'
              AND workspace.expires_at>CURRENT_TIMESTAMP;
            IF w IS NULL OR length(p_public_id) NOT BETWEEN 16 AND 64
               OR p_secret_digest !~ '^[0-9a-f]{64}$'
            THEN RAISE EXCEPTION 'AGENT_CAPABILITY_DENIED' USING ERRCODE='P0002'; END IF;
            INSERT INTO control.capability(workspace_id,public_id,secret_digest,scopes,expires_at,
                resource_constraints,source_origins,request_quota,mutation_quota,delete_quota,upload_quota,
                browser_max_runs, browser_max_concurrent_runs)
            VALUES (w.id,p_public_id,p_secret_digest,w.effective_scopes,w.expires_at,
                w.resource_constraints,w.source_origins,w.request_quota,w.mutation_quota,w.delete_quota,w.upload_quota,
                w.browser_quota, LEAST(2, w.browser_quota)) RETURNING capability.id INTO capability_id;
            RETURN QUERY SELECT c.id,c.public_id,c.workspace_id,w.site_id,c.scopes,c.created_at,c.expires_at,
                c.resource_constraints,c.source_origins,c.request_quota,c.mutation_quota,c.delete_quota,c.upload_quota
                FROM control.capability c WHERE c.id=capability_id;
        END; $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_human_agent_capability_revoke(
            p_workspace_id uuid, p_site_id uuid, p_user_id uuid, p_public_id text
        ) RETURNS boolean LANGUAGE sql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
            UPDATE control.capability c SET revoked_at=CURRENT_TIMESTAMP
            FROM control.workspace w WHERE c.workspace_id=w.id AND c.public_id=p_public_id
              AND w.id=p_workspace_id AND w.site_id=p_site_id
              AND (COALESCE(w.delegator_id,w.created_by)=p_user_id OR EXISTS (SELECT 1 FROM control.platform_administrator WHERE user_account_id=p_user_id))
              AND c.revoked_at IS NULL RETURNING TRUE
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_human_agent_capability_list(
            p_workspace_id uuid, p_site_id uuid, p_user_id uuid
        ) RETURNS TABLE(public_id text, created_at timestamptz, expires_at timestamptz, revoked_at timestamptz)
        LANGUAGE sql SECURITY DEFINER STABLE SET search_path = pg_catalog AS $fn$
            SELECT c.public_id,c.created_at,c.expires_at,c.revoked_at FROM control.capability c
            JOIN control.workspace w ON w.id=c.workspace_id
            WHERE c.workspace_id=p_workspace_id AND w.site_id=p_site_id
              AND (COALESCE(w.delegator_id,w.created_by)=p_user_id OR EXISTS (SELECT 1 FROM control.platform_administrator WHERE user_account_id=p_user_id))
            ORDER BY c.created_at DESC, c.id DESC
        $fn$
        """
    )
    for name, signature in (
        (
            "slaif_human_agent_workspace_create",
            "uuid,uuid,text,text,text,text[],jsonb,text[],integer,integer,integer,integer,integer,integer",
        ),
        ("slaif_human_agent_workspace_get", "uuid,uuid,uuid"),
        ("slaif_human_agent_capability_create", "uuid,uuid,uuid,text,text"),
        ("slaif_human_agent_capability_revoke", "uuid,uuid,uuid,text"),
        ("slaif_human_agent_capability_list", "uuid,uuid,uuid"),
    ):
        op.execute(f'ALTER FUNCTION control.{name}({signature}) OWNER TO "slaif_owner"')
        op.execute(f"REVOKE ALL ON FUNCTION control.{name}({signature}) FROM PUBLIC")
        op.execute(
            f'GRANT EXECUTE ON FUNCTION control.{name}({signature}) TO "slaif_control"'
        )


def downgrade() -> None:
    for name, signature in (
        (
            "slaif_human_agent_workspace_create",
            "uuid,uuid,text,text,text,text[],jsonb,text[],integer,integer,integer,integer,integer,integer",
        ),
        ("slaif_human_agent_workspace_get", "uuid,uuid,uuid"),
        ("slaif_human_agent_capability_create", "uuid,uuid,uuid,text,text"),
        ("slaif_human_agent_capability_revoke", "uuid,uuid,uuid,text"),
        ("slaif_human_agent_capability_list", "uuid,uuid,uuid"),
    ):
        op.execute(f"DROP FUNCTION IF EXISTS control.{name}({signature}) CASCADE")
