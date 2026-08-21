"""Add non-COW site, trusted mapping, quota, and resolver foundations."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "013_001"
down_revision: str | Sequence[str] | None = "012_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_SITE_RESULT = """
    "site_id" uuid, "site_key" text, "display_name" text, "status" text,
    "canonical_revision" bigint, "default_locale" text,
    "component_catalog_version" text, "content_model_revision" bigint,
    "created_at" timestamp with time zone, "updated_at" timestamp with time zone
"""


def _secure(functions: tuple[str, ...]) -> None:
    for function in functions:
        op.execute(f'ALTER FUNCTION "control".{function} OWNER TO "slaif_owner"')
        op.execute(f'REVOKE ALL ON FUNCTION "control".{function} FROM PUBLIC')
        op.execute(f'GRANT EXECUTE ON FUNCTION "control".{function} TO "slaif_control"')


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE "control"."site_policy" (
            "singleton" boolean PRIMARY KEY DEFAULT TRUE,
            "max_sites" integer NOT NULL DEFAULT 100,
            CONSTRAINT "site_policy_singleton" CHECK (singleton),
            CONSTRAINT "site_policy_max_sites_bounded"
                CHECK (max_sites BETWEEN 1 AND 1000),
            CONSTRAINT "site_policy_installation_fk" FOREIGN KEY (singleton)
                REFERENCES "control"."installation_state" (singleton)
                ON DELETE RESTRICT
        )
        """
    )
    op.execute('INSERT INTO "control"."site_policy" DEFAULT VALUES')
    op.execute(
        """
        CREATE TABLE "control"."site" (
            "id" uuid PRIMARY KEY DEFAULT pg_catalog.gen_random_uuid(),
            "site_key" text NOT NULL,
            "display_name" text NOT NULL,
            "status" text NOT NULL DEFAULT 'ACTIVE',
            "canonical_revision" bigint NOT NULL DEFAULT 0,
            "default_locale" text NOT NULL,
            "component_catalog_version" text NOT NULL,
            "content_model_revision" bigint NOT NULL DEFAULT 0,
            "created_at" timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updated_at" timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "site_key_unique" UNIQUE (site_key),
            CONSTRAINT "site_key_shape" CHECK (
                site_key ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'
                AND char_length(site_key) BETWEEN 1 AND 63
            ),
            CONSTRAINT "site_display_name_bounded" CHECK (
                char_length(display_name) BETWEEN 1 AND 128
                AND display_name = pg_catalog.btrim(display_name)
            ),
            CONSTRAINT "site_status" CHECK (status IN ('ACTIVE', 'ARCHIVED')),
            CONSTRAINT "site_canonical_revision_nonnegative"
                CHECK (canonical_revision >= 0),
            CONSTRAINT "site_content_model_revision_nonnegative"
                CHECK (content_model_revision >= 0),
            CONSTRAINT "site_default_locale_bounded"
                CHECK (char_length(default_locale) BETWEEN 2 AND 35),
            CONSTRAINT "site_catalog_version_bounded" CHECK (
                char_length(component_catalog_version) BETWEEN 1 AND 64
                AND component_catalog_version ~ '^[A-Za-z0-9][A-Za-z0-9._-]*$'
            )
        )
        """
    )
    op.execute(
        """
        CREATE TABLE "control"."site_domain" (
            "id" uuid PRIMARY KEY DEFAULT pg_catalog.gen_random_uuid(),
            "site_id" uuid NOT NULL
                REFERENCES "control"."site" ("id") ON DELETE RESTRICT,
            "hostname" text NOT NULL,
            "path_prefix" text NOT NULL,
            "is_primary" boolean NOT NULL DEFAULT FALSE,
            "created_at" timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT "site_domain_mapping_unique"
                UNIQUE (hostname, path_prefix),
            CONSTRAINT "site_domain_hostname_bounded" CHECK (
                char_length(hostname) BETWEEN 1 AND 253
                AND hostname = pg_catalog.lower(hostname)
                AND hostname !~ '[:/@?#]'
                AND pg_catalog.strpos(hostname, E'\\\\') = 0
            ),
            CONSTRAINT "site_domain_path_prefix_bounded" CHECK (
                char_length(path_prefix) BETWEEN 1 AND 512
                AND left(path_prefix, 1) = '/'
                AND (path_prefix = '/' OR right(path_prefix, 1) <> '/')
                AND path_prefix !~ '//|%|[?#]'
                AND pg_catalog.strpos(path_prefix, E'\\\\') = 0
            )
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX "site_domain_one_primary_per_site"
        ON "control"."site_domain" ("site_id") WHERE is_primary
        """
    )
    op.execute(
        """
        CREATE INDEX "site_domain_resolution_order"
        ON "control"."site_domain" ("hostname", char_length("path_prefix") DESC)
        """
    )
    for table in ("site_policy", "site", "site_domain"):
        op.execute(f'ALTER TABLE "control"."{table}" OWNER TO "slaif_owner"')
        op.execute(f'REVOKE ALL ON TABLE "control"."{table}" FROM PUBLIC')

    op.execute(
        f"""
        CREATE FUNCTION "control"."slaif_site_create"(
            "p_site_key" text, "p_display_name" text,
            "p_default_locale" text, "p_component_catalog_version" text
        ) RETURNS TABLE ({_SITE_RESULT})
        LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
        SET search_path = pg_catalog ROWS 1 AS $function$
        DECLARE quota integer; created "control"."site"%ROWTYPE;
        BEGIN
            SELECT max_sites INTO STRICT quota
            FROM "control"."site_policy" WHERE singleton FOR UPDATE;
            IF (SELECT count(*) FROM "control"."site") >= quota THEN
                RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'site quota reached';
            END IF;
            INSERT INTO "control"."site" (
                site_key, display_name, default_locale, component_catalog_version
            ) VALUES (
                p_site_key, p_display_name, p_default_locale,
                p_component_catalog_version
            ) RETURNING * INTO created;
            RETURN QUERY SELECT created.id, created.site_key, created.display_name,
                created.status, created.canonical_revision, created.default_locale,
                created.component_catalog_version, created.content_model_revision,
                created.created_at, created.updated_at;
        END $function$
        """
    )
    op.execute(
        f"""
        CREATE FUNCTION "control"."slaif_site_get"("p_site_id" uuid)
        RETURNS TABLE ({_SITE_RESULT})
        LANGUAGE sql STABLE SECURITY DEFINER PARALLEL SAFE
        SET search_path = pg_catalog ROWS 1 AS $function$
            SELECT site.id, site.site_key, site.display_name, site.status,
                site.canonical_revision, site.default_locale,
                site.component_catalog_version, site.content_model_revision,
                site.created_at, site.updated_at
            FROM "control"."site" AS site WHERE site.id = p_site_id
        $function$
        """
    )
    op.execute(
        f"""
        CREATE FUNCTION "control"."slaif_site_list"()
        RETURNS TABLE ({_SITE_RESULT})
        LANGUAGE sql STABLE SECURITY DEFINER PARALLEL SAFE
        SET search_path = pg_catalog AS $function$
            SELECT site.id, site.site_key, site.display_name, site.status,
                site.canonical_revision, site.default_locale,
                site.component_catalog_version, site.content_model_revision,
                site.created_at, site.updated_at
            FROM "control"."site" AS site ORDER BY site.site_key
        $function$
        """
    )
    op.execute(
        f"""
        CREATE FUNCTION "control"."slaif_site_update"(
            "p_site_id" uuid, "p_display_name" text, "p_default_locale" text
        ) RETURNS TABLE ({_SITE_RESULT})
        LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
        SET search_path = pg_catalog ROWS 1 AS $function$
        DECLARE changed "control"."site"%ROWTYPE;
        BEGIN
            UPDATE "control"."site" AS site SET
                display_name = p_display_name,
                default_locale = p_default_locale,
                updated_at = CURRENT_TIMESTAMP
            WHERE site.id = p_site_id AND site.status = 'ACTIVE'
            RETURNING site.* INTO changed;
            IF NOT FOUND THEN RETURN; END IF;
            RETURN QUERY SELECT changed.id, changed.site_key, changed.display_name,
                changed.status, changed.canonical_revision, changed.default_locale,
                changed.component_catalog_version, changed.content_model_revision,
                changed.created_at, changed.updated_at;
        END $function$
        """
    )
    op.execute(
        f"""
        CREATE FUNCTION "control"."slaif_site_archive"("p_site_id" uuid)
        RETURNS TABLE ({_SITE_RESULT})
        LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
        SET search_path = pg_catalog ROWS 1 AS $function$
        DECLARE changed "control"."site"%ROWTYPE;
        BEGIN
            SELECT * INTO changed FROM "control"."site"
                WHERE id = p_site_id FOR UPDATE;
            IF NOT FOUND THEN RETURN; END IF;
            IF changed.status = 'ACTIVE' THEN
                UPDATE "control"."site" SET status = 'ARCHIVED',
                    updated_at = CURRENT_TIMESTAMP WHERE id = p_site_id
                    RETURNING * INTO changed;
            END IF;
            RETURN QUERY SELECT changed.id, changed.site_key, changed.display_name,
                changed.status, changed.canonical_revision, changed.default_locale,
                changed.component_catalog_version, changed.content_model_revision,
                changed.created_at, changed.updated_at;
        END $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_site_domain_put"(
            "p_site_id" uuid, "p_domain_id" uuid, "p_hostname" text,
            "p_path_prefix" text, "p_is_primary" boolean
        ) RETURNS TABLE (
            "domain_id" uuid, "site_id" uuid, "hostname" text,
            "path_prefix" text, "is_primary" boolean,
            "created_at" timestamp with time zone
        ) LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
        SET search_path = pg_catalog ROWS 1 AS $function$
        DECLARE changed "control"."site_domain"%ROWTYPE;
        BEGIN
            PERFORM 1 FROM "control"."site" WHERE id = p_site_id
                AND status = 'ACTIVE' FOR UPDATE;
            IF NOT FOUND THEN RETURN; END IF;
            PERFORM 1 FROM "control"."site_domain" AS mapping
                WHERE mapping.site_id = p_site_id
                FOR UPDATE;
            IF p_domain_id IS NULL THEN
                IF p_is_primary THEN
                    UPDATE "control"."site_domain" AS mapping
                        SET is_primary = FALSE
                        WHERE mapping.site_id = p_site_id AND mapping.is_primary;
                END IF;
                INSERT INTO "control"."site_domain" (
                    site_id, hostname, path_prefix, is_primary
                ) VALUES (p_site_id, p_hostname, p_path_prefix, p_is_primary)
                RETURNING * INTO changed;
            ELSE
                PERFORM 1 FROM "control"."site_domain" AS mapping
                    WHERE mapping.id = p_domain_id
                      AND mapping.site_id = p_site_id FOR UPDATE;
                IF NOT FOUND THEN RETURN; END IF;
                IF p_is_primary THEN
                    UPDATE "control"."site_domain" AS mapping
                        SET is_primary = FALSE
                        WHERE mapping.site_id = p_site_id
                          AND mapping.id <> p_domain_id AND mapping.is_primary;
                END IF;
                UPDATE "control"."site_domain" AS mapping SET hostname = p_hostname,
                    path_prefix = p_path_prefix, is_primary = p_is_primary
                    WHERE mapping.id = p_domain_id
                      AND mapping.site_id = p_site_id
                    RETURNING mapping.* INTO changed;
            END IF;
            RETURN QUERY SELECT changed.id, changed.site_id, changed.hostname,
                changed.path_prefix, changed.is_primary, changed.created_at;
        END $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_site_domain_remove"(
            "p_site_id" uuid, "p_domain_id" uuid
        ) RETURNS boolean
        LANGUAGE plpgsql VOLATILE SECURITY DEFINER PARALLEL UNSAFE
        SET search_path = pg_catalog AS $function$
        DECLARE target "control"."site_domain"%ROWTYPE;
        BEGIN
            PERFORM 1 FROM "control"."site" WHERE id = p_site_id FOR UPDATE;
            IF NOT FOUND THEN RETURN FALSE; END IF;
            SELECT * INTO target FROM "control"."site_domain" AS mapping
                WHERE mapping.id = p_domain_id
                  AND mapping.site_id = p_site_id FOR UPDATE;
            IF NOT FOUND OR target.is_primary THEN RETURN FALSE; END IF;
            DELETE FROM "control"."site_domain" AS mapping
                WHERE mapping.id = p_domain_id
                  AND mapping.site_id = p_site_id;
            RETURN FOUND;
        END $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_site_resolve"(
            "p_hostname" text, "p_path" text
        ) RETURNS TABLE (
            "site_id" uuid, "site_key" text, "status" text,
            "canonical_revision" bigint, "default_locale" text,
            "matched_hostname" text, "matched_path_prefix" text
        ) LANGUAGE sql STABLE SECURITY DEFINER PARALLEL SAFE
        SET search_path = pg_catalog AS $function$
            SELECT site.id, site.site_key, site.status,
                site.canonical_revision, site.default_locale,
                mapping.hostname, mapping.path_prefix
            FROM "control"."site_domain" AS mapping
            JOIN "control"."site" AS site ON site.id = mapping.site_id
            WHERE site.status = 'ACTIVE' AND mapping.hostname = p_hostname
              AND (mapping.path_prefix = '/' OR p_path = mapping.path_prefix
                   OR left(p_path, char_length(mapping.path_prefix) + 1)
                      = mapping.path_prefix || '/')
            ORDER BY char_length(mapping.path_prefix) DESC, mapping.id
            LIMIT 2
        $function$
        """
    )
    op.execute(
        """
        CREATE FUNCTION "control"."slaif_site_resolve_local"("p_site_key" text)
        RETURNS TABLE (
            "site_id" uuid, "site_key" text, "status" text,
            "canonical_revision" bigint, "default_locale" text
        ) LANGUAGE sql STABLE SECURITY DEFINER PARALLEL SAFE
        SET search_path = pg_catalog ROWS 1 AS $function$
            SELECT site.id, site.site_key, site.status,
                site.canonical_revision, site.default_locale
            FROM "control"."site" AS site
            WHERE site.status = 'ACTIVE' AND site.site_key = p_site_key
        $function$
        """
    )

    _secure(
        (
            '"slaif_site_create"(text, text, text, text)',
            '"slaif_site_get"(uuid)',
            '"slaif_site_list"()',
            '"slaif_site_update"(uuid, text, text)',
            '"slaif_site_archive"(uuid)',
            '"slaif_site_domain_put"(uuid, uuid, text, text, boolean)',
            '"slaif_site_domain_remove"(uuid, uuid)',
            '"slaif_site_resolve"(text, text)',
            '"slaif_site_resolve_local"(text)',
        )
    )


def downgrade() -> None:
    for function in (
        '"slaif_site_resolve_local"(text)',
        '"slaif_site_resolve"(text, text)',
        '"slaif_site_domain_remove"(uuid, uuid)',
        '"slaif_site_domain_put"(uuid, uuid, text, text, boolean)',
        '"slaif_site_archive"(uuid)',
        '"slaif_site_update"(uuid, text, text)',
        '"slaif_site_list"()',
        '"slaif_site_get"(uuid)',
        '"slaif_site_create"(text, text, text, text)',
    ):
        op.execute(f'DROP FUNCTION "control".{function}')
    op.execute('DROP TABLE "control"."site_domain"')
    op.execute('DROP TABLE "control"."site"')
    op.execute('DROP TABLE "control"."site_policy"')
