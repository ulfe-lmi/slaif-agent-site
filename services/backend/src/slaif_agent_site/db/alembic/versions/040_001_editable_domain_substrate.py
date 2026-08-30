# ruff: noqa: E501
"""Add site-confined translations, normalized relations, and field tenancy."""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "040_001"
down_revision: str | Sequence[str] | None = "039_001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _drop_field_functions() -> None:
    for signature in (
        "uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb",
        "uuid",
        "uuid",
        "uuid,text,boolean,boolean,integer,integer,jsonb,jsonb",
    ):
        for name in (
            "slaif_field_definition_create",
            "slaif_field_definition_list",
            "slaif_field_definition_get",
            "slaif_field_definition_update",
        ):
            op.execute(f"DROP FUNCTION IF EXISTS content.{name}({signature}) CASCADE")
    op.execute(
        "DROP FUNCTION IF EXISTS content.slaif_field_definition_delete(uuid) CASCADE"
    )


def upgrade() -> None:
    _drop_field_functions()
    op.execute(
        "ALTER TABLE content.content_type ADD CONSTRAINT uq_content_type_site_id UNIQUE (site_id,id)"
    )
    op.execute(
        "ALTER TABLE content.content_item ADD CONSTRAINT uq_content_item_site_id UNIQUE (site_id,id)"
    )
    op.execute("ALTER TABLE content.field_definition ADD COLUMN site_id uuid")
    op.execute(
        "UPDATE content.field_definition f SET site_id=t.site_id FROM content.content_type t WHERE t.id=f.type_id"
    )
    op.execute(
        "DO $$ BEGIN IF EXISTS (SELECT 1 FROM content.field_definition WHERE site_id IS NULL) THEN RAISE EXCEPTION 'FIELD_DEFINITION_SITE_INCONSISTENT' USING ERRCODE='P0001'; END IF; END $$"
    )
    op.execute("ALTER TABLE content.field_definition ALTER COLUMN site_id SET NOT NULL")
    op.execute(
        "ALTER TABLE content.field_definition ADD CONSTRAINT field_definition_site_type_fk FOREIGN KEY (site_id,type_id) REFERENCES content.content_type(site_id,id) DEFERRABLE INITIALLY IMMEDIATE"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_field_definition_site_type_key ON content.field_definition(site_id,type_id,key)"
    )
    op.execute(
        "ALTER TABLE content.field_definition ADD CONSTRAINT uq_field_definition_site_id UNIQUE (site_id,id)"
    )
    op.execute("""
        CREATE OR REPLACE FUNCTION content.slaif_immutable_site_id() RETURNS trigger
        LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$
        BEGIN
          IF TG_OP='INSERT' AND NEW.site_id IS NULL THEN
            SELECT site_id INTO NEW.site_id FROM content.content_type WHERE id=NEW.type_id;
          END IF;
          IF TG_OP='UPDATE' AND NEW.site_id IS DISTINCT FROM OLD.site_id THEN
            RAISE EXCEPTION 'SITE_ID_IMMUTABLE' USING ERRCODE='P0003'; END IF; RETURN NEW; END $$
    """)
    op.execute(
        "CREATE TRIGGER field_definition_site_immutable BEFORE INSERT OR UPDATE ON content.field_definition FOR EACH ROW EXECUTE FUNCTION content.slaif_immutable_site_id()"
    )

    op.execute("""
        CREATE TABLE content.content_item_translation (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(), site_id uuid NOT NULL,
          item_id uuid NOT NULL, locale text NOT NULL,
          localized_values jsonb NOT NULL DEFAULT '{}'::jsonb,
          row_version integer NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
          CONSTRAINT translation_locale_bounded CHECK (locale ~ '^[A-Za-z]{2,8}(-[A-Za-z0-9]{1,8}){0,3}$'),
          CONSTRAINT translation_values_object CHECK (jsonb_typeof(localized_values)='object' AND octet_length(localized_values::text)<=65536),
          CONSTRAINT translation_site_item_fk FOREIGN KEY (site_id,item_id) REFERENCES content.content_item(site_id,id) DEFERRABLE INITIALLY IMMEDIATE,
          CONSTRAINT translation_item_locale_unique UNIQUE (site_id,item_id,locale)
        )
    """)
    op.execute("""
        CREATE TABLE content.item_relation (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(), site_id uuid NOT NULL,
          source_item_id uuid NOT NULL, field_definition_id uuid NOT NULL, target_item_id uuid NOT NULL,
          position integer NOT NULL DEFAULT 0, metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
          row_version integer NOT NULL DEFAULT 1, created_at timestamptz NOT NULL DEFAULT now(), updated_at timestamptz NOT NULL DEFAULT now(),
          CONSTRAINT relation_position_bounded CHECK (position BETWEEN 0 AND 999),
          CONSTRAINT relation_metadata_bounded CHECK (jsonb_typeof(metadata)='object' AND octet_length(metadata::text)<=16384),
          CONSTRAINT relation_source_fk FOREIGN KEY (site_id,source_item_id) REFERENCES content.content_item(site_id,id) DEFERRABLE INITIALLY IMMEDIATE,
          CONSTRAINT relation_target_fk FOREIGN KEY (site_id,target_item_id) REFERENCES content.content_item(site_id,id) DEFERRABLE INITIALLY IMMEDIATE,
          CONSTRAINT relation_field_fk FOREIGN KEY (site_id,field_definition_id) REFERENCES content.field_definition(site_id,id) DEFERRABLE INITIALLY IMMEDIATE,
          CONSTRAINT relation_source_field_position_unique UNIQUE (site_id,source_item_id,field_definition_id,position)
        )
    """)
    for table in ("content_item_translation", "item_relation"):
        op.execute(
            f"CREATE TRIGGER {table}_site_immutable BEFORE UPDATE ON content.{table} FOR EACH ROW EXECUTE FUNCTION content.slaif_immutable_site_id()"
        )

    # Recreate field functions with the repaired return shape.
    op.execute("""
      CREATE FUNCTION content.slaif_field_definition_create(p_type_id uuid,p_key text,p_label text,p_field_type text,p_required boolean,p_localized boolean,p_cardinality integer,p_position integer,p_validation jsonb,p_ui_options jsonb)
      RETURNS TABLE(id uuid,site_id uuid,type_id uuid,key text,label text,field_type text,required boolean,localized boolean,cardinality integer,"position" integer,validation jsonb,ui_options jsonb,definition_version integer,created_at timestamptz,updated_at timestamptz)
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN INSERT INTO content.field_definition(site_id,type_id,key,label,field_type,required,localized,cardinality,position,validation,ui_options) SELECT t.site_id,p_type_id,p_key,p_label,p_field_type,p_required,p_localized,p_cardinality,p_position,p_validation,p_ui_options FROM content.content_type t WHERE t.id=p_type_id; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; RETURN QUERY SELECT f.id,f.site_id,f.type_id,f.key,f.label,f.field_type,f.required,f.localized,f.cardinality,f.position,f.validation,f.ui_options,f.definition_version,f.created_at,f.updated_at FROM content.field_definition f WHERE f.type_id=p_type_id AND f.key=p_key; END $$
    """)
    op.execute(
        """CREATE FUNCTION content.slaif_field_definition_list(p_type_id uuid) RETURNS TABLE(id uuid,site_id uuid,type_id uuid,key text,label text,field_type text,required boolean,localized boolean,cardinality integer,\"position\" integer,validation jsonb,ui_options jsonb,definition_version integer,created_at timestamptz,updated_at timestamptz) LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT id,site_id,type_id,key,label,field_type,required,localized,cardinality,\"position\",validation,ui_options,definition_version,created_at,updated_at FROM content.field_definition WHERE type_id=p_type_id ORDER BY \"position\",key COLLATE \"C\" $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_field_definition_get(p_field_id uuid) RETURNS TABLE(id uuid,site_id uuid,type_id uuid,key text,label text,field_type text,required boolean,localized boolean,cardinality integer,\"position\" integer,validation jsonb,ui_options jsonb,definition_version integer,created_at timestamptz,updated_at timestamptz) LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT id,site_id,type_id,key,label,field_type,required,localized,cardinality,\"position\",validation,ui_options,definition_version,created_at,updated_at FROM content.field_definition WHERE id=p_field_id $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_field_definition_update(p_field_id uuid,p_label text,p_required boolean,p_localized boolean,p_cardinality integer,p_position integer,p_validation jsonb,p_ui_options jsonb) RETURNS TABLE(id uuid,site_id uuid,type_id uuid,key text,label text,field_type text,required boolean,localized boolean,cardinality integer,\"position\" integer,validation jsonb,ui_options jsonb,definition_version integer,created_at timestamptz,updated_at timestamptz) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN UPDATE content.field_definition SET label=coalesce(p_label,label),required=coalesce(p_required,required),localized=coalesce(p_localized,localized),cardinality=coalesce(p_cardinality,cardinality),\"position\"=coalesce(p_position,\"position\"),validation=coalesce(p_validation,validation),ui_options=coalesce(p_ui_options,ui_options),definition_version=definition_version+1,updated_at=now() WHERE id=p_field_id; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; RETURN QUERY SELECT * FROM content.slaif_field_definition_get(p_field_id); END $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_field_definition_delete(p_field_id uuid) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN DELETE FROM content.field_definition WHERE id=p_field_id; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; END $$"""
    )
    for name, signature in (
        (
            "slaif_field_definition_create",
            "uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb",
        ),
        ("slaif_field_definition_list", "uuid"),
        ("slaif_field_definition_get", "uuid"),
        (
            "slaif_field_definition_update",
            "uuid,text,boolean,boolean,integer,integer,jsonb,jsonb",
        ),
    ):
        op.execute(f"REVOKE ALL ON FUNCTION content.{name}({signature}) FROM PUBLIC")
    op.execute(
        "REVOKE ALL ON FUNCTION content.slaif_field_definition_delete(uuid) FROM PUBLIC"
    )
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_field_definition_create(uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb),content.slaif_field_definition_list(uuid),content.slaif_field_definition_get(uuid),content.slaif_field_definition_update(uuid,text,boolean,boolean,integer,integer,jsonb,jsonb),content.slaif_field_definition_delete(uuid) TO slaif_editor_runtime,slaif_control"
    )

    # Preserve the Agent API's established shape while repairing its insert
    # path to populate the immutable tenant column.
    op.execute(
        "DROP FUNCTION IF EXISTS content.slaif_agent_field_definition_create(uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb) CASCADE"
    )
    op.execute("""
      CREATE FUNCTION content.slaif_agent_field_definition_create(p_site_id uuid,p_type_id uuid,p_key text,p_label text,p_field_type text,p_required boolean,p_localized boolean,p_cardinality integer,p_position integer,p_validation jsonb,p_ui_options jsonb)
      RETURNS TABLE(id uuid,type_id uuid,key text,label text,field_type text,required boolean,localized boolean,cardinality integer,"position" integer,validation jsonb,ui_options jsonb,definition_version integer,created_at timestamptz,updated_at timestamptz)
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN
        IF NOT EXISTS (SELECT 1 FROM content.content_type t WHERE t.id=p_type_id AND t.site_id=p_site_id AND t.status='ACTIVE') THEN RAISE EXCEPTION 'FIELD_TYPE_SITE_NOT_FOUND' USING ERRCODE='P0002'; END IF;
        INSERT INTO content.field_definition(site_id,type_id,key,label,field_type,required,localized,cardinality,"position",validation,ui_options) VALUES(p_site_id,p_type_id,p_key,p_label,p_field_type,p_required,p_localized,p_cardinality,p_position,p_validation,p_ui_options);
        RETURN QUERY SELECT f.id,f.type_id,f.key,f.label,f.field_type,f.required,f.localized,f.cardinality,f."position",f.validation,f.ui_options,f.definition_version,f.created_at,f.updated_at FROM content.field_definition f WHERE f.site_id=p_site_id AND f.type_id=p_type_id AND f.key=p_key ORDER BY f.created_at DESC LIMIT 1;
      END $$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_agent_field_definition_create(uuid,uuid,text,text,text,boolean,boolean,integer,integer,jsonb,jsonb) TO slaif_agent_runtime"
    )
    op.execute(
        "DROP FUNCTION IF EXISTS content.slaif_agent_field_definition_list(uuid,uuid) CASCADE"
    )
    op.execute("""
      CREATE FUNCTION content.slaif_agent_field_definition_list(p_site_id uuid,p_type_id uuid)
      RETURNS TABLE(id uuid,type_id uuid,key text,label text,field_type text,required boolean,localized boolean,cardinality integer,"position" integer,validation jsonb,ui_options jsonb,definition_version integer,created_at timestamptz,updated_at timestamptz)
      LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $$
        SELECT f.id,f.type_id,f.key,f.label,f.field_type,f.required,f.localized,f.cardinality,f."position",f.validation,f.ui_options,f.definition_version,f.created_at,f.updated_at
        FROM content.field_definition f JOIN content.content_type t ON t.id=f.type_id AND t.site_id=p_site_id
        WHERE f.site_id=p_site_id AND f.type_id=p_type_id AND t.status <> 'DELETED' ORDER BY f."position",f.key COLLATE "C"
      $$
    """)
    op.execute(
        "GRANT EXECUTE ON FUNCTION content.slaif_agent_field_definition_list(uuid,uuid) TO slaif_agent_runtime"
    )

    # Generic CRUD functions deliberately enforce site identity and bounded state.
    op.execute("""
      CREATE FUNCTION content.slaif_content_item_translation_create(p_site_id uuid,p_item_id uuid,p_locale text,p_values jsonb) RETURNS TABLE(id uuid,site_id uuid,item_id uuid,locale text,localized_values jsonb,row_version integer,created_at timestamptz,updated_at timestamptz) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN IF p_locale !~ '^[A-Za-z]{2,8}(-[A-Za-z0-9]{1,8}){0,3}$' OR jsonb_typeof(p_values)<>'object' THEN RAISE EXCEPTION 'TRANSLATION_INVALID' USING ERRCODE='P0003'; END IF; INSERT INTO content.content_item_translation(site_id,item_id,locale,localized_values) VALUES(p_site_id,p_item_id,p_locale,p_values); RETURN QUERY SELECT * FROM content.content_item_translation WHERE site_id=p_site_id AND item_id=p_item_id AND locale=p_locale; END $$
    """)
    op.execute(
        """CREATE FUNCTION content.slaif_content_item_translation_list(p_site_id uuid,p_item_id uuid) RETURNS SETOF content.content_item_translation LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT * FROM content.content_item_translation WHERE site_id=p_site_id AND item_id=p_item_id ORDER BY locale $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_content_item_translation_get(p_site_id uuid,p_id uuid) RETURNS SETOF content.content_item_translation LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT * FROM content.content_item_translation WHERE site_id=p_site_id AND id=p_id $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_content_item_translation_update(p_site_id uuid,p_id uuid,p_locale text,p_values jsonb,p_expected integer) RETURNS SETOF content.content_item_translation LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN UPDATE content.content_item_translation SET locale=coalesce(p_locale,locale),localized_values=coalesce(p_values,localized_values),row_version=row_version+1,updated_at=now() WHERE site_id=p_site_id AND id=p_id AND (p_expected IS NULL OR row_version=p_expected); IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; RETURN QUERY SELECT * FROM content.content_item_translation WHERE site_id=p_site_id AND id=p_id; END $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_content_item_translation_delete(p_site_id uuid,p_id uuid) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN DELETE FROM content.content_item_translation WHERE site_id=p_site_id AND id=p_id; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; END $$"""
    )
    op.execute("""
      CREATE FUNCTION content.slaif_item_relation_create(p_site_id uuid,p_source uuid,p_field uuid,p_target uuid,p_position integer,p_metadata jsonb) RETURNS SETOF content.item_relation LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN IF p_position NOT BETWEEN 0 AND 999 OR jsonb_typeof(p_metadata)<>'object' THEN RAISE EXCEPTION 'RELATION_INVALID' USING ERRCODE='P0003'; END IF; INSERT INTO content.item_relation(site_id,source_item_id,field_definition_id,target_item_id,position,metadata) VALUES(p_site_id,p_source,p_field,p_target,p_position,p_metadata); RETURN QUERY SELECT * FROM content.item_relation WHERE site_id=p_site_id AND source_item_id=p_source AND field_definition_id=p_field AND position=p_position; END $$
    """)
    op.execute(
        """CREATE FUNCTION content.slaif_item_relation_list(p_site_id uuid,p_source uuid) RETURNS SETOF content.item_relation LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT * FROM content.item_relation WHERE site_id=p_site_id AND source_item_id=p_source ORDER BY field_definition_id,position $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_item_relation_get(p_site_id uuid,p_id uuid) RETURNS SETOF content.item_relation LANGUAGE sql SECURITY DEFINER SET search_path=pg_catalog STABLE AS $$ SELECT * FROM content.item_relation WHERE site_id=p_site_id AND id=p_id $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_item_relation_update(p_site_id uuid,p_id uuid,p_target uuid,p_position integer,p_metadata jsonb) RETURNS SETOF content.item_relation LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN UPDATE content.item_relation SET target_item_id=coalesce(p_target,target_item_id),position=coalesce(p_position,position),metadata=coalesce(p_metadata,metadata),row_version=row_version+1,updated_at=now() WHERE site_id=p_site_id AND id=p_id; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; RETURN QUERY SELECT * FROM content.item_relation WHERE site_id=p_site_id AND id=p_id; END $$"""
    )
    op.execute(
        """CREATE FUNCTION content.slaif_item_relation_delete(p_site_id uuid,p_id uuid) RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $$ BEGIN DELETE FROM content.item_relation WHERE site_id=p_site_id AND id=p_id; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_FOUND' USING ERRCODE='P0002'; END IF; END $$"""
    )
    op.execute(
        """DO $$ DECLARE f text; BEGIN FOREACH f IN ARRAY ARRAY['slaif_content_item_translation_create(uuid,uuid,text,jsonb)','slaif_content_item_translation_list(uuid,uuid)','slaif_content_item_translation_get(uuid,uuid)','slaif_content_item_translation_update(uuid,uuid,text,jsonb,integer)','slaif_content_item_translation_delete(uuid,uuid)','slaif_item_relation_create(uuid,uuid,uuid,uuid,integer,jsonb)','slaif_item_relation_list(uuid,uuid)','slaif_item_relation_get(uuid,uuid)','slaif_item_relation_update(uuid,uuid,uuid,integer,jsonb)','slaif_item_relation_delete(uuid,uuid)'] LOOP EXECUTE 'REVOKE ALL ON FUNCTION content.'||f||' FROM PUBLIC'; EXECUTE 'GRANT EXECUTE ON FUNCTION content.'||f||' TO slaif_editor_runtime,slaif_control'; END LOOP; END $$"""
    )


def downgrade() -> None:
    for name, signature in (
        ("slaif_content_item_translation_create", "uuid,uuid,text,jsonb"),
        ("slaif_content_item_translation_list", "uuid,uuid"),
        ("slaif_content_item_translation_get", "uuid,uuid"),
        ("slaif_content_item_translation_update", "uuid,uuid,text,jsonb,integer"),
        ("slaif_content_item_translation_delete", "uuid,uuid"),
        ("slaif_item_relation_create", "uuid,uuid,uuid,uuid,integer,jsonb"),
        ("slaif_item_relation_list", "uuid,uuid"),
        ("slaif_item_relation_get", "uuid,uuid"),
        ("slaif_item_relation_update", "uuid,uuid,uuid,integer,jsonb"),
        ("slaif_item_relation_delete", "uuid,uuid"),
    ):
        op.execute(f"DROP FUNCTION IF EXISTS content.{name}({signature}) CASCADE")
    op.execute("DROP TABLE IF EXISTS content.item_relation CASCADE")
    op.execute("DROP TABLE IF EXISTS content.content_item_translation CASCADE")
    op.execute(
        "DROP TRIGGER IF EXISTS field_definition_site_immutable ON content.field_definition"
    )
    op.execute("DROP INDEX IF EXISTS content.uq_field_definition_site_type_key")
    op.execute(
        "ALTER TABLE content.field_definition DROP CONSTRAINT IF EXISTS uq_field_definition_site_id"
    )
    op.execute(
        "ALTER TABLE content.field_definition DROP CONSTRAINT IF EXISTS field_definition_site_type_fk"
    )
    op.execute("ALTER TABLE content.field_definition DROP COLUMN IF EXISTS site_id")
    op.execute(
        "ALTER TABLE content.content_item DROP CONSTRAINT IF EXISTS uq_content_item_site_id"
    )
    op.execute(
        "ALTER TABLE content.content_type DROP CONSTRAINT IF EXISTS uq_content_type_site_id"
    )
