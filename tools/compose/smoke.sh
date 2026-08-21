#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
PROJECT=${1-slaif007smoke}
NEGATIVE_PROJECT="${PROJECT}negative"

validate_project() {
  case "$1" in
    slaif007[a-z0-9]*|slaif009[a-z0-9]*|slaif010[a-z0-9]*) return 0 ;;
    *) echo "compose-smoke: unsafe project name" >&2; return 2 ;;
  esac
}
validate_project "$PROJECT"
if test "${2:-}" = --validate-project
then
  exit 0
fi

HEADER_FILE=
TOKEN_FILE=
E2E_SECRET_FILE=
NEGATIVE_OUTPUT_FILE=

cleanup() {
  test -z "$HEADER_FILE" || rm -f "$HEADER_FILE"
  test -z "$TOKEN_FILE" || rm -f "$TOKEN_FILE"
  test -z "$E2E_SECRET_FILE" || rm -f "$E2E_SECRET_FILE"
  test -z "$NEGATIVE_OUTPUT_FILE" || rm -f "$NEGATIVE_OUTPUT_FILE"
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
chmod 600 "$TOKEN_FILE" "$E2E_SECRET_FILE"

cd "$ROOT"
docker compose config --quiet
python tools/compose/verify.py --root "$ROOT"
docker compose build --pull
docker compose -p "$PROJECT" up --build --wait
python tools/compose/verify.py --root "$ROOT" --project "$PROJECT"

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

curl --fail --show-error --silent http://localhost:8080/ | grep -q "Self-hosted human control"
docker compose -p "$PROJECT" logs --no-color bootstrap 2>/dev/null \
  | sed -n 's/^.*setup-token-secret: //p' >"$TOKEN_FILE"
test "$(wc -l <"$TOKEN_FILE" | tr -d ' ')" = 1
tools/compose/e2e.sh "$TOKEN_FILE" "$E2E_SECRET_FILE"
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

docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT readiness_state || ' safe=' || safe FROM control.bootstrap_readiness WHERE singleton" \
  | grep -q '^EMPTY_SAFE safe=true$'
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

python tools/compose/control_readiness.py "$PROJECT" --existing

fingerprint() {
  docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
    --user 0:0 --volume "${PROJECT}_local-secrets:/secrets:ro" \
    --entrypoint python slaif-agent-site-backend:local -c \
    "import hashlib,pathlib; h=hashlib.sha256(); [h.update(p.read_bytes()) for p in sorted(pathlib.Path('/secrets').iterdir())]; print(h.hexdigest())"
}
before=$(fingerprint)
docker compose -p "$PROJECT" stop
docker compose -p "$PROJECT" up --wait
after=$(fingerprint)
test "$before" = "$after"
test "$(docker compose -p "$PROJECT" logs --no-color bootstrap 2>/dev/null | grep -c 'setup-token-secret:')" = 1
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT site_key || '|' || display_name || '|' || default_locale || '|' || status FROM control.site WHERE site_key = 'demo'" \
  | grep -q '^demo|SLAIF Demo Site|en|ACTIVE$'

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
docker compose -p "$PROJECT" up -d --force-recreate --no-deps render-api >/dev/null
docker compose -p "$PROJECT" up --wait >/dev/null

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
python -m unittest discover -s tests/packaging -p 'test_*.py'
echo "compose-smoke: OK"
