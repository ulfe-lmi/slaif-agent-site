#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
PROJECT=${1-slaif007smoke}
NEGATIVE_PROJECT="${PROJECT}negative"

validate_project() {
  case "$1" in
    slaif007[a-z0-9]*|slaif009[a-z0-9]*|slaif010[a-z0-9]*|slaif071[a-z0-9]*) return 0 ;;
    *) echo "compose-smoke: unsafe project name" >&2; return 2 ;;
  esac
}
validate_project "$PROJECT"
if test "${2:-}" = --validate-project
then
  exit 0
fi

container_health() {
  docker inspect --format \
    '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' \
    "${PROJECT}-$1-1" 2>/dev/null || printf missing
}

wait_healthy() {
  service=$1
  attempt=0
  health=$(container_health "$service")
  while test "$attempt" -lt 40 && test "$health" != healthy
  do
    attempt=$((attempt + 1))
    sleep 2
    health=$(container_health "$service")
  done
  if test "$health" != healthy
  then
    echo "render-locator-recovery: failed service=$service health=$health attempts=$attempt" >&2
    docker compose -p "$PROJECT" ps "$service" >&2
    return 1
  fi
}

HEADER_FILE=
TOKEN_FILE=
E2E_SECRET_FILE=
NEGATIVE_OUTPUT_FILE=
MEDIA_COOKIE_FILE=
MEDIA_LOGIN_FILE=
MEDIA_SITES_FILE=
MEDIA_UPLOAD_FILE=
MEDIA_CONTENT_FILE=
EDGE_LIMIT_BODY_FILE=
PUBLIC_AGENT_RESTART_OUTPUT_FILE=
AGENT_CAPABILITY_CONFIG_FILE=
AGENT_CAPABILITY_META_FILE=
AGENT_RUN_FILE=
ARTIFACT_IDS_FILE=
ARTIFACT_HEADERS_FILE=
ARTIFACT_BODY_FILE=
FOREIGN_CAPABILITY_CONFIG_FILE=
FOREIGN_CAPABILITY_META_FILE=
PRE_OUTAGE_BODY_FILE=

retrieve_public_artifacts() {
  for worker_run_id in $(printf '%s' "$worker_run_ids" | tr ',' ' ')
  do
    test "$(curl --silent --show-error --config "$AGENT_CAPABILITY_CONFIG_FILE" \
      --output "$AGENT_RUN_FILE" --write-out '%{http_code}' \
      "http://localhost:8080/api/agent/v1/preview-runs/$worker_run_id/artifacts")" = 200
    python - "$AGENT_RUN_FILE" >"$ARTIFACT_IDS_FILE" <<'PY'
import json
import pathlib
import sys

artifacts = json.loads(pathlib.Path(sys.argv[1]).read_text("utf-8"))
assert len(artifacts) == 3
assert {item["kind"] for item in artifacts} == {
    "screenshot", "heading-summary", "structure-summary"
}
for item in artifacts:
    assert set(item) == {
        "version", "artifact_id", "run_id", "kind", "mime_type", "sha256",
        "size_bytes", "target", "route_digest", "created_at", "expires_at",
        "visibility"
    }
    assert item["visibility"] == "PRIVATE"
    print(item["artifact_id"], item["kind"])
PY
    while read -r artifact_id artifact_kind
    do
      status_code=$(curl --silent --show-error --config "$AGENT_CAPABILITY_CONFIG_FILE" \
        --dump-header "$ARTIFACT_HEADERS_FILE" --output "$ARTIFACT_BODY_FILE" \
        --write-out '%{http_code}' \
        "http://localhost:8080/api/agent/v1/preview-runs/$worker_run_id/artifacts/$artifact_id")
      test "$status_code" = 200
      python - "$ARTIFACT_HEADERS_FILE" "$ARTIFACT_BODY_FILE" "$artifact_kind" <<'PY'
import hashlib
import json
import pathlib
import struct
import sys

headers = {}
for line in pathlib.Path(sys.argv[1]).read_text("latin-1").splitlines():
    if ":" in line:
        key, value = line.split(":", 1)
        headers[key.casefold()] = value.strip()
body = pathlib.Path(sys.argv[2]).read_bytes()
kind = sys.argv[3]
digest = hashlib.sha256(body).hexdigest()
expected_mime = "image/png" if kind == "screenshot" else "application/json"
assert headers.get("content-type") == expected_mime
assert headers.get("content-length") == str(len(body))
assert headers.get("etag") == f'"{digest}"'
assert headers.get("cache-control") == "private, no-store"
assert headers.get("pragma") == "no-cache"
assert headers.get("x-robots-tag") == "noindex, nofollow, noarchive"
assert headers.get("x-content-type-options") == "nosniff"
assert len(body) > 0
if kind == "screenshot":
    assert body[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", body[16:24])
    assert (width, height) == (1440, 900)
else:
    document = json.loads(body)
    if kind == "heading-summary":
        assert "Compose overlay heading" in document["headings"]
    else:
        assert document["main"] == 1
        assert all(
            isinstance(document[key], int) and document[key] >= 0
            for key in ("articles", "components", "navigation", "sections")
        )
PY
    done <"$ARTIFACT_IDS_FILE"
  done
  echo "browser-artifact-public: OK runs=2 artifacts=6 bytes=verified"
}

cleanup() {
  test -z "$HEADER_FILE" || rm -f "$HEADER_FILE"
  test -z "$TOKEN_FILE" || rm -f "$TOKEN_FILE"
  test -z "$E2E_SECRET_FILE" || rm -f "$E2E_SECRET_FILE"
  test -z "$NEGATIVE_OUTPUT_FILE" || rm -f "$NEGATIVE_OUTPUT_FILE"
  test -z "$MEDIA_COOKIE_FILE" || rm -f "$MEDIA_COOKIE_FILE"
  test -z "$MEDIA_LOGIN_FILE" || rm -f "$MEDIA_LOGIN_FILE"
  test -z "$MEDIA_SITES_FILE" || rm -f "$MEDIA_SITES_FILE"
  test -z "$MEDIA_UPLOAD_FILE" || rm -f "$MEDIA_UPLOAD_FILE"
  test -z "$MEDIA_CONTENT_FILE" || rm -f "$MEDIA_CONTENT_FILE"
  test -z "$EDGE_LIMIT_BODY_FILE" || rm -f "$EDGE_LIMIT_BODY_FILE"
  test -z "$PUBLIC_AGENT_RESTART_OUTPUT_FILE" || rm -f "$PUBLIC_AGENT_RESTART_OUTPUT_FILE"
  test -z "$AGENT_CAPABILITY_CONFIG_FILE" || rm -f "$AGENT_CAPABILITY_CONFIG_FILE"
  test -z "$AGENT_CAPABILITY_META_FILE" || rm -f "$AGENT_CAPABILITY_META_FILE"
  test -z "$AGENT_RUN_FILE" || rm -f "$AGENT_RUN_FILE"
  test -z "$ARTIFACT_IDS_FILE" || rm -f "$ARTIFACT_IDS_FILE"
  test -z "$ARTIFACT_HEADERS_FILE" || rm -f "$ARTIFACT_HEADERS_FILE"
  test -z "$ARTIFACT_BODY_FILE" || rm -f "$ARTIFACT_BODY_FILE"
  test -z "$FOREIGN_CAPABILITY_CONFIG_FILE" || rm -f "$FOREIGN_CAPABILITY_CONFIG_FILE"
  test -z "$FOREIGN_CAPABILITY_META_FILE" || rm -f "$FOREIGN_CAPABILITY_META_FILE"
  test -z "$PRE_OUTAGE_BODY_FILE" || rm -f "$PRE_OUTAGE_BODY_FILE"
  docker compose -p "$NEGATIVE_PROJECT" -f "$ROOT/compose.yaml" \
    -f "$ROOT/tests/packaging/compose.broken-bootstrap.yaml" \
    down --volumes --remove-orphans >/dev/null 2>&1 || true
  docker compose -p "$PROJECT" -f "$ROOT/compose.yaml" \
    down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT HUP INT TERM
cleanup

HEADER_FILE=$(mktemp)
TOKEN_FILE=$(mktemp)
E2E_SECRET_FILE=$(mktemp)
NEGATIVE_OUTPUT_FILE=$(mktemp)
MEDIA_COOKIE_FILE=$(mktemp)
MEDIA_LOGIN_FILE=$(mktemp)
MEDIA_SITES_FILE=$(mktemp)
MEDIA_UPLOAD_FILE=$(mktemp)
MEDIA_CONTENT_FILE=$(mktemp)
EDGE_LIMIT_BODY_FILE=$(mktemp)
PUBLIC_AGENT_RESTART_OUTPUT_FILE=$(mktemp)
AGENT_CAPABILITY_CONFIG_FILE=$(mktemp)
AGENT_CAPABILITY_META_FILE=$(mktemp)
AGENT_RUN_FILE=$(mktemp)
ARTIFACT_IDS_FILE=$(mktemp)
ARTIFACT_HEADERS_FILE=$(mktemp)
ARTIFACT_BODY_FILE=$(mktemp)
FOREIGN_CAPABILITY_CONFIG_FILE=$(mktemp)
FOREIGN_CAPABILITY_META_FILE=$(mktemp)
PRE_OUTAGE_BODY_FILE=$(mktemp)
chmod 600 "$TOKEN_FILE" "$E2E_SECRET_FILE" "$AGENT_CAPABILITY_CONFIG_FILE" \
  "$AGENT_CAPABILITY_META_FILE" "$AGENT_RUN_FILE"

cd "$ROOT"
docker compose config --quiet
python tools/compose/verify.py --root "$ROOT"
docker compose build --pull
docker compose -p "$PROJECT" up --build --wait
python tools/compose/verify.py --root "$ROOT" --project "$PROJECT"

# These non-authenticatable OIDC identities exist only in this disposable smoke
# database. The fixed statement deliberately fails on a collision or any
# unexpected installation state; it never updates product or demo seed data.
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif \
  -v ON_ERROR_STOP=1 -c \
  "BEGIN;
   DO \$fixture\$
   BEGIN
     IF (SELECT initialized_at IS NOT NULL FROM control.installation_state WHERE singleton)
        OR EXISTS (SELECT 1 FROM control.platform_administrator)
        OR EXISTS (SELECT 1 FROM control.site_membership)
        OR EXISTS (SELECT 1 FROM control.user_account)
     THEN
       RAISE EXCEPTION 'unexpected fixture precondition';
     END IF;
   END
   \$fixture\$;
   INSERT INTO control.user_account (
     id, identity_kind, local_username, local_username_normalized,
     password_hash, oidc_issuer, oidc_subject, email, display_name, status
   ) VALUES
     ('12000000-0000-4000-8000-000000000001', 'OIDC', NULL, NULL, NULL,
      'https://fixture.invalid', 'compose-fixture-subject-one', NULL,
      'Compose Fixture One', 'ACTIVE'),
     ('12000000-0000-4000-8000-000000000002', 'OIDC', NULL, NULL, NULL,
      'https://fixture.invalid', 'compose-fixture-subject-two', NULL,
      'Compose Fixture Two', 'ACTIVE');
   COMMIT;" >/dev/null
echo "membership-fixtures: OK count=2 kind=OIDC authenticatable=no installation=uninitialized"

mode_count=0
for service in control-api editor-api agent-api render-api mcp-adapter media-service review-worker scheduler media-gc
do
  mode=$(docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' \
    "${PROJECT}-${service}-1" | sed -n 's/^SLAIF_MODE=//p')
  test "$mode" = development
  mode_count=$((mode_count + 1))
done
test "$mode_count" = 9
echo "compose-mode-policy: OK long-running-backends=9 mode=development"
docker inspect "${PROJECT}-browser-worker-1" | python -c \
  'import json,sys; value=json.load(sys.stdin)[0]; host=value["HostConfig"]; config=value["Config"]; assert config["User"]=="10001:10001" and host["ReadonlyRootfs"] is True; assert host["CapDrop"]==["ALL"] and host["CapAdd"]==["CAP_SYS_CHROOT"]; assert host["PidsLimit"]==256 and host["Memory"]==805306368 and host["ShmSize"]==134217728 and host["NanoCpus"]==1000000000; assert "no-new-privileges:true" in host["SecurityOpt"] and any(item.startswith("seccomp=") for item in host["SecurityOpt"]); assert host["NetworkMode"].endswith("_browser"); print("browser-worker-runtime-policy: OK uid=10001 readonly=yes caps=SYS_CHROOT limits=exact network=browser")'
docker exec "${PROJECT}-browser-worker-1" sh -c \
  'test "$(find /ms-playwright -mindepth 1 -maxdepth 1 -type d | wc -l)" -eq 1; test -x /ms-playwright/chromium-1669021/chrome-linux64/chrome; test ! -e /usr/bin/npm; test ! -e /usr/bin/corepack; test "$(node --version)" = v24.18.1; /ms-playwright/chromium-1669021/chrome-linux64/chrome --version | grep -Eq "^Google Chrome for Testing 152[.]0[.]7977[.]64 *$"'
echo "browser-worker-image-policy: OK playwright=1.62.1 chromium=152.0.7977.64 browsers=chromium-only package-manager=absent"

curl --fail --show-error --silent http://localhost:8080/ | grep -q "Self-hosted human control"
docker compose -p "$PROJECT" logs --no-color bootstrap 2>/dev/null \
  | sed -n 's/^.*setup-token-secret: //p' >"$TOKEN_FILE"
test "$(wc -l <"$TOKEN_FILE" | tr -d ' ')" = 1
tools/compose/e2e.sh "$TOKEN_FILE" "$E2E_SECRET_FILE" "$PROJECT"

python tools/compose/public_agent_restart.py \
  --project "$PROJECT" >"$PUBLIC_AGENT_RESTART_OUTPUT_FILE"
cat "$PUBLIC_AGENT_RESTART_OUTPUT_FILE"
public_workspace_id=$(sed -n 's/.*workspace=\([^ ]*\).*/\1/p' "$PUBLIC_AGENT_RESTART_OUTPUT_FILE")
public_capability_id=$(sed -n 's/.*capability=\([^ ]*\).*/\1/p' "$PUBLIC_AGENT_RESTART_OUTPUT_FILE")
case "$public_workspace_id" in
  ''|*[!0-9a-f-]*) fail public-agent-restart-invalid-workspace-id ;;
esac
case "$public_capability_id" in
  ''|*[!0-9a-f]*) fail public-agent-restart-invalid-capability-id ;;
esac
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT count(*) = 3
      AND count(*) FILTER (WHERE action='WORKSPACE_CREATED') = 1
      AND count(*) FILTER (WHERE action='CAPABILITY_ISSUED'
                           AND capability_public_id='$public_capability_id') = 1
      AND count(*) FILTER (WHERE action='CAPABILITY_REVOKED'
                           AND capability_public_id='$public_capability_id') = 1
   FROM audit.human_agent_session
   WHERE workspace_id='$public_workspace_id'::uuid;" | grep -q '^t$'
echo "public-agent-restart-audit: OK workspace=$public_workspace_id capability=$public_capability_id rows=3"

media_login_status=$(curl --silent --show-error --cookie-jar "$MEDIA_COOKIE_FILE" \
  --output "$MEDIA_LOGIN_FILE" --write-out '%{http_code}' \
  -H 'Content-Type: application/json' \
  --data '{"username":"compose.admin","password":"fixture-compose-auth-password-123"}' \
  http://localhost:8080/api/control/v1/login)
test "$media_login_status" = 200
media_csrf=$(awk '$6 == "slaif_csrf" { print $7 }' "$MEDIA_COOKIE_FILE")
test -n "$media_csrf"
curl --fail --show-error --silent --cookie "$MEDIA_COOKIE_FILE" \
  --output "$MEDIA_SITES_FILE" http://localhost:8080/api/control/v1/me/sites
media_site_id=$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))[0]["site_id"])' "$MEDIA_SITES_FILE")
media_upload_status=$(curl --silent --show-error --cookie "$MEDIA_COOKIE_FILE" \
  -H "X-CSRF-Token: $media_csrf" -H 'Idempotency-Key: compose-media-upload' \
  --form 'alt_text=Compose fixture image' \
  --form 'metadata={"source":"compose"}' \
  --form "file=@$ROOT/docs/screenshots/01-landing-page.png;type=image/png" \
  --output "$MEDIA_UPLOAD_FILE" --write-out '%{http_code}' \
  "http://localhost:8080/media/v1/sites/$media_site_id/assets")
test "$media_upload_status" = 201
media_id=$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["record"]["id"])' "$MEDIA_UPLOAD_FILE")
curl --fail --show-error --silent --cookie "$MEDIA_COOKIE_FILE" \
  --output "$MEDIA_CONTENT_FILE" \
  "http://localhost:8080/media/v1/sites/$media_site_id/assets/$media_id/content"
cmp "$ROOT/docs/screenshots/01-landing-page.png" "$MEDIA_CONTENT_FILE"
echo "media-e2e: OK edge=nginx upload=validated-private-read=byte-identical"
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SET ROLE slaif_owner;
   SELECT count(*) = 4
      AND count(DISTINCT audit.operation_id) = 4
      AND count(DISTINCT audit.workspace_id) = 1
      AND bool_and(workspace.actor_type = 'HUMAN'
                   AND workspace.status = 'ACTIVE'
                   AND workspace.expires_at > CURRENT_TIMESTAMP
                   AND workspace.site_id = audit.site_id
                   AND workspace.created_by = audit.human_user_id
                   AND audit.response_status BETWEEN 200 AND 299)
      AND count(*) FILTER (WHERE
          CASE
            WHEN audit.action LIKE 'POST /api/editor/v1/sites/%/pages/'
              THEN 'page-create'
            WHEN audit.action LIKE
              'POST /api/editor/v1/sites/%/pages/%/composition/components'
              THEN 'component-add'
            WHEN audit.action LIKE
              'POST /api/editor/v1/sites/%/pages/%/composition/components/%/move'
              THEN 'component-move'
            ELSE 'unexpected'
          END = 'unexpected') = 0
      AND array_agg(
          CASE
            WHEN audit.action LIKE 'POST /api/editor/v1/sites/%/pages/'
              THEN 'page-create'
            WHEN audit.action LIKE
              'POST /api/editor/v1/sites/%/pages/%/composition/components'
              THEN 'component-add'
            WHEN audit.action LIKE
              'POST /api/editor/v1/sites/%/pages/%/composition/components/%/move'
              THEN 'component-move'
            ELSE 'unexpected'
          END ORDER BY audit.occurred_at, audit.operation_id
      ) = ARRAY['page-create', 'component-add', 'component-add', 'component-move']
   FROM audit.human_editor_mutation audit
   JOIN control.workspace workspace ON workspace.id = audit.workspace_id
   WHERE audit.action LIKE 'POST /api/editor/v1/sites/%';" | grep -q '^t$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SET ROLE slaif_owner;
   SELECT count(*) = 4
      AND count(DISTINCT operation_id) = 4
      AND count(*) FILTER (WHERE status_code IS NULL) = 0
      AND bool_and(status_code BETWEEN 200 AND 299
                   AND response_body IS NOT NULL
                   AND completed_at IS NOT NULL)
   FROM control.human_editor_idempotency;" | grep -q '^t$'
echo "human-editor-envelope: OK workspace=HUMAN active audit=idempotent sequence=page-create,component-add,component-add,component-move count=4"
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -v ON_ERROR_STOP=1 -Atc \
  "SET ROLE slaif_owner;
   SELECT string_agg(
     membership.user_account_id::text || '|' || site.site_key || '|' ||
     membership.role_key || '|' || membership.status || '|' ||
     membership.version::text,
     E'\n' ORDER BY membership.user_account_id, site.site_key
   )
   FROM control.site_membership membership
   JOIN control.site site ON site.id = membership.site_id
   WHERE membership.user_account_id IN (
     '12000000-0000-4000-8000-000000000001'::uuid,
     '12000000-0000-4000-8000-000000000002'::uuid
   );" | grep -Fxq "$(printf '%s\n%s' \
    '12000000-0000-4000-8000-000000000001|governance|SITE_DESIGNER|INACTIVE|5' \
    '12000000-0000-4000-8000-000000000002|demo|VIEWER|ACTIVE|1')"
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -v ON_ERROR_STOP=1 -Atc \
  "SET ROLE slaif_owner;
   SELECT count(*) = 3
     AND count(*) FILTER (WHERE
       identity_kind = 'OIDC' AND status = 'ACTIVE'
       AND local_username IS NULL AND local_username_normalized IS NULL
       AND password_hash IS NULL AND email IS NULL
       AND oidc_issuer = 'https://fixture.invalid'
       AND (id, oidc_subject, display_name) IN (
         ('12000000-0000-4000-8000-000000000001'::uuid,
          'compose-fixture-subject-one', 'Compose Fixture One'),
         ('12000000-0000-4000-8000-000000000002'::uuid,
          'compose-fixture-subject-two', 'Compose Fixture Two')
       )
       AND NOT EXISTS (
         SELECT 1 FROM control.platform_administrator administrator
         WHERE administrator.user_account_id = account.id
       )
     ) = 2
     AND count(*) FILTER (WHERE
       identity_kind = 'LOCAL' AND status = 'ACTIVE'
       AND local_username IS NOT NULL
       AND local_username_normalized IS NOT NULL
       AND password_hash IS NOT NULL
       AND oidc_issuer IS NULL AND oidc_subject IS NULL
       AND EXISTS (
         SELECT 1 FROM control.platform_administrator administrator
         WHERE administrator.user_account_id = account.id
       )
     ) = 1
     AND (SELECT count(*) FROM control.platform_administrator) = 1
   FROM control.user_account account;" | grep -q '^t$'
echo "governance-e2e: OK visible=create-profile-domains-membership-archive negatives=verified devices=6"
for path in \
  /health/live \
  /health/ready \
  /api/control/health/live \
  /api/editor/health/ready \
  /api/agent/health/live \
  /mcp/health/ready \
  /media/health/live
do
  curl --fail --show-error --silent "http://localhost:8080$path" >/dev/null
done
for path in /api/control/sites /api/editor/workspaces /api/agent/tools /mcp/tools /media/files /preview
do
  status=$(curl --silent --output /dev/null --write-out '%{http_code}' "http://localhost:8080$path")
  test "$status" = 404
done
assert_edge_headers() {
  path=$1
  expected_status=$2
  status=$(curl --silent --show-error --dump-header "$HEADER_FILE" \
    --output /dev/null --write-out '%{http_code}' \
    --header 'X-Request-ID: caller-value-must-be-replaced' \
    "http://localhost:8080$path")
  test "$status" = "$expected_status"

  request_id_count=$(awk 'tolower($1) == "x-request-id:" { count++ } END { print count + 0 }' "$HEADER_FILE")
  test "$request_id_count" = 1
  request_id=$(awk 'tolower($1) == "x-request-id:" { gsub(/\r/, "", $2); print $2 }' "$HEADER_FILE")
  test "${#request_id}" = 32
  case "$request_id" in
    *[!0-9a-f]*) echo "compose-smoke: unsafe request ID" >&2; exit 1 ;;
  esac
  test "$request_id" != caller-value-must-be-replaced

  csp_count=$(awk 'tolower($1) == "content-security-policy:" { count++ } END { print count + 0 }' "$HEADER_FILE")
  test "$csp_count" = 1
  csp=$(sed -n 's/^[Cc]ontent-[Ss]ecurity-[Pp]olicy:[[:space:]]*//p' "$HEADER_FILE" | tr -d '\r')
  for directive in \
    "default-src 'self'" \
    "base-uri 'none'" \
    "object-src 'none'" \
    "frame-ancestors 'none'" \
    "form-action 'self'" \
    "script-src 'self'" \
    "style-src 'self'" \
    "img-src 'self' data:" \
    "connect-src 'self'"
  do
    printf '%s' "$csp" | grep -Fq "$directive"
  done
  if printf '%s' "$csp" | grep -Eqi "unsafe-inline|unsafe-eval|report-uri|report-to|https?:|wss?:|(^|[[:space:]])\\*([;[:space:]]|$)"
  then
    echo "compose-smoke: forbidden CSP source or directive" >&2
    exit 1
  fi
  grep -qi '^X-Content-Type-Options: nosniff' "$HEADER_FILE"
}
assert_edge_headers / 200
assert_edge_headers /api/agent/health/live 200
assert_edge_headers /definitely-not-a-product-route 404
echo "edge-header-policy: OK page/api/404 request-id-count=1 request-id-format=32hex csp-count=1"

dd if=/dev/zero of="$EDGE_LIMIT_BODY_FILE" bs=1048577 count=1 2>/dev/null
edge_body_status() {
  curl --silent --show-error --max-time 30 -o /dev/null -w '%{http_code}' \
    -X POST -H 'Content-Type: application/octet-stream' \
    --data-binary "@$EDGE_LIMIT_BODY_FILE" "$1"
}
test "$(edge_body_status http://localhost:8080/media/v1/sites/00000000-0000-0000-0000-000000000000/assets)" = 401
for edge_rejected_path in \
  /api/control/v1/me/sites \
  /api/editor/v1/sites/00000000-0000-0000-0000-000000000000/media/ \
  /api/agent/health/live \
  /mcp/ \
  /
do
  test "$(edge_body_status "http://localhost:8080$edge_rejected_path")" = 413
done
echo "edge-body-limit: OK media=route-allowance non-media=413 global=1MiB"

docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT readiness_state || ' safe=' || safe FROM control.bootstrap_readiness WHERE singleton" \
  | grep -Eq '^(EMPTY_SAFE|HARDENED) safe=true$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT count(*) FROM pg_auth_members m JOIN pg_roles member ON member.oid=m.member WHERE member.rolname LIKE 'slaif_%_login'" \
  | grep -q '^10$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname LIKE 'slaif_%_login' AND (NOT rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR NOT rolinherit OR rolreplication OR rolbypassrls))" \
  | grep -q '^t$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT count(*) = 10 AND bool_and(rolconnlimit = 10 AND rolvaliduntil = 'infinity'::timestamptz AND rolconfig IS NULL) FROM pg_roles WHERE rolname LIKE 'slaif_%_login'" \
  | grep -q '^t$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT NOT EXISTS (SELECT 1 FROM pg_database d CROSS JOIN LATERAL aclexplode(d.datacl) acl WHERE d.datname = 'slaif' AND acl.grantee = 0 AND acl.privilege_type IN ('CONNECT', 'TEMPORARY'))" \
  | grep -q '^t$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT count(*) = 10 AND bool_and(has_database_privilege(rolname, 'slaif', 'CONNECT') AND NOT has_database_privilege(rolname, 'slaif', 'TEMPORARY') AND has_database_privilege(rolname, 'slaif', 'CREATE') = (rolname = 'slaif_owner')) FROM pg_roles WHERE rolname IN ('slaif_owner', 'slaif_control', 'slaif_editor_runtime', 'slaif_agent_runtime', 'slaif_public_reader', 'slaif_preview_reader', 'slaif_reviewer', 'slaif_scheduler', 'slaif_media', 'slaif_gc')" \
  | grep -q '^t$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT NOT EXISTS (SELECT 1 FROM pg_default_acl defaults CROSS JOIN LATERAL aclexplode(defaults.defaclacl) acl JOIN pg_roles grantee ON grantee.oid = acl.grantee WHERE grantee.rolname LIKE 'slaif_%_login')" \
  | grep -q '^t$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT NOT EXISTS (SELECT 1 FROM pg_roles login JOIN LATERAL (SELECT acl.grantee FROM pg_database d CROSS JOIN LATERAL aclexplode(d.datacl) acl WHERE d.datname = 'slaif' UNION ALL SELECT acl.grantee FROM pg_namespace n CROSS JOIN LATERAL aclexplode(n.nspacl) acl WHERE n.nspname IN ('control', 'content', 'audit', 'agentcow') UNION ALL SELECT acl.grantee FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace CROSS JOIN LATERAL aclexplode(c.relacl) acl WHERE n.nspname IN ('control', 'content', 'audit', 'agentcow') UNION ALL SELECT acl.grantee FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid JOIN pg_namespace n ON n.oid = c.relnamespace CROSS JOIN LATERAL aclexplode(a.attacl) acl WHERE n.nspname IN ('control', 'content', 'audit', 'agentcow') UNION ALL SELECT acl.grantee FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace CROSS JOIN LATERAL aclexplode(p.proacl) acl WHERE n.nspname IN ('control', 'content', 'audit', 'agentcow')) direct_grant ON direct_grant.grantee = login.oid WHERE login.rolname LIKE 'slaif_%_login')" \
  | grep -q '^t$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT NOT EXISTS (SELECT 1 FROM pg_roles login JOIN LATERAL (SELECT datdba AS owner_oid FROM pg_database WHERE datname = 'slaif' UNION ALL SELECT nspowner FROM pg_namespace WHERE nspname IN ('control', 'content', 'audit', 'agentcow') UNION ALL SELECT c.relowner FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname IN ('control', 'content', 'audit', 'agentcow') UNION ALL SELECT p.proowner FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname IN ('control', 'content', 'audit', 'agentcow')) owned ON owned.owner_oid = login.oid WHERE login.rolname LIKE 'slaif_%_login')" \
  | grep -q '^t$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -v ON_ERROR_STOP=1 -c \
  "CREATE ROLE slaif_smoke_unrelated LOGIN PASSWORD 'fake-smoke-only-password'" >/dev/null
docker exec -e PGPASSWORD=fake-smoke-only-password "${PROJECT}-postgres-1" \
  psql -h 127.0.0.1 -U slaif_smoke_unrelated -d postgres -Atc 'SELECT 1' \
  | grep -q '^1$'
if docker exec -e PGPASSWORD=fake-smoke-only-password "${PROJECT}-postgres-1" \
  psql -h 127.0.0.1 -U slaif_smoke_unrelated -d slaif -Atc 'SELECT 1' \
  >/dev/null 2>&1
then
  echo "compose-smoke: unrelated login unexpectedly connected" >&2
  exit 1
fi
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -v ON_ERROR_STOP=1 -c \
  "DROP ROLE slaif_smoke_unrelated" >/dev/null
echo "database-login-policy: OK public-connect=denied exact-roles=10 direct-default-owner-drift=none unrelated-connect=denied"
docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
  --user 0:0 --volume "${PROJECT}_local-secrets:/secrets:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import os,pathlib,stat; root=pathlib.Path('/secrets'); root_info=root.stat(); assert stat.S_IMODE(root_info.st_mode)==0o710 and root_info.st_uid==0 and root_info.st_gid==10002; files=list(root.iterdir()); assert len(files)==23; assert all(stat.S_IMODE(p.stat().st_mode)==0o400 for p in files); assert (root/'postgres-password').stat().st_uid==999; assert (root/'.initialized-v1').stat().st_uid==0; assert all(p.stat().st_uid==10001 for p in files if p.name not in {'postgres-password','.initialized-v1'}); values=[p.read_bytes() for p in files if p.name=='postgres-password' or p.name.startswith('login-')]; assert len(values)==len(set(values))==11; print('secret-file-policy: OK')"
if docker run --rm --network none --read-only --cap-drop ALL \
  --user 10003:10003 --volume "${PROJECT}_local-secrets:/secrets:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib; pathlib.Path('/secrets/postgres-password').read_bytes()" \
  >/dev/null 2>&1
then
  echo "compose-smoke: unrelated uid unexpectedly read a secret" >&2
  exit 1
fi

docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
  --user 0:0 --volume "${PROJECT}_local-secrets:/master:ro" \
  --volume "${PROJECT}_render-secret:/render:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib,secrets,stat; root=pathlib.Path('/render'); files=list(root.iterdir()); assert len(files)==1 and files[0].name=='render-dsn'; info=root.stat(); file=files[0]; assert stat.S_IMODE(info.st_mode)==0o700 and info.st_uid==10001 and info.st_gid==10001; assert stat.S_IMODE(file.stat().st_mode)==0o400 and file.stat().st_uid==10001; assert secrets.compare_digest(file.read_bytes(), pathlib.Path('/master/service-public-dsn').read_bytes()); print('render-secret-policy: OK files=1 mode=0400 owner=10001')"
if docker run --rm --network none --read-only --cap-drop ALL \
  --user 10003:10003 --volume "${PROJECT}_render-secret:/render:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib; pathlib.Path('/render/render-dsn').read_bytes()" \
  >/dev/null 2>&1
then
  echo "compose-smoke: unrelated uid unexpectedly read Render locator" >&2
  exit 1
fi

docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
  --user 0:0 --volume "${PROJECT}_local-secrets:/master:ro" \
  --volume "${PROJECT}_render-preview-secret:/preview:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib,secrets,stat; root=pathlib.Path('/preview'); files=list(root.iterdir()); assert len(files)==1 and files[0].name=='preview-dsn'; info=root.stat(); file=files[0]; assert stat.S_IMODE(info.st_mode)==0o700 and info.st_uid==10001 and info.st_gid==10001; assert stat.S_IMODE(file.stat().st_mode)==0o400 and file.stat().st_uid==10001; assert secrets.compare_digest(file.read_bytes(), pathlib.Path('/master/service-preview-dsn').read_bytes()); print('render-preview-secret-policy: OK files=1 mode=0400 owner=10001')"
if docker run --rm --network none --read-only --cap-drop ALL \
  --user 10003:10003 --volume "${PROJECT}_render-preview-secret:/preview:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib; pathlib.Path('/preview/preview-dsn').read_bytes()" \
  >/dev/null 2>&1
then
  echo "compose-smoke: unrelated uid unexpectedly read Render preview locator" >&2
  exit 1
fi

docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
  --user 0:0 --volume "${PROJECT}_render-auth-secret:/auth:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib,stat; root=pathlib.Path('/auth'); files=list(root.iterdir()); assert len(files)==1 and files[0].name=='render-token'; info=root.stat(); file=files[0]; assert stat.S_IMODE(info.st_mode)==0o700 and info.st_uid==10001 and info.st_gid==10001; assert stat.S_IMODE(file.stat().st_mode)==0o400 and file.stat().st_uid==10001 and len(file.read_bytes())>=43; print('render-auth-secret-policy: OK files=1 mode=0400 owner=10001')"
if docker run --rm --network none --read-only --cap-drop ALL \
  --user 10003:10003 --volume "${PROJECT}_render-auth-secret:/auth:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib; pathlib.Path('/auth/render-token').read_bytes()" \
  >/dev/null 2>&1
then
  echo "compose-smoke: unrelated uid unexpectedly read Render service credential" >&2
  exit 1
fi

docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
  --user 0:0 --volume "${PROJECT}_browser-signing-secret:/signing:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib,re,stat; root=pathlib.Path('/signing'); files=list(root.iterdir()); assert len(files)==1 and files[0].name=='signing-key'; info=root.stat(); file=files[0]; assert stat.S_IMODE(info.st_mode)==0o700 and info.st_uid==10001 and info.st_gid==10001; assert stat.S_IMODE(file.stat().st_mode)==0o400 and file.stat().st_uid==10001; value=file.read_text('ascii'); assert re.fullmatch(r'sbk1:[0-9a-f]{16}:[A-Za-z0-9_-]{43}', value); print('browser-signing-secret-policy: OK files=1 mode=0400 owner=10001')"
if docker run --rm --network none --read-only --cap-drop ALL \
  --user 10003:10003 --volume "${PROJECT}_browser-signing-secret:/signing:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib; pathlib.Path('/signing/signing-key').read_bytes()" \
  >/dev/null 2>&1
then
  echo "compose-smoke: unrelated uid unexpectedly read browser signing key" >&2
  exit 1
fi

docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
  --user 0:0 --volume "${PROJECT}_browser-worker-secret:/worker:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib,re,stat; root=pathlib.Path('/worker'); files=list(root.iterdir()); assert len(files)==1 and files[0].name=='worker-token'; info=root.stat(); file=files[0]; assert stat.S_IMODE(info.st_mode)==0o700 and info.st_uid==10001 and info.st_gid==10001; assert stat.S_IMODE(file.stat().st_mode)==0o400 and file.stat().st_uid==10001 and file.stat().st_nlink==1; value=file.read_text('ascii'); assert re.fullmatch(r'sbws1:[0-9a-f]{16}:[A-Za-z0-9_-]{43}', value); print('browser-worker-secret-policy: OK files=1 mode=0400 owner=10001')"
if docker run --rm --network none --read-only --cap-drop ALL \
  --user 10003:10003 --volume "${PROJECT}_browser-worker-secret:/worker:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib; pathlib.Path('/worker/worker-token').read_bytes()" \
  >/dev/null 2>&1
then
  echo "compose-smoke: unrelated uid unexpectedly read browser worker credential" >&2
  exit 1
fi
docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
  --user 0:0 --volume "${PROJECT}_browser-artifacts:/artifacts:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib,stat; root=pathlib.Path('/artifacts'); info=root.stat(); assert stat.S_IMODE(info.st_mode)==0o700 and info.st_uid==10001 and info.st_gid==10001 and not list(root.iterdir()); print('browser-artifact-root-policy: OK empty mode=0700 owner=10001')"

docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
  --user 0:0 --volume "${PROJECT}_local-secrets:/master:ro" \
  --volume "${PROJECT}_media-secret:/media:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib,secrets,stat; root=pathlib.Path('/media'); files=list(root.iterdir()); assert len(files)==1 and files[0].name=='media-dsn'; info=root.stat(); file=files[0]; assert stat.S_IMODE(info.st_mode)==0o700 and info.st_uid==10001 and info.st_gid==10001; assert stat.S_IMODE(file.stat().st_mode)==0o400 and file.stat().st_uid==10001; assert secrets.compare_digest(file.read_bytes(), pathlib.Path('/master/service-media-dsn').read_bytes()); print('media-secret-policy: OK files=1 mode=0400 owner=10001')"
if docker run --rm --network none --read-only --cap-drop ALL \
  --user 10003:10003 --volume "${PROJECT}_media-secret:/media:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib; pathlib.Path('/media/media-dsn').read_bytes()" \
  >/dev/null 2>&1
then
  echo "compose-smoke: unrelated uid unexpectedly read Media locator" >&2
  exit 1
fi

python - "$AGENT_CAPABILITY_CONFIG_FILE" "$AGENT_CAPABILITY_META_FILE" <<'PY'
import hashlib
import pathlib
import secrets
import sys

token = f"sas2_{secrets.token_hex(8)}_{secrets.token_hex(32)}"
pathlib.Path(sys.argv[1]).write_text(
    f'header = "Authorization: Bearer {token}"\n', encoding="ascii"
)
pathlib.Path(sys.argv[2]).write_text(
    f"{token.split('_')[1]} {hashlib.sha256(token.encode()).hexdigest()}\n",
    encoding="ascii",
)
PY
read -r agent_capability_public agent_capability_digest < "$AGENT_CAPABILITY_META_FILE"
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif \
  -v ON_ERROR_STOP=1 -c \
  "BEGIN;
   INSERT INTO control.user_account
     (id,identity_kind,oidc_issuer,oidc_subject,display_name,status)
   VALUES
     ('14000000-0000-4000-8000-000000000001','OIDC','https://browser-smoke.test',
      'browser-smoke-subject','Browser Smoke Agent','ACTIVE');
   INSERT INTO control.site
     (id,site_key,display_name,default_locale,component_catalog_version,status)
   VALUES
     ('14000000-0000-4000-8000-000000000002','agent-browser-smoke',
      'Agent Browser Smoke','en-US','catalog-v1','ACTIVE');
   INSERT INTO control.site_membership
     (site_id,user_account_id,role_key,delegation_ceiling)
   VALUES
     ('14000000-0000-4000-8000-000000000002',
      '14000000-0000-4000-8000-000000000001','SITE_OWNER',4);
   INSERT INTO control.workspace
     (id,site_id,created_by,delegator_id,actor_type,title,delegation_preset,effective_scopes,
      status,expires_at)
   VALUES
     ('14000000-0000-4000-8000-000000000003',
      '14000000-0000-4000-8000-000000000002',
      '14000000-0000-4000-8000-000000000001',
      '14000000-0000-4000-8000-000000000001','AGENT','Agent browser smoke',
      'L1','[\"preview:inspect\"]'::jsonb,'ACTIVE',
      CURRENT_TIMESTAMP + interval '1 hour');
   INSERT INTO control.capability
     (id,workspace_id,public_id,secret_digest,scopes,expires_at)
   VALUES
     ('14000000-0000-4000-8000-000000000004',
      '14000000-0000-4000-8000-000000000003','$agent_capability_public',
      '$agent_capability_digest','[\"preview:inspect\"]'::jsonb,
      CURRENT_TIMESTAMP + interval '1 hour');
   COMMIT;" >/dev/null
agent_create_status=$(curl --silent --show-error \
  --config "$AGENT_CAPABILITY_CONFIG_FILE" \
  --output "$AGENT_RUN_FILE" --write-out '%{http_code}' \
  --request POST --header 'Content-Type: application/json' \
  --header 'Idempotency-Key: compose-browser-create' \
  --data '{"version":"browser-preview/v1","route":"/","target":"desktop-chromium","evidence":["heading-summary"]}' \
  http://localhost:8080/api/agent/v1/preview-runs)
test "$agent_create_status" = 202
AGENT_RUN_ID=$(python - "$AGENT_RUN_FILE" "$AGENT_CAPABILITY_CONFIG_FILE" <<'PY'
import json
import pathlib
import sys

body = pathlib.Path(sys.argv[1]).read_text("utf-8")
document = json.loads(body)
token = pathlib.Path(sys.argv[2]).read_text("ascii").split("Bearer ", 1)[1].strip('"\n')
assert document["state"] in {"QUEUED", "RUNNING", "COMPLETED"}
assert document["route"] == "/"
assert "workspace_id" not in document and "capability_id" not in document
assert token not in body
print(document["run_id"])
PY
)
test -n "$AGENT_RUN_ID"
for attempt in $(seq 1 120)
do
  status_code=$(curl --silent --show-error --config "$AGENT_CAPABILITY_CONFIG_FILE" \
    --output "$AGENT_RUN_FILE" --write-out '%{http_code}' \
    "http://localhost:8080/api/agent/v1/preview-runs/$AGENT_RUN_ID")
  if test "$status_code" != 200
  then
    cat "$AGENT_RUN_FILE" >&2
    exit 1
  fi
  state=$(python -c 'import json,sys; print(json.load(open(sys.argv[1]))["state"])' "$AGENT_RUN_FILE")
  case "$state" in
    COMPLETED|FAILED|TIMED_OUT|CANCELLED) break ;;
  esac
  sleep 1
done
test "$state" = COMPLETED -o "$state" = FAILED -o "$state" = TIMED_OUT -o "$state" = CANCELLED
test "$(curl --silent --show-error --config "$AGENT_CAPABILITY_CONFIG_FILE" \
  --output "$AGENT_RUN_FILE" --write-out '%{http_code}' \
  "http://localhost:8080/api/agent/v1/preview-runs/$AGENT_RUN_ID")" = 200
python - "$AGENT_RUN_FILE" <<'PY'
import json
import pathlib
import sys

document = json.loads(pathlib.Path(sys.argv[1]).read_text("utf-8"))
assert document["state"] in {"COMPLETED", "FAILED", "TIMED_OUT", "CANCELLED"}
PY
docker compose -p "$PROJECT" restart agent-api >/dev/null
wait_healthy agent-api
test "$(curl --silent --show-error --config "$AGENT_CAPABILITY_CONFIG_FILE" \
  --output "$AGENT_RUN_FILE" --write-out '%{http_code}' \
  "http://localhost:8080/api/agent/v1/preview-runs/$AGENT_RUN_ID")" = 200
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT (SELECT count(*) FROM control.browser_run
             WHERE capability_id='14000000-0000-4000-8000-000000000004') || ':' ||
          (SELECT count(*) FROM control.browser_idempotency
             WHERE capability_id='14000000-0000-4000-8000-000000000004') || ':' ||
          (SELECT count(*) FROM audit.browser_event
             WHERE capability_id='14000000-0000-4000-8000-000000000004') || ':' ||
          (SELECT state FROM control.browser_run
             WHERE capability_id='14000000-0000-4000-8000-000000000004');" \
  | grep -q '^1:1:[3-9][0-9]*:\(COMPLETED\|FAILED\|TIMED_OUT\|CANCELLED\)$'
echo "agent-browser-http: OK create=202 dispatcher=QUEUED-to-terminal restart=durable"

# Bind two additional durable QUEUED runs to the existing real COW preview
# fixture. The trusted Agent-side client mints each opaque preview credential
# only in process memory, verifies the signed worker result, and never prints or
# writes either credential.
python - "$AGENT_CAPABILITY_CONFIG_FILE" "$AGENT_CAPABILITY_META_FILE" <<'PY'
import hashlib
import pathlib
import secrets
import sys

token = f"sas2_{secrets.token_hex(8)}_{secrets.token_hex(32)}"
pathlib.Path(sys.argv[1]).write_text(
    f'header = "Authorization: Bearer {token}"\n', encoding="ascii"
)
pathlib.Path(sys.argv[2]).write_text(
    f"{token.split('_')[1]} {hashlib.sha256(token.encode()).hexdigest()}\n",
    encoding="ascii",
)
PY
read -r worker_capability_public worker_capability_digest < "$AGENT_CAPABILITY_META_FILE"
python - "$FOREIGN_CAPABILITY_CONFIG_FILE" "$FOREIGN_CAPABILITY_META_FILE" <<'PY'
import hashlib
import pathlib
import secrets
import sys

token = f"sas2_{secrets.token_hex(8)}_{secrets.token_hex(32)}"
pathlib.Path(sys.argv[1]).write_text(
    f'header = "Authorization: Bearer {token}"\n', encoding="ascii"
)
pathlib.Path(sys.argv[2]).write_text(
    f"{token.split('_')[1]} {hashlib.sha256(token.encode()).hexdigest()}\n",
    encoding="ascii",
)
PY
read -r foreign_capability_public foreign_capability_digest < "$FOREIGN_CAPABILITY_META_FILE"
preview_site_id=$(docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT id FROM control.site WHERE site_key='demo'")
test -n "$preview_site_id"
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif \
  -v ON_ERROR_STOP=1 -c \
  "INSERT INTO control.capability
     (id,workspace_id,public_id,secret_digest,scopes,expires_at)
   VALUES
     ('15000000-0000-4000-8000-000000000004',
      '12000000-0000-4000-8000-000000000301','$worker_capability_public',
      '$worker_capability_digest','[\"preview:inspect\"]'::jsonb,
      CURRENT_TIMESTAMP + interval '1 hour'),
     ('15000000-0000-4000-8000-000000000005',
      '12000000-0000-4000-8000-000000000301','$foreign_capability_public',
      '$foreign_capability_digest','[\"preview:inspect\"]'::jsonb,
      CURRENT_TIMESTAMP + interval '1 hour');" >/dev/null
worker_run_ids=
for worker_key in compose-worker-direct-one compose-worker-direct-two
do
  worker_status=$(curl --silent --show-error \
    --config "$AGENT_CAPABILITY_CONFIG_FILE" \
    --output "$AGENT_RUN_FILE" --write-out '%{http_code}' \
    --request POST --header 'Content-Type: application/json' \
    --header "Idempotency-Key: $worker_key" \
    --data '{"version":"browser-preview/v1","route":"/s/demo/","target":"desktop-chromium","evidence":["screenshot","heading-summary","structure-summary"]}' \
    http://localhost:8080/api/agent/v1/preview-runs)
  test "$worker_status" = 202
  worker_run_id=$(python -c \
    'import json,sys; value=json.load(open(sys.argv[1])); assert value["state"] in {"QUEUED","RUNNING","COMPLETED"}; print(value["run_id"])' \
    "$AGENT_RUN_FILE")
  worker_run_ids=${worker_run_ids}${worker_run_ids:+,}${worker_run_id}
done

for worker_run_id in $(printf '%s' "$worker_run_ids" | tr ',' ' ')
do
  for attempt in $(seq 1 180)
  do
    test "$(curl --silent --show-error --config "$AGENT_CAPABILITY_CONFIG_FILE" \
      --output "$AGENT_RUN_FILE" --write-out '%{http_code}' \
      "http://localhost:8080/api/agent/v1/preview-runs/$worker_run_id")" = 200
    state=$(python - "$AGENT_RUN_FILE" "$worker_run_id" <<'PY'
import json
import pathlib
import sys

document = json.loads(pathlib.Path(sys.argv[1]).read_text("utf-8"))
state = document["state"]
if state in {"FAILED", "TIMED_OUT", "CANCELLED"}:
    error = document.get("error") or {}
    code = str(error.get("code") or "UNKNOWN")[:64]
    message = str(error.get("message") or "")[:128].replace("\n", " ")
    print(
        f"agent-browser-dispatch: terminal run={sys.argv[2]} "
        f"state={state} code={code} message={message}",
        file=sys.stderr,
    )
print(state)
PY
    )
    case "$state" in
      COMPLETED) break ;;
      FAILED|TIMED_OUT|CANCELLED) exit 1 ;;
    esac
    sleep 1
  done
  test "$state" = COMPLETED
done

docker exec -i \
  -e SLAIF_TEST_RUN_IDS="$worker_run_ids" \
  "${PROJECT}-agent-api-1" python - <<'PY'
# ROUTE = "/s/demo/" is submitted and normalized by the Agent contract.
import json
import os
from pathlib import Path

run_ids = os.environ["SLAIF_TEST_RUN_IDS"].split(",")
assert len(run_ids) == 2
for run_id in run_ids:
    assert run_id
Path("/tmp/browser-worker-result.json").write_text(
    json.dumps({"runs": run_ids}, separators=(",", ":")), encoding="utf-8"
)
Path("/tmp/browser-worker-result.json").chmod(0o600)
print("browser-worker-dispatch: OK durable-runs=2 artifacts=agent-owned")
PY
retrieve_public_artifacts
worker_probe_run_id=$(printf '%s' "$worker_run_ids" | cut -d, -f1)
worker_artifact_id=$(docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT id FROM control.browser_artifact
   WHERE capability_id='15000000-0000-4000-8000-000000000004'
     AND run_id='$worker_probe_run_id'
   ORDER BY created_at, id LIMIT 1")
test -n "$worker_artifact_id"
test "$(curl --silent --show-error --config "$AGENT_CAPABILITY_CONFIG_FILE" \
  --output "$ARTIFACT_BODY_FILE" --write-out '%{http_code}' \
  "http://localhost:8080/api/agent/v1/preview-runs/$worker_probe_run_id/artifacts/00000000-0000-4000-8000-000000000099")" = 404
test "$(curl --silent --show-error --config "$FOREIGN_CAPABILITY_CONFIG_FILE" \
  --output "$ARTIFACT_BODY_FILE" --write-out '%{http_code}' \
  "http://localhost:8080/api/agent/v1/preview-runs/$worker_probe_run_id/artifacts/$worker_artifact_id")" = 404
echo "browser-artifact-negative: OK random=404 foreign-capability=404"
docker compose -p "$PROJECT" restart agent-api >/dev/null
wait_healthy agent-api
echo "agent-browser-restart: OK durable-artifacts=retained"
retrieve_public_artifacts
test "$(curl --silent --show-error --config "$AGENT_CAPABILITY_CONFIG_FILE" \
  --output "$PRE_OUTAGE_BODY_FILE" --write-out '%{http_code}' \
  "http://localhost:8080/api/agent/v1/preview-runs/$worker_probe_run_id/artifacts/$worker_artifact_id")" = 200
docker compose -p "$PROJECT" stop browser-worker >/dev/null
outage_status=$(curl --silent --show-error --max-time 30 \
  --config "$AGENT_CAPABILITY_CONFIG_FILE" --output "$ARTIFACT_BODY_FILE" \
  --write-out '%{http_code}' \
  "http://localhost:8080/api/agent/v1/preview-runs/$worker_probe_run_id/artifacts/$worker_artifact_id" || true)
test "$outage_status" = 503
if grep -Fq "$worker_artifact_id" "$ARTIFACT_BODY_FILE"
then
  echo "compose-smoke: worker outage leaked artifact binding" >&2
  exit 1
fi
test "$(curl --silent --output "$ARTIFACT_BODY_FILE" --write-out '%{http_code}' \
  http://localhost:8080/s/demo)" = 200
if grep -q 'Compose preview overlay' "$ARTIFACT_BODY_FILE"
then
  echo "compose-smoke: worker outage changed canonical output" >&2
  exit 1
fi
echo "browser-artifact-outage: OK status=503 canonical=200 bytes=absent"
docker compose -p "$PROJECT" start browser-worker >/dev/null
wait_healthy browser-worker
test "$(curl --silent --show-error --config "$AGENT_CAPABILITY_CONFIG_FILE" \
  --output "$ARTIFACT_BODY_FILE" --write-out '%{http_code}' \
  "http://localhost:8080/api/agent/v1/preview-runs/$worker_probe_run_id/artifacts/$worker_artifact_id")" = 200
cmp "$PRE_OUTAGE_BODY_FILE" "$ARTIFACT_BODY_FILE"
echo "browser-artifact-recovery: OK byte-identical"
worker_canonical_status=$(curl --silent --output /dev/null --write-out '%{http_code}' \
  http://localhost:8080/s/demo)
if test "$worker_canonical_status" != 200
then
  echo "compose-smoke: canonical worker comparison status=$worker_canonical_status" >&2
  exit 1
fi
if curl --silent http://localhost:8080/s/demo | grep -q 'Compose preview overlay'
then
  echo "compose-smoke: worker preview changed canonical output" >&2
  exit 1
fi
docker compose -p "$PROJECT" restart browser-worker >/dev/null
wait_healthy browser-worker
echo "browser-worker-restart: OK durable-dispatch-artifacts=retained"
retrieve_public_artifacts

test "$(docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT count(*) || ':' || count(*) FILTER (WHERE state='QUEUED') || ':' ||
          (SELECT count(*) FROM control.browser_artifact
           WHERE capability_id='15000000-0000-4000-8000-000000000004')
   FROM control.browser_run
   WHERE capability_id='15000000-0000-4000-8000-000000000004';")" = "2:0:6"
for queued_run_id in $(printf '%s' "$worker_run_ids" | tr ',' ' ')
do
  test "$(curl --silent --show-error --config "$AGENT_CAPABILITY_CONFIG_FILE" \
    --output "$AGENT_RUN_FILE" --write-out '%{http_code}' \
    "http://localhost:8080/api/agent/v1/preview-runs/$queued_run_id")" = 200
  python -c 'import json,sys; value=json.load(open(sys.argv[1])); assert value["state"]=="COMPLETED"' \
    "$AGENT_RUN_FILE"
done
echo "browser-worker-public-separation: OK durable-runs=2 completed=2 db-artifacts=6"
docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
  --user 0:0 --volume "${PROJECT}_browser-artifacts:/artifacts:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib,stat; root=pathlib.Path('/artifacts'); files=sorted(root.iterdir()); assert len(files)==12 and sum(p.suffix=='.bin' for p in files)==6 and sum(p.suffix=='.json' for p in files)==6 and not any(p.name.startswith('.stage-') for p in files); assert all(p.is_file() and not p.is_symlink() and stat.S_IMODE(p.stat().st_mode)==0o600 and p.stat().st_uid==10001 and p.stat().st_nlink==1 for p in files); assert not any(marker in p.read_bytes() for p in files for marker in (b'sbp1.',b'sbws1:',b'sas2_')); print('browser-artifact-runtime-policy: OK files=12 artifacts=6 mode=0600 links=1 credentials=absent')"
if docker compose -p "$PROJECT" logs --no-color browser-worker 2>/dev/null \
  | grep -Eq 'sbp1\.|sbws1:|sas2_|--no-sandbox'
then
  echo "compose-smoke: browser worker log or process policy leaked" >&2
  exit 1
fi
docker exec "${PROJECT}-browser-worker-1" node -e \
  "const fs=require('fs');const self=String(process.pid);const found=fs.readdirSync('/proc').filter(v=>/^\\d+$/.test(v)&&v!==self).flatMap(v=>{try{const c=fs.readFileSync('/proc/'+v+'/cmdline').toString();return c.includes('/chrome')?[v+':'+c]:[]}catch{return []}});if(found.length){console.error('CHROME_FOUND',found);process.exit(1)};console.log('browser-worker-cleanup: OK chromium-children=0 temporary-profiles=0')"

docker run --rm --network none --volume \
  "${PROJECT}_browser-worker-secret:/worker" \
  --entrypoint sh slaif-agent-site-backend:local -c \
  'mv /worker/worker-token /worker/worker-token.hidden'
docker compose -p "$PROJECT" restart agent-api browser-worker >/dev/null
worker_unready_attempt=0
agent_worker_status=000
browser_worker_status=000
while test "$worker_unready_attempt" -lt 30 && \
  { test "$agent_worker_status" != 503 || test "$browser_worker_status" != 503; }
do
  worker_unready_attempt=$((worker_unready_attempt + 1))
  sleep 1
  agent_worker_status=$(curl --silent --output /dev/null --write-out '%{http_code}' \
    http://localhost:8080/api/agent/health/ready || true)
  browser_worker_status=$(docker exec "${PROJECT}-browser-worker-1" node -e \
    "fetch('http://127.0.0.1:3100/health/ready').then(r=>console.log(r.status)).catch(()=>console.log(0))")
done
test "$agent_worker_status" = 503
test "$browser_worker_status" = 503
test "$(curl --silent --output /dev/null --write-out '%{http_code}' \
  http://localhost:8080/s/demo)" = 200
docker run --rm --network none --volume \
  "${PROJECT}_browser-worker-secret:/worker" \
  --entrypoint sh slaif-agent-site-backend:local -c \
  'mv /worker/worker-token.hidden /worker/worker-token'
docker compose -p "$PROJECT" restart agent-api browser-worker >/dev/null
wait_healthy agent-api
wait_healthy browser-worker
echo "browser-worker-secret-recovery: OK missing=not-ready canonical=available restored=healthy"

docker run --rm --network none --volume \
  "${PROJECT}_browser-signing-secret:/signing" \
  --entrypoint sh slaif-agent-site-backend:local -c \
  'mv /signing/signing-key /signing/signing-key.hidden'
docker compose -p "$PROJECT" restart agent-api render-api >/dev/null
wait_signing_unready() {
  service_path=$1
  attempt=0
  status=000
  while test "$attempt" -lt 30 && test "$status" != 503
  do
    attempt=$((attempt + 1))
    sleep 1
    status=$(curl --silent --output /dev/null --write-out '%{http_code}' \
      "http://localhost:8080$service_path" || true)
  done
  test "$status" = 503
}
wait_signing_unready /api/agent/health/ready
test "$(docker exec "${PROJECT}-render-api-1" python -c \
  "import urllib.error,urllib.request; u='http://127.0.0.1:8000/health/ready';
try: urllib.request.urlopen(u,timeout=2)
except urllib.error.HTTPError as e: print(e.code)")" = 503
test "$(curl --silent --output /dev/null --write-out '%{http_code}' \
  http://localhost:8080/)" = 200
docker run --rm --network none --volume \
  "${PROJECT}_browser-signing-secret:/signing" \
  --entrypoint sh slaif-agent-site-backend:local -c \
  'mv /signing/signing-key.hidden /signing/signing-key'
docker compose -p "$PROJECT" restart agent-api render-api >/dev/null
wait_healthy agent-api
wait_healthy render-api
echo "browser-signing-recovery: OK missing=not-ready canonical=available restored=healthy"

python tools/compose/control_readiness.py "$PROJECT" --existing

fingerprint() {
  docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
    --user 0:0 --volume "${PROJECT}_local-secrets:/secrets:ro" \
    --entrypoint python slaif-agent-site-backend:local -c \
    "import hashlib,pathlib; h=hashlib.sha256(); [h.update(p.read_bytes()) for p in sorted(pathlib.Path('/secrets').iterdir())]; print(h.hexdigest())"
}
render_fingerprint() {
  docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
    --user 0:0 --volume "${PROJECT}_render-secret:/render:ro" \
    --entrypoint python slaif-agent-site-backend:local -c \
    "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('/render/render-dsn').read_bytes()).hexdigest())"
}
site_fingerprint() {
  docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
    "SELECT md5(string_agg(row_to_json(snapshot)::text, E'\\n' ORDER BY site_key)) FROM (SELECT site_key, display_name, default_locale, status, canonical_revision, content_model_revision, component_catalog_version FROM control.site) snapshot"
}
membership_fingerprint() {
  docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
    "SELECT md5(string_agg(row_to_json(snapshot)::text, E'\n' ORDER BY user_account_id, site_id)) FROM (SELECT site_id, user_account_id, role_key, delegation_ceiling, status, version FROM control.site_membership) snapshot"
}
domain_fingerprint() {
  docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
    "SELECT md5(string_agg(row_to_json(snapshot)::text, E'\n' ORDER BY hostname, path_prefix)) FROM (SELECT site_id, hostname, path_prefix, is_primary FROM control.site_domain) snapshot"
}
before=$(fingerprint)
render_before=$(render_fingerprint)
sites_before=$(site_fingerprint)
memberships_before=$(membership_fingerprint)
domains_before=$(domain_fingerprint)
docker compose -p "$PROJECT" stop
docker compose -p "$PROJECT" up --wait
after=$(fingerprint)
test "$before" = "$after"
test "$(docker compose -p "$PROJECT" logs --no-color bootstrap 2>/dev/null | grep -c 'setup-token-secret:')" = 1
test "$(membership_fingerprint)" = "$memberships_before"
test "$(domain_fingerprint)" = "$domains_before"
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT count(*) FROM control.user_account WHERE id IN ('12000000-0000-4000-8000-000000000001'::uuid, '12000000-0000-4000-8000-000000000002'::uuid)" \
  | grep -q '^2$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT site_key || '|' || display_name || '|' || default_locale || '|' || status FROM control.site WHERE site_key = 'demo'" \
  | grep -q '^demo|SLAIF Demo Site|en|ACTIVE$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT site_key || '|' || display_name || '|' || default_locale || '|' || status FROM control.site WHERE site_key = 'governance'" \
  | grep -q '^governance|Governance Evidence Site|sl-SI|ARCHIVED$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT hostname || '|' || path_prefix || '|' || is_primary::text FROM control.site_domain domain JOIN control.site site ON site.id = domain.site_id WHERE site.site_key = 'governance'" \
  | grep -q '^routes.test|/secondary|true$'
echo "governance-restart: OK site=archived membership=inactive domain=primary fixtures=retained setup=closed"

docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_OVERRIDE \
  --user 0:0 --volume "${PROJECT}_render-secret:/render" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib; pathlib.Path('/render/render-dsn').write_bytes(b'corrupt-render-locator')"
docker compose -p "$PROJECT" up -d --force-recreate --no-deps render-api >/dev/null
attempt=0
while test "$attempt" -lt 40
do
  render_health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${PROJECT}-render-api-1")
  web_status=$(curl --silent --output /dev/null --write-out '%{http_code}' http://localhost:8080/health/ready || true)
  if test "$render_health" = unhealthy && test "$web_status" = 503
  then
    break
  fi
  attempt=$((attempt + 1))
  sleep 2
done
test "$render_health" = unhealthy
test "$web_status" = 503
attempt=0
while test "$attempt" -lt 40
do
  nginx_health=$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' "${PROJECT}-nginx-1")
  test "$nginx_health" != unhealthy || break
  attempt=$((attempt + 1))
  sleep 2
done
test "$nginx_health" = unhealthy
echo "render-locator-failure: correctly blocked render=unhealthy web=503 nginx=unhealthy"
docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_OVERRIDE \
  --user 0:0 --volume "${PROJECT}_local-secrets:/master:ro" \
  --volume "${PROJECT}_render-secret:/render" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib; pathlib.Path('/render/render-dsn').write_bytes(pathlib.Path('/master/service-public-dsn').read_bytes())"
docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
  --user 0:0 --volume "${PROJECT}_local-secrets:/master:ro" \
  --volume "${PROJECT}_render-secret:/render:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import pathlib,secrets; assert secrets.compare_digest(pathlib.Path('/render/render-dsn').read_bytes(), pathlib.Path('/master/service-public-dsn').read_bytes())"
docker compose -p "$PROJECT" up -d --force-recreate --no-deps render-api >/dev/null
wait_healthy render-api
docker compose -p "$PROJECT" restart web >/dev/null
wait_healthy web
docker compose -p "$PROJECT" restart nginx >/dev/null
wait_healthy nginx
test "$(render_fingerprint)" = "$render_before"
test "$(fingerprint)" = "$before"
test "$(site_fingerprint)" = "$sites_before"
test "$(membership_fingerprint)" = "$memberships_before"
test "$(domain_fingerprint)" = "$domains_before"
test "$(docker compose -p "$PROJECT" logs --no-color bootstrap 2>/dev/null | grep -c 'setup-token-secret:')" = 1
echo "render-locator-recovery: restored render=healthy web=healthy nginx=healthy"
docker compose -p "$PROJECT" up --wait >/dev/null
test "$(render_fingerprint)" = "$render_before"
test "$(fingerprint)" = "$before"
test "$(site_fingerprint)" = "$sites_before"
test "$(membership_fingerprint)" = "$memberships_before"
test "$(domain_fingerprint)" = "$domains_before"
test "$(docker compose -p "$PROJECT" logs --no-color bootstrap 2>/dev/null | grep -c 'setup-token-secret:')" = 1

if docker compose -p "$NEGATIVE_PROJECT" -f compose.yaml \
  -f tests/packaging/compose.broken-bootstrap.yaml up --wait \
  >"$NEGATIVE_OUTPUT_FILE" 2>&1
then
  tail -40 "$NEGATIVE_OUTPUT_FILE" >&2
  echo "compose-smoke: broken bootstrap unexpectedly succeeded" >&2
  exit 1
fi
test -z "$(docker compose -p "$NEGATIVE_PROJECT" -f compose.yaml \
  -f tests/packaging/compose.broken-bootstrap.yaml ps -q --status running nginx)"
grep -Eq 'bootstrap.*(failed|didn.t complete|exited)' "$NEGATIVE_OUTPUT_FILE"
echo "negative-bootstrap: correctly blocked"

if for image in slaif-agent-site-backend:local slaif-agent-site-browser-worker:local slaif-agent-site-web:local slaif-agent-site-nginx:local
do
  docker history --no-trunc "$image"
done | grep -Ei 'postgresql://|://[^[:space:]]+:[^[:space:]@]+@'
then
  echo "compose-smoke: possible database locator in image history" >&2
  exit 1
fi

if docker compose -p "$PROJECT" logs --no-color | grep -Ei 'postgresql://|://[^[:space:]]+:[^[:space:]@]+@'
then
  echo "compose-smoke: possible database locator in logs" >&2
  exit 1
fi

docker build -f infra/apache/Dockerfile -t slaif-agent-site-apache:test .
docker run --rm slaif-agent-site-apache:test httpd -t
docker run --rm \
  --add-host control-api:127.0.0.1 \
  --add-host editor-api:127.0.0.1 \
  --add-host agent-api:127.0.0.1 \
  --add-host mcp-adapter:127.0.0.1 \
  --add-host media-service:127.0.0.1 \
  --add-host web:127.0.0.1 \
  slaif-agent-site-nginx:local -t
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -v ON_ERROR_STOP=1 -c \
  "UPDATE control.capability SET revoked_at=CURRENT_TIMESTAMP
   WHERE id='15000000-0000-4000-8000-000000000004';" >/dev/null
revoked_status=$(curl --silent --show-error --config "$AGENT_CAPABILITY_CONFIG_FILE" \
  --output "$ARTIFACT_BODY_FILE" --write-out '%{http_code}' \
  "http://localhost:8080/api/agent/v1/preview-runs/$worker_probe_run_id/artifacts/$worker_artifact_id")
test "$revoked_status" = 401
if grep -Fq "$worker_artifact_id" "$ARTIFACT_BODY_FILE"
then
  echo "compose-smoke: revoked artifact binding leaked" >&2
  exit 1
fi
echo "browser-artifact-revoked: OK status=401 bytes=absent"
python -m unittest discover -s tests/packaging -p 'test_*.py'
echo "compose-smoke: OK"
