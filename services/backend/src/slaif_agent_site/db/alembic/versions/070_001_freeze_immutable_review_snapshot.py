# ruff: noqa: E501
"""Durable review jobs, the immutable review snapshot, and the real freeze."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "070_001"
down_revision: str | Sequence[str] | None = "069_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_WORKER_FUNCTIONS = (
    "control.slaif_review_job_claim(text)",
    "control.slaif_review_job_heartbeat(uuid)",
    "control.slaif_review_job_terminal(uuid,text,text)",
    "control.slaif_review_snapshot_complete(uuid,jsonb)",
    "control.slaif_review_workspace_state(uuid)",
    "control.slaif_review_browser_runs_cancel(uuid)",
)


def upgrade() -> None:
    # The workspace row gains the immutable-snapshot binding.
    op.execute(
        "ALTER TABLE control.workspace ADD COLUMN IF NOT EXISTS review_snapshot_id UUID"
    )

    # Durable review-job queue: at most one live job per workspace+kind.
    op.execute(
        """
        CREATE TABLE control.review_job (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workspace_id UUID NOT NULL,
            site_id UUID NOT NULL,
            job_kind TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'QUEUED',
            attempt_count INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3,
            claimed_by TEXT,
            claimed_at TIMESTAMPTZ,
            last_heartbeat TIMESTAMPTZ,
            payload JSONB,
            error TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT review_job_kind_allowed CHECK (
                job_kind IN ('FREEZE','ACCEPT','DISCARD')
            ),
            CONSTRAINT review_job_status_allowed CHECK (
                status IN ('QUEUED','CLAIMED','SUCCEEDED','FAILED')
            ),
            CONSTRAINT review_job_attempts_bounded CHECK (
                attempt_count BETWEEN 0 AND max_attempts
                AND max_attempts BETWEEN 1 AND 10
            ),
            CONSTRAINT review_job_terminal_shape CHECK (
                (status IN ('QUEUED','CLAIMED') AND error IS NULL)
                OR (status = 'SUCCEEDED' AND error IS NULL)
                OR (status = 'FAILED' AND error IS NOT NULL
                    AND error ~ '^[A-Z][A-Z0-9_]{0,63}$')
            ),
            CONSTRAINT review_job_claim_shape CHECK (
                (status = 'QUEUED' AND claimed_by IS NULL
                    AND claimed_at IS NULL AND last_heartbeat IS NULL)
                OR (status <> 'QUEUED' AND claimed_by IS NOT NULL
                    AND claimed_at IS NOT NULL
                    AND last_heartbeat IS NOT NULL
                    AND claimed_by ~ '^[A-Za-z0-9._:-]{1,128}$')
            ),
            CONSTRAINT review_job_error_shape CHECK (
                error IS NULL OR error ~ '^[A-Z][A-Z0-9_]{0,63}$'
            )
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX review_job_live_unique "
        "ON control.review_job (workspace_id, job_kind) "
        "WHERE status IN ('QUEUED','CLAIMED')"
    )
    op.execute(
        "CREATE INDEX review_job_claim_order "
        "ON control.review_job (status, created_at, id)"
    )
    op.execute(
        "CREATE INDEX review_job_stale_scan "
        "ON control.review_job (status, last_heartbeat)"
    )

    # Immutable complete review snapshots.
    op.execute(
        """
        CREATE TABLE control.review_snapshot (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            workspace_id UUID NOT NULL,
            site_id UUID NOT NULL,
            status TEXT NOT NULL,
            revision_watermark BIGINT NOT NULL,
            versions JSONB NOT NULL,
            normalized_state JSONB NOT NULL,
            validation_report JSONB NOT NULL,
            media_references JSONB NOT NULL,
            browser_evidence JSONB NOT NULL,
            payload JSONB NOT NULL,
            digest TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT review_snapshot_complete_only CHECK (
                status = 'COMPLETE'
            ),
            CONSTRAINT review_snapshot_digest_shape CHECK (
                digest ~ '^[0-9a-f]{64}$'
            ),
            CONSTRAINT review_snapshot_created_by_shape CHECK (
                created_by ~ '^[A-Za-z0-9._:-]{1,128}$'
            ),
            CONSTRAINT review_snapshot_payload_object CHECK (
                jsonb_typeof(payload) = 'object'
            ),
            CONSTRAINT review_snapshot_versions_object CHECK (
                jsonb_typeof(versions) = 'object'
            ),
            CONSTRAINT review_snapshot_normalized_object CHECK (
                jsonb_typeof(normalized_state) = 'object'
            ),
            CONSTRAINT review_snapshot_validation_object CHECK (
                jsonb_typeof(validation_report) = 'object'
            ),
            CONSTRAINT review_snapshot_media_array CHECK (
                jsonb_typeof(media_references) = 'array'
            ),
            CONSTRAINT review_snapshot_evidence_array CHECK (
                jsonb_typeof(browser_evidence) = 'array'
            )
        )
        """
    )
    op.execute(
        "CREATE INDEX review_snapshot_workspace "
        "ON control.review_snapshot (workspace_id, created_at)"
    )

    # ------------------------------------------------------------------
    # Canonical jsonb text: byte-compatible with Python's
    # json.dumps(value, sort_keys=True, separators=(",", ":"),
    # ensure_ascii=True) for every object the product produces.
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE FUNCTION control._slaif_jsonb_codepoint(p_ch text)
        RETURNS bigint LANGUAGE plpgsql IMMUTABLE STRICT
        SET search_path = pg_catalog AS $fn$
        DECLARE
            bytes bytea;
            n integer;
            b0 integer;
        BEGIN
            bytes := convert_to(p_ch, 'UTF8');
            n := octet_length(bytes);
            b0 := get_byte(bytes, 0);
            IF n = 1 THEN
                RETURN b0;
            ELSIF n = 2 THEN
                RETURN (b0 - 192) * 64 + (get_byte(bytes, 1) - 128);
            ELSIF n = 3 THEN
                RETURN (b0 - 224) * 4096
                    + (get_byte(bytes, 1) - 128) * 64
                    + (get_byte(bytes, 2) - 128);
            ELSIF n = 4 THEN
                RETURN (b0 - 240) * 262144
                    + (get_byte(bytes, 1) - 128) * 4096
                    + (get_byte(bytes, 2) - 128) * 64
                    + (get_byte(bytes, 3) - 128);
            END IF;
            RAISE EXCEPTION 'REVIEW_CANONICAL_BAD_UTF8' USING ERRCODE = '22023';
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control._slaif_hex4(p_value bigint)
        RETURNS text LANGUAGE plpgsql IMMUTABLE STRICT
        SET search_path = pg_catalog AS $fn$
        DECLARE
            result text := '';
            digit bigint;
        BEGIN
            IF p_value < 0 THEN
                RAISE EXCEPTION 'REVIEW_CANONICAL_BAD_CODEPOINT'
                    USING ERRCODE = '22023';
            END IF;
            WHILE p_value > 0 LOOP
                digit := p_value % 16;
                result := substr('0123456789abcdef', (digit + 1)::integer, 1) || result;
                p_value := p_value / 16;
            END LOOP;
            WHILE length(result) < 4 LOOP
                result := '0' || result;
            END LOOP;
            RETURN result;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control._slaif_jsonb_escape_string(p_value text)
        RETURNS text LANGUAGE plpgsql IMMUTABLE STRICT
        SET search_path = pg_catalog AS $fn$
        DECLARE
            ch text;
            code bigint;
            adj bigint;
            result text := '';
            bs text := chr(92);
        BEGIN
            FOR ch IN SELECT substr(p_value, i, 1) AS ch
                       FROM generate_series(1, length(p_value)) AS i
            LOOP
                IF ch = chr(34) THEN
                    result := result || bs || chr(34);
                ELSIF ch = bs THEN
                    result := result || bs || bs;
                ELSIF ch = chr(8) THEN
                    result := result || bs || 'b';
                ELSIF ch = chr(12) THEN
                    result := result || bs || 'f';
                ELSIF ch = chr(10) THEN
                    result := result || bs || 'n';
                ELSIF ch = chr(13) THEN
                    result := result || bs || 'r';
                ELSIF ch = chr(9) THEN
                    result := result || bs || 't';
                ELSE
                    code := control._slaif_jsonb_codepoint(ch);
                    IF code < 32 THEN
                        result := result || bs || 'u'
                            || control._slaif_hex4(code);
                    ELSIF code > 126 THEN
                        IF code <= 65535 THEN
                            result := result || bs || 'u'
                                || control._slaif_hex4(code);
                        ELSE
                            adj := code - 65536;
                            result := result || bs || 'u'
                                || control._slaif_hex4(55296 + adj / 1024)
                                || bs || 'u'
                                || control._slaif_hex4(56320 + adj % 1024);
                        END IF;
                    ELSE
                        result := result || ch;
                    END IF;
                END IF;
            END LOOP;
            RETURN result;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_canonical_jsonb_text(p_value jsonb)
        RETURNS text LANGUAGE plpgsql IMMUTABLE STRICT
        SET search_path = pg_catalog AS $fn$
        DECLARE
            key text;
            item jsonb;
            keys text[];
            parts text[];
        BEGIN
            CASE jsonb_typeof(p_value)
            WHEN 'object' THEN
                SELECT array_agg(k ORDER BY k COLLATE "C") INTO keys
                FROM jsonb_object_keys(p_value) AS k;
                parts := ARRAY[]::text[];
                FOR key IN SELECT k FROM unnest(keys) AS k
                LOOP
                    parts := array_append(
                        parts,
                        chr(34) || control._slaif_jsonb_escape_string(key) || '":'
                            || control.slaif_canonical_jsonb_text(p_value -> key)
                    );
                END LOOP;
                RETURN '{' || array_to_string(parts, ',') || '}';
            WHEN 'array' THEN
                parts := ARRAY[]::text[];
                FOR item IN SELECT value FROM jsonb_array_elements(p_value) AS v
                LOOP
                    parts := array_append(
                        parts, control.slaif_canonical_jsonb_text(item)
                    );
                END LOOP;
                RETURN '[' || array_to_string(parts, ',') || ']';
            WHEN 'string' THEN
                RETURN chr(34)
                    || control._slaif_jsonb_escape_string(p_value #>> '{}')
                    || chr(34);
            WHEN 'number' THEN
                RETURN p_value::text;
            WHEN 'boolean' THEN
                RETURN p_value::text;
            ELSE
                RETURN 'null';
            END CASE;
        END;
        $fn$
        """
    )
    for function in (
        "control._slaif_jsonb_codepoint(text)",
        "control._slaif_jsonb_escape_string(text)",
        "control._slaif_hex4(bigint)",
        "control.slaif_canonical_jsonb_text(jsonb)",
    ):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")

    # ------------------------------------------------------------------
    # Real freeze: ACTIVE -> FREEZING, revoke capabilities, enqueue the
    # durable FREEZE job. NEVER sets REVIEW (the worker does that only
    # after a complete verified snapshot).
    # ------------------------------------------------------------------
    op.execute("DROP FUNCTION IF EXISTS control.slaif_workspace_freeze(uuid)")
    op.execute(
        """
        CREATE FUNCTION control.slaif_workspace_freeze(
            p_workspace_id uuid
        ) RETURNS TABLE (
            id uuid, job_id uuid
        ) LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            ws_status text;
        BEGIN
            UPDATE control.workspace
               SET status = 'FREEZING', frozen_at = CURRENT_TIMESTAMP
             WHERE control.workspace.id = p_workspace_id
               AND status = 'ACTIVE'
               AND expires_at > CURRENT_TIMESTAMP;
            IF FOUND THEN
                UPDATE control.capability
                   SET revoked_at = CURRENT_TIMESTAMP
                 WHERE workspace_id = p_workspace_id
                   AND revoked_at IS NULL;
                INSERT INTO control.review_job
                    (workspace_id, site_id, job_kind, payload)
                SELECT p_workspace_id, w.site_id, 'FREEZE', '{}'::jsonb
                FROM control.workspace AS w
                WHERE w.id = p_workspace_id
                ON CONFLICT (workspace_id, job_kind)
                    WHERE status IN ('QUEUED','CLAIMED') DO NOTHING;
                RETURN QUERY
                    SELECT p_workspace_id, j.id
                    FROM control.review_job AS j
                    WHERE j.workspace_id = p_workspace_id
                      AND j.job_kind = 'FREEZE'
                      AND j.status IN ('QUEUED','CLAIMED');
            END IF;
            SELECT status INTO ws_status
            FROM control.workspace
            WHERE control.workspace.id = p_workspace_id;
            IF ws_status IS NULL THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_FOUND' USING ERRCODE = 'P0002';
            END IF;
            IF ws_status IS DISTINCT FROM 'FREEZING' THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_ACTIVE' USING ERRCODE = 'P0002';
            END IF;
            -- Retry after a semantic failure: a FREEZING workspace with no
            -- live FREEZE job accepts exactly one new job (the partial
            -- unique index still guarantees at most one live job).
            INSERT INTO control.review_job
                (workspace_id, site_id, job_kind, payload)
            SELECT p_workspace_id, w.site_id, 'FREEZE', '{}'::jsonb
            FROM control.workspace AS w
            WHERE w.id = p_workspace_id
            ON CONFLICT (workspace_id, job_kind)
                WHERE status IN ('QUEUED','CLAIMED') DO NOTHING;
            RETURN QUERY
                SELECT p_workspace_id, j.id
                FROM control.review_job AS j
                WHERE j.workspace_id = p_workspace_id
                  AND j.job_kind = 'FREEZE'
                  AND j.status IN ('QUEUED','CLAIMED');
        END;
        $fn$
        """
    )
    op.execute(
        "ALTER FUNCTION control.slaif_workspace_freeze(uuid) OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_workspace_freeze(uuid) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_workspace_freeze(uuid) "
        "TO slaif_control"
    )

    # Idempotency lookup for the Control freeze endpoint.
    op.execute(
        """
        CREATE FUNCTION control.slaif_review_live_freeze_job(p_workspace_id uuid)
        RETURNS uuid LANGUAGE sql SECURITY DEFINER STABLE
        SET search_path = pg_catalog AS $fn$
            SELECT id FROM control.review_job
            WHERE workspace_id = p_workspace_id
              AND job_kind = 'FREEZE'
              AND status IN ('QUEUED','CLAIMED')
            ORDER BY id LIMIT 1
        $fn$
        """
    )
    op.execute(
        "ALTER FUNCTION control.slaif_review_live_freeze_job(uuid) OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_review_live_freeze_job(uuid) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_review_live_freeze_job(uuid) "
        "TO slaif_control"
    )

    # Human Control freeze entry point: exact site binding + workspace:freeze
    # authority re-check, then the real freeze in the caller's transaction.
    # Actor type is intentionally unrestricted: the permission is a
    # site-governance key, so a governor may freeze HUMAN or AGENT workspaces
    # of the site. Unknown workspace or missing authority yields no row
    # (uniform 404 with the established control-plane pattern); a
    # non-freezable state propagates the real freeze's stable error.
    op.execute(
        """
        CREATE FUNCTION control.slaif_human_agent_workspace_freeze(
            p_workspace_id uuid, p_site_id uuid, p_user_id uuid
        ) RETURNS TABLE (job_id uuid, status text)
        LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            freeze_row record;
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM control.workspace AS w
                WHERE w.id = p_workspace_id
                  AND w.site_id = p_site_id
            ) THEN
                RETURN;
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM control.platform_administrator
                WHERE user_account_id = p_user_id
            ) AND NOT EXISTS (
                SELECT 1
                FROM control.slaif_effective_human_membership(
                    p_user_id, p_site_id
                ) AS m
                WHERE 'workspace:freeze' = ANY(m.effective_permissions)
            ) THEN
                RETURN;
            END IF;
            SELECT * INTO freeze_row
            FROM control.slaif_workspace_freeze(p_workspace_id);
            RETURN QUERY SELECT freeze_row.job_id, 'FREEZING';
        END;
        $fn$
        """
    )
    op.execute(
        "ALTER FUNCTION control.slaif_human_agent_workspace_freeze("
        "uuid, uuid, uuid) OWNER TO slaif_owner"
    )
    op.execute(
        "REVOKE ALL ON FUNCTION control.slaif_human_agent_workspace_freeze("
        "uuid, uuid, uuid) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_human_agent_workspace_freeze("
        "uuid, uuid, uuid) TO slaif_control"
    )

    # ------------------------------------------------------------------
    # Worker job lifecycle (EXECUTE: slaif_review_worker only).
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE FUNCTION control.slaif_review_job_claim(p_claimant text)
        RETURNS TABLE (
            id uuid, workspace_id uuid, site_id uuid, job_kind text,
            status text, attempt_count integer, max_attempts integer,
            claimed_by text, claimed_at timestamptz,
            last_heartbeat timestamptz, payload jsonb, error text,
            created_at timestamptz, updated_at timestamptz
        ) LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            selected control.review_job%ROWTYPE;
        BEGIN
            IF p_claimant IS NULL
               OR p_claimant !~ '^[A-Za-z0-9._:-]{1,128}$'
            THEN
                RAISE EXCEPTION 'REVIEW_CLAIMANT_INVALID' USING ERRCODE = '22023';
            END IF;
            -- Stale-claim recovery: a CLAIMED job without a fresh heartbeat
            -- is re-queued while attempts remain, and FAILED at the budget.
            UPDATE control.review_job
               SET status = 'QUEUED', claimed_by = NULL, claimed_at = NULL,
                   last_heartbeat = NULL, updated_at = CURRENT_TIMESTAMP
             WHERE control.review_job.status = 'CLAIMED'
               AND control.review_job.last_heartbeat
                   < CURRENT_TIMESTAMP - interval '60 seconds'
               AND control.review_job.attempt_count
                   < control.review_job.max_attempts;
            UPDATE control.review_job
               SET status = 'FAILED', error = 'REVIEW_JOB_STALE_AT_BUDGET',
                   updated_at = CURRENT_TIMESTAMP
             WHERE control.review_job.status = 'CLAIMED'
               AND control.review_job.last_heartbeat
                   < CURRENT_TIMESTAMP - interval '60 seconds'
               AND control.review_job.attempt_count
                   >= control.review_job.max_attempts;
            SELECT * INTO selected
            FROM control.review_job AS job
            WHERE job.status = 'QUEUED'
            ORDER BY job.created_at, job.id
            LIMIT 1
            FOR UPDATE SKIP LOCKED;
            IF NOT FOUND THEN
                RETURN;
            END IF;
            UPDATE control.review_job
               SET status = 'CLAIMED', claimed_by = p_claimant,
                   claimed_at = CURRENT_TIMESTAMP,
                   last_heartbeat = CURRENT_TIMESTAMP,
                   attempt_count = control.review_job.attempt_count + 1,
                   updated_at = CURRENT_TIMESTAMP
             WHERE control.review_job.id = selected.id;
            RETURN QUERY SELECT job.id, job.workspace_id, job.site_id,
                job.job_kind, job.status, job.attempt_count, job.max_attempts,
                job.claimed_by, job.claimed_at, job.last_heartbeat,
                job.payload, job.error, job.created_at, job.updated_at
            FROM control.review_job AS job
            WHERE job.id = selected.id;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_review_job_heartbeat(p_job_id uuid)
        RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE control.review_job
               SET last_heartbeat = CURRENT_TIMESTAMP,
                   updated_at = CURRENT_TIMESTAMP
             WHERE id = p_job_id AND status = 'CLAIMED';
            RETURN FOUND;
        END;
        $fn$
        """
    )
    op.execute(
        """
        CREATE FUNCTION control.slaif_review_job_terminal(
            p_job_id uuid, p_status text, p_error text
        ) RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        BEGIN
            IF p_status NOT IN ('SUCCEEDED','FAILED')
               OR (p_status = 'FAILED'
                   AND (p_error IS NULL OR p_error !~ '^[A-Z][A-Z0-9_]{0,63}$'))
               OR (p_status = 'SUCCEEDED' AND p_error IS NOT NULL)
            THEN
                RAISE EXCEPTION 'REVIEW_TERMINAL_INVALID' USING ERRCODE = '22023';
            END IF;
            UPDATE control.review_job
               SET status = p_status, error = p_error,
                   updated_at = CURRENT_TIMESTAMP
             WHERE id = p_job_id AND status = 'CLAIMED';
            IF NOT FOUND THEN
                RAISE EXCEPTION 'REVIEW_JOB_NOT_CLAIMED' USING ERRCODE = 'P0002';
            END IF;
            RETURN TRUE;
        END;
        $fn$
        """
    )

    # ------------------------------------------------------------------
    # Snapshot completion: the ONLY path into REVIEW.
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE FUNCTION control.slaif_review_snapshot_complete(
            p_workspace_id uuid, p_row jsonb
        ) RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            computed text;
            snapshot_id uuid;
        BEGIN
            IF jsonb_typeof(p_row) <> 'object'
               OR NOT (p_row ?& ARRAY[
                    'workspace_id','site_id','status','revision_watermark',
                    'versions','normalized_state','validation_report',
                    'media_references','browser_evidence','payload','digest',
                    'created_by']::text[])
               OR p_row->>'workspace_id' IS DISTINCT FROM p_workspace_id::text
               OR p_row->>'status' IS DISTINCT FROM 'COMPLETE'
               OR jsonb_typeof(p_row->'revision_watermark') <> 'number'
               OR (p_row->'revision_watermark')::bigint < 0
               OR jsonb_typeof(p_row->'versions') <> 'object'
               OR jsonb_typeof(p_row->'normalized_state') <> 'object'
               OR jsonb_typeof(p_row->'validation_report') <> 'object'
               OR jsonb_typeof(p_row->'media_references') <> 'array'
               OR jsonb_typeof(p_row->'browser_evidence') <> 'array'
               OR jsonb_typeof(p_row->'payload') <> 'object'
               OR p_row->>'digest' IS NULL
               OR p_row->>'digest' !~ '^[0-9a-f]{64}$'
               OR p_row->>'created_by' IS NULL
               OR p_row->>'created_by' !~ '^[A-Za-z0-9._:-]{1,128}$'
            THEN
                RAISE EXCEPTION 'SNAPSHOT_ROW_INVALID' USING ERRCODE = 'P0002';
            END IF;
            computed := encode(
                sha256(convert_to(
                    control.slaif_canonical_jsonb_text(p_row->'payload'), 'UTF8'
                )),
                'hex'
            );
            IF computed IS DISTINCT FROM p_row->>'digest' THEN
                RAISE EXCEPTION 'SNAPSHOT_DIGEST_MISMATCH'
                    USING ERRCODE = 'P0002';
            END IF;
            INSERT INTO control.review_snapshot (
                workspace_id, site_id, status, revision_watermark, versions,
                normalized_state, validation_report, media_references,
                browser_evidence, payload, digest, created_by
            ) VALUES (
                p_workspace_id, (p_row->>'site_id')::uuid, 'COMPLETE',
                (p_row->'revision_watermark')::bigint, p_row->'versions',
                p_row->'normalized_state', p_row->'validation_report',
                p_row->'media_references', p_row->'browser_evidence',
                p_row->'payload', p_row->>'digest', p_row->>'created_by'
            ) RETURNING id INTO snapshot_id;
            UPDATE control.workspace
               SET status = 'REVIEW', review_snapshot_id = snapshot_id
             WHERE id = p_workspace_id AND status = 'FREEZING';
            IF NOT FOUND THEN
                RAISE EXCEPTION 'WORKSPACE_NOT_FREEZING' USING ERRCODE = 'P0002';
            END IF;
            RETURN snapshot_id;
        END;
        $fn$
        """
    )

    # ------------------------------------------------------------------
    # Snapshot materialization: the trusted render surface under the
    # workspace COW context. EXECUTE: slaif_review_worker only.
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE FUNCTION control.slaif_review_workspace_state(p_workspace_id uuid)
        RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            ws control.workspace%ROWTYPE;
            site_row record;
            page_row record;
            nodes_row jsonb;
            node_props jsonb;
            route text;
            media_key text;
            media_id uuid;
            media_row record;
            page_docs jsonb := '[]'::jsonb;
            media_docs jsonb := '{}'::jsonb;
            doc jsonb;
        BEGIN
            SELECT * INTO ws FROM control.workspace
            WHERE id = p_workspace_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'REVIEW_WORKSPACE_NOT_FOUND'
                    USING ERRCODE = 'P0002';
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM control.site AS site
                WHERE site.id = ws.site_id AND site.status = 'ACTIVE'
            ) THEN
                RAISE EXCEPTION 'REVIEW_SITE_NOT_ACTIVE'
                    USING ERRCODE = 'P0002';
            END IF;
            PERFORM pg_advisory_xact_lock(
                hashtextextended(p_workspace_id::text, 280)
            );
            PERFORM set_config('app.session_id', p_workspace_id::text, true);
            SELECT site_key, display_name, default_locale,
                   component_catalog_version
              INTO site_row
              FROM control.site WHERE id = ws.site_id;

            FOR page_row IN
                SELECT p.*
                FROM content.page AS p
                WHERE p.site_id = ws.site_id
                  AND p.deleted_at IS NULL
                  AND p.status IN ('PUBLISHED','DRAFT')
                ORDER BY p.locale COLLATE "C", p.slug COLLATE "C", p.id
            LOOP
                BEGIN
                    route := content.slaif_agent_page_effective_route(
                        page_row.id
                    );
                EXCEPTION WHEN OTHERS THEN
                    route := NULL;
                END;
                SELECT coalesce(
                    jsonb_agg(row_to_json(c) ORDER BY c.slot_key, c.order_key,
                               c.id),
                    '[]'::jsonb
                ) INTO nodes_row
                FROM (SELECT * FROM content.page_composition AS c
                      WHERE c.site_id = ws.site_id
                        AND c.page_id = page_row.id) AS c;
                -- Collect the media references of this page's composition.
                IF nodes_row IS NOT NULL THEN
                    FOR node_props IN
                        SELECT c2.props FROM content.page_composition AS c2
                        WHERE c2.site_id = ws.site_id
                          AND c2.page_id = page_row.id
                    LOOP
                        IF node_props IS NULL THEN
                            CONTINUE;
                        END IF;
                        IF jsonb_typeof(node_props -> 'mediaId') = 'string' THEN
                            BEGIN
                                media_id := (node_props ->> 'mediaId')::uuid;
                                media_key := media_id::text;
                                IF not (media_docs ? media_key) THEN
                                    SELECT * INTO media_row
                                    FROM content.slaif_render_media_resolve(
                                        ws.site_id, media_id
                                    );
                                    IF FOUND THEN
                                        media_docs := media_docs || jsonb_build_object(
                                            media_key, jsonb_build_object(
                                                'id', media_id,
                                                'mime_type', media_row.mime_type,
                                                'size_bytes',
                                                    media_row.size_bytes,
                                                'content_hash',
                                                    media_row.content_hash,
                                                'public_status',
                                                    media_row.public_status
                                            )
                                        );
                                    END IF;
                                END IF;
                            EXCEPTION WHEN invalid_text_representation THEN
                                NULL;
                            END;
                        END IF;
                        IF jsonb_typeof(node_props -> 'items') = 'array' THEN
                            FOR media_key IN
                                SELECT item ->> 'mediaId'
                                FROM jsonb_array_elements(
                                    node_props -> 'items'
                                ) AS item
                                WHERE jsonb_typeof(item -> 'mediaId')
                                      = 'string'
                            LOOP
                                BEGIN
                                    media_id := media_key::uuid;
                                    media_key := media_id::text;
                                    IF not (media_docs ? media_key) THEN
                                        SELECT * INTO media_row
                                        FROM content.slaif_render_media_resolve(
                                            ws.site_id, media_id
                                        );
                                        IF FOUND THEN
                                            media_docs := media_docs || jsonb_build_object(
                                                media_key, jsonb_build_object(
                                                    'id', media_id,
                                                    'mime_type',
                                                        media_row.mime_type,
                                                    'size_bytes',
                                                        media_row.size_bytes,
                                                    'content_hash',
                                                        media_row.content_hash,
                                                    'public_status',
                                                        media_row.public_status
                                                )
                                            );
                                        END IF;
                                    END IF;
                                EXCEPTION WHEN invalid_text_representation THEN
                                    NULL;
                                END;
                            END LOOP;
                        END IF;
                    END LOOP;
                END IF;
                page_docs := page_docs || jsonb_build_object(
                    'id', page_row.id,
                    'site_id', page_row.site_id,
                    'slug', page_row.slug,
                    'title', page_row.title,
                    'status', page_row.status,
                    'locale', page_row.locale,
                    'parent_id', page_row.parent_id,
                    'route_template', page_row.route_template,
                    'effective_route', route,
                    'row_version', page_row.row_version,
                    'nodes', nodes_row
                );
            END LOOP;

            doc := jsonb_build_object(
                'state_version', 'review-snapshot/v1',
                'workspace_id', p_workspace_id,
                'site_id', ws.site_id,
                'site', jsonb_build_object(
                    'site_key', site_row.site_key,
                    'display_name', site_row.display_name,
                    'default_locale', site_row.default_locale,
                    'component_catalog_version',
                        site_row.component_catalog_version
                ),
                'base_site_revision', ws.base_site_revision,
                'operation_watermark', ws.operation_watermark,
                'locales', (
                    SELECT coalesce(
                        jsonb_agg(jsonb_build_object(
                            'tag', l.tag, 'enabled', l.enabled,
                            'is_default', l.is_default, 'position', l.position
                        ) ORDER BY l.position, l.tag COLLATE "C"),
                        '[]'::jsonb
                    )
                    FROM content.site_locale AS l
                    WHERE l.site_id = ws.site_id
                ),
                'theme', (
                    SELECT row_to_json(t)
                    FROM content.slaif_theme_project(ws.site_id) AS t
                ),
                'regions', (
                    SELECT coalesce(
                        jsonb_agg(row_to_json(r)
                            ORDER BY r.region_key, r.variant),
                        '[]'::jsonb
                    )
                    FROM content.slaif_region_list(ws.site_id) AS r
                ),
                'navigation', jsonb_build_object(
                    'definitions', (
                        SELECT coalesce(
                            jsonb_agg(row_to_json(d)
                                ORDER BY d.key COLLATE "C"),
                            '[]'::jsonb
                        )
                        FROM content.navigation AS d
                        WHERE d.site_id = ws.site_id
                    ),
                    'items', (
                        SELECT coalesce(
                            jsonb_agg(row_to_json(n)
                                ORDER BY n.navigation_id, n."position", n.id),
                            '[]'::jsonb
                        )
                        FROM content.slaif_render_navigation_items(
                            ws.site_id, site_row.default_locale,
                            ARRAY['PUBLISHED','DRAFT']
                        ) AS n
                    )
                ),
                'redirects', (
                    SELECT coalesce(
                        jsonb_agg(row_to_json(rd)
                            ORDER BY rd.source_route COLLATE "C",
                                     rd.locale NULLS FIRST),
                        '[]'::jsonb
                    )
                    FROM (SELECT id, site_id, source_route, target,
                                 status_code, locale
                          FROM content.redirect
                          WHERE site_id = ws.site_id) AS rd
                ),
                'pages', page_docs,
                'media', media_docs
            );
            RETURN doc;
        END;
        $fn$
        """
    )

    # ------------------------------------------------------------------
    # Browser-run freeze policy: bounded cancel of outstanding durable
    # runs. The CANCELLED terminal shape is exactly the one 035_001's
    # CHECK constraints already permit; RUNNING runs keep their current
    # lease as terminal_lease_id, QUEUED runs mint one (their lease_id
    # is NULL). No 035_001 state machine is widened.
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE FUNCTION control.slaif_review_browser_runs_cancel(
            p_workspace_id uuid
        ) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER
        SET search_path = pg_catalog AS $fn$
        DECLARE
            run_row control.browser_run%ROWTYPE;
            cancelled jsonb := '[]'::jsonb;
        BEGIN
            FOR run_row IN
                SELECT r.*
                FROM control.browser_run AS r
                WHERE r.workspace_id = p_workspace_id
                  AND r.state IN ('QUEUED','RUNNING')
                ORDER BY r.created_at, r.id
                FOR UPDATE
            LOOP
                UPDATE control.browser_run
                   SET state = 'CANCELLED',
                       completed_at = CURRENT_TIMESTAMP,
                       summary = jsonb_build_object(
                           'cancelled_by_freeze', true
                       ),
                       error_code = 'FREEZE_CANCEL',
                       error_message = 'Cancelled by workspace freeze drain.',
                       terminal_lease_id = COALESCE(
                           run_row.lease_id, gen_random_uuid()
                       ),
                       lease_id = NULL,
                       lease_expires_at = NULL
                 WHERE id = run_row.id;
                INSERT INTO audit.browser_event (
                    run_id, operation_id, capability_id, workspace_id,
                    site_id, delegator_id, event_type, attempt, lease_id,
                    details
                ) VALUES (
                    run_row.id, run_row.operation_id, run_row.capability_id,
                    run_row.workspace_id, run_row.site_id, run_row.delegator_id,
                    'CANCELLED', run_row.attempt_count,
                    CASE WHEN run_row.state = 'RUNNING'
                         THEN run_row.lease_id ELSE NULL END,
                    jsonb_build_object('error_code', 'FREEZE_CANCEL')
                );
                cancelled := cancelled || jsonb_build_object(
                    'id', run_row.id,
                    'previous_state', run_row.state,
                    'route', run_row.route
                );
            END LOOP;
            RETURN jsonb_build_object('cancelled', cancelled);
        END;
        $fn$
        """
    )

    for function in _WORKER_FUNCTIONS:
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
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO slaif_review_worker")

    # ------------------------------------------------------------------
    # Table grants: worker-only DML on its own queues; the snapshot is
    # insert-only for everyone and owner-mutable only.
    # ------------------------------------------------------------------
    for relation in ("control.review_job", "control.review_snapshot"):
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
    op.execute("GRANT USAGE ON SCHEMA control TO slaif_review_worker")
    op.execute(
        "GRANT SELECT ON control.workspace, control.site, control.capability, "
        "control.browser_run TO slaif_review_worker"
    )
    op.execute(
        "GRANT SELECT, INSERT, UPDATE ON control.review_job TO slaif_review_worker"
    )
    op.execute("GRANT SELECT, INSERT ON control.review_snapshot TO slaif_review_worker")

    # ------------------------------------------------------------------
    # R4 shared-lock retrofit: verified, no function change.
    # Every live product-mutation family already takes the workspace
    # lifecycle lock (key 280) before its in-transaction ACTIVE recheck:
    # Agent REST data plane via control.slaif_agent_require_capability
    # (shared 280 since 050_001, before every 994-family lock); human
    # editor asserts via slaif_human_editor_workspace_assert (exclusive
    # 280 under p_lock since 028_001, re-asserted in 069_001); media
    # asserts via control.slaif_media_workspace_assert (exclusive 280
    # since 030_001/031_001, before every 702/913 lock); the browser
    # control plane since 035_001-037_001 (shared 280). The freeze job
    # (slaif_review_workspace_state) is the only long-lived exclusive
    # 280 acquirer; see the R4 compliance table in the 082-a report.
    # ------------------------------------------------------------------


def downgrade() -> None:
    op.execute(
        "DROP FUNCTION IF EXISTS control.slaif_human_agent_workspace_freeze("
        "uuid, uuid, uuid)"
    )
    for function in _WORKER_FUNCTIONS:
        op.execute(f"DROP FUNCTION IF EXISTS {function}")
    op.execute("DROP FUNCTION IF EXISTS control.slaif_review_live_freeze_job(uuid)")
    op.execute("DROP FUNCTION IF EXISTS control.slaif_canonical_jsonb_text(jsonb)")
    op.execute("DROP FUNCTION IF EXISTS control._slaif_jsonb_escape_string(text)")
    op.execute("DROP FUNCTION IF EXISTS control._slaif_hex4(bigint)")
    op.execute("DROP FUNCTION IF EXISTS control._slaif_jsonb_codepoint(text)")
    # Restore the exact 024_001 freeze stub.
    op.execute("DROP FUNCTION IF EXISTS control.slaif_workspace_freeze(uuid)")
    op.execute(
        """
        CREATE FUNCTION control.slaif_workspace_freeze(
            p_workspace_id uuid
        ) RETURNS TABLE (
            id uuid, status text
        ) LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog AS $fn$
        BEGIN
            UPDATE control.workspace SET
                status = 'FREEZING',
                frozen_at = CURRENT_TIMESTAMP
            WHERE id = p_workspace_id AND status = 'ACTIVE';
            IF NOT FOUND THEN
                RAISE EXCEPTION 'NOT_FOUND_OR_NOT_ACTIVE' USING ERRCODE = 'P0002';
            END IF;
            UPDATE control.workspace SET status = 'REVIEW' WHERE id = p_workspace_id;
            RETURN QUERY SELECT w.id, w.status FROM control.workspace w WHERE w.id = p_workspace_id;
        END;
        $fn$
        """
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION control.slaif_workspace_freeze(uuid) TO slaif_control"
    )
    op.execute("DROP TABLE IF EXISTS control.review_snapshot CASCADE")
    op.execute("DROP TABLE IF EXISTS control.review_job CASCADE")
    op.execute("ALTER TABLE control.workspace DROP COLUMN IF EXISTS review_snapshot_id")
