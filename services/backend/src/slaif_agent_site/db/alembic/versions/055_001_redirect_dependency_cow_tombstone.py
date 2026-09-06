# ruff: noqa: E501
"""Skip hidden COW iterator rows during redirect page dependency checks."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "055_001"
down_revision: str | Sequence[str] | None = "054_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_redirect_page_target_dependency(
            p_site_id uuid, p_route text, p_page_id uuid
        ) RETURNS boolean LANGUAGE plpgsql STABLE SECURITY DEFINER
        SET search_path=pg_catalog AS $fn$
        DECLARE incoming record; candidate record; default_locale text;
        BEGIN
            SELECT l.tag INTO default_locale FROM content.site_locale l
            WHERE l.site_id=p_site_id AND l.enabled AND l.is_default;
            FOR incoming IN
                SELECT r.* FROM content.redirect r
                WHERE r.site_id=p_site_id AND r.target=p_route
            LOOP
                FOR candidate IN
                    SELECT p.id FROM content.page p
                    WHERE p.site_id=p_site_id AND p.id<>p_page_id
                      AND p.deleted_at IS NULL AND p.route_template IS NULL
                      AND p.locale=coalesce(incoming.locale,default_locale)
                LOOP
                    BEGIN
                        IF content.slaif_agent_page_effective_route(candidate.id)=p_route
                        THEN
                            CONTINUE;
                        END IF;
                    EXCEPTION WHEN SQLSTATE 'P0002' THEN
                        -- A concurrent COW tombstone is not a live alternate
                        -- route and must not escape as top-level PAGE_NOT_FOUND.
                        CONTINUE;
                    END;
                END LOOP;
                IF EXISTS (
                    SELECT 1 FROM content.redirect alternate
                    WHERE alternate.site_id=p_site_id
                      AND alternate.source_route=p_route
                      AND (
                        (incoming.locale IS NOT NULL AND
                         (alternate.locale=incoming.locale OR alternate.locale IS NULL))
                        OR (incoming.locale IS NULL AND alternate.locale IS NULL)
                      )
                ) THEN
                    CONTINUE;
                END IF;
                RETURN true;
            END LOOP;
            RETURN false;
        END; $fn$
        """
    )
    for function in ("content.slaif_redirect_page_target_dependency(uuid,text,uuid)",):
        op.execute(f"ALTER FUNCTION {function} OWNER TO slaif_owner")
        op.execute(f"REVOKE ALL ON FUNCTION {function} FROM PUBLIC")


def downgrade() -> None:
    # 051's implementation is recreated by the preceding immutable migration
    # only on a full fresh downgrade path; keep the function owner restricted.
    op.execute(
        "DROP FUNCTION IF EXISTS content.slaif_redirect_page_target_dependency(uuid,text,uuid)"
    )
