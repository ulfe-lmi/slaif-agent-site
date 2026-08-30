# ruff: noqa: E501
"""Version and confine collection-view query contracts."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "041_001"
down_revision: str | Sequence[str] | None = "040_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE content.collection_view ADD COLUMN definition_version integer NOT NULL DEFAULT 1"
    )
    op.execute(
        "ALTER TABLE content.collection_view ADD COLUMN row_version integer NOT NULL DEFAULT 1"
    )
    op.execute(
        "ALTER TABLE content.collection_view ADD CONSTRAINT uq_collection_view_site_id UNIQUE (site_id,id)"
    )
    op.execute(
        "ALTER TABLE content.collection_view ADD CONSTRAINT collection_view_site_type_fk FOREIGN KEY (site_id,type_id) REFERENCES content.content_type(site_id,id) DEFERRABLE INITIALLY IMMEDIATE"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_collection_view_site_type_key ON content.collection_view(site_id,type_id,key)"
    )
    op.execute("""
      CREATE FUNCTION content.slaif_collection_view_v2_create(p_site_id uuid,p_type_id uuid,p_key text,p_filter jsonb,p_sort jsonb,p_projection jsonb,p_pagination jsonb,p_definition_version integer) RETURNS TABLE(id uuid,site_id uuid,type_id uuid,key text,filter_spec jsonb,sort_spec jsonb,projection_spec jsonb,pagination_spec jsonb,created_at timestamptz,updated_at timestamptz,definition_version integer,row_version integer) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN IF NOT EXISTS (SELECT 1 FROM content.content_type t WHERE t.id=p_type_id AND t.site_id=p_site_id AND t.status <> 'DELETED' AND t.definition_version=p_definition_version) THEN RAISE EXCEPTION 'COLLECTION_TYPE_VERSION_INVALID' USING ERRCODE='P0003'; END IF; INSERT INTO content.collection_view(site_id,type_id,key,filter_spec,sort_spec,projection_spec,pagination_spec,definition_version) VALUES(p_site_id,p_type_id,p_key,p_filter,p_sort,p_projection,p_pagination,p_definition_version); RETURN QUERY SELECT v.id,v.site_id,v.type_id,v.key,v.filter_spec,v.sort_spec,v.projection_spec,v.pagination_spec,v.created_at,v.updated_at,v.definition_version,v.row_version FROM content.collection_view v WHERE v.site_id=p_site_id AND v.type_id=p_type_id AND v.key=p_key ORDER BY v.created_at DESC LIMIT 1; END $$""")
    op.execute(
        """CREATE FUNCTION content.slaif_collection_view_v2_list(p_site_id uuid,p_type_id uuid) RETURNS SETOF content.collection_view LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT v.* FROM content.collection_view v WHERE v.site_id=p_site_id AND v.type_id=p_type_id ORDER BY v.key COLLATE \"C\",v.id $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_collection_view_v2_get(p_site_id uuid,p_view_id uuid) RETURNS SETOF content.collection_view LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT v.* FROM content.collection_view v WHERE v.site_id=p_site_id AND v.id=p_view_id $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_collection_view_v2_update(p_site_id uuid,p_view_id uuid,p_filter jsonb,p_sort jsonb,p_projection jsonb,p_pagination jsonb,p_expected integer) RETURNS SETOF content.collection_view LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ DECLARE old content.collection_view; BEGIN SELECT v.* INTO old FROM content.collection_view v WHERE v.site_id=p_site_id AND v.id=p_view_id FOR UPDATE; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; IF old.row_version <> p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF; UPDATE content.collection_view SET filter_spec=coalesce(p_filter,filter_spec),sort_spec=coalesce(p_sort,sort_spec),projection_spec=coalesce(p_projection,projection_spec),pagination_spec=coalesce(p_pagination,pagination_spec),row_version=row_version+1,updated_at=now() WHERE site_id=p_site_id AND id=p_view_id; RETURN QUERY SELECT v.* FROM content.collection_view v WHERE v.site_id=p_site_id AND v.id=p_view_id; END $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_collection_view_v2_delete(p_site_id uuid,p_view_id uuid,p_expected integer) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN DELETE FROM content.collection_view WHERE site_id=p_site_id AND id=p_view_id AND row_version=p_expected; IF NOT FOUND THEN IF EXISTS (SELECT 1 FROM content.collection_view v WHERE v.site_id=p_site_id AND v.id=p_view_id) THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; ELSE RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; END IF; END $$"""
    )
    op.execute(
        """GRANT EXECUTE ON FUNCTION content.slaif_collection_view_v2_create(uuid,uuid,text,jsonb,jsonb,jsonb,jsonb,integer),content.slaif_collection_view_v2_list(uuid,uuid),content.slaif_collection_view_v2_get(uuid,uuid),content.slaif_collection_view_v2_update(uuid,uuid,jsonb,jsonb,jsonb,jsonb,integer),content.slaif_collection_view_v2_delete(uuid,uuid,integer) TO slaif_editor_runtime,slaif_control"""
    )


def downgrade() -> None:
    op.execute(
        """DO $$ DECLARE n text; BEGIN IF pg_catalog.to_regprocedure('agentcow.teardown_cow(text,text)') IS NOT NULL THEN FOREACH n IN ARRAY ARRAY['collection_view','content_type'] LOOP IF EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace s ON s.oid=c.relnamespace WHERE s.nspname='content' AND c.relname=n AND c.relkind='v') THEN EXECUTE format('SELECT agentcow.teardown_cow(%L,%L)','content',n); IF EXISTS (SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace s ON s.oid=c.relnamespace WHERE s.nspname='content' AND c.relname=n||'_base' AND c.relkind='r') THEN EXECUTE format('ALTER TABLE content.%I RENAME TO %I',n||'_base',n); END IF; END IF; END LOOP; END IF; END $$"""
    )
    for name, signature in (
        (
            "slaif_collection_view_v2_create",
            "uuid,uuid,text,jsonb,jsonb,jsonb,jsonb,integer",
        ),
        ("slaif_collection_view_v2_list", "uuid,uuid"),
        ("slaif_collection_view_v2_get", "uuid,uuid"),
        (
            "slaif_collection_view_v2_update",
            "uuid,uuid,jsonb,jsonb,jsonb,jsonb,integer",
        ),
        ("slaif_collection_view_v2_delete", "uuid,uuid,integer"),
    ):
        op.execute(f"DROP FUNCTION IF EXISTS content.{name}({signature}) CASCADE")
    op.execute("DROP INDEX IF EXISTS content.uq_collection_view_site_type_key")
    op.execute(
        "ALTER TABLE content.collection_view DROP CONSTRAINT IF EXISTS collection_view_site_type_fk"
    )
    op.execute(
        "ALTER TABLE content.collection_view DROP CONSTRAINT IF EXISTS uq_collection_view_site_id"
    )
    op.execute("ALTER TABLE content.collection_view DROP COLUMN IF EXISTS row_version")
    op.execute(
        "ALTER TABLE content.collection_view DROP COLUMN IF EXISTS definition_version"
    )
