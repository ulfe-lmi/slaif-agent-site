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

fail() {
  echo "compose-e2e: FAILED stage=$1 reason=$2" >&2
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
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif \
  -v ON_ERROR_STOP=1 -c \
  "BEGIN;
   INSERT INTO control.workspace
     (id, site_id, created_by, actor_type, title, delegation_preset, status, expires_at)
   VALUES ('$workspace_id'::uuid, '$site_id'::uuid, '$admin_id'::uuid,
           'HUMAN', 'Compose preview fixture', 'L4_SITE_ARCHITECT', 'ACTIVE',
           CURRENT_TIMESTAMP + interval '1 hour');
   SET LOCAL app.session_id = '$workspace_id';
   SET LOCAL app.operation_id = '12000000-0000-4000-8000-000000000302';
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
   UPDATE content.page
   SET title = 'Compose preview overlay'
   WHERE site_id = '$site_id'::uuid AND slug = 'home' AND locale = 'en';
   UPDATE content.page_composition
   SET props = '{\"text\":\"Compose overlay heading\",\"level\":2}'::jsonb
   WHERE site_id = '$site_id'::uuid
     AND page_id = (SELECT id FROM content.page_base
                    WHERE site_id = '$site_id'::uuid AND slug = 'home' AND locale = 'en')
     AND component_type = 'Heading' AND order_key = 0;
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
   INSERT INTO content.redirect(site_id,source_route,target,status_code,locale)
   VALUES
     ('$site_id'::uuid,'/compose-redirect','/',301,NULL),
     ('$site_id'::uuid,'/compose-redirect-301','/',301,NULL),
     ('$site_id'::uuid,'/compose-redirect-302','/',302,NULL),
     ('$site_id'::uuid,'/compose-redirect-303','/',303,NULL),
     ('$site_id'::uuid,'/compose-redirect-307','/',307,NULL),
     ('$site_id'::uuid,'/compose-redirect-308','/',308,NULL),
     ('$site_id'::uuid,'/compose-redirect-external',
      'https://example.test/compose-target',301,NULL);
   COMMIT;" >/dev/null

if ! SLAIF_E2E_SECRET_FILE="$SECRET_FILE" \
  SLAIF_E2E_PREVIEW_WORKSPACE_ID="$workspace_id" \
  SLAIF_E2E_OUTPUT_DIR="$OUTPUT_DIR" \
  pnpm exec playwright test --no-deps --project=preview
then
  fail browser preview-contract
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
echo "compose-e2e: OK projects=11 setup=1 governance=1 preview=1 stable-devices=6 agent-sessions=2 artifacts=disabled"
