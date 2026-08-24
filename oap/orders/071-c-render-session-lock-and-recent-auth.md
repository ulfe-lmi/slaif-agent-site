# OAP Work Order — 071-c

## Objective

Continue Objective 071 on the existing PR #62. Preserve all accepted 071-a and
071-b Render/Web/projection/browser work and correct only two concrete defects
in the new preview-session SQL: ordinary preview touch must never renew
`recent_auth_at`, and the workspace shared advisory transaction lock must be
taken before mutable session/workspace row inspection or locking. Add direct
deterministic proof, rerun all required gates, and do not merge.

## Verified starting state and source findings

- Numeric objective: `071`; round: `071-c`.
- Mode: `AMEND_EXISTING_PR`; amend only PR #62 on
  `oap/071-render-api-page-preview`. Create no new PR.
- Begin from verified remote 071-b report head
  `536d175703e4ba52814d5a216bf4998ca1fc80d6`; its sole parent is
  implementation head `eab228ce583169ce9eebf52ae62ceef11ddc49cf`
  and its sole changed path is
  `oap/reports/071-b-render-security-isolation-and-proof.md`.
- Remote main remains
  `88decb8f59894672d4c63cc7434196749b424647`; PR #62 is open and
  mergeable. Report-head CI was still running when this round was selected.
- 071-b is genuine and retained: session idle/absolute/revocation checks;
  trusted COW recheck; HUMAN/AGENT/IMPORT preview; descriptor-confined Web
  secret read with fresh green CodeQL; parent-slot/catalog/prop validation;
  namespaced projected collection values; exact-root routing; honest media
  placeholder; deterministic revocation race; and real nine-project preview
  browser smoke.
- Finding 1 — migration 033's regular preview touch executes a `CASE` that sets
  `recent_auth_at = now_at` when the prior recent-auth window has expired.
  Normal read authentication updates only `last_seen_at`; it must never create
  recent authentication. The current request returns the old value, but the
  next preview can observe the silently renewed timestamp and appear recent.
- Finding 2 — the same wrapper selects `user_session` and `workspace` `FOR
  UPDATE`, evaluates mutable authority, and only then calls
  `pg_advisory_xact_lock_shared`. The accepted product lock order is shared
  workspace advisory lock first, followed by mutable authorization checks. The
  current order can block revocation behind row locks and invert freeze/read
  lock ordering.
- Existing 071-b race proves reauthorization after revocation but does not prove
  row locks are absent while waiting for the workspace lock, nor that stale
  `recent_auth_at` remains unchanged across repeated preview reads.

## Bounded correction

- Do not edit migrations 006 through 033. Add one forward migration 034 that
  replaces only the Render preview authorization function and leaves one linear
  Alembic head.
- Validate bounded arguments and acquire the shared transaction-scoped
  workspace advisory lock immediately, before selecting or locking the human
  session, workspace, account, site, or membership state. Then perform the full
  idle/absolute/revocation/account/site/membership/workspace/permission checks
  under that lock.
- Preserve the existing two-phase service flow: initial authorization derives
  the trusted UUID; the COW connection reasserts the complete authority and
  holds its shared lock through all projection reads. No content read occurs
  before the in-transaction recheck.
- On the normal touch interval, update only `last_seen_at`. Never update,
  synthesize, extend, reset, or otherwise modify `recent_auth_at` during a
  preview/read request. Return `recent_auth` from the persisted timestamp and
  configured window exactly as normal human session authentication does.
- Preserve absolute/idle expiry, revocation, creator/read-all,
  `preview:inspect`, HUMAN/AGENT/IMPORT, site binding, and all existing narrow
  grants. Do not grant generic session-finalizer, table, lifecycle, reviewer,
  or mutation authority.

## Deterministic proof

Using real PostgreSQL and the real preview role/wrapper:

1. create a valid session whose `last_seen_at` requires a touch and whose
   `recent_auth_at` is outside the recent-auth window; preview successfully,
   prove `last_seen_at` advances, prove `recent_auth_at` is byte/time identical,
   prove returned recent-auth is false, repeat preview, and prove it remains
   false and unchanged;
2. create a genuinely recent session and prove preview does not alter its
   `recent_auth_at` while reporting the correct current result;
3. on one owner connection hold the exclusive workspace advisory transaction
   lock, start preview authorization on the preview role, and prove it waits;
   while it waits, update/revoke the session or workspace on a second owner
   connection without blocking on a row lock; release the exclusive lock, prove
   preview denies after recheck, and prove zero page/COW/idempotency/audit leak;
4. prove the COW projection transaction holds the shared workspace lock until
   response completion and releases it on success, denial, cancellation, and
   exception; pool context remains reusable and clean; and
5. retain the 071-b post-initial-authorization race, expiry, AGENT/IMPORT,
   multi-site, collection, route, service-secret, and browser tests.

The lock test must use explicit bounded events/waiter inspection rather than
timing-only sleeps. It must fail against the 033 ordering or otherwise provide
equally concrete source/lock evidence. Record exact chronology and connection
roles in the report.

## Non-goals and safety

- No projection/renderer/route/collection/media/service-secret redesign, no
  new UI or browser behavior, no component-catalogue change, and no dependency.
- No review/freeze/promotion/publication/browser-worker/dynamic-News work.
- Do not edit activated 071-a/071-b orders or published reports.
- No broad privilege/configuration/docs rewrite. Update docs only if they
  currently imply preview renews recent authentication or misstate lock order.
- No extra PR and no merge.

## Acceptance and verification

- Preview reads can touch idle activity but can never make authentication
  recent; repeated reads preserve stale `recent_auth_at`.
- The shared workspace advisory transaction lock is acquired before mutable row
  inspection/locking and remains held through the COW projection transaction.
- Revocation/freeze can proceed without row-lock inversion while preview waits,
  and the resumed request fails closed with no residue.
- Migration 034 is the sole new migration, prior migration bytes remain
  unchanged, privileges stay least-privileged, and all 071 behavior remains
  green.

Run and report focused migration/session/lock/race/Render tests; full backend
unit/repository/integration suites; CI-scope Ruff/format, Mypy, build, process
checks; full Node gates; clean nine-project Compose/browser smoke; migration
upgrade/downgrade and privilege validation; PostgreSQL 14–18; Markdown/Mermaid;
supply-chain; and every fresh GitHub required check. Record every failure,
interruption, retry, and reused/not-run result honestly.

Commit/push the exact strategic 071-c order and active bytes unchanged on the
same branch, then the forward migration/tests and any strictly necessary
documentation. Publish exactly
`oap/reports/071-c-render-session-lock-and-recent-auth.md` as one report-only
child with `Report publication commit: SELF`; verify literal parent and remote
path/head before signaling exact FIFO `OK`. Do not merge.

The report must state result/status, PR/base/branch/all SHAs, old/new lock and
touch chronology, exact timestamp evidence, role/grant/row-lock/advisory-lock/
residue/pool proof, migration/diff state, files/dependencies/docs, every local
and CI result/intermediate failure, limitations/non-goals, and no new PR/merge.
