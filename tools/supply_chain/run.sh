#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: tools/supply_chain/run.sh EVIDENCE_DIRECTORY" >&2
  exit 2
fi

repository_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
evidence_directory=$1
case "$evidence_directory" in
  /*) ;;
  *) evidence_directory="$repository_root/$evidence_directory" ;;
esac

if [ -e "$evidence_directory" ]; then
  echo "evidence directory already exists: $evidence_directory" >&2
  exit 2
fi

revision=${GITHUB_SHA:-local}
if [ "$revision" != local ] \
  && ! printf '%s\n' "$revision" | grep -Eq '^[0-9a-f]{40}$'; then
    echo "GITHUB_SHA must be local or a lowercase full commit SHA" >&2
    exit 2
fi

temporary_root=$(mktemp -d -p "${TMPDIR:-/tmp}" slaif-supply-chain.XXXXXX)
run_identity="slaif-supply-$$"
created_tags=""
created_containers=""
run_succeeded=0

if docker info >/dev/null 2>&1; then
  docker_command=docker
else
  docker_command="sudo docker"
fi

docker_run() {
  if [ "$docker_command" = docker ]; then
    docker "$@"
  else
    sudo docker "$@"
  fi
}

pull_exact_image() {
  reference=$1
  if docker_run image inspect "$reference" >/dev/null 2>&1; then
    echo "immutable-image: present $reference"
    return
  fi
  attempt=1
  while ! docker_run pull "$reference"; do
    if [ "$attempt" -ge 3 ]; then
      echo "failed to pull immutable image after $attempt attempts: $reference" >&2
      return 1
    fi
    attempt=$((attempt + 1))
    echo "immutable-image: retry $attempt/3 in 30 seconds: $reference" >&2
    sleep 30
  done
}

cleanup() {
  for container in $created_containers; do
    docker_run container rm --force "$container" >/dev/null 2>&1 || true
  done
  for tag in $created_tags; do
    docker_run image rm --force "$tag" >/dev/null 2>&1 || true
  done
  rm -rf -- "$temporary_root"
}

on_exit() {
  exit_status=$?
  if [ "$run_succeeded" -ne 1 ]; then
    (cd "$repository_root" && python -m tools.supply_chain.failure_diagnostics retain \
      --temporary-root "$temporary_root" \
      --evidence "$evidence_directory" \
      --exit-status "$exit_status") || true
  fi
  cleanup
  exit "$exit_status"
}
trap on_exit EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

mkdir -p \
  "$evidence_directory/artifacts" \
  "$evidence_directory/dependencies" \
  "$evidence_directory/images" \
  "$evidence_directory/manifests" \
  "$evidence_directory/reproducibility/images" \
  "$evidence_directory/sboms" \
  "$evidence_directory/scan-sboms" \
  "$evidence_directory/scanner" \
  "$evidence_directory/scans" \
  "$temporary_root/first" \
  "$temporary_root/second" \
  "$temporary_root/grype-db"

cd "$repository_root"

uv sync --frozen --all-groups
pnpm install --frozen-lockfile
uv run --frozen python -m tools.supply_chain.policy validate
uv run --frozen python -m tools.supply_chain.policy inventory \
  --output "$evidence_directory/dependencies"
uv run --frozen python -m tools.supply_chain.policy notices --check
uv run --frozen python -m tools.supply_chain.reproducible \
  --output "$evidence_directory/reproducibility"

syft_reference=$(python -c \
  'import json; print(json.load(open("supply-chain/policy.json"))["scanner_tools"]["syft"]["image"])')
grype_reference=$(python -c \
  'import json; print(json.load(open("supply-chain/policy.json"))["scanner_tools"]["grype"]["image"])')
postgres_reference=$(python -c \
  'import json; print(json.load(open("supply-chain/policy.json"))["oci_sources"]["postgres"])')

pull_exact_image "$syft_reference"
pull_exact_image "$grype_reference"
pull_exact_image "$postgres_reference"
docker_run run --rm --network none "$syft_reference" version \
  > "$evidence_directory/scanner/syft-version.txt"
docker_run run --rm --network none \
  --env GRYPE_CHECK_FOR_APP_UPDATE=false \
  "$grype_reference" version \
  > "$evidence_directory/scanner/grype-version.txt"

cp supply-chain/scanner-commands.txt \
  "$evidence_directory/scanner/commands.txt"

build_image() {
  image_name=$1
  dockerfile=$2
  attempt=$3
  tag=$4
  network_attempt=1
  while ! docker_run build \
      --pull \
      --no-cache \
      --build-arg SOURCE_DATE_EPOCH=1704067200 \
      --build-arg SLAIF_IMAGE_CREATED=2024-01-01T00:00:00Z \
      --build-arg "SLAIF_IMAGE_REVISION=$revision" \
      --build-arg SLAIF_IMAGE_VERSION=0.0.0 \
      --file "$dockerfile" \
      --tag "$tag" \
      .; do
    if [ "$network_attempt" -ge 3 ]; then
      echo "$image_name $attempt build failed after $network_attempt attempts" >&2
      return 1
    fi
    network_attempt=$((network_attempt + 1))
    echo "$image_name $attempt build: retry $network_attempt/3 in 30 seconds" >&2
    sleep 30
  done
  created_tags="$created_tags $tag"
}

inspect_image() {
  reference=$1
  output=$2
  docker_run image inspect "$reference" \
    | python -m tools.supply_chain.evidence normalize-image-metadata \
        --input - \
        --output "$output"
}

measure_browser_identity() {
  reference=$1
  metadata=$2
  output=$3
  image_id=$(python -c \
    'import json,sys; print(json.load(open(sys.argv[1]))["image_id"])' "$metadata")
  executable_version=$(docker_run run --rm --network none "$reference" sh -c \
    '"$BROWSER_WORKER_CHROMIUM_EXECUTABLE" --version')
  executable_sha256=$(docker_run run --rm --network none "$reference" sh -c \
    'sha256sum "$BROWSER_WORKER_CHROMIUM_EXECUTABLE" | cut -d" " -f1')
  python -m tools.supply_chain.evidence browser-identity \
    --output "$output" \
    --image-id "$image_id" \
    --executable-version "$executable_version" \
    --executable-sha256 "$executable_sha256" \
    --source-revision "$revision"
}

archive_image() {
  reference=$1
  destination=$2
  docker_run image save "$reference" > "$destination"
}

export_rootfs() {
  image_name=$1
  reference=$2
  attempt=$3
  destination=$4
  container="$run_identity-$image_name-$attempt"
  docker_run container create --name "$container" "$reference" >/dev/null
  created_containers="$created_containers $container"
  docker_run container export "$container" > "$destination"
  docker_run container rm "$container" >/dev/null
  created_containers=$(printf '%s' "$created_containers" | sed "s/ $container//")
}

generate_sbom() {
  image_name=$1
  archive=$2
  metadata=$3
  destination=$4
  browser_identity=$5
  raw="$temporary_root/$image_name.raw.spdx.json"
  docker_run run \
    --rm \
    --network none \
    --env HOME=/tmp \
    --env SYFT_CACHE_DIR=/tmp/syft-cache \
    --env SYFT_CHECK_FOR_APP_UPDATE=false \
    --volume "$archive:/scan/image.tar:ro" \
    "$syft_reference" \
    docker-archive:/scan/image.tar \
    --output spdx-json \
    > "$raw"
  image_id=$(python -c \
    'import json,sys; print(json.load(open(sys.argv[1]))["image_id"])' "$metadata")
  if [ -n "$browser_identity" ]; then
    python -m tools.supply_chain.evidence normalize-sbom \
      --input "$raw" \
      --output "$destination" \
      --image-name "$image_name" \
      --image-id "$image_id" \
      --source-revision "$revision" \
      --browser-identity "$browser_identity"
  else
    python -m tools.supply_chain.evidence normalize-sbom \
      --input "$raw" \
      --output "$destination" \
      --image-name "$image_name" \
      --image-id "$image_id" \
      --source-revision "$revision"
  fi
}

generate_scan_sbom() {
  image_name=$1
  archive=$2
  metadata=$3
  destination=$4
  browser_identity=$5
  raw="$temporary_root/$image_name.raw.syft.json"
  docker_run run \
    --rm \
    --network none \
    --env HOME=/tmp \
    --env SYFT_CACHE_DIR=/tmp/syft-cache \
    --env SYFT_CHECK_FOR_APP_UPDATE=false \
    --env SYFT_GOLANG_CAPTURE_SYMBOLS=stdlib \
    --volume "$archive:/scan/image.tar:ro" \
    "$syft_reference" \
    docker-archive:/scan/image.tar \
    --output syft-json \
    > "$raw"
  image_id=$(python -c \
    'import json,sys; print(json.load(open(sys.argv[1]))["image_id"])' "$metadata")
  archive_config_id=$(python -m tools.supply_chain.evidence archive-config-id \
    --archive "$archive")
  if [ -n "$browser_identity" ]; then
    python -m tools.supply_chain.evidence normalize-scan-sbom \
      --input "$raw" \
      --output "$destination" \
      --image-name "$image_name" \
      --image-id "$image_id" \
      --archive-config-id "$archive_config_id" \
      --source-revision "$revision" \
      --browser-identity "$browser_identity"
  else
    python -m tools.supply_chain.evidence normalize-scan-sbom \
      --input "$raw" \
      --output "$destination" \
      --image-name "$image_name" \
      --image-id "$image_id" \
      --archive-config-id "$archive_config_id" \
      --source-revision "$revision"
  fi
}

build_and_compare() {
  image_name=$1
  dockerfile=$2
  first_tag="$run_identity-$image_name:first"
  second_tag="$run_identity-$image_name:second"
  build_image "$image_name" "$dockerfile" first "$first_tag"
  build_image "$image_name" "$dockerfile" second "$second_tag"
  first_metadata="$evidence_directory/images/$image_name.json"
  second_metadata="$temporary_root/second/$image_name.image.json"
  inspect_image "$first_tag" "$first_metadata"
  inspect_image "$second_tag" "$second_metadata"
  first_browser_identity=""
  second_browser_identity=""
  if [ "$image_name" = browser-worker ]; then
    first_identity="$temporary_root/first/browser-runtime.json"
    second_identity="$temporary_root/second/browser-runtime.json"
    measure_browser_identity "$first_tag" "$first_metadata" "$first_identity"
    measure_browser_identity "$second_tag" "$second_metadata" "$second_identity"
    python - "$first_identity" "$second_identity" <<'PY'
import json
import sys

first = json.load(open(sys.argv[1], encoding="utf-8"))
second = json.load(open(sys.argv[2], encoding="utf-8"))
for key in (
    "cataloger",
    "executable",
    "executable_sha256",
    "executable_version",
    "source_archive_sha256",
    "source_archive_url",
    "source_revision",
):
    if first[key] != second[key]:
        raise SystemExit(f"browser identity drift: {key}")
PY
    first_browser_identity="$first_identity"
    second_browser_identity="$second_identity"
  fi
  first_archive="$temporary_root/first/$image_name.image.tar"
  second_archive="$temporary_root/second/$image_name.image.tar"
  archive_image "$first_tag" "$first_archive"
  archive_image "$second_tag" "$second_archive"
  first_sbom="$evidence_directory/sboms/$image_name.spdx.json"
  second_sbom="$temporary_root/second/$image_name.spdx.json"
  generate_sbom \
    "$image_name" "$first_archive" "$first_metadata" "$first_sbom" "$first_browser_identity"
  generate_sbom \
    "$image_name" "$second_archive" "$second_metadata" "$second_sbom" "$second_browser_identity"
  generate_scan_sbom \
    "$image_name" \
    "$first_archive" \
    "$first_metadata" \
    "$evidence_directory/scan-sboms/$image_name.syft.json" \
    "$first_browser_identity"
  first_rootfs="$temporary_root/first/$image_name.rootfs.tar"
  second_rootfs="$temporary_root/second/$image_name.rootfs.tar"
  export_rootfs "$image_name" "$first_tag" first "$first_rootfs"
  export_rootfs "$image_name" "$second_tag" second "$second_rootfs"
  first_files="$evidence_directory/manifests/$image_name.files.json"
  second_files="$temporary_root/second/$image_name.files.json"
  python -m tools.supply_chain.evidence rootfs-manifest \
    --archive "$first_rootfs" \
    --output "$first_files" \
    --image-name "$image_name"
  python -m tools.supply_chain.evidence rootfs-manifest \
    --archive "$second_rootfs" \
    --output "$second_files" \
    --image-name "$image_name"
  python -m tools.supply_chain.evidence compare-builds \
    --first-sbom "$first_sbom" \
    --second-sbom "$second_sbom" \
    --first-files "$first_files" \
    --second-files "$second_files" \
    --first-metadata "$first_metadata" \
    --second-metadata "$second_metadata" \
    --output "$evidence_directory/reproducibility/images/$image_name.json" \
    --image-name "$image_name"
}

build_and_compare backend services/backend/Dockerfile
build_and_compare browser-worker services/browser-worker/Dockerfile
build_and_compare web apps/web/Dockerfile
build_and_compare nginx infra/nginx/Dockerfile
build_and_compare apache infra/apache/Dockerfile
build_and_compare postgres infra/postgres/Dockerfile

docker_run run \
  --rm \
  --user "$(id -u):$(id -g)" \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=512m,mode=1777 \
  --env GRYPE_CHECK_FOR_APP_UPDATE=false \
  --env GRYPE_DB_CACHE_DIR=/database \
  --volume "$temporary_root/grype-db:/database" \
  "$grype_reference" \
  db update
docker_run run \
  --rm \
  --network none \
  --user "$(id -u):$(id -g)" \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=512m,mode=1777 \
  --env GRYPE_CHECK_FOR_APP_UPDATE=false \
  --env GRYPE_DB_AUTO_UPDATE=false \
  --env GRYPE_DB_CACHE_DIR=/database \
  --volume "$temporary_root/grype-db:/database" \
  "$grype_reference" \
  db status -o json \
  | python -m tools.supply_chain.evidence normalize-database-status \
      --input - \
      --output "$evidence_directory/scanner/grype-database.json"

for image_name in apache backend browser-worker nginx postgres web; do
  sbom="$evidence_directory/scan-sboms/$image_name.syft.json"
  raw_scan="$temporary_root/$image_name.raw.grype.json"
  sbom_sha256=$(sha256sum "$sbom" | cut -d' ' -f1)
  docker_run run \
    --rm \
    --network none \
    --user "$(id -u):$(id -g)" \
    --tmpfs /tmp:rw,noexec,nosuid,nodev,size=512m,mode=1777 \
    --env GRYPE_CHECK_FOR_APP_UPDATE=false \
    --env GRYPE_DB_AUTO_UPDATE=false \
    --env GRYPE_DB_CACHE_DIR=/database \
    --volume "$temporary_root/grype-db:/database" \
    --volume "$evidence_directory:/evidence:ro" \
    "$grype_reference" \
    "sbom:/evidence/scan-sboms/$image_name.syft.json" \
    --output json \
    > "$raw_scan"
  python -m tools.supply_chain.evidence normalize-scan \
    --input "$raw_scan" \
    --output "$evidence_directory/scans/$image_name.grype.json" \
    --image-name "$image_name" \
    --sbom-sha256 "$sbom_sha256"
done

python -m tools.supply_chain.evidence finalize \
  --evidence "$evidence_directory" \
  --revision "$revision"
python -m tools.supply_chain.evidence validate-bundle \
  --evidence "$evidence_directory"

git diff --exit-code -- uv.lock pnpm-lock.yaml THIRD_PARTY_NOTICES.md
run_succeeded=1
echo "supply-chain-gate: OK evidence=$evidence_directory"
