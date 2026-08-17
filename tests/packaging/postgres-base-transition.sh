#!/bin/sh
set -eu

OLD_IMAGE='docker.io/library/postgres:18.6-trixie@sha256:06cad38a5d9f5d24b4d83d86def30795d5e4b757fedbf5281172b576dedcd941'
NEW_IMAGE='docker.io/library/postgres:18.6-alpine3.23@sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f'
BACKEND_IMAGE='slaif-agent-site-backend:local'
PREFIX=${1:-slaif008transitionlocal}

case "$PREFIX" in
  slaif008transition*) ;;
  *) echo "postgres-base-transition: unsafe prefix" >&2; exit 2 ;;
esac
case "$PREFIX" in
  *[!a-z0-9]*) echo "postgres-base-transition: unsafe prefix" >&2; exit 2 ;;
esac
if [ "${#PREFIX}" -gt 48 ]; then
  echo "postgres-base-transition: unsafe prefix" >&2
  exit 2
fi

NETWORK="${PREFIX}-network"
DATA_VOLUME="${PREFIX}-postgres-data"
OLD_CONTAINER="${PREFIX}-old-postgres"
NEW_CONTAINER="${PREFIX}-new-postgres"
SECRET_CONTAINER="${PREFIX}-secrets"
BOOTSTRAP_CONTAINER="${PREFIX}-bootstrap"
VALIDATE_BEFORE_CONTAINER="${PREFIX}-validate-before"
VALIDATE_AFTER_CONTAINER="${PREFIX}-validate-after"
LOGIN_BEFORE_CONTAINER="${PREFIX}-login-before"
LOGIN_AFTER_CONTAINER="${PREFIX}-login-after"
CREDENTIAL_DIR=
DATABASE_CONTAINER=
STAGE=preflight

fail() {
  echo "postgres-base-transition: FAIL stage=$STAGE reason=$1" >&2
  exit 1
}

resource_collision() {
  for container in \
    "$OLD_CONTAINER" \
    "$NEW_CONTAINER" \
    "$SECRET_CONTAINER" \
    "$BOOTSTRAP_CONTAINER" \
    "$VALIDATE_BEFORE_CONTAINER" \
    "$VALIDATE_AFTER_CONTAINER" \
    "$LOGIN_BEFORE_CONTAINER" \
    "$LOGIN_AFTER_CONTAINER"
  do
    if docker container inspect "$container" >/dev/null 2>&1; then
      fail "exact disposable container already exists"
    fi
  done
  if docker network inspect "$NETWORK" >/dev/null 2>&1; then
    fail "exact disposable network already exists"
  fi
  if docker volume inspect "$DATA_VOLUME" >/dev/null 2>&1; then
    fail "exact disposable volume already exists"
  fi
}

cleanup() {
  result=$?
  trap - EXIT HUP INT TERM
  set +e
  cleanup_failed=0
  for container in \
    "$OLD_CONTAINER" \
    "$NEW_CONTAINER" \
    "$SECRET_CONTAINER" \
    "$BOOTSTRAP_CONTAINER" \
    "$VALIDATE_BEFORE_CONTAINER" \
    "$VALIDATE_AFTER_CONTAINER" \
    "$LOGIN_BEFORE_CONTAINER" \
    "$LOGIN_AFTER_CONTAINER"
  do
    if docker container inspect "$container" >/dev/null 2>&1; then
      if ! docker container rm --force "$container" >/dev/null 2>&1; then
        echo "postgres-base-transition: cleanup resource=container result=FAIL" >&2
        cleanup_failed=1
      fi
    fi
  done
  if docker network inspect "$NETWORK" >/dev/null 2>&1; then
    if ! docker network rm "$NETWORK" >/dev/null 2>&1; then
      echo "postgres-base-transition: cleanup resource=network result=FAIL" >&2
      cleanup_failed=1
    fi
  fi
  if docker volume inspect "$DATA_VOLUME" >/dev/null 2>&1; then
    if ! docker volume rm "$DATA_VOLUME" >/dev/null 2>&1; then
      echo "postgres-base-transition: cleanup resource=volume result=FAIL" >&2
      cleanup_failed=1
    fi
  fi
  if [ -n "$CREDENTIAL_DIR" ] && [ -d "$CREDENTIAL_DIR" ]; then
    docker run --rm --network none --read-only --cap-drop ALL \
      --cap-add DAC_OVERRIDE --user 0:0 \
      --volume "$CREDENTIAL_DIR:/credentials" \
      --entrypoint python "$BACKEND_IMAGE" -c \
      'import pathlib; root = pathlib.Path("/credentials"); [item.unlink() for item in root.iterdir()]' \
      >/dev/null 2>&1 || {
        echo "postgres-base-transition: cleanup resource=credentials-content result=FAIL" >&2
        cleanup_failed=1
      }
    if ! sudo rmdir "$CREDENTIAL_DIR" >/dev/null 2>&1; then
      echo "postgres-base-transition: cleanup resource=credentials-directory result=FAIL" >&2
      cleanup_failed=1
    fi
  fi
  if [ "$cleanup_failed" -ne 0 ]; then
    echo "postgres-base-transition: cleanup FAILED exact-prefix=$PREFIX" >&2
    result=1
  else
    echo "postgres-base-transition: cleanup OK containers=removed network=removed volume=removed credentials=removed"
  fi
  exit "$result"
}

trap cleanup EXIT
trap 'exit 130' HUP INT TERM

pull_exact() {
  role=$1
  reference=$2
  expected_digest=${reference##*@sha256:}
  output=$(docker pull "$reference" 2>&1) || fail "$role image pull failed"
  docker image inspect "$reference" >/dev/null 2>&1 \
    || fail "$role exact image is not locally addressable"
  case "$output" in
    *"Digest: sha256:$expected_digest"*) ;;
    *) fail "$role pull did not confirm the expected top-level digest" ;;
  esac
  echo "postgres-base-transition: image role=$role digest=sha256:$expected_digest verified=true"
}

safe_log_findings() {
  container=$1
  docker logs "$container" 2>&1 | grep -Ei \
    'collation.*(mismatch|version)|version mismatch|invalid.*index|index.*invalid|database files are incompatible|data directory.*(incompatible|invalid|wrong)|could not.*locale|invalid locale|fatal:.*(locale|collation|data directory)|panic:' \
    || true
}

wait_ready() {
  container=$1
  count=0
  while [ "$count" -lt 60 ]; do
    if docker exec "$container" pg_isready --quiet --username postgres --dbname slaif
    then
      echo "postgres-base-transition: health container=$container ready=true"
      return 0
    fi
    running=$(docker inspect --format '{{.State.Running}}' "$container" 2>/dev/null || true)
    if [ "$running" != true ]; then
      findings=$(safe_log_findings "$container")
      if [ -n "$findings" ]; then
        printf '%s\n' "$findings" >&2
      fi
      fail "PostgreSQL container stopped before readiness"
    fi
    count=$((count + 1))
    sleep 2
  done
  findings=$(safe_log_findings "$container")
  if [ -n "$findings" ]; then
    printf '%s\n' "$findings" >&2
  fi
  fail "PostgreSQL readiness timeout"
}

start_postgres() {
  container=$1
  image=$2
  docker run --detach --name "$container" \
    --label "io.slaif.test-prefix=$PREFIX" \
    --network "$NETWORK" --network-alias postgres \
    --read-only --cap-drop ALL \
    --cap-add CHOWN --cap-add DAC_OVERRIDE --cap-add FOWNER \
    --cap-add SETGID --cap-add SETUID --group-add 10002 \
    --env PGDATA=/var/lib/postgresql/data \
    --env POSTGRES_DB=slaif \
    --env POSTGRES_PASSWORD_FILE=/run/slaif-secrets/postgres-password \
    --env POSTGRES_USER=postgres \
    --tmpfs /tmp:mode=1777,nosuid,nodev,noexec,size=16m \
    --tmpfs /var/run/postgresql:uid=999,gid=999,mode=3775,nosuid,nodev,noexec,size=16m \
    --volume "$DATA_VOLUME:/var/lib/postgresql/data" \
    --volume "$CREDENTIAL_DIR:/run/slaif-secrets:ro" \
    "$image" >/dev/null
  DATABASE_CONTAINER=$container
  wait_ready "$container"
}

run_backend() {
  container=$1
  shift
  docker run --rm --name "$container" \
    --label "io.slaif.test-prefix=$PREFIX" \
    --network "$NETWORK" --read-only --cap-drop ALL --group-add 10002 \
    --env SLAIF_BOOTSTRAP_EXPECTED_DATABASE=slaif \
    --env SLAIF_BOOTSTRAP_LOCAL_SECRETS_DIR=/run/slaif-secrets \
    --env SLAIF_BOOTSTRAP_MODE=production \
    --env SLAIF_BOOTSTRAP_OWNER_DSN_FILE=/run/slaif-secrets/owner-dsn \
    --env SLAIF_BOOTSTRAP_PROVISIONER_DSN_FILE=/run/slaif-secrets/provisioner-dsn \
    --tmpfs /tmp:mode=1777,nosuid,nodev,noexec,size=16m \
    --volume "$CREDENTIAL_DIR:/run/slaif-secrets:ro" \
    "$BACKEND_IMAGE" "$@"
}

LOGIN_VALIDATOR='
import asyncio
import sys

from slaif_agent_site.bootstrap.config import BootstrapSettings
from slaif_agent_site.bootstrap.service import _authenticate_local_logins
from slaif_agent_site.db.connections import provisioner_connection
from slaif_agent_site.db.roles import DATABASE_LOGINS, local_login_violations


async def check():
    settings = BootstrapSettings.load()
    async with provisioner_connection(
        settings.resolved_provisioner_dsn(),
        expected_database=settings.expected_database,
    ) as connection:
        violations = await local_login_violations(connection)
    authenticated = await _authenticate_local_logins(settings)
    if violations or authenticated != tuple(login.name for login in DATABASE_LOGINS):
        raise RuntimeError
    print("local-login-validate: OK principals=10 authenticated=10")


try:
    asyncio.run(check())
except Exception:
    print("local-login-validate: FAILED", file=sys.stderr)
    raise SystemExit(1)
'

run_validations() {
  phase=$1
  if [ "$phase" = before ]; then
    validate_container=$VALIDATE_BEFORE_CONTAINER
    login_container=$LOGIN_BEFORE_CONTAINER
  else
    validate_container=$VALIDATE_AFTER_CONTAINER
    login_container=$LOGIN_AFTER_CONTAINER
  fi
  run_backend "$validate_container" \
    python -m slaif_agent_site.bootstrap validate
  run_backend "$login_container" python -c "$LOGIN_VALIDATOR"
}

psql_query() {
  docker exec "$DATABASE_CONTAINER" \
    psql -X -qAt -v ON_ERROR_STOP=1 --username postgres --dbname slaif \
    --command "$1"
}

locale_fact() {
  psql_query \
    "SELECT concat_ws('|', 'encoding=' || pg_encoding_to_char(encoding), 'provider=' || datlocprovider::text, 'locale=' || coalesce(datlocale, ''), 'collate=' || datcollate, 'ctype=' || datctype, 'stored=' || coalesce(datcollversion, ''), 'actual=' || coalesce(pg_database_collation_actual_version(oid), '')) FROM pg_database WHERE datname = 'slaif'"
}

control_fact() {
  docker exec --user postgres "$DATABASE_CONTAINER" \
    sh -c 'pg_controldata "$PGDATA"' | awk -F ': *' '
      $1 == "pg_control version number" ||
      $1 == "Catalog version number" ||
      $1 == "Database system identifier" ||
      $1 == "Database block size" ||
      $1 == "WAL block size" ||
      $1 == "Bytes per WAL segment" ||
      $1 == "Maximum data alignment" ||
      $1 == "Data page checksum version" ||
      $1 == "Float8 argument passing" {
        if (seen++) printf ";"
        printf "%s=%s", $1, $2
      }
      END { print "" }
    '
}

marker_fact() {
  psql_query \
    "SELECT concat_ws('|', 'alembic=' || (SELECT version_num FROM control.alembic_version), 'migration=' || migration_revision, 'state=' || readiness_state, 'safe=' || safe::text) FROM control.bootstrap_readiness WHERE singleton"
}

role_fact() {
  psql_query \
    "SELECT string_agg(rolname, ',' ORDER BY rolname) FROM pg_roles WHERE rolname LIKE 'slaif\\_%' ESCAPE '\\'"
}

structure_fact() {
  psql_query \
    "SELECT concat_ws('|', 'parent_rows=' || (SELECT count(*) FROM transition_test.parent), 'child_rows=' || (SELECT count(*) FROM transition_test.child), 'constraints=' || (SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace WHERE n.nspname = 'transition_test' AND c.contype IN ('p', 'f') AND c.convalidated), 'order_index=' || coalesce((SELECT (indisvalid AND indisready)::text FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname = 'transition_test' AND c.relname = 'transition_order_idx'), 'false'))"
}

data_digest() {
  rows=$(psql_query \
    "SELECT concat_ws('|', p.id::text, encode(convert_to(p.unicode_text, 'UTF8'), 'hex'), encode(convert_to(p.ordered_text, 'UTF8'), 'hex'), p.amount::text, to_char(p.occurred_at AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS.US'), p.payload::text, string_agg(c.label, ',' ORDER BY c.id)) FROM transition_test.parent p JOIN transition_test.child c ON c.parent_id = p.id GROUP BY p.id, p.unicode_text, p.ordered_text, p.amount, p.occurred_at, p.payload ORDER BY p.id") \
    || fail "representative data query failed"
  [ -n "$rows" ] || fail "representative data query returned no rows"
  printf '%s\n' "$rows" | sha256sum | cut -d ' ' -f 1
}

order_digest() {
  rows=$(psql_query \
    "SET enable_seqscan = off; SELECT encode(convert_to(ordered_text, 'UTF8'), 'hex') FROM transition_test.parent ORDER BY ordered_text COLLATE \"default\", id") \
    || fail "ordered index query failed"
  [ -n "$rows" ] || fail "ordered index query returned no rows"
  printf '%s\n' "$rows" | sha256sum | cut -d ' ' -f 1
}

compare_fact() {
  label=$1
  before=$2
  after=$3
  if [ "$before" = "$after" ]; then
    echo "postgres-base-transition: compare fact=$label result=PASS"
  else
    echo "postgres-base-transition: compare fact=$label result=FAIL before=$before after=$after" >&2
    COMPATIBILITY_FAILED=1
  fi
}

record_log_result() {
  phase=$1
  findings=$(safe_log_findings "$DATABASE_CONTAINER")
  if [ -n "$findings" ]; then
    printf '%s\n' "$findings" >&2
    echo "postgres-base-transition: logs phase=$phase result=FAIL" >&2
    COMPATIBILITY_FAILED=1
  else
    echo "postgres-base-transition: logs phase=$phase result=PASS"
  fi
}

resource_collision
docker image inspect "$BACKEND_IMAGE" >/dev/null 2>&1 \
  || fail "accepted backend image is unavailable"
CREDENTIAL_DIR=$(mktemp -d "${TMPDIR:-/tmp}/${PREFIX}.credentials.XXXXXX")

STAGE=pull-images
pull_exact old "$OLD_IMAGE"
pull_exact new "$NEW_IMAGE"

STAGE=create-resources
docker network create --label "io.slaif.test-prefix=$PREFIX" "$NETWORK" >/dev/null
docker volume create --label "io.slaif.test-prefix=$PREFIX" "$DATA_VOLUME" >/dev/null
docker run --rm --name "$SECRET_CONTAINER" --network none --read-only \
  --cap-drop ALL --cap-add CHOWN --cap-add DAC_READ_SEARCH --user 0:0 \
  --volume "$CREDENTIAL_DIR:/run/slaif-secrets" \
  "$BACKEND_IMAGE" python /opt/slaif/bin/initialize-local-secrets.py \
  --directory /run/slaif-secrets
echo "postgres-base-transition: credentials generated=true values-printed=false"

STAGE=initialize-old
start_postgres "$OLD_CONTAINER" "$OLD_IMAGE"
OLD_VERSION=$(docker exec --user postgres "$OLD_CONTAINER" postgres --version)
case "$OLD_VERSION" in
  *" 18.6"*) ;;
  *) fail "old server is not PostgreSQL 18.6" ;;
esac
echo "postgres-base-transition: server phase=old version=$OLD_VERSION"

STAGE=bootstrap-old
run_backend "$BOOTSTRAP_CONTAINER" \
  python -m slaif_agent_site.bootstrap compose

STAGE=create-representative-data
docker exec -i "$OLD_CONTAINER" \
  psql -X -q -v ON_ERROR_STOP=1 --username postgres --dbname slaif <<'SQL'
CREATE SCHEMA transition_test AUTHORIZATION postgres;
CREATE TABLE transition_test.parent (
    id bigint PRIMARY KEY,
    unicode_text text NOT NULL,
    ordered_text text COLLATE "default" NOT NULL,
    amount numeric(20, 6) NOT NULL,
    occurred_at timestamptz NOT NULL,
    payload jsonb NOT NULL
);
CREATE INDEX transition_order_idx
    ON transition_test.parent (ordered_text COLLATE "default", id);
CREATE TABLE transition_test.child (
    id bigint PRIMARY KEY,
    parent_id bigint NOT NULL REFERENCES transition_test.parent(id),
    label text NOT NULL
);
INSERT INTO transition_test.parent VALUES
    (1, 'Živjo, svet', 'Ångström', 1234567890.123456, '2024-01-01T00:00:00Z', '{"kind":"latin","active":true}'),
    (2, '東京', 'Zulu', -42.500000, '2024-02-29T12:34:56.123456Z', '{"kind":"cjk","items":[1,2,3]}'),
    (3, 'emoji 😀', 'apple', 0.000001, '2025-06-30T23:59:59Z', '{"kind":"emoji","value":null}'),
    (4, U&'e\\0301', 'Éclair', 999.990000, '2026-08-17T08:15:30Z', '{"kind":"combining","nested":{"a":1}}'),
    (5, 'العربية', 'ábaco', 7.000000, '2023-12-31T23:59:59Z', '{"kind":"rtl","active":false}');
INSERT INTO transition_test.child VALUES
    (101, 1, 'alpha'),
    (102, 1, 'beta'),
    (201, 2, 'gamma'),
    (301, 3, 'delta'),
    (401, 4, 'epsilon'),
    (501, 5, 'zeta');
SQL

STAGE=record-before
run_validations before
LOCALE_BEFORE=$(locale_fact)
CONTROL_BEFORE=$(control_fact)
MARKER_BEFORE=$(marker_fact)
ROLES_BEFORE=$(role_fact)
STRUCTURE_BEFORE=$(structure_fact)
DATA_BEFORE=$(data_digest)
ORDER_BEFORE=$(order_digest)
echo "postgres-base-transition: before locale=$LOCALE_BEFORE"
echo "postgres-base-transition: before control=$CONTROL_BEFORE"
echo "postgres-base-transition: before marker=$MARKER_BEFORE"
echo "postgres-base-transition: before roles=$ROLES_BEFORE"
echo "postgres-base-transition: before structure=$STRUCTURE_BEFORE"
echo "postgres-base-transition: before data-sha256=$DATA_BEFORE order-sha256=$ORDER_BEFORE"
COMPATIBILITY_FAILED=0
record_log_result old

STAGE=stop-old
docker stop --time 60 "$OLD_CONTAINER" >/dev/null
OLD_EXIT=$(docker inspect --format '{{.State.ExitCode}}' "$OLD_CONTAINER")
[ "$OLD_EXIT" = 0 ] || fail "old server did not stop cleanly"
docker rm "$OLD_CONTAINER" >/dev/null
echo "postgres-base-transition: old-stop clean=true volume-preserved=true"

STAGE=start-new
start_postgres "$NEW_CONTAINER" "$NEW_IMAGE"
NEW_VERSION=$(docker exec --user postgres "$NEW_CONTAINER" postgres --version)
case "$NEW_VERSION" in
  *" 18.6"*) ;;
  *) fail "new server is not PostgreSQL 18.6" ;;
esac
echo "postgres-base-transition: server phase=new version=$NEW_VERSION"

STAGE=record-after
LOCALE_AFTER=$(locale_fact)
CONTROL_AFTER=$(control_fact)
MARKER_AFTER=$(marker_fact)
ROLES_AFTER=$(role_fact)
STRUCTURE_AFTER=$(structure_fact)
DATA_AFTER=$(data_digest)
ORDER_AFTER=$(order_digest)
run_validations after
echo "postgres-base-transition: after locale=$LOCALE_AFTER"
echo "postgres-base-transition: after control=$CONTROL_AFTER"
echo "postgres-base-transition: after marker=$MARKER_AFTER"
echo "postgres-base-transition: after roles=$ROLES_AFTER"
echo "postgres-base-transition: after structure=$STRUCTURE_AFTER"
echo "postgres-base-transition: after data-sha256=$DATA_AFTER order-sha256=$ORDER_AFTER"
compare_fact locale "$LOCALE_BEFORE" "$LOCALE_AFTER"
compare_fact control "$CONTROL_BEFORE" "$CONTROL_AFTER"
compare_fact marker "$MARKER_BEFORE" "$MARKER_AFTER"
compare_fact roles "$ROLES_BEFORE" "$ROLES_AFTER"
compare_fact structure "$STRUCTURE_BEFORE" "$STRUCTURE_AFTER"
compare_fact data-digest "$DATA_BEFORE" "$DATA_AFTER"
compare_fact order-digest "$ORDER_BEFORE" "$ORDER_AFTER"
record_log_result alpine-first-start

STAGE=restart-new
docker stop --time 60 "$NEW_CONTAINER" >/dev/null
NEW_EXIT=$(docker inspect --format '{{.State.ExitCode}}' "$NEW_CONTAINER")
[ "$NEW_EXIT" = 0 ] || fail "new server did not stop cleanly"
docker start "$NEW_CONTAINER" >/dev/null
wait_ready "$NEW_CONTAINER"
LOCALE_RESTART=$(locale_fact)
CONTROL_RESTART=$(control_fact)
MARKER_RESTART=$(marker_fact)
STRUCTURE_RESTART=$(structure_fact)
DATA_RESTART=$(data_digest)
ORDER_RESTART=$(order_digest)
compare_fact restart-locale "$LOCALE_AFTER" "$LOCALE_RESTART"
compare_fact restart-control "$CONTROL_AFTER" "$CONTROL_RESTART"
compare_fact restart-marker "$MARKER_AFTER" "$MARKER_RESTART"
compare_fact restart-structure "$STRUCTURE_AFTER" "$STRUCTURE_RESTART"
compare_fact restart-data-digest "$DATA_AFTER" "$DATA_RESTART"
compare_fact restart-order-digest "$ORDER_AFTER" "$ORDER_RESTART"
record_log_result alpine-restart

if [ "$COMPATIBILITY_FAILED" -ne 0 ]; then
  fail "locale, control, data, index, or log compatibility check failed"
fi

STAGE=complete
echo "postgres-base-transition: PASS from=postgres-18.6-trixie to=postgres-18.6-alpine3.23 data-preserved=true restart=true"
