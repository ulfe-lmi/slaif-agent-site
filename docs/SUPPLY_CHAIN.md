# Supply-chain verification

SLAIF Agent-Site has a self-hosted build gate for frozen dependencies,
reproducible application artifacts, OCI package inventories, and current
vulnerability evidence. The gate is build and CI tooling. Syft and Grype do not
enter a product image, dependency lock, or runtime service.

The authoritative machine-readable contract is
[`supply-chain/policy.json`](../supply-chain/policy.json). It records exact
registries, GitHub Action commits, readable OCI tags with top-level digests,
scanner versions and digests, license categories, vulnerability thresholds,
evidence formats, and retention. Exception files are governed inputs, not an
invitation for an automated agent to suppress a failure.

## Trust and network model

The gate consumes committed source, `uv.lock`, `pnpm-lock.yaml`, exact OCI
references, installed frozen metadata, and the public Grype vulnerability
database. It rejects mutable external dependency sources, mutable actions or
images, unapproved package registries, package lifecycle scripts, hosted SDK
prefixes, and enabled-by-default telemetry.

Only these operations need public network access:

- frozen package or exact image acquisition when the local cache is empty; and
- `grype db update`, which obtains a public vulnerability database without an
  account.

Syft catalogs saved local image archives with no network. Grype database status
and all six vulnerability matches run with no network after the update. Scanner
containers receive neither the Docker socket nor source, site data, credentials,
database volumes, browser artifacts, or host files outside the exact read-only
evidence inputs.

The policy pins these build-only scanners:

| Tool | Version | Exact image digest source | License |
| --- | --- | --- | --- |
| Syft | `1.51.0` | `supply-chain/policy.json` `scanner_tools.syft.image` | Apache-2.0 |
| Grype | `0.117.0` | `supply-chain/policy.json` `scanner_tools.grype.image` | Apache-2.0 |

The policy also records the reviewed source commit and SHA-256 values of each
release checksum, signature, and certificate file. This is recorded provenance,
not a signed project attestation or SLSA claim.

## Reproduce the checks locally

Use the repository's exact Node, pnpm, Python, and uv versions. The complete
gate needs Docker Engine and enough temporary disk for two clean builds of each
project image. Its destination must not already exist.

```bash
uv sync --frozen --all-groups
pnpm install --frozen-lockfile
uv run --frozen python -m tools.supply_chain.policy validate
uv run --frozen python -m tools.supply_chain.policy notices --check
uv run --frozen python -m tools.supply_chain.reproducible \
  --output /tmp/slaif-reproducibility
tools/supply_chain/run.sh /tmp/slaif-supply-chain-evidence
python -m tools.supply_chain.evidence validate-bundle \
  --evidence /tmp/slaif-supply-chain-evidence
```

The all-in-one runner repeats the policy, notice, and artifact checks itself.
The separate commands are useful for focused diagnosis. To regenerate the
committed application notice after an authorized dependency or review-map
change, run:

```bash
uv run --frozen python -m tools.supply_chain.policy notices
uv run --frozen python -m tools.supply_chain.policy notices --check
```

Notice generation reads the frozen local environments. It must not query a
mutable registry to rewrite committed attribution.

## Reproducibility contract

The fixed `SOURCE_DATE_EPOCH` is `1704067200`, or
`2024-01-01T00:00:00Z`. Ordinary Compose builds inject honest defaults of
version `0.0.0` and revision `local`; CI injects its verified full commit SHA.

The gate proves the following bounded contracts:

- One wheel and one source distribution are built twice from clean copied
  Python sources with frozen, offline uv inputs. Names, sizes, and SHA-256
  values must be byte-identical.
- Next.js receives a stable 32-hex build ID derived from sorted, versioned Web,
  package, configuration, lock, and logo inputs. Two clean Web builds must have
  identical distributed path, mode, size, link-target, and content digests.
- The browser worker compiles its frozen TypeScript source and declares exact
  `playwright-core==1.62.1`. Its normalized source/security-profile manifest,
  deployed production package closure, and retained Chromium revision-1234
  runtime tree must reproduce exactly.
- Every project image is built twice with the same exact inputs and without a
  Docker build cache. Normalized package inventories and application runtime
  files must match.

Whole BuildKit image IDs are outside the reproducibility claim. BuildKit may
create different OCI wrapper, attestation, and layer metadata even when the
runtime filesystem and package graph are equal. Evidence therefore records
both the daemon/index image ID and the SHA-256-verified config blob ID in the
saved image archive. For Web runtime files only, the gate normalizes the three
named Next.js preview keys and the named server-action encryption key in their
three exact manifest files. An unrelated file or field difference still fails.

Generated OpenAPI or product contracts are currently absent and must remain so
until an owning product objective defines them. Build caches and generated
distributions are ignored and must not become tracked source.

## Image and SBOM coverage

The evidence covers exactly:

1. `slaif-agent-site-backend:local`;
2. `slaif-agent-site-browser-worker:local`;
3. `slaif-agent-site-web:local`;
4. `slaif-agent-site-nginx:local`;
5. `slaif-agent-site-apache:test`; and
6. the exact PostgreSQL image pinned by Compose.

Each image has normalized SPDX 2.3 JSON under `sboms/`. The SPDX document is
the interoperable retained inventory and includes packages, relationships,
PURLs or CPEs where Syft provides them, creator version, image association, and
source revision. A second normalized Syft JSON document under `scan-sboms/`
retains Go standard-library symbol evidence needed for accurate Grype matches.
Grype scans that checksummed document; the index links both forms.

The browser worker uses the digest-pinned official Playwright 1.62.1 Noble
image, Node 24.18.1, exact `playwright-core==1.62.1`, and Chromium revision 1669021
(`152.0.7977.64`). The exact linux/amd64 archive is SHA-256 verified before
extraction by the bounded source-controlled parser. Its runtime removes
Firefox, WebKit, the duplicate Chromium
headless shell, ffmpeg, npm, and Corepack. Evidence requires the worker package
and `playwright-core`, rejects Firefox/WebKit inventory, and hashes the retained
`/ms-playwright/chromium-1669021` tree during both clean image builds. The separate
root E2E runner still installs all three test-only browser families outside the
product image.

## Vulnerability gate and database freshness

Grype must successfully update and report a valid database whose build time is
at most 120 hours old. Evidence records its build timestamp, official source
checksum, and age at validation. Acquisition failure, malformed status, stale
data, missing image coverage, missing scan, or checksum drift fails closed.

Every unexcepted `Critical` finding fails, including one with no fix. `High`
findings do not pass silently: per-image and total counts remain in JSON,
`SUMMARY.txt`, and human-readable scan summaries as review evidence. Lower and
unknown severity counts also remain visible. A pass means zero unexcepted
Critical findings in that time-bounded database; it does not mean zero
vulnerabilities. The temporary 2026-08-28 human-approved exception for the
41 unavoidable Chrome 152.0.7977.64 Critical findings is recorded in
[`supply-chain/vulnerability-exceptions.json`](../supply-chain/vulnerability-exceptions.json)
and tracked at [issue #67](https://github.com/ulfe-lmi/slaif-agent-site/issues/67).
It expires 2026-09-04, applies only to `browser-worker`, and must be removed
when official stable 152.0.7977.65 or newer is available. Validation requires
every entry to match a current Critical finding's exact ID, PURL, and scope;
unused, stale, near-match, duplicate, or wrong-severity entries fail closed.

## Evidence bundle

The runner creates deterministic UTF-8 JSON/text evidence plus exact binary
Python application artifacts with this shape:

```text
artifacts/          retained Python wheel and source distribution
dependencies/       Python/npm and source/action/image inventories
images/              normalized image identity and OCI labels
manifests/           normalized project runtime file manifests
reproducibility/     application and per-image comparison results
sboms/               six normalized SPDX 2.3 documents
scan-sboms/          six normalized symbol-aware Syft documents
scanner/             tool versions and vulnerability database status
scans/               six normalized Grype JSON and text summaries
index.json           image, base, SBOM, scan, count, and checksum mapping
SUMMARY.txt          bounded human summary
SHA256SUMS           checksum of every preceding evidence file
```

Finalization validates expected components, OCI labels, revision association,
database age, scan-source checksums, and all six targets. It scans every text or
binary file bytewise and rejects configured host path prefixes, DSNs,
private-key markers, token-like markers, and Docker socket references before
writing `SHA256SUMS`. Bundle validation then recomputes every checksum and
rejects missing, extra, or tampered content relative to that manifest.

CI uploads exactly this directory with the full commit SHA in the artifact name.
The official upload action is full-commit pinned, rejects an empty path, does
not overwrite, excludes hidden files, and retains the artifact for 14 days.
The artifact is private CI evidence, not a release, publication, or deployment.

Image publication requires a separate durable review and packaging step for
OS/runtime license texts, notices, and any applicable source-offer material.
The 14-day CI artifact preserves time-bounded inventory evidence but is not a
durable release notice or source-offer bundle. No image may be published based
only on that artifact.

## Exceptions and updates

Both exception lists are empty by default; the only current vulnerability
exception is the owner-approved, seven-day Chrome 152.0.7977.64 entry set of
41 current findings tracked by [issue #67](https://github.com/ulfe-lmi/slaif-agent-site/issues/67).
An entry requires all of:

- exact vulnerability ID or license expression in `identifier`;
- exact package PURL in `affected`;
- exact image key for a vulnerability or dependency scope for a license in
  `scope`;
- meaningful rationale and `human:` approver identity;
- exact GitHub issue or pull-request review URL; and
- creation and expiry dates no more than 90 days apart.

Wildcards, duplicates, expired entries, missing fields, non-human approvers,
and broader lifetimes fail. Vulnerability entries must also match an actual
current Critical finding with the exact identifier, PURL, and scope; unused,
stale, near-match, and wrong-severity entries fail closed. A valid exception
changes only the conclusion for that exact finding; it never removes the
component or finding from evidence. Coding agents must not author an exception
merely to make a gate green. The owner removes this exception or upgrades to
official stable Chrome 152.0.7977.65+ immediately when available and no later
than its 2026-09-04 expiry.

An authorized update must preserve readable tags plus top-level digests,
review source/license/signature metadata, update the machine policy and narrow
tests, regenerate notices when application metadata changes, and rerun the
complete evidence and Compose gates. Language and PostgreSQL major versions,
edge families, scanner choices, or runtime dependencies require explicit
strategic scope.

## Limitations

This repository is pre-alpha. Green evidence is time-bounded engineering
evidence, not proof that vulnerabilities are absent, legal certification, a
complete provenance attestation, signature verification for project images,
SLSA certification, release approval, or production readiness. OS package
license metadata may be incomplete and is retained for legal review rather
than reclassified as permissive. See the
[license policy](LICENSE_POLICY.md) for the application/data/OS distinction.
