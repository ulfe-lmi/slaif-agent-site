#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
PROJECT=${1:-slaif007smoke}
NEGATIVE_PROJECT="${PROJECT}negative"
HEADER_FILE=$(mktemp)

case "$PROJECT" in
  slaif007[a-z0-9]*) ;;
  *) echo "compose-smoke: unsafe project name" >&2; exit 2 ;;
esac

cleanup() {
  rm -f "$HEADER_FILE"
  docker compose -p "$NEGATIVE_PROJECT" -f "$ROOT/compose.yaml" \
    -f "$ROOT/tests/packaging/compose.broken-bootstrap.yaml" \
    down --volumes --remove-orphans >/dev/null 2>&1 || true
  docker compose -p "$PROJECT" -f "$ROOT/compose.yaml" \
    down --volumes --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT HUP INT TERM
cleanup

cd "$ROOT"
docker compose config --quiet
python tools/compose/verify.py --root "$ROOT"
docker compose build --pull
docker compose -p "$PROJECT" up --build --wait
python tools/compose/verify.py --root "$ROOT" --project "$PROJECT"

curl --fail --show-error --silent http://localhost:8080/ | grep -q "Pre-alpha deployment skeleton"
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
for path in /api/control/sites /api/editor/workspaces /api/agent/tools /mcp/tools /media/files /admin /preview
do
  status=$(curl --silent --output /dev/null --write-out '%{http_code}' "http://localhost:8080$path")
  test "$status" = 404
done
curl --silent --dump-header "$HEADER_FILE" --output /dev/null \
  http://localhost:8080/
grep -qi '^X-Request-ID:' "$HEADER_FILE"
grep -qi '^X-Content-Type-Options: nosniff' "$HEADER_FILE"

docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT readiness_state || ' safe=' || safe FROM control.bootstrap_readiness WHERE singleton" \
  | grep -q '^EMPTY_SAFE safe=true$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT count(*) FROM pg_auth_members m JOIN pg_roles member ON member.oid=m.member WHERE member.rolname LIKE 'slaif_%_login'" \
  | grep -q '^10$'
docker exec "${PROJECT}-postgres-1" psql -U postgres -d slaif -Atc \
  "SELECT NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname LIKE 'slaif_%_login' AND (NOT rolcanlogin OR rolsuper OR rolcreatedb OR rolcreaterole OR NOT rolinherit OR rolreplication OR rolbypassrls))" \
  | grep -q '^t$'
docker run --rm --network none --read-only --cap-drop ALL --cap-add DAC_READ_SEARCH \
  --user 0:0 --volume "${PROJECT}_local-secrets:/secrets:ro" \
  --entrypoint python slaif-agent-site-backend:local -c \
  "import os,pathlib,stat; root=pathlib.Path('/secrets'); files=list(root.iterdir()); assert len(files)==23; assert all(stat.S_IMODE(p.stat().st_mode)==0o400 for p in files); assert (root/'postgres-password').stat().st_uid==999; assert (root/'.initialized-v1').stat().st_uid==0; assert all(p.stat().st_uid==10001 for p in files if p.name not in {'postgres-password','.initialized-v1'}); values=[p.read_bytes() for p in files if p.name=='postgres-password' or p.name.startswith('login-')]; assert len(values)==len(set(values))==11; print('secret-file-policy: OK')"

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

if docker compose -p "$NEGATIVE_PROJECT" -f compose.yaml \
  -f tests/packaging/compose.broken-bootstrap.yaml up --wait
then
  echo "compose-smoke: broken bootstrap unexpectedly succeeded" >&2
  exit 1
fi
test -z "$(docker compose -p "$NEGATIVE_PROJECT" -f compose.yaml \
  -f tests/packaging/compose.broken-bootstrap.yaml ps -q --status running nginx)"

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
