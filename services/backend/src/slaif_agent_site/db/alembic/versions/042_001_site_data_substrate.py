# ruff: noqa: E501
"""Add fixed, site-confined locales, navigation items, redirects, and proposals."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "042_001"
down_revision: str | Sequence[str] | None = "041_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE content.navigation ADD CONSTRAINT uq_navigation_site_id UNIQUE (site_id,id)"
    )
    op.execute(
        "ALTER TABLE content.page ADD CONSTRAINT uq_page_site_id UNIQUE (site_id,id)"
    )
    op.execute(
        """
        CREATE TABLE content.site_locale (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(), site_id uuid NOT NULL,
          tag text NOT NULL, enabled boolean NOT NULL DEFAULT true,
          is_default boolean NOT NULL DEFAULT false, position integer NOT NULL DEFAULT 0,
          metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
          row_version integer NOT NULL DEFAULT 1,
          created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
          CONSTRAINT site_locale_site_fk FOREIGN KEY (site_id) REFERENCES control.site(id),
          CONSTRAINT site_locale_tag_bounded CHECK (tag ~ '^[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?(-[A-Za-z0-9]{5,8})*$'),
          CONSTRAINT site_locale_position_bounded CHECK (position BETWEEN 0 AND 999),
          CONSTRAINT site_locale_metadata_bounded CHECK (jsonb_typeof(metadata)='object' AND octet_length(metadata::text)<=16384),
          CONSTRAINT site_locale_tag_unique UNIQUE (site_id,tag)
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX site_locale_one_default ON content.site_locale(site_id) WHERE is_default"
    )
    op.execute(
        """
        CREATE TABLE content.navigation_item (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(), site_id uuid NOT NULL,
          navigation_id uuid NOT NULL, parent_id uuid, page_id uuid,
          target_kind text NOT NULL, target_value text NOT NULL,
          labels jsonb NOT NULL DEFAULT '{}'::jsonb, locale text,
          position integer NOT NULL DEFAULT 0, row_version integer NOT NULL DEFAULT 1,
          created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
          CONSTRAINT navigation_item_site_id_unique UNIQUE (site_id,id),
          CONSTRAINT navigation_item_site_fk FOREIGN KEY (site_id,navigation_id) REFERENCES content.navigation(site_id,id) DEFERRABLE INITIALLY IMMEDIATE,
          CONSTRAINT navigation_item_parent_fk FOREIGN KEY (site_id,parent_id) REFERENCES content.navigation_item(site_id,id) DEFERRABLE INITIALLY IMMEDIATE,
          CONSTRAINT navigation_item_page_fk FOREIGN KEY (site_id,page_id) REFERENCES content.page(site_id,id) DEFERRABLE INITIALLY IMMEDIATE,
          CONSTRAINT navigation_item_kind CHECK (target_kind IN ('PAGE','INTERNAL','EXTERNAL')),
          CONSTRAINT navigation_item_target_bounded CHECK (octet_length(target_value)<=2048 AND target_value !~ '[[:cntrl:]]'),
          CONSTRAINT navigation_item_labels_bounded CHECK (jsonb_typeof(labels)='object' AND octet_length(labels::text)<=16384),
          CONSTRAINT navigation_item_position_bounded CHECK (position BETWEEN 0 AND 999)
        )
        """
    )
    op.execute(
        "CREATE INDEX navigation_item_tree_order ON content.navigation_item(site_id,navigation_id,parent_id,position,id)"
    )
    op.execute(
        r"""
        CREATE TABLE content.redirect (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(), site_id uuid NOT NULL,
          source_route text NOT NULL, target text NOT NULL,
          status_code integer NOT NULL DEFAULT 302, locale text,
          row_version integer NOT NULL DEFAULT 1,
          created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
          CONSTRAINT redirect_site_fk FOREIGN KEY (site_id) REFERENCES control.site(id),
          CONSTRAINT redirect_source_bounded CHECK (source_route ~ '^/[A-Za-z0-9._~/-]*$' AND source_route !~ '//|\.\.|%|\\'),
          CONSTRAINT redirect_target_bounded CHECK (octet_length(target)<=2048 AND target !~ '[[:cntrl:]]'),
          CONSTRAINT redirect_status CHECK (status_code BETWEEN 301 AND 308)
        )
        """
    )
    op.execute(
        "CREATE UNIQUE INDEX redirect_site_source_locale ON content.redirect(site_id,source_route,coalesce(locale,''))"
    )
    op.execute(
        """
        CREATE TABLE content.proposed_side_effect (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(), site_id uuid NOT NULL,
          workspace_id uuid NOT NULL, kind text NOT NULL, payload jsonb NOT NULL,
          state text NOT NULL DEFAULT 'PROPOSED', created_at timestamptz NOT NULL DEFAULT now(),
          updated_at timestamptz NOT NULL DEFAULT now(),
          CONSTRAINT proposed_effect_site_fk FOREIGN KEY (site_id) REFERENCES control.site(id),
          CONSTRAINT proposed_effect_kind CHECK (kind IN ('analytics_event','cache_purge')),
          CONSTRAINT proposed_effect_payload CHECK (jsonb_typeof(payload)='object' AND octet_length(payload::text)<=16384),
          CONSTRAINT proposed_effect_state CHECK (state='PROPOSED')
        )
        """
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_locale_create(p_site_id uuid,p_tag text,p_enabled boolean,p_default boolean,p_position integer,p_metadata jsonb)
        RETURNS SETOF content.site_locale LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
        BEGIN
          IF p_tag !~ '^[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?(-[A-Za-z0-9]{5,8})*$' OR p_position NOT BETWEEN 0 AND 999 OR jsonb_typeof(p_metadata)<>'object' THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF;
          IF p_default THEN UPDATE content.site_locale SET is_default=false WHERE site_id=p_site_id; END IF;
          INSERT INTO content.site_locale(site_id,tag,enabled,is_default,position,metadata) VALUES(p_site_id,p_tag,p_enabled,p_default,p_position,p_metadata);
          RETURN QUERY SELECT l.* FROM content.site_locale l WHERE l.site_id=p_site_id AND l.tag=p_tag;
        END $$
        """
    )
    op.execute(
        """CREATE FUNCTION content.slaif_locale_list(p_site_id uuid) RETURNS SETOF content.site_locale LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT l.* FROM content.site_locale l WHERE l.site_id=p_site_id ORDER BY l.position,l.tag COLLATE "C" $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_locale_get(p_site_id uuid,p_id uuid) RETURNS SETOF content.site_locale LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT l.* FROM content.site_locale l WHERE l.site_id=p_site_id AND l.id=p_id $$"""
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_locale_update(p_site_id uuid,p_id uuid,p_tag text,p_enabled boolean,p_default boolean,p_position integer,p_metadata jsonb,p_expected integer)
        RETURNS SETOF content.site_locale LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ DECLARE old content.site_locale;
        BEGIN SELECT l.* INTO old FROM content.site_locale l WHERE l.site_id=p_site_id AND l.id=p_id FOR UPDATE; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF; IF p_tag IS NOT NULL AND p_tag !~ '^[A-Za-z]{2,3}(-[A-Za-z]{4})?(-([A-Za-z]{2}|[0-9]{3}))?(-[A-Za-z0-9]{5,8})*$' OR coalesce(p_position,old.position) NOT BETWEEN 0 AND 999 THEN RAISE EXCEPTION 'LOCALE_INVALID' USING ERRCODE='P0003'; END IF; IF p_default THEN UPDATE content.site_locale SET is_default=false WHERE site_id=p_site_id AND id<>p_id; END IF; UPDATE content.site_locale SET tag=coalesce(p_tag,tag),enabled=coalesce(p_enabled,enabled),is_default=coalesce(p_default,is_default),position=coalesce(p_position,position),metadata=coalesce(p_metadata,metadata),row_version=row_version+1,updated_at=now() WHERE site_id=p_site_id AND id=p_id; RETURN QUERY SELECT l.* FROM content.site_locale l WHERE l.site_id=p_site_id AND l.id=p_id; END $$
        """
    )
    op.execute(
        """CREATE FUNCTION content.slaif_locale_delete(p_site_id uuid,p_id uuid,p_expected integer) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ DECLARE old content.site_locale; BEGIN SELECT l.* INTO old FROM content.site_locale l WHERE l.site_id=p_site_id AND l.id=p_id FOR UPDATE; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF; IF old.is_default OR EXISTS(SELECT 1 FROM content.page p WHERE p.site_id=p_site_id AND p.locale=old.tag) OR EXISTS(SELECT 1 FROM content.navigation_item n WHERE n.site_id=p_site_id AND n.locale=old.tag) OR EXISTS(SELECT 1 FROM content.redirect r WHERE r.site_id=p_site_id AND r.locale=old.tag) THEN RAISE EXCEPTION 'LOCALE_REFERENCED' USING ERRCODE='P0003'; END IF; DELETE FROM content.site_locale WHERE site_id=p_site_id AND id=p_id; END $$"""
    )
    op.execute(
        """
        CREATE FUNCTION content.slaif_navigation_item_create(p_site_id uuid,p_navigation_id uuid,p_parent_id uuid,p_page_id uuid,p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,p_position integer)
        RETURNS SETOF content.navigation_item LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ DECLARE nav_site uuid; parent_nav uuid; BEGIN SELECT n.site_id INTO nav_site FROM content.navigation n WHERE n.id=p_navigation_id AND n.site_id=p_site_id; IF nav_site IS NULL THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; IF p_parent_id IS NOT NULL THEN SELECT n.navigation_id INTO parent_nav FROM content.navigation_item n WHERE n.id=p_parent_id AND n.site_id=p_site_id; IF parent_nav IS NULL OR parent_nav<>p_navigation_id THEN RAISE EXCEPTION 'NAVIGATION_PARENT_INVALID' USING ERRCODE='P0003'; END IF; END IF; IF p_page_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM content.page p WHERE p.id=p_page_id AND p.site_id=p_site_id) THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF; IF p_target_kind NOT IN ('PAGE','INTERNAL','EXTERNAL') OR p_position NOT BETWEEN 0 AND 999 OR jsonb_typeof(p_labels)<>'object' THEN RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003'; END IF; INSERT INTO content.navigation_item(site_id,navigation_id,parent_id,page_id,target_kind,target_value,labels,locale,position) VALUES(p_site_id,p_navigation_id,p_parent_id,p_page_id,p_target_kind,p_target_value,p_labels,p_locale,p_position); RETURN QUERY SELECT i.* FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.navigation_id=p_navigation_id AND i.id=currval('content.navigation_item_id_seq')::uuid; END $$
        """
    )
    # UUID keys have no sequence; replace the create function's final lookup
    # with a deterministic latest-row lookup in a corrected definition below.
    op.execute(
        "DROP FUNCTION content.slaif_navigation_item_create(uuid,uuid,uuid,uuid,text,text,jsonb,text,integer)"
    )
    op.execute(
        """CREATE FUNCTION content.slaif_navigation_item_create(p_site_id uuid,p_navigation_id uuid,p_parent_id uuid,p_page_id uuid,p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,p_position integer) RETURNS SETOF content.navigation_item LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ DECLARE created uuid; parent_nav uuid; BEGIN IF NOT EXISTS(SELECT 1 FROM content.navigation n WHERE n.id=p_navigation_id AND n.site_id=p_site_id) THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; IF p_parent_id IS NOT NULL THEN SELECT n.navigation_id INTO parent_nav FROM content.navigation_item n WHERE n.id=p_parent_id AND n.site_id=p_site_id; IF parent_nav IS NULL OR parent_nav<>p_navigation_id THEN RAISE EXCEPTION 'NAVIGATION_PARENT_INVALID' USING ERRCODE='P0003'; END IF; END IF; IF p_page_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM content.page p WHERE p.id=p_page_id AND p.site_id=p_site_id) THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF; IF p_target_kind NOT IN ('PAGE','INTERNAL','EXTERNAL') OR p_position NOT BETWEEN 0 AND 999 OR jsonb_typeof(p_labels)<>'object' THEN RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003'; END IF; INSERT INTO content.navigation_item(site_id,navigation_id,parent_id,page_id,target_kind,target_value,labels,locale,position) VALUES(p_site_id,p_navigation_id,p_parent_id,p_page_id,p_target_kind,p_target_value,p_labels,p_locale,p_position) RETURNING id INTO created; RETURN QUERY SELECT i.* FROM content.navigation_item i WHERE i.id=created AND i.site_id=p_site_id; END $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_navigation_item_list(p_site_id uuid,p_navigation_id uuid) RETURNS SETOF content.navigation_item LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT i.* FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.navigation_id=p_navigation_id ORDER BY i.position,i.id $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_navigation_item_get(p_site_id uuid,p_id uuid) RETURNS SETOF content.navigation_item LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT i.* FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.id=p_id $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_navigation_item_update(p_site_id uuid,p_id uuid,p_parent_id uuid,p_page_id uuid,p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,p_position integer,p_expected integer) RETURNS SETOF content.navigation_item LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ DECLARE old content.navigation_item; parent_nav uuid; BEGIN SELECT i.* INTO old FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.id=p_id FOR UPDATE; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF; IF p_parent_id IS NOT NULL THEN SELECT i.navigation_id INTO parent_nav FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.id=p_parent_id; IF parent_nav IS NULL OR parent_nav<>old.navigation_id OR p_parent_id=p_id THEN RAISE EXCEPTION 'NAVIGATION_PARENT_INVALID' USING ERRCODE='P0003'; END IF; END IF; IF p_page_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM content.page p WHERE p.site_id=p_site_id AND p.id=p_page_id) THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF; UPDATE content.navigation_item SET parent_id=p_parent_id,page_id=coalesce(p_page_id,page_id),target_kind=coalesce(p_target_kind,target_kind),target_value=coalesce(p_target_value,target_value),labels=coalesce(p_labels,labels),locale=p_locale,position=coalesce(p_position,position),row_version=row_version+1,updated_at=now() WHERE site_id=p_site_id AND id=p_id; RETURN QUERY SELECT i.* FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.id=p_id; END $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_navigation_item_delete(p_site_id uuid,p_id uuid,p_expected integer) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN IF EXISTS(SELECT 1 FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.id=p_id AND i.row_version<>p_expected) THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF; IF EXISTS(SELECT 1 FROM content.navigation_item i WHERE i.site_id=p_site_id AND i.id=p_id AND EXISTS(SELECT 1 FROM content.navigation_item c WHERE c.site_id=p_site_id AND c.parent_id=i.id)) THEN RAISE EXCEPTION 'NAVIGATION_CHILDREN' USING ERRCODE='P0003'; END IF; DELETE FROM content.navigation_item WHERE site_id=p_site_id AND id=p_id AND row_version=p_expected; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; END $$"""
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION content.slaif_navigation_item_create(
          p_site_id uuid,p_navigation_id uuid,p_parent_id uuid,p_page_id uuid,
          p_target_kind text,p_target_value text,p_labels jsonb,p_locale text,p_position integer
        ) RETURNS SETOF content.navigation_item LANGUAGE plpgsql SECURITY DEFINER
        SET search_path=pg_catalog AS $$ DECLARE created uuid; parent_nav uuid;
        BEGIN
          IF NOT EXISTS(SELECT 1 FROM content.navigation n WHERE n.id=p_navigation_id AND n.site_id=p_site_id) THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF;
          IF p_parent_id IS NOT NULL THEN SELECT n.navigation_id INTO parent_nav FROM content.navigation_item n WHERE n.id=p_parent_id AND n.site_id=p_site_id; IF parent_nav IS NULL OR parent_nav<>p_navigation_id THEN RAISE EXCEPTION 'NAVIGATION_PARENT_INVALID' USING ERRCODE='P0003'; END IF; END IF;
          IF p_page_id IS NOT NULL AND NOT EXISTS(SELECT 1 FROM content.page p WHERE p.site_id=p_site_id AND p.id=p_page_id) THEN RAISE EXCEPTION 'NAVIGATION_PAGE_INVALID' USING ERRCODE='P0003'; END IF;
          IF p_target_kind NOT IN ('PAGE','INTERNAL','EXTERNAL') OR p_position NOT BETWEEN 0 AND 999 OR jsonb_typeof(p_labels)<>'object' THEN RAISE EXCEPTION 'NAVIGATION_INVALID' USING ERRCODE='P0003'; END IF;
          INSERT INTO content.navigation_item(site_id,navigation_id,parent_id,page_id,target_kind,target_value,labels,locale,position) VALUES(p_site_id,p_navigation_id,p_parent_id,p_page_id,p_target_kind,p_target_value,p_labels,p_locale,p_position) RETURNING id INTO created;
          RETURN QUERY SELECT n.* FROM content.navigation_item n WHERE n.id=created AND n.site_id=p_site_id;
        END $$
        """
    )
    op.execute(
        r"""CREATE FUNCTION content.slaif_redirect_create(p_site_id uuid,p_source text,p_target text,p_status integer,p_locale text) RETURNS SETOF content.redirect LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ DECLARE created uuid; BEGIN IF p_source !~ '^/[A-Za-z0-9._~/-]*$' OR p_source ~ '//|\.\.|%|\\' OR p_source=p_target OR p_status NOT BETWEEN 301 AND 308 OR p_target ~ '[[:cntrl:] ]' OR (p_target !~ '^/' AND p_target !~ '^https?://[^/@?#]+([/?#].*)?$') THEN RAISE EXCEPTION 'REDIRECT_INVALID' USING ERRCODE='P0003'; END IF; IF p_target ~ '^/' AND p_target ~ '^/(api|admin|agent|control|editor|health|internal|login|logout|mcp|media|preview|setup|_next|static)(/|$)' THEN RAISE EXCEPTION 'REDIRECT_RESERVED' USING ERRCODE='P0003'; END IF; INSERT INTO content.redirect(site_id,source_route,target,status_code,locale) VALUES(p_site_id,p_source,p_target,p_status,p_locale) RETURNING id INTO created; RETURN QUERY SELECT r.* FROM content.redirect r WHERE r.id=created; END $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_redirect_list(p_site_id uuid) RETURNS SETOF content.redirect LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT r.* FROM content.redirect r WHERE r.site_id=p_site_id ORDER BY r.source_route COLLATE "C",coalesce(r.locale,'') $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_redirect_get(p_site_id uuid,p_id uuid) RETURNS SETOF content.redirect LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT r.* FROM content.redirect r WHERE r.site_id=p_site_id AND r.id=p_id $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_redirect_update(p_site_id uuid,p_id uuid,p_source text,p_target text,p_status integer,p_locale text,p_expected integer) RETURNS SETOF content.redirect LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ DECLARE old content.redirect; BEGIN SELECT r.* INTO old FROM content.redirect r WHERE r.site_id=p_site_id AND r.id=p_id FOR UPDATE; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; IF old.row_version<>p_expected THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; END IF; UPDATE content.redirect SET source_route=coalesce(p_source,source_route),target=coalesce(p_target,target),status_code=coalesce(p_status,status_code),locale=p_locale,row_version=row_version+1,updated_at=now() WHERE site_id=p_site_id AND id=p_id; RETURN QUERY SELECT r.* FROM content.redirect r WHERE r.site_id=p_site_id AND r.id=p_id; END $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_redirect_delete(p_site_id uuid,p_id uuid,p_expected integer) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN DELETE FROM content.redirect WHERE site_id=p_site_id AND id=p_id AND row_version=p_expected; IF NOT FOUND THEN IF EXISTS(SELECT 1 FROM content.redirect WHERE site_id=p_site_id AND id=p_id) THEN RAISE EXCEPTION 'ROW_VERSION_MISMATCH' USING ERRCODE='P0004'; ELSE RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; END IF; END $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_proposed_side_effect_create(p_site_id uuid,p_workspace_id uuid,p_kind text,p_payload jsonb) RETURNS SETOF content.proposed_side_effect LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ DECLARE created uuid; BEGIN IF p_kind NOT IN ('analytics_event','cache_purge') OR jsonb_typeof(p_payload)<>'object' OR octet_length(p_payload::text)>16384 OR NOT EXISTS(SELECT 1 FROM control.workspace w WHERE w.id=p_workspace_id AND w.site_id=p_site_id) THEN RAISE EXCEPTION 'SIDE_EFFECT_INVALID' USING ERRCODE='P0003'; END IF; INSERT INTO content.proposed_side_effect(site_id,workspace_id,kind,payload) VALUES(p_site_id,p_workspace_id,p_kind,p_payload) RETURNING id INTO created; RETURN QUERY SELECT s.* FROM content.proposed_side_effect s WHERE s.id=created; END $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_proposed_side_effect_list(p_site_id uuid,p_workspace_id uuid) RETURNS SETOF content.proposed_side_effect LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT s.* FROM content.proposed_side_effect s WHERE s.site_id=p_site_id AND s.workspace_id=p_workspace_id ORDER BY s.created_at,s.id $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_navigation_item_parent_guard() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ DECLARE found_id uuid; found_depth integer; BEGIN IF NEW.parent_id IS NULL THEN RETURN NEW; END IF; WITH RECURSIVE ancestors(id,depth) AS (SELECT NEW.parent_id,1 UNION ALL SELECT i.parent_id,a.depth+1 FROM content.navigation_item i JOIN ancestors a ON i.id=a.id WHERE i.parent_id IS NOT NULL AND a.depth<10) SELECT id,depth INTO found_id,found_depth FROM ancestors WHERE id=NEW.id OR depth>8 LIMIT 1; IF found_id=NEW.id OR found_depth>8 THEN RAISE EXCEPTION 'NAVIGATION_CYCLE_OR_DEPTH' USING ERRCODE='P0003'; END IF; RETURN NEW; END $$"""
    )
    op.execute(
        """CREATE TRIGGER navigation_item_parent_guard BEFORE INSERT OR UPDATE OF parent_id ON content.navigation_item FOR EACH ROW EXECUTE FUNCTION content.slaif_navigation_item_parent_guard()"""
    )
    op.execute(
        """DO $$ DECLARE fn text; sig text; BEGIN FOREACH fn IN ARRAY ARRAY['slaif_locale_create','slaif_locale_list','slaif_locale_get','slaif_locale_update','slaif_locale_delete','slaif_navigation_item_create','slaif_navigation_item_list','slaif_navigation_item_get','slaif_navigation_item_update','slaif_navigation_item_delete','slaif_navigation_item_parent_guard','slaif_redirect_create','slaif_redirect_list','slaif_redirect_get','slaif_redirect_update','slaif_redirect_delete','slaif_proposed_side_effect_create','slaif_proposed_side_effect_list'] LOOP SELECT pg_get_function_identity_arguments(p.oid) INTO sig FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='content' AND p.proname=fn LIMIT 1; IF sig IS NOT NULL THEN EXECUTE format('REVOKE ALL ON FUNCTION content.%I(%s) FROM PUBLIC',fn,sig); EXECUTE format('GRANT EXECUTE ON FUNCTION content.%I(%s) TO slaif_editor_runtime,slaif_control',fn,sig); END IF; END LOOP; END $$"""
    )
    op.execute(
        """CREATE OR REPLACE FUNCTION content.slaif_navigation_create(p_site_id uuid,p_key text,p_label text,p_settings jsonb) RETURNS TABLE(id uuid,site_id uuid,"key" text,label text,settings jsonb,created_at timestamptz,updated_at timestamptz) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN INSERT INTO content.navigation(site_id,"key",label,settings) VALUES(p_site_id,p_key,p_label,p_settings); RETURN QUERY SELECT n.* FROM content.navigation n WHERE n.site_id=p_site_id AND n."key"=p_key LIMIT 1; END $$"""
    )
    op.execute(
        """CREATE OR REPLACE FUNCTION content.slaif_navigation_list(p_site_id uuid) RETURNS TABLE(id uuid,site_id uuid,"key" text,label text,settings jsonb,created_at timestamptz,updated_at timestamptz) LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT n.* FROM content.navigation n WHERE n.site_id=p_site_id ORDER BY n."key" COLLATE "C" $$"""
    )
    op.execute(
        """CREATE OR REPLACE FUNCTION content.slaif_navigation_get(p_nav_id uuid) RETURNS TABLE(id uuid,site_id uuid,"key" text,label text,settings jsonb,created_at timestamptz,updated_at timestamptz) LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT n.* FROM content.navigation n WHERE n.id=p_nav_id $$"""
    )
    op.execute(
        """CREATE OR REPLACE FUNCTION content.slaif_navigation_update(p_nav_id uuid,p_label text,p_settings jsonb) RETURNS TABLE(id uuid,site_id uuid,"key" text,label text,settings jsonb,created_at timestamptz,updated_at timestamptz) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN UPDATE content.navigation n SET label=coalesce(p_label,n.label),settings=coalesce(p_settings,n.settings),updated_at=now() WHERE n.id=p_nav_id; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; RETURN QUERY SELECT n.* FROM content.navigation n WHERE n.id=p_nav_id; END $$"""
    )


def downgrade() -> None:
    op.execute(
        """DO $$ DECLARE n text; BEGIN IF pg_catalog.to_regprocedure('agentcow.teardown_cow(text,text)') IS NOT NULL THEN FOREACH n IN ARRAY ARRAY['proposed_side_effect','redirect','navigation_item','site_locale','page_composition','page','navigation'] LOOP IF EXISTS(SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace s ON s.oid=c.relnamespace WHERE s.nspname='content' AND c.relname=n AND c.relkind='v') THEN EXECUTE format('SELECT agentcow.teardown_cow(%L,%L)','content',n); IF EXISTS(SELECT 1 FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace s ON s.oid=c.relnamespace WHERE s.nspname='content' AND c.relname=n||'_base' AND c.relkind='r') THEN EXECUTE format('ALTER TABLE content.%I RENAME TO %I',n||'_base',n); END IF; END IF; END LOOP; END IF; END $$"""
    )
    op.execute(
        """DO $$ DECLARE f record; BEGIN FOR f IN SELECT p.proname,pg_get_function_identity_arguments(p.oid) AS args FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='content' AND (p.proname LIKE 'slaif_locale_%' OR p.proname LIKE 'slaif_navigation_item_%' OR p.proname LIKE 'slaif_redirect_%' OR p.proname LIKE 'slaif_proposed_side_effect_%') LOOP EXECUTE format('DROP FUNCTION IF EXISTS content.%I(%s) CASCADE',f.proname,f.args); END LOOP; END $$"""
    )
    for table in ("proposed_side_effect", "redirect", "navigation_item", "site_locale"):
        op.execute(f"DROP TABLE IF EXISTS content.{table} CASCADE")
    op.execute("ALTER TABLE content.page DROP CONSTRAINT IF EXISTS uq_page_site_id")
    op.execute(
        "ALTER TABLE content.navigation DROP CONSTRAINT IF EXISTS uq_navigation_site_id"
    )
