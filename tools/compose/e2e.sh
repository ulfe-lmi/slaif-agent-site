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
# The overlay (page title, heading props, seven redirects) is written
# through the same trusted definer envelope the editor HTTP path executes
# per request, under the SAME role topology as that path:
#   - the CONTROL login (slaif_control_login) creates the human session
#     (control.slaif_create_human_session is granted to slaif_control
#     only), and the editor runtime (slaif_editor_runtime, login
#     slaif_editor_login) executes the envelope through the product
#     EditorDatabase: its pool initialization verifies the actual
#     session_user/current_user login and runtime-role membership, then
#     each envelope is one COW transaction - trusted workspace assert,
#     idempotency reservation, the supported mutation function, and
#     idempotency completion writing the 078 trusted journal + family
#     audit row;
#   - the owner performs only baseline setup (the canonical seed above,
#     before any overlay operation) and the post-commit durable
#     assertions: the editor runtime holds no SELECT on the audit or
#     idempotency tables, so a committed envelope implies the rows and
#     the owner checks prove durability.
# Both helpers run inside the authorized editor-api container: each
# reads its own mounted login DSN in-process (the editor helper through
# EditorDatabaseSettings, which requires the fixed 0400 file owned by
# the worker uid), proves its actual login, and prints only bounded
# sanitized JSON.  No DSN, password, or raw database error text ever
# reaches host process metadata.  The host independently computes the
# request digest sha256(method NUL path NUL body) over the exact body
# bytes it passes, and the owner assertions require the journal,
# reservation, and family rows to carry exactly that digest.
preview_control_session() {
  # $1 admin account id; prints bounded JSON only.
  docker exec -i "${PROJECT}-editor-api-1" python - "$1" <<'PREVIEW_SESSION_PY'
import asyncio
import hashlib
import json
import sys
import uuid

import asyncpg


def emit(ok, reason=None, session_id=None):
    payload = {"ok": ok}
    if reason is not None:
        payload["reason"] = reason
    if session_id is not None:
        payload["session_id"] = session_id
    print(json.dumps(payload))


async def main():
    try:
        admin_id = uuid.UUID(sys.argv[1])
    except (IndexError, ValueError):
        emit(False, reason="argv")
        return 0
    try:
        with open("/run/slaif-control/control-dsn", encoding="ascii") as stream:
            dsn = stream.read().strip()
        connection = await asyncpg.connect(dsn, timeout=30)
    except Exception:
        emit(False, reason="control-unavailable")
        return 0
    try:
        login = await connection.fetchval("SELECT session_user::text")
        if login != "slaif_control_login":
            emit(False, reason="control-login")
            return 0
        session_id = uuid.uuid4()
        row = await connection.fetchrow(
            "SELECT * FROM control.slaif_create_human_session("
            "$1, $2, $3, $4, $5, $6, $7, $8)",
            session_id,
            "sas2_" + hashlib.md5(b"compose-e2e-preview-editor").hexdigest()[:32],
            hashlib.sha256(b"compose-e2e-preview-editor-secret").digest(),
            hashlib.sha256(b"compose-e2e-preview-editor-csrf").digest(),
            admin_id,
            3600,
            14400,
            3600,
        )
        if row is None or row["session_id"] is None:
            emit(False, reason="session-empty")
            return 0
        emit(True, session_id=str(row["session_id"]))
    except Exception:
        emit(False, reason="session-error")
    finally:
        await connection.close()


asyncio.run(main())
PREVIEW_SESSION_PY
}

preview_editor_session_json=$(preview_control_session "$admin_id") \
  || fail preview-fixture-session
case "$preview_editor_session_json" in
  '{"ok": true'*) ;;
  *)
    echo "compose-e2e: preview session: $preview_editor_session_json" >&2
    fail preview-fixture-session
    ;;
esac
preview_editor_session_id=$(printf '%s\n' "$preview_editor_session_json" \
  | sed -n 's/^{"ok": true, "session_id": "\([0-9a-f-]*\)"}$/\1/p')
test -n "$preview_editor_session_id" || fail preview-fixture-session

preview_overlay_op() {
  # $1 idempotency key; $2 HTTP method; $3 real editor API path;
  # $4 request body JSON (the exact bytes the editor digest covers);
  # $5 permission key; $6 mutation selector (page|composition|redirect);
  # $7..$9 mutation arguments (cross-checked against the body inside the
  # container - the body bytes are what the digest and journal cover).
  case "$6" in
    redirect) preview_expected_status=201 ;;
    *) preview_expected_status=200 ;;
  esac
  preview_expected_digest=$(printf '%s\0%s\0%s' "$2" "$3" "$4" \
    | sha256sum | cut -d' ' -f1)
  preview_op_json=$(docker exec -i "${PROJECT}-editor-api-1" python - \
    "$workspace_id" "$admin_id" "$site_id" "$preview_editor_session_id" \
    "$2" "$3" "$4" "$1" "$5" "$6" "${7:-}" "${8:-}" "${9:-}" <<'PREVIEW_ENVELOPE_PY'
import asyncio
import hashlib
import json
import re
import sys
import uuid

from slaif_agent_site.content_model.service import ContentModelServiceError
from slaif_agent_site.content_model.site_data_models import CreateRedirectRequest
from slaif_agent_site.editor_api.config import EditorDatabaseSettings
from slaif_agent_site.editor_api.database import (
    EditorIdempotencyMismatchError,
    EditorIdempotencyReplayError,
    EditorDatabase,
)

KEY = re.compile(r"^[A-Za-z0-9._~-]{1,128}$")
PERMISSIONS = frozenset(
    {"page:write", "component-content-props:write", "redirect:create"}
)


def emit(ok, reason=None, operation_id=None, resource_id=None):
    payload = {"ok": ok}
    if reason is not None:
        payload["reason"] = reason
    if operation_id is not None:
        payload["operation_id"] = operation_id
    if resource_id is not None:
        payload["resource_id"] = resource_id
    print(json.dumps(payload))


async def main():
    args = sys.argv[1:]
    if len(args) != 13:
        emit(False, reason="argv")
        return 0
    try:
        workspace_id = uuid.UUID(args[0])
        admin_id = uuid.UUID(args[1])
        site_id = uuid.UUID(args[2])
        session_id = uuid.UUID(args[3])
    except ValueError:
        emit(False, reason="argv")
        return 0
    method, path, body, key, permission, selector = args[4:10]
    sel_args = args[10:]
    if method not in ("PATCH", "POST"):
        emit(False, reason="method")
        return 0
    if not path.startswith("/api/editor/v1/"):
        emit(False, reason="path")
        return 0
    if not KEY.fullmatch(key):
        emit(False, reason="key")
        return 0
    if permission not in PERMISSIONS:
        emit(False, reason="permission")
        return 0
    if selector not in ("page", "composition", "redirect"):
        emit(False, reason="selector")
        return 0
    try:
        request_body = json.loads(body)
    except ValueError:
        emit(False, reason="body")
        return 0
    if not isinstance(request_body, dict):
        emit(False, reason="body")
        return 0

    # The mutation inputs are bound to the parsed body (the exact bytes
    # the digest covers); the path-derived ids and the host-passed
    # selector arguments are cross-checked against it so the fixture
    # cannot journal one body while applying another.
    parts = [part for part in path.split("/") if part]
    if (
        len(parts) < 5
        or parts[0] != "api"
        or parts[1] != "editor"
        or parts[2] != "v1"
        or parts[3] != "sites"
        or parts[4] != str(site_id)
    ):
        emit(False, reason="path")
        return 0

    if selector == "page":
        if len(parts) != 7 or parts[5] != "pages":
            emit(False, reason="path")
            return 0
        try:
            page_id = uuid.UUID(parts[6])
        except ValueError:
            emit(False, reason="path")
            return 0
        # Fixed 13-argument transport: the unused third slot must be
        # empty for page mutations.
        if len(sel_args) != 3 or sel_args[2] != "" or str(page_id) != sel_args[0]:
            emit(False, reason="selector-args")
            return 0
        if set(request_body) != {
            "slug", "title", "status", "expected_row_version"
        }:
            emit(False, reason="body-shape")
            return 0
        slug = request_body["slug"]
        title = request_body["title"]
        status = request_body["status"]
        expected_row_version = request_body["expected_row_version"]
        if slug is not None and (
            not isinstance(slug, str) or not 1 <= len(slug) <= 63
        ):
            emit(False, reason="body-shape")
            return 0
        if title is None or not isinstance(title, str) or not (
            1 <= len(title) <= 256
        ):
            emit(False, reason="body-shape")
            return 0
        if title != sel_args[1]:
            emit(False, reason="selector-args")
            return 0
        if status is not None and status not in (
            "DRAFT", "PUBLISHED", "ARCHIVED"
        ):
            emit(False, reason="body-shape")
            return 0
        if expected_row_version is not None and (
            not isinstance(expected_row_version, int)
            or isinstance(expected_row_version, bool)
        ):
            emit(False, reason="body-shape")
            return 0
    elif selector == "composition":
        if (
            len(parts) != 10
            or parts[5] != "pages"
            or parts[7] != "composition"
            or parts[8] != "components"
        ):
            emit(False, reason="path")
            return 0
        try:
            node_id = uuid.UUID(parts[9])
        except ValueError:
            emit(False, reason="path")
            return 0
        # Fixed 13-argument transport: the unused third slot must be
        # empty for composition mutations.
        if len(sel_args) != 3 or sel_args[2] != "" or str(node_id) != sel_args[0]:
            emit(False, reason="selector-args")
            return 0
        if set(request_body) != {"props", "slot_key", "order_key"}:
            emit(False, reason="body-shape")
            return 0
        props = request_body["props"]
        slot_key = request_body["slot_key"]
        order_key = request_body["order_key"]
        if not isinstance(props, dict):
            emit(False, reason="body-shape")
            return 0
        try:
            args_props = json.loads(sel_args[1])
        except ValueError:
            emit(False, reason="selector-args")
            return 0
        if args_props != props:
            emit(False, reason="selector-args")
            return 0
        if slot_key is not None and not isinstance(slot_key, str):
            emit(False, reason="body-shape")
            return 0
        if order_key is not None and (
            not isinstance(order_key, int) or isinstance(order_key, bool)
        ):
            emit(False, reason="body-shape")
            return 0
    else:
        if len(parts) != 6 or parts[5] != "redirects":
            emit(False, reason="path")
            return 0
        if len(sel_args) != 3:
            emit(False, reason="selector-args")
            return 0
        if set(request_body) != {
            "source_route", "target", "status_code", "locale"
        }:
            emit(False, reason="body-shape")
            return 0
        source_route = request_body["source_route"]
        target = request_body["target"]
        status_code = request_body["status_code"]
        locale = request_body["locale"]
        if (
            not isinstance(source_route, str)
            or not source_route.startswith("/")
            or not 1 <= len(source_route) <= 1024
        ):
            emit(False, reason="body-shape")
            return 0
        if not isinstance(target, str) or not 1 <= len(target) <= 2048:
            emit(False, reason="body-shape")
            return 0
        if (
            not isinstance(status_code, int)
            or isinstance(status_code, bool)
            or status_code not in (301, 302, 303, 307, 308)
        ):
            emit(False, reason="body-shape")
            return 0
        if locale is not None and not isinstance(locale, str):
            emit(False, reason="body-shape")
            return 0
        if (
            source_route != sel_args[0]
            or target != sel_args[1]
            or str(status_code) != sel_args[2]
        ):
            emit(False, reason="selector-args")
            return 0

    # The digest the editor HTTP layer computes: sha256 over the exact
    # method NUL path NUL body bytes.
    digest = hashlib.sha256(
        method.encode("ascii")
        + b"\x00"
        + path.encode("utf-8")
        + b"\x00"
        + body.encode("utf-8")
    ).hexdigest()

    try:
        settings = EditorDatabaseSettings.load()
    except Exception:
        emit(False, reason="editor-config")
        return 0
    database = EditorDatabase(settings)
    try:
        await database.start()
    except Exception:
        emit(False, reason="editor-start")
        return 0
    try:
        async with database.request_content_service(
            workspace_id=workspace_id,
            human_user_id=admin_id,
            site_id=site_id,
            human_session_id=session_id,
            permission_key=permission,
            state_changing=True,
            idempotency_key=key,
            request_digest=digest,
        ) as context:
            if selector == "page":
                record = await context.service.update_page(
                    page_id=page_id,
                    slug=slug,
                    title=title,
                    status=status,
                    expected_row_version=expected_row_version,
                )
            elif selector == "composition":
                record = await context.service.update_composition_node(
                    node_id=node_id,
                    props=props,
                    slot_key=slot_key,
                    order_key=order_key,
                )
            else:
                record = await context.service.create_redirect(
                    site_id,
                    CreateRedirectRequest(
                        source_route=source_route,
                        target=target,
                        status_code=status_code,
                        locale=locale,
                    ),
                )
            response_status = 201 if selector == "redirect" else 200
            await database.complete_request(
                context,
                response_status=response_status,
                response_body=record.model_dump(mode="json"),
                action=f"{method} {path}",
                resource_type="editor.sites",
                resource_id=record.id,
            )
        emit(
            True,
            operation_id=str(context.operation_id),
            resource_id=str(record.id),
        )
    except (EditorIdempotencyMismatchError, EditorIdempotencyReplayError):
        emit(False, reason="envelope-idempotency")
    except ContentModelServiceError:
        emit(False, reason="service-error")
    except RuntimeError:
        emit(False, reason="editor-unavailable")
    except Exception:
        emit(False, reason="envelope-error")
    finally:
        try:
            await database.stop()
        except Exception:
            pass


asyncio.run(main())
PREVIEW_ENVELOPE_PY
  ) || fail preview-overlay-envelope "$1"
  case "$preview_op_json" in
    '{"ok": true'*) ;;
    *)
      echo "compose-e2e: overlay-op $1: $preview_op_json" >&2
      fail preview-overlay-envelope "$1"
      ;;
  esac
  preview_op_id=$(printf '%s\n' "$preview_op_json" \
    | sed -n 's/^{"ok": true, "operation_id": "\([0-9a-f-]*\)", "resource_id": "[0-9a-f-]*"}$/\1/p')
  preview_resource_id=$(printf '%s\n' "$preview_op_json" \
    | sed -n 's/^{"ok": true, "operation_id": "[0-9a-f-]*", "resource_id": "\([0-9a-f-]*\)"}$/\1/p')
  test -n "$preview_op_id" || fail preview-overlay-envelope "$1"
  test -n "$preview_resource_id" || fail preview-overlay-envelope "$1"
  # Durable post-commit assertions, owner-only (the editor runtime holds
  # no SELECT on the audit or idempotency tables): the real session is
  # unrevoked, the idempotency reservation completed, and the 078
  # trusted journal + family audit row exist - all bound to the exact
  # server-generated operation and to the digest the host computed over
  # the exact request bytes.
  preview_durable_state=$(docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif \
    -Atc "
      SELECT
        (SELECT count(*) FROM control.user_session s
           WHERE s.id = '$preview_editor_session_id'
             AND s.user_account_id = '$admin_id'
             AND s.revoked_at IS NULL) || '|' ||
        (SELECT count(*) FROM control.human_editor_idempotency i
           WHERE i.workspace_id = '$workspace_id'
             AND i.idempotency_key = '$1'
             AND i.operation_id = '$preview_op_id'
             AND i.request_digest = '$preview_expected_digest'
             AND i.status_code = $preview_expected_status
             AND i.response_body IS NOT NULL) || '|' ||
        (SELECT count(*) FROM audit.mutation_completion mc
           WHERE mc.operation_id = '$preview_op_id'
             AND mc.family = 'human_editor'
             AND mc.disposition = 'completed'
             AND mc.workspace_id = '$workspace_id'
             AND mc.site_id = '$site_id'
             AND mc.human_user_id = '$admin_id'
             AND mc.request_digest = '$preview_expected_digest') || '|' ||
        (SELECT count(*) FROM audit.human_editor_mutation m
           WHERE m.operation_id = '$preview_op_id'
             AND m.workspace_id = '$workspace_id'
             AND m.site_id = '$site_id'
             AND m.human_user_id = '$admin_id'
             AND m.action = '$2 $3'
             AND m.resource_type = 'editor.sites'
             AND m.resource_id = '$preview_resource_id'
             AND m.request_digest = '$preview_expected_digest'
             AND m.response_status = $preview_expected_status)")
  test "$preview_durable_state" = "1|1|1|1" \
    || fail preview-overlay-envelope "$1"
}

preview_overlay_op \
  compose-page-overlay \
  PATCH \
  "/api/editor/v1/sites/$site_id/pages/12000000-0000-4000-8000-000000000330" \
  "{\"slug\":null,\"title\":\"Compose preview overlay\",\"status\":null,\"expected_row_version\":null}" \
  page:write \
  page \
  12000000-0000-4000-8000-000000000330 \
  "Compose preview overlay"
preview_overlay_op \
  compose-props-overlay \
  PATCH \
  "/api/editor/v1/sites/$site_id/pages/12000000-0000-4000-8000-000000000330/composition/components/12000000-0000-4000-8000-000000000331" \
  "{\"props\":{\"text\":\"Compose overlay heading\",\"level\":2},\"slot_key\":null,\"order_key\":null}" \
  component-content-props:write \
  composition \
  12000000-0000-4000-8000-000000000331 \
  "{\"text\":\"Compose overlay heading\",\"level\":2}"
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
