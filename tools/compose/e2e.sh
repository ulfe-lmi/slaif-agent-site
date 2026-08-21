#!/bin/sh
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
TOKEN_FILE=$1
SECRET_FILE=$2
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
  pnpm exec playwright test
then
  fail browser contract
fi
echo "compose-e2e: OK projects=8 setup=1 governance=1 stable-devices=6 artifacts=disabled"
