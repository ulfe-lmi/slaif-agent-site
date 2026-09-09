# OAP Coding-Agent Report — 078-o

## Work order

- Identifier: `078-o-next-security-patch`
- Work-order file: `oap/orders/078-o-next-security-patch.md`
- Work-order SHA-256: `778ffe369d616a9f8924952afc6eae0254074c091638015afde958aa0c170803`
- Objective: `078`; increment: `078/1`; round: `078-o`
- PR mode: `AMEND_EXISTING_PR`

## Status

`COMPLETE` for the authorized dependency repair and qualification. Strategic
acceptance and merge remain pending; the coding agent did not merge PR #77.

## Executive summary

The active `078-o` order was read after the exact FIFO `OK` and executed as
the sole scope. The security repair updates Next.js from exact `16.3.1` to
exact `16.3.3`, including its matching lockfile artifacts, production notice
rows, SBOM, deployment integrity record, and repository pin assertions.

The built Web workspace and standalone runtime both resolve Next.js `16.3.3`.
The complete local Node, repository, supply-chain policy, Compose, edge, and
browser qualification passed. The authoritative remote implementation-head
CI is fully green, including the required six-image supply-chain evidence
workflow with zero unexcepted Critical findings and no occurrence of either
previously reported advisory in the patched Web scan.

No application source code, migration, architecture policy, vulnerability
exception, scanner suppression, lint exclusion, unrelated dependency, or
feature was changed. The prior immutable-order link correction remains the
only historical correction; no historical order or report was rewritten in
this round.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77), `OPEN`
- Branch: `oap/078-agent-composition-design-semantics`
- Base: `main`
- Verified base: `ae3a4a681bb888260192b7bb1b2a337b4906828d`
- Starting report head: `602086512ddeebdd2c912f9c5f011c8af685cf85`
- Accepted product implementation: `6e41a5201215015e48d266995242b9c58067b95c`
- Literal implementation SHA: `59c478d43a7c5bce7167f7e9da5b3af705a1d1cc`
- Remote implementation head before report publication: `59c478d43a7c5bce7167f7e9da5b3af705a1d1cc`
- Report publication commit: `SELF`
- Report-only parent: `59c478d43a7c5bce7167f7e9da5b3af705a1d1cc`
- PR merge/auto-merge/close: `NO`

The implementation commit contains exactly the scoped dependency, evidence,
current-ledger, assertion, active-pointer, and order changes listed below.

## Exact dependency repair

- Previous Web dependency: `next@16.3.1`
- New Web dependency: `next@16.3.3`
- npm registry: `https://registry.npmjs.org/next/-/next-16.3.3.tgz`
- License: `MIT`
- Node engine: `>=20.9.0`
- npm integrity: `sha512-tuRTx1nQ/yVw83cwJBo9F+njGUgMn3UHQycreWHB8XsStvvAh1AthbI8/4IpKnFaF58F+iSiHejYOlMQ/eq83g==`
- Registry metadata was independently queried during execution and matched
  the order exactly.
- The two repaired advisories are [GHSA-2xp9-vwfh-vxw4](https://github.com/vercel/next.js/security/advisories/GHSA-2xp9-vwfh-vxw4)
  and [GHSA-p293-qw3h-jr36](https://github.com/vercel/next.js/security/advisories/GHSA-p293-qw3h-jr36).

The generated lockfile updates only the Web Next package and its matching
`@next/env` and platform `@next/swc-*` artifacts. Existing unrelated package
metadata was not retained from the package-manager regeneration.

## Changed files and scope

- `apps/web/package.json`
- `pnpm-lock.yaml`
- `THIRD_PARTY_NOTICES.md`
- `docs/DEPLOYMENT.md`
- `sbom.json`
- `tools/check_repository.py`
- `tests/repository/test_repository_policy.py`
- `oap/INCREMENTS.md`
- `oap/MVP-PROGRESS.md`
- `oap/MVP-CONTRACT-AUDIT.md`
- `oap/audits/078-k-closure-evidence.md`
- `oap/orders/078-o-next-security-patch.md`
- `oap/active`

The mutable current ledgers now record 078-o and its security qualification;
the historical 078-m and earlier reports/orders remain unchanged. No theme,
global region, exact-workspace Puck, media, MCP, review, promotion,
publication, cleanup, migration, or unrelated upgrade was added.

## Actual resolved and built version

- `node -p "require('./apps/web/node_modules/next/package.json').version"`:
  `16.3.3`.
- The standalone build contains
  `apps/web/.next/standalone/node_modules/.pnpm/next@16.3.3_.../next/package.json`.
- The direct patched Web production build printed `▲ Next.js 16.3.3 (webpack)`
  and completed successfully.
- The root production build also printed Next.js `16.3.3` and completed
  successfully.
- The generated committed SBOM contains one Next component:
  `pkg:npm/next@16.3.3`.

## Local verification

All local commands below passed on the patched worktree:

- `node --version`: `v24.14.1`.
- `pnpm --version`: `11.22.0`.
- `uv --version`: `0.12.5`.
- `pnpm install --frozen-lockfile`.
- `uv sync --frozen --all-groups`.
- `pnpm lint`.
- `pnpm format:check`.
- `pnpm typecheck`.
- `pnpm test`: Web tests 11/11, package and browser-worker tests passed, and
  contract tests 9/9 passed.
- `pnpm build`.
- `pnpm licenses list --json` (exit 0).
- `uv run --frozen python -m tools.supply_chain.policy validate`.
- `uv run --frozen python -m tools.supply_chain.policy notices --check`.
- `python -m unittest discover -s tests/repository -p 'test_*.py'`: 58 tests,
  `OK`.
- `python -m unittest discover -s tests/supply_chain -p 'test_*.py'`: 34
  tests, `OK`.
- `python tools/check_repository.py`: `PASS repository policy`.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: 0 issues in 447 files.
- `git diff --check`.
- `python tools/generate_sbom.py`: 68 components, license check passed.
- `sh tools/compose/smoke.sh slaif007ci`: `compose-smoke: OK`, including six
  stable browser projects, setup/governance/preview E2E, Agent sessions,
  private artifact retrieval and outage/restart/revoke negatives, edge
  headers/body limits, database/secret policy, recovery, and negative
  bootstrap/Apache checks.

The local build and smoke use disposable local dependencies and containers;
they do not replace the authoritative remote CI result.

## Remote implementation-head CI

CI run `34339623608` and CodeQL run `34339623504` were observed on literal
implementation SHA `59c478d43a7c5bce7167f7e9da5b3af705a1d1cc`. Every required
check is `SUCCESS` and no required check is pending, cancelled, or failed:

- Repository policy
- Detect supported languages
- Node contracts
- Python 3.12, 3.13, and 3.14 quality and package
- Foundation PostgreSQL 14, 15, 16, 17, and 18
- Compose and edge packaging
- Supply-chain evidence
- Markdown
- Mermaid
- Dependency review
- Analyze (actions), Analyze (python), and Analyze (javascript-typescript)
- CodeQL

Relevant check links include [Node contracts](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34339623608/job/102427088323),
[Compose and edge packaging](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34339623608/job/102427087936),
[Supply-chain evidence](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34339623608/job/102427088268),
and [CodeQL](https://github.com/ulfe-lmi/slaif-agent-site/runs/102427254332).

## Supply-chain evidence

The [successful supply-chain job](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34339623608/job/102427088268)
reported:

- `supply-chain-evidence: OK images=6 critical=0 high=44`.
- `supply-chain-evidence-checksum: OK`.
- `supply-chain-gate: OK`.
- Vulnerability database built at `2026-09-09T06:31:00Z` with checksum
  `sha256:f842f2a17dd4934dca9e1f283ebd7ce397dfcf14cc8a08a8cebb2f5530c131e0`.
- Evidence artifact: `supply-chain-evidence-bb1b7135b7feeb683218a3f2cac87b887369674f`,
  artifact ID `10099519289`.

The retained Web image identity is:

- Base: `docker.io/library/node:24.14.1-alpine3.23@sha256:8510330d3eb72c804231a834b1a8ebb55cb3796c3e4431297a24d246b8add4d5`.
- Image ID: `sha256:0d8cf84c07f1148c7d8bf58b7b096c4e13994dad595acf21d320d580d68ba6e4`.
- Package count: `154` (`134` npm packages).
- Web SBOM SHA-256: `d551bca9ad5f0ad4dae38486b7577e061a4bcb095606080636387500bcfef7dd`.
- Scan SBOM SHA-256: `2dc90cf4127488ab51c0b5cfefacc228c4cbc5c084096c3f2d7558c4239c649a`.
- Grype scan SHA-256: `72962bb7faf1329ea37ff037b1b0a1ff2c58b1af71169c7cb8ffbf165542494b`.
- Scan SBOM contains exactly `next`, version `16.3.3`, purl
  `pkg:npm/next@16.3.3`.
- Vulnerability result: `Critical: 0`, `unexcepted_critical: 0`, `High: 5`,
  `Medium: 9`, `Low: 4`, `Unknown: 0`.
- Querying the retained Web scan for both repaired GHSA IDs returned `[]`.

The full six-image evidence bundle records zero unexcepted Critical findings;
the 44 High findings remain visible review evidence as required by policy.

## Scope, safety, and acceptance boundary

- The Next.js patch is a security defect repair necessary to qualify the
  frozen increment, not an expansion of Objective 078.
- No vulnerability exception, scanner suppression, stale database, test skip,
  lint exclusion, or policy relaxation was used.
- No production system, production credential, capability, cookie, hosted
  runtime, or Docker socket outside the disposable qualification environment
  was accessed.
- No extra PR was created. PR #77 was not merged, auto-merged, or closed.
- `Report publication commit: SELF` must be the report-only commit whose first
  parent is the literal implementation SHA above.

## Completion condition

The 078-o coding order is complete and ready for strategic review. Objective
078/1 and PR #77 may be declared accepted only after strategy independently
verifies the remote green implementation-head state, reviews the exact
dependency/security delta and retained evidence, and merges PR #77. The
coding agent is not authorized to merge. Broader Objective 078 remains
`PARTIAL` until its separately ordered future increments are accepted and
merged.
