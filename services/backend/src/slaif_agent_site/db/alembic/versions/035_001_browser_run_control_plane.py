# ruff: noqa: E501
"""Add durable, capability-bound browser preview-run control state."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "035_001"
down_revision: str | Sequence[str] | None = "034_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_AGENT_FUNCTIONS = (
    "control.slaif_agent_capability_authenticate(text)",
    "control.slaif_agent_browser_run_begin(uuid,uuid,uuid,uuid,text,text,uuid,uuid,text,text,text,text,text[],integer,bigint,integer,integer)",
    "control.slaif_agent_browser_run_get(uuid,uuid,uuid,uuid,uuid)",
    "control.slaif_agent_browser_artifact_list(uuid,uuid,uuid,uuid,uuid)",
    "control.slaif_agent_browser_run_claim(uuid,integer)",
    "control.slaif_agent_browser_run_renew(uuid,uuid,integer)",
    "control.slaif_agent_browser_run_release(uuid,uuid)",
    "control.slaif_agent_browser_run_complete(uuid,uuid,text,jsonb,text,text)",
    "control.slaif_agent_browser_artifact_register(uuid,uuid,uuid,text,text,text,bigint,text,text,timestamptz)",
)
_PRIVATE_FUNCTIONS = ("control.slaif_agent_browser_authorized(uuid,uuid,uuid,uuid)",)


def _secure_functions() -> None:
    for function in (*_AGENT_FUNCTIONS, *_PRIVATE_FUNCTIONS):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")
        for role in (
            "slaif_control",
            "slaif_editor_runtime",
            "slaif_agent_runtime",
            "slaif_public_reader",
            "slaif_preview_reader",
            "slaif_reviewer",
            "slaif_scheduler",
            "slaif_media",
            "slaif_gc",
        ):
            op.execute(f"REVOKE ALL ON FUNCTION {function} FROM {role}")
    for function in _AGENT_FUNCTIONS:
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO slaif_agent_runtime")


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE control.capability
            ADD COLUMN browser_max_runs INTEGER NOT NULL DEFAULT 20,
            ADD COLUMN browser_max_concurrent_runs INTEGER NOT NULL DEFAULT 2,
            ADD COLUMN browser_max_screenshots INTEGER NOT NULL DEFAULT 50,
            ADD COLUMN browser_max_artifact_bytes BIGINT NOT NULL DEFAULT 104857600,
            ADD COLUMN browser_max_routes_per_run INTEGER NOT NULL DEFAULT 10,
            ADD COLUMN browser_max_evidence_per_run INTEGER NOT NULL DEFAULT 9,
            ADD COLUMN browser_max_duration_seconds INTEGER NOT NULL DEFAULT 120,
            ADD COLUMN browser_max_attempts INTEGER NOT NULL DEFAULT 3,
            ADD COLUMN browser_allowed_targets TEXT[] NOT NULL DEFAULT
                ARRAY['desktop-chromium','tablet','mobile-chromium']::text[],
            ADD CONSTRAINT capability_browser_max_runs_bounded
                CHECK (browser_max_runs BETWEEN 0 AND 2000),
            ADD CONSTRAINT capability_browser_concurrent_bounded
                CHECK (browser_max_concurrent_runs BETWEEN 0 AND 32
                    AND browser_max_concurrent_runs <= browser_max_runs),
            ADD CONSTRAINT capability_browser_screenshots_bounded
                CHECK (browser_max_screenshots BETWEEN 0 AND 10000),
            ADD CONSTRAINT capability_browser_artifact_bytes_bounded
                CHECK (browser_max_artifact_bytes BETWEEN 0 AND 1073741824),
            ADD CONSTRAINT capability_browser_routes_bounded
                CHECK (browser_max_routes_per_run BETWEEN 0 AND 10),
            ADD CONSTRAINT capability_browser_evidence_bounded
                CHECK (browser_max_evidence_per_run BETWEEN 0 AND 9),
            ADD CONSTRAINT capability_browser_duration_bounded
                CHECK (browser_max_duration_seconds BETWEEN 5 AND 600),
            ADD CONSTRAINT capability_browser_attempts_bounded
                CHECK (browser_max_attempts BETWEEN 1 AND 5),
            ADD CONSTRAINT capability_browser_targets_bounded CHECK (
                array_ndims(browser_allowed_targets) = 1
                AND cardinality(browser_allowed_targets) BETWEEN 1 AND 3
                AND array_position(browser_allowed_targets, NULL) IS NULL
                AND browser_allowed_targets <@ ARRAY[
                    'desktop-chromium','tablet','mobile-chromium'
                ]::text[]
                AND cardinality(browser_allowed_targets) =
                    (CASE WHEN 'desktop-chromium' = ANY(browser_allowed_targets) THEN 1 ELSE 0 END)
                    + (CASE WHEN 'tablet' = ANY(browser_allowed_targets) THEN 1 ELSE 0 END)
                    + (CASE WHEN 'mobile-chromium' = ANY(browser_allowed_targets) THEN 1 ELSE 0 END)
            ),
            ADD CONSTRAINT capability_id_workspace_unique UNIQUE (id, workspace_id)
        """
    )
    op.execute(
        """
        ALTER TABLE control.workspace
            ADD CONSTRAINT workspace_site_delegator_unique
            UNIQUE (id, site_id, created_by)
        """
    )
    op.execute(
        """
        CREATE TABLE control.browser_run (
            id UUID PRIMARY KEY,
            operation_id UUID NOT NULL UNIQUE,
            capability_id UUID NOT NULL,
            workspace_id UUID NOT NULL,
            site_id UUID NOT NULL,
            delegator_id UUID NOT NULL,
            contract_version TEXT NOT NULL,
            route TEXT NOT NULL,
            route_digest TEXT NOT NULL,
            target TEXT NOT NULL,
            evidence TEXT[] NOT NULL,
            request_digest TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'QUEUED',
            reserved_screenshots INTEGER NOT NULL,
            reserved_artifact_bytes BIGINT NOT NULL,
            reserved_routes INTEGER NOT NULL,
            reserved_evidence INTEGER NOT NULL,
            max_duration_seconds INTEGER NOT NULL,
            max_attempts INTEGER NOT NULL,
            attempt_count INTEGER NOT NULL DEFAULT 0,
            lease_id UUID,
            lease_expires_at TIMESTAMPTZ,
            terminal_lease_id UUID,
            summary JSONB,
            error_code TEXT,
            error_message TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMPTZ,
            completed_at TIMESTAMPTZ,
            expires_at TIMESTAMPTZ NOT NULL,
            CONSTRAINT browser_run_capability_workspace_fk
                FOREIGN KEY (capability_id, workspace_id)
                REFERENCES control.capability(id, workspace_id),
            CONSTRAINT browser_run_workspace_site_delegator_fk
                FOREIGN KEY (workspace_id, site_id, delegator_id)
                REFERENCES control.workspace(id, site_id, created_by),
            CONSTRAINT browser_run_correlation_unique
                UNIQUE (id, site_id, workspace_id, capability_id, delegator_id),
            CONSTRAINT browser_run_contract_version_exact
                CHECK (contract_version = 'browser-preview/v1'),
            CONSTRAINT browser_run_digest_shapes CHECK (
                request_digest ~ '^[0-9a-f]{64}$'
                AND route_digest ~ '^[0-9a-f]{64}$'
            ),
            CONSTRAINT browser_run_target_allowed CHECK (
                target IN ('desktop-chromium','tablet','mobile-chromium')
            ),
            CONSTRAINT browser_run_evidence_bounded CHECK (
                array_ndims(evidence) = 1
                AND cardinality(evidence) BETWEEN 1 AND 9
                AND array_position(evidence, NULL) IS NULL
                AND evidence <@ ARRAY[
                    'screenshot','accessibility-summary','structure-summary',
                    'heading-summary','link-summary','media-summary',
                    'overflow-summary','console-summary','failed-request-summary'
                ]::text[]
                AND cardinality(evidence) =
                    (CASE WHEN 'screenshot' = ANY(evidence) THEN 1 ELSE 0 END)
                    + (CASE WHEN 'accessibility-summary' = ANY(evidence) THEN 1 ELSE 0 END)
                    + (CASE WHEN 'structure-summary' = ANY(evidence) THEN 1 ELSE 0 END)
                    + (CASE WHEN 'heading-summary' = ANY(evidence) THEN 1 ELSE 0 END)
                    + (CASE WHEN 'link-summary' = ANY(evidence) THEN 1 ELSE 0 END)
                    + (CASE WHEN 'media-summary' = ANY(evidence) THEN 1 ELSE 0 END)
                    + (CASE WHEN 'overflow-summary' = ANY(evidence) THEN 1 ELSE 0 END)
                    + (CASE WHEN 'console-summary' = ANY(evidence) THEN 1 ELSE 0 END)
                    + (CASE WHEN 'failed-request-summary' = ANY(evidence) THEN 1 ELSE 0 END)
            ),
            CONSTRAINT browser_run_route_bounded CHECK (
                octet_length(route) BETWEEN 1 AND 2048
                AND left(route, 1) = '/'
                AND left(route, 2) <> '//'
                AND position('#' IN route) = 0
                AND position(E'\\\\' IN route) = 0
                AND route !~ '[[:cntrl:][:space:]]'
                AND position(chr(37) || '2f' IN lower(route)) = 0
                AND position(chr(37) || '5c' IN lower(route)) = 0
                AND position(chr(37) || '2e' IN lower(route)) = 0
                AND route !~ '(^|/)\\.{1,2}(/|\\?|$)'
                AND route !~* '[?&][^=&]*(token|secret|credential|password|cookie|authorization|api[_-]?key|access[_-]?key|signature)='
                AND route !~* 'sas2_[0-9a-f]+_'
            ),
            CONSTRAINT browser_run_state_allowed CHECK (
                state IN ('QUEUED','RUNNING','COMPLETED','FAILED','TIMED_OUT','CANCELLED')
            ),
            CONSTRAINT browser_run_reservations_bounded CHECK (
                reserved_screenshots = CASE WHEN 'screenshot' = ANY(evidence) THEN 1 ELSE 0 END
                AND reserved_artifact_bytes BETWEEN 0 AND 1073741824
                AND reserved_routes = 1
                AND reserved_evidence = cardinality(evidence)
                AND max_duration_seconds BETWEEN 5 AND 600
                AND max_attempts BETWEEN 1 AND 5
                AND attempt_count BETWEEN 0 AND max_attempts
            ),
            CONSTRAINT browser_run_lease_shape CHECK (
                (state = 'RUNNING' AND lease_id IS NOT NULL
                    AND lease_expires_at IS NOT NULL AND started_at IS NOT NULL
                    AND completed_at IS NULL AND terminal_lease_id IS NULL)
                OR
                (state <> 'RUNNING' AND lease_id IS NULL AND lease_expires_at IS NULL)
            ),
            CONSTRAINT browser_run_terminal_shape CHECK (
                (state IN ('QUEUED','RUNNING') AND completed_at IS NULL
                    AND summary IS NULL AND error_code IS NULL
                    AND error_message IS NULL AND terminal_lease_id IS NULL)
                OR
                (state = 'COMPLETED' AND completed_at IS NOT NULL
                    AND summary IS NOT NULL AND jsonb_typeof(summary) = 'object'
                    AND octet_length(summary::text) <= 16384
                    AND error_code IS NULL AND error_message IS NULL
                    AND terminal_lease_id IS NOT NULL)
                OR
                (state IN ('FAILED','TIMED_OUT','CANCELLED')
                    AND completed_at IS NOT NULL
                    AND summary IS NOT NULL AND jsonb_typeof(summary) = 'object'
                    AND octet_length(summary::text) <= 16384
                    AND error_code ~ '^[A-Z][A-Z0-9_]{0,63}$'
                    AND length(error_message) BETWEEN 1 AND 512
                    AND terminal_lease_id IS NOT NULL)
            ),
            CONSTRAINT browser_run_time_order CHECK (
                expires_at > created_at
                AND (started_at IS NULL OR started_at >= created_at)
                AND (completed_at IS NULL OR completed_at >= created_at)
                AND (lease_expires_at IS NULL OR lease_expires_at > created_at)
            )
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX browser_run_active_lease_unique "
        "ON control.browser_run(lease_id) WHERE lease_id IS NOT NULL"
    )
    op.execute(
        "CREATE INDEX browser_run_claim_order ON control.browser_run(state, created_at, id)"
    )
    op.execute(
        "CREATE INDEX browser_run_capability_state ON control.browser_run(capability_id, state, created_at)"
    )
    op.execute(
        """
        CREATE TABLE control.browser_idempotency (
            capability_id UUID NOT NULL,
            workspace_id UUID NOT NULL,
            site_id UUID NOT NULL,
            delegator_id UUID NOT NULL,
            idempotency_key TEXT NOT NULL,
            request_digest TEXT NOT NULL,
            operation_id UUID NOT NULL UNIQUE,
            run_id UUID NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (capability_id, idempotency_key),
            CONSTRAINT browser_idempotency_key_bounded CHECK (
                length(idempotency_key) BETWEEN 1 AND 128
                AND idempotency_key ~ '^[A-Za-z0-9._~-]+$'
            ),
            CONSTRAINT browser_idempotency_digest_shape
                CHECK (request_digest ~ '^[0-9a-f]{64}$'),
            CONSTRAINT browser_idempotency_capability_workspace_fk
                FOREIGN KEY (capability_id, workspace_id)
                REFERENCES control.capability(id, workspace_id),
            CONSTRAINT browser_idempotency_workspace_site_delegator_fk
                FOREIGN KEY (workspace_id, site_id, delegator_id)
                REFERENCES control.workspace(id, site_id, created_by),
            CONSTRAINT browser_idempotency_run_fk
                FOREIGN KEY (run_id, site_id, workspace_id, capability_id, delegator_id)
                REFERENCES control.browser_run(id, site_id, workspace_id, capability_id, delegator_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE control.browser_artifact (
            id UUID PRIMARY KEY,
            run_id UUID NOT NULL,
            site_id UUID NOT NULL,
            workspace_id UUID NOT NULL,
            capability_id UUID NOT NULL,
            delegator_id UUID NOT NULL,
            kind TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            size_bytes BIGINT NOT NULL,
            target TEXT NOT NULL,
            route_digest TEXT NOT NULL,
            visibility TEXT NOT NULL DEFAULT 'PRIVATE',
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMPTZ NOT NULL,
            CONSTRAINT browser_artifact_run_kind_unique UNIQUE (run_id, kind),
            CONSTRAINT browser_artifact_run_binding_fk
                FOREIGN KEY (run_id, site_id, workspace_id, capability_id, delegator_id)
                REFERENCES control.browser_run(id, site_id, workspace_id, capability_id, delegator_id),
            CONSTRAINT browser_artifact_kind_allowed CHECK (
                kind IN (
                    'screenshot','accessibility-summary','structure-summary',
                    'heading-summary','link-summary','media-summary',
                    'overflow-summary','console-summary','failed-request-summary'
                )
            ),
            CONSTRAINT browser_artifact_mime_allowed CHECK (
                mime_type IN ('image/png','application/json','text/plain')
                AND (kind <> 'screenshot' OR mime_type = 'image/png')
            ),
            CONSTRAINT browser_artifact_digest_shapes CHECK (
                sha256 ~ '^[0-9a-f]{64}$'
                AND route_digest ~ '^[0-9a-f]{64}$'
            ),
            CONSTRAINT browser_artifact_size_bounded
                CHECK (size_bytes BETWEEN 1 AND 1073741824),
            CONSTRAINT browser_artifact_target_allowed CHECK (
                target IN ('desktop-chromium','tablet','mobile-chromium')
            ),
            CONSTRAINT browser_artifact_private_only CHECK (visibility = 'PRIVATE'),
            CONSTRAINT browser_artifact_time_order CHECK (expires_at > created_at)
        )
        """
    )
    op.execute(
        "CREATE INDEX browser_artifact_retention ON control.browser_artifact(expires_at, run_id, id)"
    )
    op.execute(
        """
        CREATE TABLE audit.browser_event (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id UUID NOT NULL,
            operation_id UUID NOT NULL,
            capability_id UUID NOT NULL,
            workspace_id UUID NOT NULL,
            site_id UUID NOT NULL,
            delegator_id UUID NOT NULL,
            event_type TEXT NOT NULL,
            attempt INTEGER NOT NULL,
            lease_id UUID,
            artifact_id UUID,
            details JSONB NOT NULL DEFAULT '{}'::jsonb,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT browser_event_run_binding_fk
                FOREIGN KEY (run_id, site_id, workspace_id, capability_id, delegator_id)
                REFERENCES control.browser_run(id, site_id, workspace_id, capability_id, delegator_id),
            CONSTRAINT browser_event_artifact_fk
                FOREIGN KEY (artifact_id) REFERENCES control.browser_artifact(id),
            CONSTRAINT browser_event_type_allowed CHECK (
                event_type IN (
                    'ENQUEUED','LEASED','LEASE_RENEWED','LEASE_RELEASED',
                    'COMPLETED','FAILED','TIMED_OUT','CANCELLED',
                    'ARTIFACT_REGISTERED','MAX_ATTEMPTS'
                )
            ),
            CONSTRAINT browser_event_attempt_bounded CHECK (attempt BETWEEN 0 AND 5),
            CONSTRAINT browser_event_details_bounded CHECK (
                jsonb_typeof(details) = 'object'
                AND octet_length(details::text) <= 8192
            )
        )
        """
    )
    op.execute(
        "CREATE INDEX browser_event_run_time ON audit.browser_event(run_id, occurred_at, id)"
    )

    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_capability_authenticate(
            p_public_id text
        ) RETURNS TABLE (
            id uuid, public_id text, secret_digest text, workspace_id uuid,
            site_id uuid, created_by uuid, scopes jsonb,
            created_at timestamptz, expires_at timestamptz, revoked_at timestamptz,
            browser_max_runs integer, browser_max_concurrent_runs integer,
            browser_max_screenshots integer, browser_max_artifact_bytes bigint,
            browser_max_routes_per_run integer,
            browser_max_evidence_per_run integer,
            browser_max_duration_seconds integer, browser_max_attempts integer,
            browser_allowed_targets text[]
        ) LANGUAGE sql SECURITY DEFINER STABLE
        SET search_path = pg_catalog ROWS 1 AS $fn$
            SELECT capability.id, capability.public_id, capability.secret_digest,
                workspace.id, workspace.site_id, workspace.created_by,
                capability.scopes, capability.created_at, capability.expires_at,
                capability.revoked_at, capability.browser_max_runs,
                capability.browser_max_concurrent_runs,
                capability.browser_max_screenshots,
                capability.browser_max_artifact_bytes,
                capability.browser_max_routes_per_run,
                capability.browser_max_evidence_per_run,
                capability.browser_max_duration_seconds,
                capability.browser_max_attempts,
                capability.browser_allowed_targets
            FROM control.capability AS capability
            JOIN control.workspace AS workspace
              ON workspace.id = capability.workspace_id
            WHERE capability.public_id = p_public_id
              AND capability.revoked_at IS NULL
              AND capability.expires_at > CURRENT_TIMESTAMP
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_browser_authorized(
            p_capability_id uuid, p_site_id uuid, p_workspace_id uuid,
            p_delegator_id uuid
        ) RETURNS boolean LANGUAGE sql SECURITY DEFINER STABLE
        SET search_path = pg_catalog AS $fn$
            SELECT EXISTS (
                SELECT 1
                FROM control.capability AS capability
                JOIN control.workspace AS workspace
                  ON workspace.id = capability.workspace_id
                JOIN control.site AS site ON site.id = workspace.site_id
                WHERE capability.id = p_capability_id
                  AND capability.workspace_id = p_workspace_id
                  AND workspace.site_id = p_site_id
                  AND workspace.created_by = p_delegator_id
                  AND capability.revoked_at IS NULL
                  AND capability.expires_at > CURRENT_TIMESTAMP
                  AND workspace.status = 'ACTIVE'
                  AND workspace.expires_at > CURRENT_TIMESTAMP
                  AND site.status = 'ACTIVE'
                  AND jsonb_typeof(capability.scopes) = 'array'
                  AND capability.scopes ? 'preview:inspect'
            )
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_browser_run_begin(
            p_capability_id uuid, p_site_id uuid, p_workspace_id uuid,
            p_delegator_id uuid, p_idempotency_key text,
            p_request_digest text, p_operation_id uuid, p_run_id uuid,
            p_contract_version text, p_route text, p_route_digest text,
            p_target text, p_evidence text[], p_reserved_screenshots integer,
            p_reserved_artifact_bytes bigint, p_reserved_routes integer,
            p_duration_seconds integer
        ) RETURNS TABLE (
            result text, run_id uuid, operation_id uuid, run_state text
        ) LANGUAGE plpgsql SECURITY DEFINER VOLATILE
        SET search_path = pg_catalog ROWS 1 AS $fn$
        DECLARE
            selected_capability record;
            selected_workspace record;
            existing record;
            used_runs bigint;
            used_concurrent bigint;
            used_screenshots bigint;
            used_artifact_bytes numeric;
            unique_evidence bigint;
            expected_screenshots integer;
        BEGIN
            IF p_capability_id IS NULL OR p_site_id IS NULL
               OR p_workspace_id IS NULL OR p_delegator_id IS NULL
               OR p_operation_id IS NULL OR p_run_id IS NULL
               OR p_contract_version <> 'browser-preview/v1'
               OR length(p_idempotency_key) NOT BETWEEN 1 AND 128
               OR p_idempotency_key !~ '^[A-Za-z0-9._~-]+$'
               OR p_request_digest !~ '^[0-9a-f]{64}$'
               OR p_route_digest !~ '^[0-9a-f]{64}$'
               OR octet_length(p_route) NOT BETWEEN 1 AND 2048
               OR left(p_route, 1) <> '/' OR left(p_route, 2) = '//'
               OR position('#' IN p_route) > 0 OR position(E'\\\\' IN p_route) > 0
               OR p_route ~ '[[:cntrl:][:space:]]'
               OR position(chr(37) || '2f' IN lower(p_route)) > 0
               OR position(chr(37) || '5c' IN lower(p_route)) > 0
               OR position(chr(37) || '2e' IN lower(p_route)) > 0
               OR p_route ~ '(^|/)\\.{1,2}(/|\\?|$)'
               OR p_route ~* '[?&][^=&]*(token|secret|credential|password|cookie|authorization|api[_-]?key|access[_-]?key|signature)='
               OR p_route ~* 'sas2_[0-9a-f]+_'
               OR p_target NOT IN ('desktop-chromium','tablet','mobile-chromium')
               OR p_evidence IS NULL OR array_ndims(p_evidence) <> 1
               OR cardinality(p_evidence) NOT BETWEEN 1 AND 9
               OR array_position(p_evidence, NULL) IS NOT NULL
               OR NOT p_evidence <@ ARRAY[
                    'screenshot','accessibility-summary','structure-summary',
                    'heading-summary','link-summary','media-summary',
                    'overflow-summary','console-summary','failed-request-summary'
               ]::text[]
               OR p_reserved_artifact_bytes NOT BETWEEN 0 AND 1073741824
               OR p_reserved_routes <> 1
               OR p_duration_seconds NOT BETWEEN 5 AND 600
            THEN
                RAISE EXCEPTION 'INVALID_BROWSER_RUN_INPUT' USING ERRCODE = '22023';
            END IF;
            SELECT count(DISTINCT evidence_item) INTO unique_evidence
            FROM unnest(p_evidence) AS evidence_item;
            expected_screenshots := CASE WHEN 'screenshot' = ANY(p_evidence) THEN 1 ELSE 0 END;
            IF unique_evidence <> cardinality(p_evidence)
               OR p_reserved_screenshots <> expected_screenshots
            THEN
                RAISE EXCEPTION 'INVALID_BROWSER_RUN_INPUT' USING ERRCODE = '22023';
            END IF;

            PERFORM pg_advisory_xact_lock_shared(
                hashtextextended(p_workspace_id::text, 280)
            );
            SELECT capability.* INTO selected_capability
            FROM control.capability AS capability
            JOIN control.workspace AS workspace
              ON workspace.id = capability.workspace_id
            JOIN control.site AS site ON site.id = workspace.site_id
            WHERE capability.id = p_capability_id
              AND capability.workspace_id = p_workspace_id
              AND workspace.site_id = p_site_id
              AND workspace.created_by = p_delegator_id
              AND capability.revoked_at IS NULL
              AND capability.expires_at > CURRENT_TIMESTAMP
              AND workspace.status = 'ACTIVE'
              AND workspace.expires_at > CURRENT_TIMESTAMP
              AND site.status = 'ACTIVE'
              AND jsonb_typeof(capability.scopes) = 'array'
              AND capability.scopes ? 'preview:inspect'
            FOR UPDATE OF capability;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'BROWSER_AUTHORITY_DENIED' USING ERRCODE = 'P0002';
            END IF;
            SELECT workspace.* INTO selected_workspace
            FROM control.workspace AS workspace
            WHERE workspace.id = p_workspace_id
            FOR UPDATE;

            SELECT idempotency.* INTO existing
            FROM control.browser_idempotency AS idempotency
            WHERE idempotency.capability_id = p_capability_id
              AND idempotency.idempotency_key = p_idempotency_key
            FOR UPDATE;
            IF FOUND THEN
                IF existing.request_digest <> p_request_digest THEN
                    RETURN QUERY SELECT 'MISMATCH'::text, existing.run_id,
                        existing.operation_id, NULL::text;
                ELSE
                    RETURN QUERY SELECT 'REPLAY'::text, run.id,
                        run.operation_id, run.state
                    FROM control.browser_run AS run WHERE run.id = existing.run_id;
                END IF;
                RETURN;
            END IF;

            SELECT count(*),
                count(*) FILTER (WHERE state IN ('QUEUED','RUNNING')),
                COALESCE(sum(reserved_screenshots), 0),
                COALESCE(sum(reserved_artifact_bytes), 0)
            INTO used_runs, used_concurrent, used_screenshots, used_artifact_bytes
            FROM control.browser_run AS run
            WHERE run.capability_id = p_capability_id;
            IF used_runs >= selected_capability.browser_max_runs
               OR used_concurrent >= selected_capability.browser_max_concurrent_runs
               OR used_screenshots + p_reserved_screenshots
                    > selected_capability.browser_max_screenshots
               OR used_artifact_bytes + p_reserved_artifact_bytes
                    > selected_capability.browser_max_artifact_bytes
               OR p_reserved_routes > selected_capability.browser_max_routes_per_run
               OR cardinality(p_evidence)
                    > selected_capability.browser_max_evidence_per_run
               OR NOT p_target = ANY(selected_capability.browser_allowed_targets)
               OR p_duration_seconds > selected_capability.browser_max_duration_seconds
            THEN
                RAISE EXCEPTION 'BROWSER_QUOTA_EXCEEDED' USING ERRCODE = 'P0001';
            END IF;

            INSERT INTO control.browser_run (
                id, operation_id, capability_id, workspace_id, site_id,
                delegator_id, contract_version, route, route_digest, target,
                evidence, request_digest, reserved_screenshots,
                reserved_artifact_bytes, reserved_routes, reserved_evidence,
                max_duration_seconds, max_attempts, expires_at
            ) VALUES (
                p_run_id, p_operation_id, p_capability_id, p_workspace_id,
                p_site_id, p_delegator_id, p_contract_version, p_route,
                p_route_digest, p_target, p_evidence, p_request_digest,
                p_reserved_screenshots, p_reserved_artifact_bytes,
                p_reserved_routes, cardinality(p_evidence), p_duration_seconds,
                selected_capability.browser_max_attempts,
                LEAST(selected_capability.expires_at, selected_workspace.expires_at)
            );
            INSERT INTO control.browser_idempotency (
                capability_id, workspace_id, site_id, delegator_id,
                idempotency_key, request_digest, operation_id, run_id
            ) VALUES (
                p_capability_id, p_workspace_id, p_site_id, p_delegator_id,
                p_idempotency_key, p_request_digest, p_operation_id, p_run_id
            );
            INSERT INTO audit.browser_event (
                run_id, operation_id, capability_id, workspace_id, site_id,
                delegator_id, event_type, attempt, details
            ) VALUES (
                p_run_id, p_operation_id, p_capability_id, p_workspace_id,
                p_site_id, p_delegator_id, 'ENQUEUED', 0,
                jsonb_build_object('target', p_target, 'evidence_count', cardinality(p_evidence))
            );
            RETURN QUERY SELECT 'STARTED'::text, p_run_id, p_operation_id, 'QUEUED'::text;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_browser_run_get(
            p_capability_id uuid, p_site_id uuid, p_workspace_id uuid,
            p_delegator_id uuid, p_run_id uuid
        ) RETURNS TABLE (
            contract_version text, run_id uuid, operation_id uuid, state text,
            route text, target text, evidence text[], created_at timestamptz,
            started_at timestamptz, completed_at timestamptz,
            expires_at timestamptz, summary jsonb, error_code text,
            error_message text
        ) LANGUAGE sql SECURITY DEFINER STABLE
        SET search_path = pg_catalog ROWS 1 AS $fn$
            SELECT run.contract_version, run.id, run.operation_id, run.state,
                run.route, run.target, run.evidence, run.created_at,
                run.started_at, run.completed_at, run.expires_at, run.summary,
                run.error_code, run.error_message
            FROM control.browser_run AS run
            WHERE run.id = p_run_id
              AND run.capability_id = p_capability_id
              AND run.site_id = p_site_id
              AND run.workspace_id = p_workspace_id
              AND run.delegator_id = p_delegator_id
              AND run.expires_at > CURRENT_TIMESTAMP
              AND control.slaif_agent_browser_authorized(
                    p_capability_id, p_site_id, p_workspace_id, p_delegator_id
              )
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_browser_artifact_list(
            p_capability_id uuid, p_site_id uuid, p_workspace_id uuid,
            p_delegator_id uuid, p_run_id uuid
        ) RETURNS TABLE (
            contract_version text, artifact_id uuid, run_id uuid, kind text,
            mime_type text, sha256 text, size_bytes bigint, target text,
            route_digest text, created_at timestamptz, expires_at timestamptz,
            visibility text
        ) LANGUAGE sql SECURITY DEFINER STABLE
        SET search_path = pg_catalog AS $fn$
            SELECT run.contract_version, artifact.id, artifact.run_id,
                artifact.kind, artifact.mime_type, artifact.sha256,
                artifact.size_bytes, artifact.target, artifact.route_digest,
                artifact.created_at, artifact.expires_at, artifact.visibility
            FROM control.browser_artifact AS artifact
            JOIN control.browser_run AS run ON run.id = artifact.run_id
            WHERE run.id = p_run_id
              AND run.capability_id = p_capability_id
              AND run.site_id = p_site_id
              AND run.workspace_id = p_workspace_id
              AND run.delegator_id = p_delegator_id
              AND run.expires_at > CURRENT_TIMESTAMP
              AND artifact.expires_at > CURRENT_TIMESTAMP
              AND artifact.visibility = 'PRIVATE'
              AND control.slaif_agent_browser_authorized(
                    p_capability_id, p_site_id, p_workspace_id, p_delegator_id
              )
            ORDER BY artifact.created_at, artifact.id
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_browser_run_claim(
            p_lease_id uuid, p_lease_seconds integer
        ) RETURNS TABLE (
            contract_version text, run_id uuid, operation_id uuid,
            site_id uuid, workspace_id uuid, capability_id uuid,
            delegator_id uuid, route text, route_digest text, target text,
            evidence text[], reserved_screenshots integer,
            reserved_artifact_bytes bigint, max_duration_seconds integer,
            attempt integer, lease_id uuid, lease_expires_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER VOLATILE
        SET search_path = pg_catalog ROWS 1 AS $fn$
        DECLARE
            selected_run record;
            new_expiry timestamptz;
        BEGIN
            IF p_lease_id IS NULL OR p_lease_seconds NOT BETWEEN 1 AND 60 THEN
                RAISE EXCEPTION 'INVALID_BROWSER_LEASE' USING ERRCODE = '22023';
            END IF;
            LOOP
                SELECT run.* INTO selected_run
                FROM control.browser_run AS run
                JOIN control.capability AS capability ON capability.id = run.capability_id
                JOIN control.workspace AS workspace ON workspace.id = run.workspace_id
                JOIN control.site AS site ON site.id = run.site_id
                WHERE (
                    run.state = 'QUEUED'
                    OR (run.state = 'RUNNING' AND run.lease_expires_at <= CURRENT_TIMESTAMP)
                )
                  AND run.expires_at > CURRENT_TIMESTAMP
                  AND capability.workspace_id = run.workspace_id
                  AND capability.revoked_at IS NULL
                  AND capability.expires_at > CURRENT_TIMESTAMP
                  AND jsonb_typeof(capability.scopes) = 'array'
                  AND capability.scopes ? 'preview:inspect'
                  AND run.target = ANY(capability.browser_allowed_targets)
                  AND workspace.site_id = run.site_id
                  AND workspace.created_by = run.delegator_id
                  AND workspace.status = 'ACTIVE'
                  AND workspace.expires_at > CURRENT_TIMESTAMP
                  AND site.status = 'ACTIVE'
                ORDER BY run.created_at, run.id
                FOR UPDATE OF run SKIP LOCKED LIMIT 1;
                IF NOT FOUND THEN
                    RETURN;
                END IF;
                PERFORM pg_advisory_xact_lock_shared(
                    hashtextextended(selected_run.workspace_id::text, 280)
                );
                IF NOT control.slaif_agent_browser_authorized(
                    selected_run.capability_id, selected_run.site_id,
                    selected_run.workspace_id, selected_run.delegator_id
                ) THEN
                    RETURN;
                END IF;
                IF selected_run.attempt_count >= selected_run.max_attempts THEN
                    UPDATE control.browser_run AS run
                    SET state = 'FAILED', completed_at = CURRENT_TIMESTAMP,
                        terminal_lease_id = run.lease_id,
                        lease_id = NULL, lease_expires_at = NULL,
                        summary = jsonb_build_object('attempts', run.attempt_count),
                        error_code = 'MAX_ATTEMPTS',
                        error_message = 'Maximum browser attempts reached.'
                    WHERE run.id = selected_run.id;
                    INSERT INTO audit.browser_event (
                        run_id, operation_id, capability_id, workspace_id,
                        site_id, delegator_id, event_type, attempt, lease_id,
                        details
                    ) VALUES (
                        selected_run.id, selected_run.operation_id,
                        selected_run.capability_id, selected_run.workspace_id,
                        selected_run.site_id, selected_run.delegator_id,
                        'MAX_ATTEMPTS', selected_run.attempt_count,
                        selected_run.lease_id, '{}'::jsonb
                    );
                    CONTINUE;
                END IF;
                IF selected_run.created_at
                    + make_interval(secs => selected_run.max_duration_seconds)
                    <= CURRENT_TIMESTAMP
                THEN
                    UPDATE control.browser_run AS run
                    SET state = 'TIMED_OUT', completed_at = CURRENT_TIMESTAMP,
                        terminal_lease_id = COALESCE(run.lease_id, p_lease_id),
                        lease_id = NULL, lease_expires_at = NULL,
                        summary = '{}'::jsonb, error_code = 'RUN_TIMED_OUT',
                        error_message = 'Browser run duration elapsed.'
                    WHERE run.id = selected_run.id;
                    INSERT INTO audit.browser_event (
                        run_id, operation_id, capability_id, workspace_id,
                        site_id, delegator_id, event_type, attempt, lease_id,
                        details
                    ) VALUES (
                        selected_run.id, selected_run.operation_id,
                        selected_run.capability_id, selected_run.workspace_id,
                        selected_run.site_id, selected_run.delegator_id,
                        'TIMED_OUT', selected_run.attempt_count,
                        selected_run.lease_id, '{}'::jsonb
                    );
                    CONTINUE;
                END IF;
                new_expiry := LEAST(
                    CURRENT_TIMESTAMP + make_interval(secs => p_lease_seconds),
                    selected_run.created_at
                        + make_interval(secs => selected_run.max_duration_seconds)
                );
                UPDATE control.browser_run AS run
                SET state = 'RUNNING', attempt_count = run.attempt_count + 1,
                    lease_id = p_lease_id, lease_expires_at = new_expiry,
                    started_at = COALESCE(run.started_at, CURRENT_TIMESTAMP)
                WHERE run.id = selected_run.id
                RETURNING run.* INTO selected_run;
                INSERT INTO audit.browser_event (
                    run_id, operation_id, capability_id, workspace_id, site_id,
                    delegator_id, event_type, attempt, lease_id, details
                ) VALUES (
                    selected_run.id, selected_run.operation_id,
                    selected_run.capability_id, selected_run.workspace_id,
                    selected_run.site_id, selected_run.delegator_id, 'LEASED',
                    selected_run.attempt_count, p_lease_id,
                    jsonb_build_object('lease_seconds', p_lease_seconds)
                );
                RETURN QUERY SELECT selected_run.contract_version,
                    selected_run.id, selected_run.operation_id,
                    selected_run.site_id, selected_run.workspace_id,
                    selected_run.capability_id, selected_run.delegator_id,
                    selected_run.route, selected_run.route_digest,
                    selected_run.target, selected_run.evidence,
                    selected_run.reserved_screenshots,
                    selected_run.reserved_artifact_bytes,
                    selected_run.max_duration_seconds,
                    selected_run.attempt_count, p_lease_id, new_expiry;
                RETURN;
            END LOOP;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_browser_run_renew(
            p_run_id uuid, p_lease_id uuid, p_lease_seconds integer
        ) RETURNS timestamptz LANGUAGE plpgsql SECURITY DEFINER VOLATILE
        SET search_path = pg_catalog AS $fn$
        DECLARE
            selected_run record;
            new_expiry timestamptz;
        BEGIN
            IF p_run_id IS NULL OR p_lease_id IS NULL
               OR p_lease_seconds NOT BETWEEN 1 AND 60
            THEN
                RAISE EXCEPTION 'INVALID_BROWSER_LEASE' USING ERRCODE = '22023';
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
            new_expiry := LEAST(
                CURRENT_TIMESTAMP + make_interval(secs => p_lease_seconds),
                selected_run.created_at
                    + make_interval(secs => selected_run.max_duration_seconds)
            );
            IF new_expiry <= CURRENT_TIMESTAMP THEN
                RAISE EXCEPTION 'BROWSER_LEASE_NOT_CURRENT' USING ERRCODE = 'P0002';
            END IF;
            UPDATE control.browser_run SET lease_expires_at = new_expiry
            WHERE id = p_run_id;
            INSERT INTO audit.browser_event (
                run_id, operation_id, capability_id, workspace_id, site_id,
                delegator_id, event_type, attempt, lease_id, details
            ) VALUES (
                selected_run.id, selected_run.operation_id,
                selected_run.capability_id, selected_run.workspace_id,
                selected_run.site_id, selected_run.delegator_id,
                'LEASE_RENEWED', selected_run.attempt_count, p_lease_id,
                jsonb_build_object('lease_seconds', p_lease_seconds)
            );
            RETURN new_expiry;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_browser_run_release(
            p_run_id uuid, p_lease_id uuid
        ) RETURNS text LANGUAGE plpgsql SECURITY DEFINER VOLATILE
        SET search_path = pg_catalog AS $fn$
        DECLARE
            selected_run record;
            next_state text;
        BEGIN
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
            THEN
                RAISE EXCEPTION 'BROWSER_LEASE_NOT_CURRENT' USING ERRCODE = 'P0002';
            END IF;
            IF selected_run.attempt_count >= selected_run.max_attempts THEN
                next_state := 'FAILED';
                UPDATE control.browser_run
                SET state = next_state, completed_at = CURRENT_TIMESTAMP,
                    terminal_lease_id = p_lease_id,
                    lease_id = NULL, lease_expires_at = NULL,
                    summary = jsonb_build_object('attempts', attempt_count),
                    error_code = 'MAX_ATTEMPTS',
                    error_message = 'Maximum browser attempts reached.'
                WHERE id = p_run_id;
            ELSE
                next_state := 'QUEUED';
                UPDATE control.browser_run
                SET state = next_state, lease_id = NULL, lease_expires_at = NULL
                WHERE id = p_run_id;
            END IF;
            INSERT INTO audit.browser_event (
                run_id, operation_id, capability_id, workspace_id, site_id,
                delegator_id, event_type, attempt, lease_id, details
            ) VALUES (
                selected_run.id, selected_run.operation_id,
                selected_run.capability_id, selected_run.workspace_id,
                selected_run.site_id, selected_run.delegator_id,
                CASE WHEN next_state = 'FAILED' THEN 'MAX_ATTEMPTS'
                     ELSE 'LEASE_RELEASED' END,
                selected_run.attempt_count, p_lease_id, '{}'::jsonb
            );
            RETURN next_state;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_browser_run_complete(
            p_run_id uuid, p_lease_id uuid, p_state text, p_summary jsonb,
            p_error_code text, p_error_message text
        ) RETURNS text LANGUAGE plpgsql SECURITY DEFINER VOLATILE
        SET search_path = pg_catalog AS $fn$
        DECLARE
            selected_run record;
        BEGIN
            IF p_state NOT IN ('COMPLETED','FAILED','TIMED_OUT','CANCELLED')
               OR p_summary IS NULL OR jsonb_typeof(p_summary) <> 'object'
               OR octet_length(p_summary::text) > 16384
               OR (
                    p_state = 'COMPLETED'
                    AND (p_error_code IS NOT NULL OR p_error_message IS NOT NULL)
               )
               OR (
                    p_state <> 'COMPLETED'
                    AND (p_error_code IS NULL
                        OR p_error_code !~ '^[A-Z][A-Z0-9_]{0,63}$'
                        OR p_error_message IS NULL
                        OR length(p_error_message) NOT BETWEEN 1 AND 512)
               )
            THEN
                RAISE EXCEPTION 'INVALID_BROWSER_COMPLETION' USING ERRCODE = '22023';
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
            ) THEN
                RAISE EXCEPTION 'BROWSER_AUTHORITY_DENIED' USING ERRCODE = 'P0002';
            END IF;
            IF selected_run.state IN ('COMPLETED','FAILED','TIMED_OUT','CANCELLED') THEN
                IF selected_run.terminal_lease_id IS DISTINCT FROM p_lease_id
                   OR selected_run.state <> p_state
                   OR selected_run.summary IS DISTINCT FROM p_summary
                   OR selected_run.error_code IS DISTINCT FROM p_error_code
                   OR selected_run.error_message IS DISTINCT FROM p_error_message
                THEN
                    RAISE EXCEPTION 'INVALID_BROWSER_TRANSITION' USING ERRCODE = 'P0001';
                END IF;
                RETURN selected_run.state;
            END IF;
            IF selected_run.state <> 'RUNNING'
               OR selected_run.lease_id IS DISTINCT FROM p_lease_id
               OR selected_run.lease_expires_at <= CURRENT_TIMESTAMP
            THEN
                RAISE EXCEPTION 'BROWSER_LEASE_NOT_CURRENT' USING ERRCODE = 'P0002';
            END IF;
            UPDATE control.browser_run
            SET state = p_state, summary = p_summary,
                error_code = p_error_code, error_message = p_error_message,
                completed_at = CURRENT_TIMESTAMP,
                terminal_lease_id = p_lease_id,
                lease_id = NULL, lease_expires_at = NULL
            WHERE id = p_run_id;
            INSERT INTO audit.browser_event (
                run_id, operation_id, capability_id, workspace_id, site_id,
                delegator_id, event_type, attempt, lease_id, details
            ) VALUES (
                selected_run.id, selected_run.operation_id,
                selected_run.capability_id, selected_run.workspace_id,
                selected_run.site_id, selected_run.delegator_id, p_state,
                selected_run.attempt_count, p_lease_id,
                jsonb_build_object('error_code', p_error_code)
            );
            RETURN p_state;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_agent_browser_artifact_register(
            p_run_id uuid, p_lease_id uuid, p_artifact_id uuid, p_kind text,
            p_mime_type text, p_sha256 text, p_size_bytes bigint,
            p_target text, p_route_digest text, p_expires_at timestamptz
        ) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER VOLATILE
        SET search_path = pg_catalog AS $fn$
        DECLARE
            selected_run record;
            existing record;
            used_bytes numeric;
        BEGIN
            IF p_artifact_id IS NULL
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
            WHERE artifact.id = p_artifact_id FOR UPDATE;
            IF FOUND THEN
                IF existing.run_id = p_run_id
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
                delegator_id, kind, mime_type, sha256, size_bytes, target,
                route_digest, expires_at
            ) VALUES (
                p_artifact_id, p_run_id, selected_run.site_id,
                selected_run.workspace_id, selected_run.capability_id,
                selected_run.delegator_id, p_kind, p_mime_type, p_sha256,
                p_size_bytes, p_target, p_route_digest, p_expires_at
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

    for relation in (
        "control.browser_run",
        "control.browser_idempotency",
        "control.browser_artifact",
        "audit.browser_event",
    ):
        op.execute(f"REVOKE ALL ON TABLE {relation} FROM PUBLIC")
        for role in (
            "slaif_control",
            "slaif_editor_runtime",
            "slaif_agent_runtime",
            "slaif_public_reader",
            "slaif_preview_reader",
            "slaif_reviewer",
            "slaif_scheduler",
            "slaif_media",
            "slaif_gc",
        ):
            op.execute(f"REVOKE ALL ON TABLE {relation} FROM {role}")
    op.execute("REVOKE ALL ON TABLE control.workspace FROM slaif_agent_runtime")
    op.execute("REVOKE ALL ON TABLE control.capability FROM slaif_agent_runtime")
    op.execute("GRANT USAGE ON SCHEMA control TO slaif_agent_runtime")
    _secure_functions()


def downgrade() -> None:
    for function in reversed((*_AGENT_FUNCTIONS, *_PRIVATE_FUNCTIONS)):
        op.execute(f"DROP FUNCTION IF EXISTS {function}")
    op.execute("DROP TABLE IF EXISTS audit.browser_event")
    op.execute("DROP TABLE IF EXISTS control.browser_artifact")
    op.execute("DROP TABLE IF EXISTS control.browser_idempotency")
    op.execute("DROP TABLE IF EXISTS control.browser_run")
    op.execute(
        "ALTER TABLE control.workspace DROP CONSTRAINT IF EXISTS workspace_site_delegator_unique"
    )
    op.execute(
        "ALTER TABLE control.capability "
        "DROP CONSTRAINT IF EXISTS capability_id_workspace_unique, "
        "DROP COLUMN IF EXISTS browser_allowed_targets, "
        "DROP COLUMN IF EXISTS browser_max_attempts, "
        "DROP COLUMN IF EXISTS browser_max_duration_seconds, "
        "DROP COLUMN IF EXISTS browser_max_evidence_per_run, "
        "DROP COLUMN IF EXISTS browser_max_routes_per_run, "
        "DROP COLUMN IF EXISTS browser_max_artifact_bytes, "
        "DROP COLUMN IF EXISTS browser_max_screenshots, "
        "DROP COLUMN IF EXISTS browser_max_concurrent_runs, "
        "DROP COLUMN IF EXISTS browser_max_runs"
    )
    op.execute("GRANT SELECT ON control.workspace TO slaif_agent_runtime")
    op.execute("GRANT SELECT ON control.capability TO slaif_agent_runtime")
