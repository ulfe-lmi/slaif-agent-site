# OAP Work Order — 011-e

## Objective and exact PR state

Repair two final review findings on objective-011 PR #23 only: make Render-
locator recovery deterministic after the deliberate fail-closed Compose test,
and correct the localhost landing page's now-false claim that sites are absent.
This is a narrow repair round, not a feature continuation.

- Numeric objective: `011`; round: `011-e`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#23](https://github.com/ulfe-lmi/slaif-agent-site/pull/23)
- Base/head: `main` / `oap/011-sites-trusted-resolution`
- Required starting remote head:
  `e3edde2ac3f914172552bf62338c875d0a02028f`
- 011-d implementation parent:
  `9101911a7396c9f1228a8bef32a8086d069171eb`
- Verified state: open, ready/non-draft, mergeable, no reviews/threads; correct
  report-only head/parent. Current report-head CI is final at 19 successful,
  one failed, zero pending. Only `Compose and edge packaging` failed in run
  `32441050912`, job `96651664648`.

Fetch and verify the exact PR/head. Amend only PR #23; keep it ready. Never
create another PR, merge, close, auto-merge, or workflow-rerun.

## Root causes

1. After the smoke test restores the intentionally corrupted Render locator, it
   recreates Render and immediately calls global `docker compose up --wait`.
   Web recovers, but NGINX may still carry the deliberate prior `unhealthy`
   state; Compose can exit immediately before its health state transitions.
   The implementation-head pass was timing-dependent. The report-head log ends
   with all dependencies healthy and `container slaif007ci-nginx-1 is
   unhealthy` during this recovery step.
2. `apps/web/app/page.tsx` still lists bare “sites” under “Still deliberately
   absent.” Objective 011 now implements site persistence, Platform
   Administrator site/domain APIs, trusted resolution, and routing shells. The
   text is materially false even though site-management UI, membership/RBAC,
   content, workspaces, and publication remain absent.

## Allowed scope

```text
tools/compose/smoke.sh
tests/packaging/test_compose_smoke_contract.py only if useful
apps/web/app/page.tsx
apps/web/tests/surface.test.mjs
tests/e2e/setup.spec.ts only for a direct landing-status assertion
README.md or docs only if the same exact contradiction exists
oap/active
oap/orders/011-e-deterministic-recovery-truthful-status.md
oap/reports/011-e-deterministic-recovery-truthful-status.md
```

Use the minimum subset. No backend/domain/schema/migration/secret/Compose
topology/edge config/dependency/lock/image/API/route/feature change. Preserve all
prior orders and reports byte-identically.

## Requirements

### 1. Deterministic dependency recovery

Keep the deliberate corruption proof exactly fail closed: corrupted Render
locator must still produce Render unhealthy, Web 503, and NGINX unhealthy. After
restoring the exact master-derived locator, explicitly reset/recreate/restart or
otherwise transition the Render→Web→NGINX health chain and wait in bounded
dependency order until all three are healthy before invoking any global
`docker compose up --wait` assertion.

The recovery must:

- avoid implicitly rerunning `secrets-init` against corrupt state;
- avoid reissuing setup tokens, reseeding, overwriting initialized state, or
  changing secret/site fingerprints;
- use bounded polling with a clear terminal failure and concise, secret-free
  diagnostics rather than sleep-only timing assumptions;
- prove the restored locator byte-matches `service-public-dsn` before recovery;
- print one stable marker, for example
  `render-locator-recovery: restored render=healthy web=healthy nginx=healthy`;
- retain the concise `render-locator-failure`, `negative-bootstrap`, and final
  `compose-smoke: OK` markers; and
- pass on both fast and slow GitHub runners without depending on a stale health
  state being cleared automatically.

Add the smallest static/unit contract practical for the recovery marker/bounded
logic. Do not remove the real clean Compose execution: the authoritative proof
must exercise corruption, failure propagation, restoration, recovery, and the
remaining smoke stages on the same clean project.

### 2. Truthful landing status

Update only the product-status prose so it distinguishes implemented objective-
011 behavior from deferred work. “Implemented now” must include secure local
setup/session plus trusted multi-site identity/routing and Platform
Administrator site/domain API. “Still deliberately absent” must name the actual
gaps, including membership/RBAC, site-management UI, content models/content,
workspaces/capabilities, editing/Puck, review, and publication; it must not say
that sites or site routing are wholly absent. Keep the README logo, layout,
links, auth behavior, routing shell, and honest non-production wording unchanged.

Add a source/component test that fails if the obsolete bare-sites claim returns
or if implemented/deferred status becomes overbroad. The existing Playwright
landing/setup path must remain green; add only a focused text assertion if it
materially strengthens executable evidence.

## Acceptance criteria

1. A clean Compose run always completes the corrupt→blocked→restore→healthy
   sequence before later assertions, with stable recovery/final markers and no
   secret/setup/seed mutation.
2. The landing page accurately states what objective 011 implements and what is
   still absent; tests enforce the distinction.
3. No product or infrastructure scope beyond the two repairs changes; all prior
   site/auth/Render/edge/browser evidence remains intact.
4. PR #23 alone remains ready with a correct report-only head; current-head CI
   is 20/20 successful with no workflow rerun/new PR/merge/auto-merge.

## Verification, autonomy, and report

Target 25 minutes; hard stop 45 minutes. Inspect the exact failed log first.
Run shell syntax and focused packaging/Web tests, full Node lint/format/type/
test/build, repository/Markdown checks, `git diff --check`, immutable hashes,
and secret/locator scans. Then run one clean local Compose smoke generation. A
second is allowed only after a new concrete diagnosis; no unchanged retry. Do
not run unrelated PostgreSQL matrices, browser-worker experiments, images, or
broad SBOM locally. Push one implementation generation only after local green;
inspect its complete GitHub CI and never press workflow rerun. If a new clean-
runner defect appears, report `PARTIAL` rather than entering another CI loop.

Routine tooling belongs to the disposable coding VM with passwordless sudo;
access no production credential/system/data. Do not weaken checks or hide logs.

Commit the strategic order and `oap/active` byte-identically. Atomically publish
exactly:

```text
oap/reports/011-e-deterministic-recovery-truthful-status.md
```

The final report-only `SELF` commit must parent the literal implementation SHA.
Report PR/head/draft state; exact prior failure/root cause; recovery sequence,
health/timing/marker/fingerprint evidence; exact landing copy/test evidence;
local commands and clean Compose result; current 20-check state; failures/skips;
scope/docs/security/dependencies; hashes; and explicit no-new-PR/no-rerun/no-
merge state. Signal FIFO `OK` only after the report and claimed remote state
exist.
