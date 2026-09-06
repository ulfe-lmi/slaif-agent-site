# OAP Coding-Agent Report — 077-o

## Work order

- Identifier: `077-o`
- Work-order file: `oap/orders/077-o-close-security-and-snapshot-proof.md`
- Work-order SHA-256: `67593f71fb0eea50d46b57e7452c010f3e476ee17055a7dc528c68b6c6e1c905`
- Active SHA-256: `3a9b814249542f6162a140c06d0d4e9aa423257107007dd43bf639169e539cca`
- Numeric objective: `077`
- PR mode: `AMENDED_EXISTING_PR`

## Status

`BLOCKED`

## Executive summary

The authorized Ubuntu 24.04 LTS Apache replacement is implemented and
qualified. Two reproducible builds, Apache configuration validation, Compose
edge behavior, SBOM/license evidence, and the Apache-specific Grype gate pass;
the Apache image has zero unexcepted Critical findings.

Objective 077-o remains blocked for two concrete reasons. First, the required
full-image supply-chain gate fails on eight existing Postgres `libcurl`
Critical vulnerabilities, all with a fixed Alpine version available, but that
unrelated Postgres image is outside this order's Apache scope. Second, the
required causal repeatable-read preview proof cannot be executed through the
intended public Agent writes under the current lock contract: the paused
human-preview COW transaction holds the workspace shared lifecycle lock while
the Agent structural mutation path requires the exclusive workspace lock.
Awaiting the Agent commits before releasing the read snapshot therefore
deadlocks/timeouts and returns `SERVICE_UNAVAILABLE`; releasing first is the
false-positive proof this order explicitly prohibits.

No vulnerability exception, scanner suppression, severity override, lock
weakening, or false passing test was committed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), `OPEN`, not
  merged
- Base/head: `main` /
  `oap/077-agent-site-structure-semantics`
- Starting remote report head:
  `f287acc9a176186e0354bc18aff163204e8db347`
- Implementation head SHA:
  `49ad633012d8193406de6ca5c03b769b215198c6`
- Parent of implementation:
  `f287acc9a176186e0354bc18aff163204e8db347`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (to be verified after push)
- New PR: no; existing PR amended: yes; merge/auto-merge: NO

## Changes made

- Replaced the failed official Debian Trixie Apache fallback with the exact
  Docker Official Ubuntu source:
  `docker.io/library/ubuntu:24.04@sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517`.
- Reverified the observed linux/amd64 manifest:
  `sha256:1e0a86e57d247923571b75e0aaf48a1449cf8c543d51fb3e07a4a7d7bfa79316`.
- Pinned Ubuntu standard-repository packages:
  `apache2`, `apache2-bin`, `apache2-data`, `apache2-utils` at
  `2.4.58-1ubuntu8.15`; `openssl` at `3.0.13-0ubuntu3.15`; the resulting
  image reports glibc `2.39-0ubuntu8.8`.
- Adapted the Apache package layout to `/etc/apache2`, enabled the existing
  required modules, preserved the routing/header/limit configuration, kept a
  foreground `apachectl` process, and corrected the Compose parity probe from
  `httpd -t` to `apachectl -t`.
- Updated the supply-chain policy, package contract, evidence boundary and
  supply-chain documentation. Other image pins and exception sets were not
  changed.
- Committed the exact strategy bytes for `077-o` and `oap/active` unchanged.

## Files changed

- `infra/apache/Dockerfile`
- `supply-chain/policy.json`
- `tools/supply_chain/policy.py`
- `tools/supply_chain/evidence.py`
- `tools/compose/smoke.sh`
- `tests/packaging/test_oci_contract.py`
- `docs/SUPPLY_CHAIN.md`
- exact strategy bytes: `oap/orders/077-o-close-security-and-snapshot-proof.md`,
  `oap/active`

## Acceptance-criteria evidence

### Ubuntu Apache qualification

- Two reproducible Ubuntu Apache builds completed in
  `sh tools/supply_chain/run.sh /tmp/slaif-077o-supply-chain-evidence-3`.
  Normalized package manifests and Apache application files compared equal;
  the evidence reports `application_files_equal: true` and
  `package_manifests_equal: true`.
- First and second build manifest-list digests were
  `sha256:5297d518fe9d98d47aa5e0465f6554a258696f974502f62f314c56f6e8a16006`
  and
  `sha256:b347251407434b281e47146cf8e4a95eb7a3b2b6d36cbf42826c9c081c273311`.
- `apachectl -t`: PASSED for both builds and the final Compose Apache probe.
- Compose/NGINX/Apache parity and clean edge behavior: PASSED in
  `sh tools/compose/smoke.sh slaif007o2`; the corrected run ended with
  `compose-smoke: OK` and 48 packaging tests passed.
- SBOM and license inventory completed for all six required images. Syft
  `1.51.0` and Grype `0.117.0` were run from their exact pinned scanner
  images. The fresh Grype database was valid, built
  `2026-09-05T06:27:00Z`, checksum
  `sha256:43c58300b3989b927b54a71ab7c4b53b3cba7e1a47ca1ca09c04cd288efdbc4a`.
- Apache scan result: 161 matches, zero Critical, zero Critical exceptions,
  142 Medium, 16 Low, 3 Negligible.

### Full supply-chain blocker

The same complete runner failed at the existing Postgres image after Apache
passed its gate:

- `CVE-2026-10536`, `CVE-2026-11564`, `CVE-2026-11856`,
  `CVE-2026-8924`, `CVE-2026-8925`, `CVE-2026-8926`, `CVE-2026-8927`, and
  `CVE-2026-9079`.
- All affect Alpine `libcurl 8.20.0-r0`; Grype reports fixed version
  `8.22.0-r0`, first observed `2026-09-05`.
- The runner result was:
  `supply-chain-evidence: ERROR: postgres: unexcepted Critical vulnerabilities`.

This is a full-image current-head gate failure, not an Apache finding. The
order forbids broad unrelated Postgres hardening in this round, so no change or
exception was made.

### Snapshot and cancellation proof boundary

The existing focused preview test still passes, but its historical barrier is
not causal: it pauses after `SELECT 1`, starts Agent mutations, releases the
snapshot, and only then awaits mutation results. It is therefore not claimed as
the required 077-o proof.

The deterministic attempted repair changed the barrier to query actual locale,
navigation, redirect and page-resolution data, then awaited all public Agent
page/navigation/redirect commits before releasing Render. It could not reach a
valid terminal state. The preview COW transaction's reauthorization path holds
the workspace shared lifecycle lock; the Agent mutation SQL requires the
exclusive workspace lock before its structural lock. With Render paused, the
Agent calls cannot commit and eventually return `SERVICE_UNAVAILABLE`; the
preview connection remains idle in its repeatable-read transaction. Releasing
Render first reproduces the original false-positive ordering.

The canonical owner-DML companion proof and the exact post-tentative-locale
cancellation proof were not claimed or shipped because the required preview
causal boundary is blocked by this lock contract. Existing focused tests still
pass for cancellation cleanup/retry, restart durability, browser one-time
consume semantics, locale/redirect races, and public Agent-created browser
previews, but they do not satisfy the missing causal proof.

## Local verification

- `uv lock --check`, frozen dependency sync and the full supply-chain build
  preparation: PASSED until the exact Postgres Critical gate above.
- Ruff check, Ruff format check, mypy: PASSED.
- Repository policy, repository unit tests, Markdownlint and Mermaid: PASSED.
- Python unit/repository tests: 522 passed, one existing Starlette/httpx
  deprecation warning.
- Backend integration suite: 169 passed in 23m44s.
- Focused Render cancellation/projection tests: 2 passed.
- Focused public Agent-created browser preview: 1 passed.
- Focused locale structural race/cancellation test: 1 passed.
- Browser HTTP restart and Render preview lock tests: 2 passed.
- Node version: Node `v24.14.1`, pnpm `11.22.0`.
- Node lint, format, build, tests, licenses and sequential typecheck: PASSED.
  The first parallel typecheck attempt raced the build-generated `.next/types`
  files and was rerun sequentially successfully.
- Corrected clean Compose/public Agent/browser/edge smoke:
  `sh tools/compose/smoke.sh slaif007o2`: PASSED, ending with
  `compose-smoke: OK`.

## GitHub CI / required checks

The new head `49ad633012d8193406de6ca5c03b769b215198c6` was pushed before CI
observation. At report time the PR checks were still running or queued:

- `Repository policy`, `Node contracts`, Python 3.12/3.13/3.14,
  Foundation PostgreSQL 14–18, Compose and edge packaging, Supply-chain
  evidence, Markdown, Mermaid, Dependency review and CodeQL: `IN_PROGRESS` or
  `QUEUED`.
- No pending check is counted as pass. The prior head's Supply-chain evidence
  failure is superseded by this current-head run but the local fresh scan above
  already identifies the same full-image Postgres blocker.

## Scope, safety, and completion boundary

- No secrets, capabilities, cookies, production systems/data, extra PR, merge,
  release or issue closure occurred.
- No dynamic `{slug}` collection-detail behavior, 078 composition/design/Puck,
  media/MCP/freeze/review/promotion/source/sweep/076 work was added.
- No required check, vulnerability policy, lock policy or exception policy was
  weakened.
- The strongest reasons not to accept are the exact Postgres Critical gate and
  the causal snapshot impossibility under the current shared/exclusive COW
  lock order. Objective 077-o / PR #74 can be declared complete only when the
  full current-image Grype gate is zero Critical, the public Agent/Editor
  commits can be proven to occur after a real repeatable-read snapshot and
  before its release without lock-policy weakening, all required current-head
  checks are green, and strategy independently accepts the bounded scope.
  The coding agent is not authorized to merge.

No extra PR was created. No merge or auto-merge was performed.
