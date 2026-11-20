#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
TOKEN_FILE=$1
SECRET_FILE=$2
PROJECT=${3:?missing compose project}
OUTPUT_DIR=$(mktemp -d)

cleanup() {
  rm -f "$SECRET_FILE"
  case "$OUTPUT_DIR" in
    /tmp/*) rm -rf -- "$OUTPUT_DIR" ;;
  esac
}
trap cleanup EXIT HUP INT TERM

collect_worker_diag() {
  # Bounded sanitized collection for the CI log on any stage failure.
  # The container stdout+stderr are merged into the sanitizer (never
  # emitted raw): it re-emits ONLY the fixed bounded fields of lines
  # whose JSON message starts with the exact diagnostic prefix, and
  # drops everything else - markers embedded in other JSON fields or
  # unrelated messages, non-JSON/malformed lines, unknown keys, and
  # out-of-shape values. Capped at 60 sanitized lines.
  docker logs --tail 400 "${PROJECT}-review-worker-1" 2>&1 \
    | node "$ROOT/tools/compose/diag-sanitize.mjs" \
    | head -n 60 || true
}

fail() {
  echo "compose-e2e: FAILED stage=$1 reason=$2" >&2
  collect_worker_diag
  exit 1
}

test -s "$TOKEN_FILE" || fail secret-channel empty
chmod 600 "$TOKEN_FILE" "$SECRET_FILE" || fail secret-channel chmod
test "$(stat -c '%a' "$TOKEN_FILE")" = 600 || fail secret-channel token-mode
test "$(stat -c '%a' "$SECRET_FILE")" = 600 || fail secret-channel credential-mode

token=$(tr -d '\n' <"$TOKEN_FILE")
case "$token" in
  ''|*[!A-Za-z0-9._-]*) echo "compose-e2e: invalid secret channel" >&2; exit 1 ;;
esac
printf '{"setupToken":"%s","username":"Compose.Admin","loginUsername":"compose.admin","password":"fixture-compose-auth-password-123","fixtureUserOne":"12000000-0000-4000-8000-000000000001","fixtureUserTwo":"12000000-0000-4000-8000-000000000002"}\n' \
  "$token" >"$SECRET_FILE"
unset token

if ! SLAIF_E2E_SECRET_FILE="$SECRET_FILE" \
  SLAIF_E2E_OUTPUT_DIR="$OUTPUT_DIR" \
  pnpm exec playwright test --project=setup --project=governance
then
  fail browser setup-governance-contract
fi

workspace_id=12000000-0000-4000-8000-000000000301
admin_id=$(docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT id FROM control.user_account WHERE local_username_normalized = 'compose.admin'")
parity_site_id=12000000-0000-4000-8000-000000000300
test -n "$admin_id" || fail preview-fixture-admin
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif \
  -v ON_ERROR_STOP=1 -c \
  "BEGIN;
   INSERT INTO control.site
     (id,site_key,display_name,default_locale,component_catalog_version,status)
   VALUES ('$parity_site_id'::uuid,'parity','Renderer Parity Fixture','en',
           'catalog-v1','ACTIVE');
   INSERT INTO control.site_membership
     (site_id,user_account_id,role_key,delegation_ceiling)
   VALUES ('$parity_site_id'::uuid,'$admin_id'::uuid,'SITE_OWNER',4);
   COMMIT;" >/dev/null
site_id=$parity_site_id
test -n "$site_id" || fail preview-fixture-site
# The preview workspace carries the current 076 constructor version facts
# at creation: the freeze materializer refuses unpinned ('{}') workspaces
# with REVIEW_WORKSPACE_VERSION_UNKNOWN.
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif \
  -v ON_ERROR_STOP=1 -c \
  "BEGIN;
   INSERT INTO control.workspace
     (id, site_id, created_by, actor_type, title, delegation_preset,
      version_facts, status, expires_at)
   VALUES ('$workspace_id'::uuid, '$site_id'::uuid, '$admin_id'::uuid,
           'HUMAN', 'Compose preview fixture', 'L4_SITE_ARCHITECT',
           '{\"catalog\":\"catalog-v1\",\"composition_schema\":\"site-composition/v1\",\"content_model\":\"content-model/v1\",\"design_system\":\"design-system/v1\",\"puck\":\"0.20.2\",\"renderer\":\"renderer-v1\"}'::jsonb,
           'ACTIVE', CURRENT_TIMESTAMP + interval '1 hour');
   INSERT INTO content.site_locale_base
     (id,site_id,tag,enabled,is_default,position,metadata)
   VALUES
     ('12000000-0000-4000-8000-000000000332'::uuid,'$site_id'::uuid,
      'en',true,true,0,'{}'::jsonb),
     ('12000000-0000-4000-8000-000000000303'::uuid,'$site_id'::uuid,
      'sl-SI',true,false,1,'{}'::jsonb);
   INSERT INTO content.page_base
     (id,site_id,slug,title,status,locale,parent_id,route_template)
   VALUES
     ('12000000-0000-4000-8000-000000000330'::uuid,'$site_id'::uuid,
      'home','Parity canonical','PUBLISHED','en',NULL,NULL),
     ('12000000-0000-4000-8000-000000000304'::uuid,'$site_id'::uuid,
      'parity','Slovenska domača stran','PUBLISHED','sl-SI',NULL,NULL);
   INSERT INTO content.page_composition_base
     (id,site_id,page_id,component_type,schema_version,parent_id,slot_key,order_key,props)
   VALUES
     ('12000000-0000-4000-8000-000000000331'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000330'::uuid,'Heading','1',NULL,'default',0,
      '{\"text\":\"Parity canonical heading\",\"level\":2}'::jsonb),
     ('12000000-0000-4000-8000-000000000333'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000330'::uuid,'RichText','1',NULL,'default',1,
      '{\"content\":{\"type\":\"paragraph\",\"children\":[{\"text\":\"Parity canonical text.\"}]}}'::jsonb);
   INSERT INTO content.content_type_base
     (id,site_id,key,labels,slug_pattern,status,definition_version,settings)
   VALUES
     ('12000000-0000-4000-8000-000000000305'::uuid,'$site_id'::uuid,
      'parity-article','{\"en\":\"Parity article\",\"sl-SI\":\"Članek\"}'::jsonb,
      '/parity/{slug}','ACTIVE',1,'{}'::jsonb);
   INSERT INTO content.field_definition_base
     (id,type_id,key,label,field_type,required,localized,cardinality,position,
      validation,ui_options,definition_version)
   VALUES
     ('12000000-0000-4000-8000-000000000306'::uuid,
      '12000000-0000-4000-8000-000000000305'::uuid,'title','Title',
      'short_text',true,true,1,0,'{}'::jsonb,'{}'::jsonb,1),
     ('12000000-0000-4000-8000-000000000307'::uuid,
      '12000000-0000-4000-8000-000000000305'::uuid,'summary','Summary',
      'long_text',true,true,1,1,'{}'::jsonb,'{}'::jsonb,1),
     ('12000000-0000-4000-8000-000000000308'::uuid,
      '12000000-0000-4000-8000-000000000305'::uuid,'rank','Rank',
      'integer',true,false,1,2,'{}'::jsonb,'{}'::jsonb,1);
   INSERT INTO content.content_item_base
     (id,site_id,type_id,slug,status,type_definition_version,values)
   VALUES
     ('12000000-0000-4000-8000-000000000309'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000305'::uuid,'first','PUBLISHED',1,
      '{\"rank\":2}'::jsonb),
     ('12000000-0000-4000-8000-000000000310'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000305'::uuid,'second','PUBLISHED',1,
      '{\"rank\":1}'::jsonb);
   INSERT INTO content.content_item_translation_base
     (id,site_id,item_id,locale,localized_values)
   VALUES
     ('12000000-0000-4000-8000-000000000311'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000309'::uuid,'en',
      '{\"title\":\"First parity item\",\"summary\":\"First parity summary\"}'::jsonb),
     ('12000000-0000-4000-8000-000000000312'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000310'::uuid,'en',
      '{\"title\":\"Second parity item\",\"summary\":\"Second parity summary\"}'::jsonb),
     ('12000000-0000-4000-8000-000000000313'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000309'::uuid,'sl-SI',
      '{\"title\":\"Prvi članek\",\"summary\":\"Prvi povzetek\"}'::jsonb),
     ('12000000-0000-4000-8000-000000000314'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000310'::uuid,'sl-SI',
      '{\"title\":\"Drugi članek\",\"summary\":\"Drugi povzetek\"}'::jsonb);
   INSERT INTO content.collection_view_base
     (id,site_id,type_id,key,filter_spec,sort_spec,projection_spec,pagination_spec)
   VALUES
     ('12000000-0000-4000-8000-000000000315'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000305'::uuid,'parity-articles',
      '{}'::jsonb,'{\"field\":\"rank\",\"direction\":\"desc\"}'::jsonb,
      '{\"fields\":[\"title\",\"summary\",\"rank\"]}'::jsonb,
      '{\"limit\":10,\"offset\":0}'::jsonb);
   INSERT INTO content.page_composition_base
     (id,site_id,page_id,component_type,schema_version,parent_id,slot_key,order_key,props)
   VALUES
     ('12000000-0000-4000-8000-000000000316'::uuid,'$site_id'::uuid,
      (SELECT id FROM content.page_base WHERE site_id='$site_id'::uuid AND slug='home' AND locale='en'),
      'Section','1',NULL,'default',2,'{}'::jsonb),
     ('12000000-0000-4000-8000-000000000317'::uuid,'$site_id'::uuid,
      (SELECT id FROM content.page_base WHERE site_id='$site_id'::uuid AND slug='home' AND locale='en'),
      'Container','1','12000000-0000-4000-8000-000000000316'::uuid,'default',0,
      '{\"width\":\"md\"}'::jsonb),
     ('12000000-0000-4000-8000-000000000318'::uuid,'$site_id'::uuid,
      (SELECT id FROM content.page_base WHERE site_id='$site_id'::uuid AND slug='home' AND locale='en'),
      'Grid','1','12000000-0000-4000-8000-000000000317'::uuid,'default',0,
      '{\"columns\":2,\"gap\":\"md\"}'::jsonb),
     ('12000000-0000-4000-8000-000000000319'::uuid,'$site_id'::uuid,
      (SELECT id FROM content.page_base WHERE site_id='$site_id'::uuid AND slug='home' AND locale='en'),
      'Heading','1','12000000-0000-4000-8000-000000000318'::uuid,'default',0,
      '{\"text\":\"Parity layout\",\"level\":3}'::jsonb),
     ('12000000-0000-4000-8000-000000000320'::uuid,'$site_id'::uuid,
      (SELECT id FROM content.page_base WHERE site_id='$site_id'::uuid AND slug='home' AND locale='en'),
      'CollectionList','1',NULL,'default',3,
      '{\"viewId\":\"12000000-0000-4000-8000-000000000315\",\"limit\":2}'::jsonb),
     ('12000000-0000-4000-8000-000000000321'::uuid,'$site_id'::uuid,
      (SELECT id FROM content.page_base WHERE site_id='$site_id'::uuid AND slug='home' AND locale='en'),
      'CollectionGrid','1',NULL,'default',4,
      '{\"viewId\":\"12000000-0000-4000-8000-000000000315\",\"columns\":2}'::jsonb),
     ('12000000-0000-4000-8000-000000000322'::uuid,'$site_id'::uuid,
      (SELECT id FROM content.page_base WHERE site_id='$site_id'::uuid AND slug='home' AND locale='en'),
      'CollectionDetail','1',NULL,'default',5,
      '{\"viewId\":\"12000000-0000-4000-8000-000000000315\"}'::jsonb),
     ('12000000-0000-4000-8000-000000000323'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000304'::uuid,'Section','1',NULL,'default',0,'{}'::jsonb),
     ('12000000-0000-4000-8000-000000000324'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000304'::uuid,'Container','1',
      '12000000-0000-4000-8000-000000000323'::uuid,'default',0,'{\"width\":\"md\"}'::jsonb),
     ('12000000-0000-4000-8000-000000000325'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000304'::uuid,'Grid','1',
      '12000000-0000-4000-8000-000000000324'::uuid,'default',0,'{\"columns\":2,\"gap\":\"md\"}'::jsonb),
     ('12000000-0000-4000-8000-000000000326'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000304'::uuid,'Heading','1',
      '12000000-0000-4000-8000-000000000325'::uuid,'default',0,'{\"text\":\"Slovenska postavitev\",\"level\":3}'::jsonb),
     ('12000000-0000-4000-8000-000000000327'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000304'::uuid,'CollectionList','1',NULL,'default',1,
      '{\"viewId\":\"12000000-0000-4000-8000-000000000315\",\"limit\":2}'::jsonb),
     ('12000000-0000-4000-8000-000000000328'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000304'::uuid,'CollectionGrid','1',NULL,'default',2,
      '{\"viewId\":\"12000000-0000-4000-8000-000000000315\",\"columns\":2}'::jsonb),
     ('12000000-0000-4000-8000-000000000329'::uuid,'$site_id'::uuid,
      '12000000-0000-4000-8000-000000000304'::uuid,'CollectionDetail','1',NULL,'default',3,
      '{\"viewId\":\"12000000-0000-4000-8000-000000000315\"}'::jsonb);
   INSERT INTO content.redirect_base(site_id,source_route,target,status_code,locale)
   VALUES
     ('$site_id'::uuid,'/compose-canonical-301','/',301,NULL),
     ('$site_id'::uuid,'/compose-canonical-302','/',302,NULL),
     ('$site_id'::uuid,'/compose-canonical-303','/',303,NULL),
     ('$site_id'::uuid,'/compose-canonical-307','/',307,NULL),
     ('$site_id'::uuid,'/compose-canonical-308','/',308,NULL),
     ('$site_id'::uuid,'/compose-canonical-external',
      'https://example.test/compose-target',301,NULL);
    COMMIT;" >/dev/null

# ---------------------------------------------------------------------------
# Preview overlay as genuine trusted human-editor completion operations.
# The historical seed wrote the overlay (page title, heading props, seven
# redirects) as raw COW view writes under one pinned, unqualified fixture
# operation: nine pending changes with no 078 completion facts, which the
# 079 reviewed-operation binding lawfully refuses to freeze.  The overlay is
# now written through the same trusted definer envelope the editor HTTP
# path executes per request:
#   BEGIN;
#   SET LOCAL app.session_id  = <preview workspace>;
#   SET LOCAL app.operation_id = <server-generated uuid, never pinned>;
#   control.slaif_human_editor_workspace_assert(...);
#   control.slaif_human_editor_idempotency_begin(...);
#   content.slaif_page_update / slaif_composition_node_update /
#   slaif_redirect_create (the real supported mutation functions);
#   control.slaif_human_editor_idempotency_complete(...)
#     (writes the 078 trusted journal + family audit row);
#   COMMIT;
# The definer functions enforce the real session/workspace/permission/COW
# context checks; the request digest is the real sha256(method NUL path
# NUL body) the editor HTTP layer computes; the completion records the row
# the mutation actually wrote, including the server-generated redirect id.
preview_editor_session_id=$(docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif \
  -Atc "SELECT (control.slaif_create_human_session(
     gen_random_uuid(),
     'sas2_' || substr(md5('compose-e2e-preview-editor'), 1, 32),
     sha256(convert_to('compose-e2e-preview-editor-secret', 'UTF8')),
     sha256(convert_to('compose-e2e-preview-editor-csrf', 'UTF8')),
     '$admin_id'::uuid, 3600, 14400, 3600)).session_id")
test -n "$preview_editor_session_id" || fail preview-fixture-session

preview_overlay_op() {
  # $1 idempotency key; $2 HTTP method; $3 real editor API path;
  # $4 request body JSON (exactly what the editor digest covers);
  # $5 permission key; $6 mutation selector (page|composition|redirect);
  # $7..$9 mutation arguments.
  preview_op_id=$(docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif \
    -Atc "SELECT gen_random_uuid()")
  preview_op_digest=$(docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif \
    -Atc "SELECT encode(sha256(convert_to('$2', 'UTF8') || decode('00', 'hex') || convert_to('$3', 'UTF8') || decode('00', 'hex') || convert_to('$4', 'UTF8')), 'hex')")
  case "$6" in
    page)
      preview_mutation_sql="SELECT * INTO r FROM content.slaif_page_update(
          '$7', NULL, '$8', NULL, NULL);
      IF r.id IS NULL THEN
        RAISE EXCEPTION 'preview overlay fixture: page update missing';
      END IF;"
      preview_complete_sql="PERFORM control.slaif_human_editor_idempotency_complete(
          '$workspace_id','$admin_id','$site_id','$preview_editor_session_id','$5',
          '$1','$preview_op_digest','$preview_op_id',200,
          jsonb_build_object('id',r.id,'site_id',r.site_id,'slug',r.slug,
                             'title',r.title,'status',r.status,'locale',r.locale,
                             'parent_id',r.parent_id,'row_version',r.row_version),
          '$2 $3','editor.sites',r.id);"
      ;;
    composition)
      preview_mutation_sql="SELECT * INTO r FROM content.slaif_composition_node_update(
          '$7','$8'::jsonb,NULL,NULL);
      IF r.id IS NULL THEN
        RAISE EXCEPTION 'preview overlay fixture: composition update missing';
      END IF;"
      preview_complete_sql="PERFORM control.slaif_human_editor_idempotency_complete(
          '$workspace_id','$admin_id','$site_id','$preview_editor_session_id','$5',
          '$1','$preview_op_digest','$preview_op_id',200,
          jsonb_build_object('id',r.id,'site_id',r.site_id,'page_id',r.page_id,
                             'component_type',r.component_type,
                             'schema_version',r.schema_version,'parent_id',r.parent_id,
                             'slot_key',r.slot_key,'order_key',r.order_key,
                             'props',r.props),
          '$2 $3','editor.sites',r.id);"
      ;;
    redirect)
      preview_mutation_sql="SELECT * INTO r FROM content.slaif_redirect_create(
          '$site_id'::uuid,'$7','$8',$9,NULL);
      SELECT * INTO r FROM content.redirect
       WHERE site_id = '$site_id'::uuid AND source_route = '$7'
         AND locale IS NULL
       ORDER BY id DESC LIMIT 1;
      IF r.id IS NULL THEN
        RAISE EXCEPTION 'preview overlay fixture: redirect create missing for %',
          '$7';
      END IF;"
      preview_complete_sql="PERFORM control.slaif_human_editor_idempotency_complete(
          '$workspace_id','$admin_id','$site_id','$preview_editor_session_id','$5',
          '$1','$preview_op_digest','$preview_op_id',200,
          jsonb_build_object('id',r.id,'site_id',r.site_id,
                             'source_route',r.source_route,'target',r.target,
                             'status_code',r.status_code,'locale',r.locale,
                             'row_version',r.row_version),
          '$2 $3','editor.sites',r.id);"
      ;;
  esac
  if ! docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif \
      -v ON_ERROR_STOP=1 -c "
     BEGIN;
     SET LOCAL app.session_id = '$workspace_id';
     SET LOCAL app.operation_id = '$preview_op_id';
     DO \$pv\$
     DECLARE r record;
     BEGIN
       PERFORM control.slaif_human_editor_workspace_assert(
           '$workspace_id','$admin_id','$site_id','$preview_editor_session_id','$5',true);
       IF (SELECT state FROM control.slaif_human_editor_idempotency_begin(
              '$workspace_id','$admin_id','$site_id','$preview_editor_session_id','$5',
              '$1','$preview_op_digest','$preview_op_id')) IS DISTINCT FROM 'STARTED' THEN
         RAISE EXCEPTION 'preview overlay fixture: % envelope not started', '$1';
       END IF;
       $preview_mutation_sql
       $preview_complete_sql
       IF (SELECT count(*) FROM audit.mutation_completion mc
            WHERE mc.operation_id = '$preview_op_id'
              AND mc.family = 'human_editor'
              AND mc.disposition = 'completed') <> 1 THEN
         RAISE EXCEPTION 'preview overlay fixture: % trusted completion missing',
           '$1';
       END IF;
     END
     \$pv\$;
     COMMIT;" >"$OUTPUT_DIR/overlay-$1.log" 2>&1
  then
    sed "s/^/compose-e2e: overlay-op $1: /" "$OUTPUT_DIR/overlay-$1.log" >&2
    fail preview-overlay-envelope "$1"
  fi
}

preview_overlay_op \
  compose-page-overlay \
  PATCH \
  "/api/editor/v1/sites/$site_id/pages/12000000-0000-4000-8000-000000000330" \
  '{\"slug\":null,\"title\":\"Compose preview overlay\",\"status\":null,\"expected_row_version\":null}' \
  page:write \
  page \
  12000000-0000-4000-8000-000000000330 \
  "Compose preview overlay"
preview_overlay_op \
  compose-props-overlay \
  PATCH \
  "/api/editor/v1/sites/$site_id/pages/12000000-0000-4000-8000-000000000330/composition/components/12000000-0000-4000-8000-000000000331" \
  '{\"props\":{\"text\":\"Compose overlay heading\",\"level\":2},\"slot_key\":null,\"order_key\":null}' \
  component-content-props:write \
  composition \
  12000000-0000-4000-8000-000000000331 \
  '{\"text\":\"Compose overlay heading\",\"level\":2}'
preview_overlay_redirect_n=1
while read -r preview_redirect_source preview_redirect_target preview_redirect_status
do
  [ -n "$preview_redirect_source" ] || continue
  preview_overlay_op \
    "compose-redirect-$preview_overlay_redirect_n" \
    POST \
    "/api/editor/v1/sites/$site_id/redirects" \
    "{\"source_route\":\"$preview_redirect_source\",\"target\":\"$preview_redirect_target\",\"status_code\":$preview_redirect_status,\"locale\":null}" \
    redirect:create \
    redirect \
    "$preview_redirect_source" \
    "$preview_redirect_target" \
    "$preview_redirect_status"
  preview_overlay_redirect_n=$((preview_overlay_redirect_n + 1))
done <<'PREVIEW_OVERLAY_REDIRECTS'
/compose-redirect / 301
/compose-redirect-301 / 301
/compose-redirect-302 / 302
/compose-redirect-303 / 303
/compose-redirect-307 / 307
/compose-redirect-308 / 308
/compose-redirect-external https://example.test/compose-target 301
PREVIEW_OVERLAY_REDIRECTS
test "$preview_overlay_redirect_n" = 8 || fail preview-overlay-redirect-count

if ! SLAIF_E2E_SECRET_FILE="$SECRET_FILE" \
  SLAIF_E2E_PREVIEW_WORKSPACE_ID="$workspace_id" \
  SLAIF_E2E_OUTPUT_DIR="$OUTPUT_DIR" \
  pnpm exec playwright test --no-deps --project=preview
then
  fail browser preview-contract
fi

if ! SLAIF_E2E_SECRET_FILE="$SECRET_FILE" \
  SLAIF_E2E_OUTPUT_DIR="$OUTPUT_DIR" \
  pnpm exec playwright test --no-deps --project=preview-filtering
then
  fail browser preview-filtering-contract
fi

if ! SLAIF_E2E_SECRET_FILE="$SECRET_FILE" \
  SLAIF_E2E_OUTPUT_DIR="$OUTPUT_DIR" \
  pnpm exec playwright test --no-deps \
    --project=desktop-chromium --project=desktop-firefox --project=desktop-webkit \
    --project=tablet --project=mobile-chromium --project=mobile-webkit
then
  fail browser stable-devices-contract
fi

if ! SLAIF_E2E_SECRET_FILE="$SECRET_FILE" \
  SLAIF_E2E_OUTPUT_DIR="$OUTPUT_DIR" \
  pnpm exec playwright test --no-deps \
    --project=agent-desktop-chromium --project=agent-mobile-chromium
then
  fail browser agent-session-desktop-phone-contract
fi

if ! SLAIF_E2E_SECRET_FILE="$SECRET_FILE" \
  SLAIF_E2E_COMPOSE_PROJECT="$PROJECT" \
  SLAIF_E2E_OUTPUT_DIR="$OUTPUT_DIR" \
  pnpm exec playwright test --no-deps \
    --project=agent-workspace-puck-desktop --project=agent-workspace-puck-tablet
then
  fail browser agent-workspace-puck-contract
fi
if ! SLAIF_E2E_SECRET_FILE="$SECRET_FILE" \
  SLAIF_E2E_COMPOSE_PROJECT="$PROJECT" \
  SLAIF_E2E_OUTPUT_DIR="$OUTPUT_DIR" \
  pnpm exec playwright test --no-deps --project=review-surface
then
  fail browser review-surface-contract
fi

if ! SLAIF_E2E_SECRET_FILE="$SECRET_FILE" \
  SLAIF_E2E_COMPOSE_PROJECT="$PROJECT" \
  SLAIF_E2E_OUTPUT_DIR="$OUTPUT_DIR" \
  pnpm exec playwright test --no-deps --project=freeze-review-snapshot
then
  fail browser freeze-review-snapshot-contract
fi

if ! SLAIF_E2E_SECRET_FILE="$SECRET_FILE" \
  SLAIF_E2E_COMPOSE_PROJECT="$PROJECT" \
  SLAIF_E2E_OUTPUT_DIR="$OUTPUT_DIR" \
  pnpm exec playwright test --no-deps --project=accept-lifecycle
then
  fail browser accept-lifecycle-contract
fi

if ! SLAIF_E2E_SECRET_FILE="$SECRET_FILE" \
  SLAIF_E2E_COMPOSE_PROJECT="$PROJECT" \
  SLAIF_E2E_OUTPUT_DIR="$OUTPUT_DIR" \
  pnpm exec playwright test --no-deps --project=discard-lifecycle
then
  fail browser discard-lifecycle-contract
fi

if ! SLAIF_E2E_SECRET_FILE="$SECRET_FILE" \
  SLAIF_E2E_COMPOSE_PROJECT="$PROJECT" \
  SLAIF_E2E_PREVIEW_WORKSPACE_ID="$workspace_id" \
  SLAIF_E2E_OUTPUT_DIR="$OUTPUT_DIR" \
  pnpm exec playwright test --no-deps --project=media-publication
then
  fail browser media-publication-contract
fi
echo "compose-e2e: OK projects=19 setup=1 governance=1 preview=1 preview-filtering=1 stable-devices=6 agent-sessions=2 agent-workspace-puck=2 freeze-review-snapshot=1 review-surface=1 accept-lifecycle=1 discard-lifecycle=1 media-publication=1 artifacts=disabled"

# Dedicated ACTIVE workspace for the downstream smoke agent-browser phase,
# created only AFTER every browser project succeeded. The shared preview
# workspace above is consumed by the media-publication cycles and ends
# terminal-ACCEPTED, and a closed workspace's capabilities no longer
# authenticate, so the smoke browser runs bind this separate still-ACTIVE
# workspace (same site, no pending content). It must NOT exist while the
# projects run: control.slaif_human_editor_workspace_resolve selects the
# latest ACTIVE HUMAN workspace by created_at DESC, id DESC, and the E2E
# fixtures assert that the pinned preview workspace is the only HUMAN
# workspace on the parity site.
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif \
  -v ON_ERROR_STOP=1 -c \
  "BEGIN;
   INSERT INTO control.workspace
     (id, site_id, created_by, actor_type, title, delegation_preset,
      version_facts, status, expires_at)
   VALUES ('12000000-0000-4000-8000-000000000340'::uuid, '$site_id'::uuid,
           '$admin_id'::uuid, 'HUMAN', 'Compose smoke browser fixture',
           'L4_SITE_ARCHITECT',
           '{\"catalog\":\"catalog-v1\",\"composition_schema\":\"site-composition/v1\",\"content_model\":\"content-model/v1\",\"design_system\":\"design-system/v1\",\"puck\":\"0.20.2\",\"renderer\":\"renderer-v1\"}'::jsonb,
           'ACTIVE', CURRENT_TIMESTAMP + interval '1 hour');
   COMMIT;" >/dev/null
