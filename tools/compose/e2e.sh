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
site_id=$(docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT id FROM control.site WHERE site_key = 'demo'")
test -n "$admin_id" || fail preview-fixture-admin
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
   UPDATE content.page
   SET title = 'Compose preview overlay'
   WHERE site_id = '$site_id'::uuid AND slug = 'home' AND locale = 'en';
   UPDATE content.page_composition
   SET props = '{\"text\":\"Compose overlay heading\",\"level\":2}'::jsonb
   WHERE site_id = '$site_id'::uuid
     AND page_id = (SELECT id FROM content.page_base
                    WHERE site_id = '$site_id'::uuid AND slug = 'home' AND locale = 'en')
     AND component_type = 'Heading';
   INSERT INTO content.redirect(site_id,source_route,target,status_code,locale)
   VALUES ('$site_id'::uuid,'/compose-redirect','/',301,NULL);
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
