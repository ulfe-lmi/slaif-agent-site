# OAP Implementation Report — 076-x

## Delivery

- Order: `076-x`, `oap/orders/076-x-close-relation-view-and-supply-chain-gaps.md`.
- Delivery class: `AMENDED_EXISTING_PR`.
- Status: `BLOCKED`.
- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72), OPEN, non-draft, branch `oap/076-agent-model-content-semantics`, base `main`.
- Required starting report head: `25e27a0b368881f57c39b7ac043c25761da71fb1`; its sole parent: `2332b0026203fbb99fe385106c0c0fa398042347`.
- Remote `main` at activation: `0e83b26bf9a9f63bff6756d65cbfd527d215ec51`.
- Implementation parent: `25e27a0b368881f57c39b7ac043c25761da71fb1`.
- Literal implementation SHA: `0ba6ef3a863804a16708001cdf6396c3ec463bbc`.
- Pushed implementation commit: `0ba6ef3a863804a16708001cdf6396c3ec463bbc`.
- `oap/active` is committed unchanged as the exact selector `076-x`.
- The exact activated order is committed unchanged.
- Report publication commit: SELF

## Implemented scope

The implementation is bounded to `076-x`. It preserves the existing Agent
COW, capability, idempotency, semantic-audit, quota, optimistic-version, and
least-privilege boundaries. No new Agent entity/API or unrelated product work
was added.

- Repaired the 047/048 migration transition.
  - Revision 047 now has a forward-compatible audit semantic check for the
    exact immutable 048 relation/view action shapes, while its 047 completion
    function still rejects those later actions.
  - The 048 downgrade no longer installs a permissive `CHECK(true)` placeholder
    before restoring the canonical 047 contract.
  - A real Agent HTTP-created relation/view dataset survives the
    048 → 047 → 048 round trip with content, COW, audit, idempotency, function,
    owner, grant, check, head, readiness, replay, and read identity preserved.
- Added the missing relation/view hostile, authority, cancellation, and race
  proofs against real Agent HTTP and PostgreSQL.
  - Wrong/missing/malformed scope, site, workspace, source, path, type,
    resource, field, target, quota, delete, and version inputs are rejected
    without disclosure or unintended charge/COW/audit/idempotency residue.
  - Single-reference create and same-version PATCH races produce one winning
    mutation and one stable conflict with one row/version/charge/audit/
    idempotency/COW result.
  - Python and trusted database validators reject executable/raw-query,
    malformed, oversized, unsupported, depth, projection, pagination, replay,
    and duplicate-view attacks; a valid bounded query remains functional.
- Switched the authoritative PostgreSQL references to the exact official
  `postgres:18.6-trixie` OCI index required by the order in Compose, supply-chain
  policy, Compose verification, and deployment attribution.

## Changed files

- `compose.yaml`.
- `docs/DEPLOYMENT.md`.
- `oap/active`.
- `oap/orders/076-x-close-relation-view-and-supply-chain-gaps.md`.
- `services/backend/src/slaif_agent_site/content_model/models.py`.
- `services/backend/src/slaif_agent_site/db/alembic/versions/047_001_repair_item_semantics_and_translations.py`.
- `services/backend/src/slaif_agent_site/db/alembic/versions/048_001_agent_relations_and_collection_views.py`.
- `services/backend/tests/integration/test_agent_mutations.py`.
- `supply-chain/policy.json`.
- `tools/compose/verify.py`.

## PostgreSQL image and supply-chain evidence

Independent registry resolution verified:

- Exact reference: `docker.io/library/postgres:18.6-trixie@sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280`.
- OCI index: `sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280`.
- Linux/amd64 manifest: `sha256:7341002d2b8c7c5bdd7542a671a95b36196c0b5b888daf454ae4fc33ba5346d7`.
- Official image source: `https://github.com/docker-library/postgres.git#e00e1bd34ec5c8a8e7ad89b273b3d42efaf6d5bc:18/trixie`.
- Base: `debian:trixie-slim`; amd64 image creation time: `2026-08-25T00:40:33Z`.
- PostgreSQL packages: `postgresql-18 18.6-1.pgdg13+2` and
  `postgresql-18-jit 18.6-1.pgdg13+2`.
- OpenSSL packages in the immutable image: `libssl3t64`, `openssl`, and
  `openssl-provider-legacy`, all `3.5.6-1~deb13u2`.
- Official contract inspection passed: entrypoint `docker-entrypoint.sh`,
  command `postgres`, `SIGINT` stop signal, `/var/lib/postgresql` volume,
  runtime-owned `/var/lib/postgresql` and `/var/run/postgresql`, clean
  initialization/restart/backup assumptions, and the only-host-port NGINX
  topology were exercised by the local Compose smoke.
- Fresh local full supply-chain evidence directory:
  `/tmp/slaif-supply-chain-076x-trixie`.
- Fresh Grype database: schema `v6.1.9`, built `2026-09-01T06:32:09Z`,
  checksum `sha256:0c38b7025406d1b7a3041cc144ef7abb0523859d57633c6ed39578027a0676ec`.
- The full local runner completed policy validation, dependency inventory,
  notices, reproducible artifacts, fresh builds, image metadata, SBOMs, and
  scans, then failed the mandatory PostgreSQL zero-unexcepted-Critical gate.
- The exact Trixie scan reported unexcepted Critical findings:
  `CVE-2026-12087`, `CVE-2026-13221`, `CVE-2026-42496`, `CVE-2026-5450`,
  `CVE-2026-57433`, `CVE-2026-63073`, `CVE-2026-6653`, and `CVE-2026-8376`.
  The findings affect the immutable image's Perl, glibc, OpenSSL, and libxml2
  packages; no authorized exception covers them.
- No vulnerability exception was added, changed, repurposed, or suppressed;
  scanner freshness and severity thresholds were not weakened.

## Verification evidence

Local verification used disposable PostgreSQL and fake test credentials only.

- Focused data-bearing 048 → 047 → 048 round-trip: PASS, 1 test.
- Focused relation/view CRUD, replay, semantic audit, COW, and stale behavior:
  PASS, 2 tests.
- Focused hostile relation/view authority, validation, cancellation, and
  concurrency matrix: PASS, 1 test.
- `uv lock --check`: PASS.
- `uv sync --frozen --all-groups`: PASS.
- `uv run --frozen ruff check services/backend tests/repository tools`: PASS.
- `uv run --frozen ruff format --check services/backend tests/repository tools`: PASS.
- `uv run --frozen mypy`: PASS.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASS,
  514 tests.
- `uv run --frozen pytest services/backend/tests/integration`: PASS, 137 tests
  in 1017.10 seconds.
- `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASS; source and
  wheel built.
- `uv run --frozen pytest tests/supply_chain tests/packaging services/backend/tests/unit/test_foundation_contract.py services/backend/tests/unit/test_editable_domain_validators.py -q`: PASS, 92 tests and 51 subtests.
- All ten documented process `--check` smokes passed through the frozen uv
  interpreter: control API, Editor API, Agent API, Render API, MCP adapter,
  media service, review worker, scheduler, media GC, and bootstrap.
- `python -m compileall -q tools tests/repository`: PASS.
- Repository unittest discovery: PASS, 58 tests.
- `python tools/check_repository.py`: PASS.
- `python tools/check_mermaid.py`: PASS, 16 diagrams in 3 files.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASS, 356 files and 0 issues.
- Node 24.14.1, pnpm 11.22.0, and TypeScript 6.0.3 were used. Frozen Node
  install, lint, format check, typecheck, test, build, and license inventory:
  PASS.
- `docker compose config --quiet` and `python tools/compose/verify.py --root .`:
  PASS.
- `sh tools/compose/smoke.sh slaif071076z`: PASS, exit 0; all Compose/browser,
  restart, recovery, edge, secret, login, negative-bootstrap, and final
  cleanup assertions passed.
- Local full supply-chain command:
  `sg docker -c 'cd /home/ubuntu/codex-work/slaif-agent-site && tools/supply_chain/run.sh /tmp/slaif-supply-chain-076x-trixie'`:
  BLOCKED only at the PostgreSQL vulnerability gate described above.

## Remote check state

At the final remote observation, PR #72 was OPEN and MERGEABLE at
`0ba6ef3a863804a16708001cdf6396c3ec463bbc`; GitHub reported merge state
`UNSTABLE` solely because of Supply-chain evidence.

- Analyze (actions): PASS.
- Analyze (javascript-typescript): PASS.
- Analyze (python): PASS.
- CodeQL: PASS.
- Compose and edge packaging: PASS.
- Dependency review: PASS.
- Detect supported languages: PASS.
- Foundation PostgreSQL 14: PASS.
- Foundation PostgreSQL 15: PASS.
- Foundation PostgreSQL 16: PASS.
- Foundation PostgreSQL 17: PASS.
- Foundation PostgreSQL 18: PASS.
- Markdown: PASS.
- Mermaid: PASS.
- Node contracts: PASS.
- Python 3.12 quality and package: PASS.
- Python 3.13 quality and package: PASS.
- Python 3.14 quality and package: PASS.
- Repository policy: PASS.
- Supply-chain evidence: FAIL.

The failed remote job is [Supply-chain evidence](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/33575612793/job/100078807481). Its final log states:

`postgres: unexcepted Critical vulnerabilities: CVE-2026-12087, CVE-2026-13221, CVE-2026-42496, CVE-2026-5450, CVE-2026-57433, CVE-2026-63073, CVE-2026-6653, CVE-2026-8376`.

This is a current immutable-image/vulnerability-state blocker, not an
implementation failure in the migration or relation/view proofs.

## Governance confirmations and blocker

- No immutable historical order, prior report, architecture, constitution, or
  protocol artifact was edited.
- No second PR was created; PR #72 was amended in place.
- PR #72 was not merged, closed, or auto-merged.
- No production system, production data, credential store, or real secret was
  accessed.
- No required check was skipped, replaced, weakened, or converted into an
  exception.
- No new Agent entity/API, cleanup, refactor, feature, documentation
  enhancement, or unrelated architectural work was added.
- The substantive 076 implementation does not require reimplementation or
  further code changes based on the passing focused, full local, Compose, and
  remote checks. The coding agent is authorized only to remain idle after this
  report until strategy activates a governance-correct continuation resolving
  the PostgreSQL image vulnerability state; then it may rerun the required
  gates and amend the same PR through OAP.

Objective 076 / PR #72 can be declared complete only when an authorized
immutable official PostgreSQL image reference satisfies the order's exact
provenance/runtime requirements and the fresh full local and remote
Supply-chain evidence gates report zero unexcepted Critical findings, while
all other required checks remain green at the final report head. Strategy must
then independently complete its final consolidated public OpenAPI/NGINX/
restart acceptance and hostile audit. This coding report does not claim
acceptance or merge.
