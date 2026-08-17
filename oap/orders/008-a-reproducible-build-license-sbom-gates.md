# OAP Work Order — 008-a

## Objective

Create exactly one new GitHub pull request that establishes professional,
self-hosted supply-chain gates for the accepted deployment skeleton:

- frozen and reproducible application artifacts;
- exact dependency/source/action/base-image provenance;
- strict application-license policy plus explicit container/OS review policy;
- deterministic third-party notices;
- SPDX/CycloneDX OCI SBOMs for every default/reference image;
- critical-vulnerability scanning with explicit, expiring human-approved
  exceptions only; and
- retained, checksummed, secret-free CI evidence.

Do not add product behavior, a runtime service, or a hosted/account-bound
dependency. This objective makes the existing build verifiable before feature
development expands its dependency and image surface.

## GitHub objective state

- Numeric objective: `008`
- Execution round: `008-a`
- PR mode: `CREATE_NEW_PR`
- Existing objective PR: N/A
- Required head branch: `oap/008-supply-chain-build-gates`
- Base branch: `main`
- Required PR title: `[OAP 008] Add reproducible supply-chain and SBOM gates`
- Required PR readiness: non-draft (`draft: false`)
- Repository: `ulfe-lmi/slaif-agent-site`

## Strategic context

Objectives `003`–`007` are accepted and merged. Remote `main` is:

```text
cc09342664a8ce60414474fd8d308ee459cd0dda
```

The repository now has a fully frozen Python/Node baseline and a digest-pinned
15-service one-command Compose skeleton. The current CI verifies repository
policy, Python 3.12–14, PostgreSQL 14–18, Node contracts, Markdown, Mermaid,
dependency review, Compose/edge packaging, and CodeQL. It does not yet produce
OCI SBOMs, scan image vulnerability contents, enforce a complete license/
source exception model, prove repeatable application artifacts, or retain a
machine-readable evidence bundle.

PR `#10` is merged with its complete two-round transcript. No pull request is
currently open. PR `#5` and PR `#7` remain closed without merge; do not act on
them. `oap/active` contains the merged identifier `007-b`; this activation
changes it to `008-a`.

Selected build-only scanner baseline, verified from official releases at
activation time:

```text
Anchore Syft v1.51.0   Apache-2.0
Anchore Grype v0.117.0 Apache-2.0
```

Use their official container/CLI distribution at exact version and immutable
digest, after execution-time source/signature/checksum/license review. Do not
silently change tools or versions. Grype may download its public vulnerability
database during CI without an account; record its build/checksum/age and fail
closed if a sufficiently fresh database cannot be obtained. The scanners are
build/CI tools, not runtime dependencies and must not enter product images or
Python/Node locks.

## Allowed path scope

Keep the diff within these paths/families plus the required OAP transcript:

```text
.dockerignore
.github/workflows/ci.yml
.gitignore
AGENTS.md
CONTRIBUTING.md
NOTICE
README.md
THIRD_PARTY_NOTICES.md
apps/web/Dockerfile
apps/web/next.config.mjs
compose.yaml
docs/DEPLOYMENT.md
docs/LICENSE_POLICY.md
docs/OPERATIONS.md
docs/SUPPLY_CHAIN.md
infra/apache/Dockerfile
infra/nginx/Dockerfile
package.json
pyproject.toml
services/backend/Dockerfile
services/browser-worker/Dockerfile
supply-chain/**
tests/packaging/**
tests/repository/test_repository_policy.py
tests/supply_chain/**
tools/check_repository.py
tools/compose/**
tools/supply_chain/**
oap/active
oap/orders/008-a-reproducible-build-license-sbom-gates.md
oap/reports/008-a-reproducible-build-license-sbom-gates.md
```

`uv.lock` and `pnpm-lock.yaml` should remain byte-identical because no product
or development dependency is authorized. If a tool cannot be implemented as a
standard-library script or pinned build container and would require a lock
change, stop and report rather than adding it. Do not edit Architecture,
Security, either OAP protocol, product migrations/contracts/source behavior,
NGINX/Apache route semantics, service/network/port/secret topology, or prior
OAP artifacts.

## Scope and requirements

### A. Supply-chain policy model

Add one machine-readable, schema-validated policy under `supply-chain/` that
defines:

- approved application dependency SPDX expressions/categories;
- prohibited license families: AGPL, SSPL, BUSL/BSL, Elastic License, Commons
  Clause, noncommercial, field-of-use, source-available, and unknown direct
  application license;
- separately reviewed attribution/data categories already present, including
  `CC-BY-4.0` for `caniuse-lite` compatibility data and `0BSD`/BlueOak where
  applicable;
- container operating-system/runtime aggregation policy that inventories GPL/
  LGPL/other system packages without falsely treating normal OS aggregation as
  an application-library license grant;
- denied hosted/account-bound SDK/package prefixes and telemetry defaults;
- exact registry/source requirements for Python, npm, GitHub Actions, OCI base
  images, the foundation package, and scanner tools;
- vulnerability severity/fix policy and exception schema; and
- evidence formats, retention, normalization, and checksum rules.

Policy must distinguish:

```text
strict automatic application dependency gate
explicit data/font attribution review
container OS/runtime inventory and legal-review evidence
```

Do not claim this automation is legal advice or a complete license opinion.
Unknown/unparseable direct application licenses fail. Unknown OS metadata is
retained and highlighted for review, never silently called permissive.

### B. Explicit exception governance

Provide empty-by-default machine-readable exception files for license and
vulnerability exceptions. Each possible entry requires:

```text
stable package/PURL or vulnerability identifier
affected version/image
rationale
human approver/reference
created date
expiry date
bounded scope
```

CI rejects malformed, duplicate, wildcard, missing-approver, already-expired,
or excessively long-lived entries. The coding agent may not add an exception
to make this objective green. If the current tree has a prohibited license or
critical vulnerability, update/remove the dependency/base image within this
same PR only if unambiguously compatible and inside scope; otherwise report a
human decision/blocker.

An exception never suppresses inventory; it changes only the gate conclusion
for its exact unexpired scope.

### C. Deterministic dependency inventories and notices

Use frozen/offline-capable inputs to build normalized inventories for:

- Python direct/transitive production and development/test/build groups;
- npm direct/transitive production and development workspaces;
- GitHub Actions with full commit SHA and source repository;
- OCI base images and build-tool images with readable tag and top-level digest;
- each built product/reference image's OS/runtime/application packages.

Generate `THIRD_PARTY_NOTICES.md` deterministically from reviewed inventory
inputs. It must include component, version, ecosystem/type, license expression
or review status, source/homepage/provenance, and required attribution notes
without copying enormous license bodies. Retain the project/upstream
attribution already required by `NOTICE`; update `NOTICE` only to point to the
generated complete inventory or retain required upstream notice text.

Generation must be stable under repeated runs and CI fails on committed notice
drift. Do not query a mutable network registry to generate committed notices
after frozen inputs are present; use lockfiles, installed metadata, OCI/SBOM
metadata, and a source-controlled review map. Network verification may compare
but not silently rewrite.

### D. Reproducible application artifacts

Define and test a precise reproducibility contract rather than overclaiming
byte-identical OCI manifests when tool-created timestamps are outside the
contract.

At minimum:

- set/document one valid deterministic `SOURCE_DATE_EPOCH` policy;
- build Python wheel and sdist twice from clean copied source with frozen uv
  inputs and prove byte-identical SHA-256 outputs, or report and eliminate the
  exact nondeterministic field before acceptance;
- give Next.js a deterministic build ID derived from versioned source/lock
  inputs, not current time/randomness/host state;
- build Web/browser-worker outputs twice and compare normalized file path,
  mode, size, and SHA-256 manifests excluding only explicitly documented
  non-distributed caches;
- verify generated OpenAPI/product contracts are absent or deterministic as
  appropriate to current scope;
- build product images with fixed base digests/frozen dependencies and compare
  normalized SBOM/package/application-file manifests across two clean builds;
  if whole image IDs are not byte-identical, record the exact acceptable OCI
  metadata/layer-time source rather than claiming reproducible IDs;
- ensure no build output is tracked unintentionally.

One-command local startup must remain unchanged in usability. Do not require a
human to calculate an epoch or build ID.

### E. OCI metadata and SBOM coverage

Add standard OCI labels to every project-built image:

```text
org.opencontainers.image.title
org.opencontainers.image.description
org.opencontainers.image.source
org.opencontainers.image.licenses
org.opencontainers.image.version
org.opencontainers.image.revision
org.opencontainers.image.created
```

Local defaults may use honest `0.0.0`, `local`, and the deterministic epoch;
CI/release builds inject the verified commit SHA without making the ordinary
one-command build fail.

Generate a normalized SPDX 2.3 JSON SBOM (and optionally CycloneDX JSON) for
each of:

```text
slaif-agent-site-backend:local
slaif-agent-site-browser-worker:local
slaif-agent-site-web:local
slaif-agent-site-nginx:local
slaif-agent-site-apache:test
the exact pinned PostgreSQL image used by Compose
```

Each SBOM must include image digest/ID, OS packages, language packages,
application distribution/files where supported, PURLs/CPEs where available,
license fields, relationships, creator/tool version, and a source-revision
association. Validate schema/basic semantics and prove expected key components
appear in the correct images while forbidden packages/secrets/host paths do
not.

Produce an SBOM/checksum index mapping image, immutable source/base reference,
SBOM filename, SHA-256, package counts by type, and scan result. Browser binary
inventory is currently correctly empty; the policy/test must be ready to
require it once Playwright enters later.

### F. Vulnerability gate

Scan each normalized image SBOM with exact Grype and a fresh recorded database.

- Fail on any unexcepted `Critical` vulnerability, whether or not a fix is
  currently available; report High findings as non-passing review evidence but
  do not make them disappear. If project policy deliberately chooses a
  fix-available distinction, encode and justify it explicitly and keep the
  unfixable Critical visible.
- Fail when scanner execution/database acquisition is skipped, stale beyond a
  documented short bound, malformed, or incomplete for any required image.
- Pin/record scanner image/version/digest, database build timestamp/checksum,
  source SBOM checksum, command, result counts, and exception applications.
- Use JSON and human-summary outputs. Do not upload source/site data or contact
  a hosted account.
- Scan the scanner images' provenance/license/digest as build tools; avoid an
  infinite recursive scan requirement.

If current immutable base tags/digests contain an unexcepted Critical, update
to a compatible reviewed patch-level base digest with the same architecture
family and rerun the complete Compose gate. Do not silently change language,
PostgreSQL major version, NGINX/Apache family, or product dependency.

### G. Source and dependency drift checks

Extend deterministic policy/tests to reject:

- VCS/direct URL/local path/editable foundation or external production
  dependency;
- unlocked/mutable runtime dependency, npm range, unapproved registry, package
  patch/link/workspace escape, or unapproved install script;
- unpinned GitHub Action or mutable OCI base/scanner reference;
- hosted/cloud/account SDK prefixes and telemetry enabled by default;
- unknown direct license or prohibited license expression;
- image/package absent from the required evidence index;
- SBOM/notice/checksum drift;
- generated secret, DSN, private key, token-shaped value, Docker socket, host
  path, or source bind in evidence/product images.

Existing legitimate project/workspace editable records must be recognized as
the local project, never misclassified as an external dependency.

### H. CI evidence bundle

Add a bounded supply-chain CI job after/alongside the existing Compose job.
It must:

1. perform frozen installs and deterministic application-artifact checks;
2. build/pull the exact six image targets;
3. run existing Compose/edge policy where needed;
4. generate and validate all SBOMs;
5. run license/source/hosted-SDK policy;
6. run vulnerability scans against a fresh database;
7. regenerate/compare third-party notices;
8. create normalized JSON/text summaries and SHA-256 manifest;
9. scan the evidence bundle itself for secrets/host paths; and
10. upload the bundle as a GitHub Actions artifact with a documented bounded
    retention using an exact full-SHA-pinned official upload action.

Add the upload action to the repository's exact action allowlist only after
official source/license/version/SHA review. CI artifacts are evidence, not
release publication or runtime dependency. The job must fail if artifact
creation/upload is skipped on a successful PR run.

Avoid redundant full image builds where safe by reusing a job-local accepted
build; never trust a mutable cross-run image tag or external cache as evidence.

### I. Tests and documentation

Add standard-library policy/unit/negative tests covering every rejection class,
exception expiry/schema, deterministic sort/normalization, checksum tamper,
notice drift, missing image/SBOM, malformed scanner result, stale DB, critical
finding, unknown/prohibited license, hosted SDK, mutable source/action/image,
and secret/path leakage.

Add:

- `docs/SUPPLY_CHAIN.md` for trust model, tools, commands, evidence, scanner DB,
  update process, exceptions, CI retention, and limitations;
- `docs/LICENSE_POLICY.md` for application/data/font/OS distinctions,
  allow/deny/review categories, attribution, and legal-review disclaimer; and
- deterministic `THIRD_PARTY_NOTICES.md`.

Update deployment/operations/README/CONTRIBUTING/AGENTS only as necessary.
Keep the project pre-alpha. State explicitly that green scans are time-bounded
evidence, not absence of vulnerabilities, legal certification, provenance
attestation, or production readiness.

## Explicit non-goals

- No product feature, route, schema/table, service, image target, network,
  volume, port, credential, authentication, browser, Puck, review, promotion,
  publication, or runtime dependency.
- No Playwright/browser binary yet; the SBOM gate must report that truthfully.
- No hosted scanner/dashboard, mandatory registry account, cloud key,
  Dependabot auto-merge, release upload, package publication, signing, keyless
  OIDC attestation, SLSA certification, deployment, tag, or GitHub setting.
- No automatic legal approval, silent license/vulnerability exception,
  vulnerability database vendoring without explicit policy, broad suppress,
  severity downgrade, action-pin relaxation, or matrix reduction.
- No action on historical PR `#5`/`#7`, second objective PR, merge, or
  auto-merge.

## Acceptance criteria

1. Exactly one non-draft objective-008 PR exists with required identity and
   complete versioned OAP transcript; the coding agent does not merge.
2. Python and Web/browser application artifacts reproduce byte-for-byte or
   under an explicit narrower normalized contract with every nondeterministic
   field identified; dependency graphs and app-file manifests are identical.
3. All six image targets have valid normalized SPDX SBOMs and a checksummed
   index containing expected OS/language/application components, exact image/
   base/revision identity, and no secret/host leakage.
4. Exact pinned Syft/Grype tools and a fresh recorded vulnerability database
   scan every SBOM; every unexcepted Critical is zero and High/other counts
   remain visible. No required scan is skipped.
5. Strict application dependency source/license policy passes; prohibited/
   unknown direct licenses, hosted SDKs, mutable sources/actions/images, and
   unapproved install behavior fail deterministic negative tests.
6. OS/runtime and attribution-bearing data licenses are inventoried under their
   distinct policy; deterministic notices retain foundation/upstream and all
   current attribution obligations without overclaiming legal approval.
7. Exception files are empty unless explicitly human-approved and their schema,
   bounded scope, approver, and expiry behavior are enforced.
8. OCI labels/base/scanner references are exact and immutable; one-command
   Compose, service/network/secret/role/CSP/request-ID behavior, and all
   accepted 007 invariants remain green.
9. CI creates, validates, secret-scans, checksums, and retains one complete
   evidence artifact; upload and every required current gate succeed on the
   final head with zero open CodeQL alert.
10. Documentation and machine-readable policy state exact guarantees,
    limitations, update/exception procedures, and evidence reproduction
    commands without a release/legal/production-readiness claim.
11. `oap/active` is `008-a`, unique order/report correlation holds, prior
    artifacts remain immutable, and final remote head is report-only `SELF`
    with the literal implementation parent recorded.

## Verification required

Run the complete existing Python 3.12–14, PostgreSQL 14–18, Node, repository,
Markdown, Mermaid, Compose/edge, package, and CodeQL gates plus the new
reproducibility/supply-chain suite.

Report exact commands/results for:

- two clean Python distribution builds and hashes;
- two clean Web/browser output builds and normalized manifests;
- two clean image builds or normalized SBOM/application-file equivalence;
- OCI labels and immutable base/scanner tool references;
- all six SBOM generation/schema/semantic checks and checksums;
- dependency/action/image/registry/license/hosted-SDK inventories;
- deterministic notice regeneration with zero diff;
- vulnerability database identity/age/checksum and six scan result counts;
- every negative policy fixture and exception validation;
- evidence-bundle file/index/checksum/secret scan and CI artifact upload;
- unchanged Compose clean/restart/failure behavior;
- exact PR/scope/protected/prior-artifact hashes, checks/alerts, report parent/
  delta, and clean synchronized worktree.

No scanner, image, license, reproducibility, artifact-upload, or current
regression gate may be skipped. External scanner database or registry outage is
a reported blocker, not permission to manufacture success.

## Safety / security constraints

Use only public package/image/scanner metadata and fake local deployment data.
Never upload generated local secrets, database volumes, logs containing
credentials, private source/site data, or host paths. Build evidence in a
system temporary directory with exact cleanup. Do not prune broad Docker state
or mutate unrelated resources. Do not add an exception without human approval.

## Local execution capability

Routine image builds, scanner installation/use, vulnerability DB acquisition,
license/SBOM diagnosis, deterministic-build work, Docker cleanup, and CI-log
inspection belong to the coding agent in its disposable VM. Passwordless
`sudo` is available. Do not transfer setup to the human or strategic model.

## GitHub workflow

Create `oap/008-supply-chain-build-gates` from current remote `main`. Preserve
the activated order/pointer, implement only this supply-chain slice, run all
gates, push, and create exactly one non-draft PR with the required title.
Repair in-scope failures on that same PR. Never create another objective PR,
touch historical PRs, merge, enable auto-merge, release, or choose `009-a`.

## Required report

Atomically publish exactly:

```text
oap/reports/008-a-reproducible-build-license-sbom-gates.md
```

Use protocol 1.2 in full. Include exact tool/action/base provenance; artifact
reproducibility results; dependency/license/source/notice inventories; six
SBOM and vulnerability results; database identity; exception state; evidence
bundle/index/upload; all tests/checks/alerts; limitations; scope/security/
no-merge confirmations; literal implementation head; and
`Report publication commit: SELF`. Push and verify the report-only commit and
parent before FIFO `OK`; strategic review will independently verify the fresh
head checks.
