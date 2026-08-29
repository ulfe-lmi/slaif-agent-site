# OAP Work Order — 073-b

## Objective and verified GitHub state

Amend only Objective 073 PR #69,
<https://github.com/ulfe-lmi/slaif-agent-site/pull/69>, branch
`oap/073-repair-mvp-control-state`; no new PR and no merge. Required starting
remote report head is `7be6ccc7e7201a185d0f8812983896074df51672`, whose sole
parent is implementation `92e881508e8ba2d2689a82f9173d98f5543e6750`.
Remote `main` remains `bcaddc41f9ef4e779dd1a8c9a41eb08462250d53`.
All 20 checks are successful, but strategic review found stale contradictory
README prose, so 073-a is not yet acceptable.

## Required correction

Correct `README.md` comprehensively against the already-published
`oap/MVP-CONTRACT-AUDIT.md` and actual merged 065–072 slices. Preserve the logo,
mission, architecture/non-goals and honest incomplete-MVP verdict.

At minimum remove or replace every stale claim that:

- browser-worker automation is separate/future or the worker is a placeholder;
- the Compose deployment is merely a skeleton without real first-run
  administrator/site-management behavior;
- the supply-chain exception set is empty;
- runtime browser feedback remains wholly planned;
- the Apache example is only planned rather than implemented/tested.

State the narrow truth instead:

- Objective 072 delivers real confined Chromium preview runs, durable private
  artifacts and retrieval; approved-source tools and responsive-sweep
  orchestration remain Objective 087.
- Objective 070 delivers private immutable human media upload/CAS; Agent media
  semantics and canonical public finalization remain 079/083.
- one-time setup/login, site/membership administration, Puck HUMAN-workspace
  editing, canonical/active preview rendering and the proven 065–072 slices are
  real, while human Agent-session issuance, exact-Agent-workspace Puck,
  complete semantic REST/OpenAPI/MCP, review/promotion/reconstruction/cleanup/
  restore remain queued.
- the exact temporary 41-finding Chrome `.64` exception is documented in open
  issue #67, expires `2026-09-04`, and is not release readiness.

Audit the entire README, not only the reported lines, for status prose that
contradicts current code. Keep normative future-capability descriptions clearly
labeled as architecture, not current implementation.

## Acceptance, scope and verification

- Search results contain no `browser-worker placeholder`, `isolated browser
  placeholder`, `empty exceptions`, `runtime browser feedback` as pending, or
  “not the first-run administrator” wording.
- Current-status and delivery/repository-map sections agree with the contract
  audit and MVP tracker; no new broad completion/production/certification/
  hostile-SaaS/browser-engine claim is introduced.
- Change only `README.md`, exact unchanged 073-b order/`oap/active`, and the new
  report. Do not edit 073-a or any prior/future order/report, audit/progress/
  roadmap, product code, policy, architecture, dependency, workflow or issue.
- Run Markdownlint, repository policy, `git diff --check`, and targeted status-
  phrase searches. No broad product/Compose/browser/DB/supply-chain rerun.
- Require every current PR-head GitHub check successful before acceptance.

Publish exactly `oap/reports/073-b-correct-readme-current-state.md` as a new
immutable report-only child of the literal implementation SHA; report exact
before/after claims, files, commands/checks, no extra PR and no merge; SELF.
