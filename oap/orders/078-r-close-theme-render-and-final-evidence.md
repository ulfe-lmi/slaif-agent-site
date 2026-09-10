# OAP Work Order — 078-r: close the bounded theme increment

- Objective078; increment078/2; round078-r; AMEND_EXISTING_PR.
- Existing [PR #79](https://github.com/ulfe-lmi/slaif-agent-site/pull/79),
  branch `oap/078-2-site-theme-tokens`, base `main`.
- Verified main `3cae3d6cef2a92e7068856d21bc9a47b8190c22e`.
- Starting report-only head `ce255470e76d4639d436d4ace6b19a8cd858c0d1`,
  exact implementation parent `8c0b36bc50b136d027fc1f37c7b5ab9e3c8d0401`.
- Current report-head checks pending at review; implementation-head gates green.
- No new PR, replacement agent, or additional feature scope.

## Acceptance boundary and reviewed state

Finish the existing bounded site-theme increment, not all Objective078. The
finite remaining targets are V1–V2 and Firefox from
`oap/audits/078-2-theme-increment-review.md`, plus the small lock-order and proof
residuals identified below. Do not reopen D1/D2 generally: strategic independent
PostgreSQL/public-HTTP rerun now proves read-only no-effect200 and direct SQL
null palette rejection. The original078-p/q reports and orders stay immutable.

## 1. Preserve lifecycle ordering and make race evidence deterministic

Current065 `_agent_update_sql` takes theme advisory995 BEFORE invoking
`slaif_agent_require_capability`, which obtains lifecycle shared280. This reverses
the required order. Acquire the pure workspace lifecycle shared advisory lock
first, then theme995, then reassert active capability/state and required scopes.
Do not naively move the entire capability helper's FOR SHARE row-locking phase
before995 and recreate lock-conversion deadlocks. Preserve actual-change
classification and recheck under the serialized transaction. Prove both public
and direct-runtime paths respect lifecycle280 before995; controlled exclusive
lifecycle blocking must not leave a theme lock granted to a waiting mutation.
No new freeze/review/promotion feature is requested.

The current theme race test assumes which palette wins its first race. If that
winner is ember, its next ember PATCH is a no-effect request and validly need
not conflict. Select both second-race values from the actual winner's remaining
alternatives, so BOTH really change the current state. Make the cancellation
payload actually changed too. Keep exact DB barriers/two waiters/one durable
effect, stale conflict and no-effect semantics; never force write/no-op behavior
to satisfy a faulty test. Exercise both winner orderings deterministically.

## 2. Complete exact migration-restoration evidence

078-q now preserves/restores the resource helper and two legacy theme wrappers
as original function objects. Its metadata test covers those three only.
065 also replaces semantic idempotency completion and no-effect completion;
extend the exact pre/post definition/signature/owner/ACL/volatility comparison
to EVERY replaced function and relevant semantic constraint. Capture a genuine
fresh064 baseline before it ever passes through065, not merely the result of
the downgrade under test. Repair any actual restoration difference minimally.
Keep valid data-bearing round-trip, invalid/pending-state rejection, least
privilege and private legacy-schema isolation. No edits to merged060–064.

## 3. V1: theme defaults must preserve explicit local design

Independent Chromium with production CSS reproduced both:

- `.renderer-theme-gap--lg` forces Grid gap24px despite explicit local none
  (desktop) and mobile-sm (mobile), which must remain0px/8px.
- Meadow palette forces a `.renderer-button--ghost` background to solid green,
  overriding its transparent variant. Inspect secondary and responsive variants
  too; no broad design/catalog expansion.

Repair static stylesheet precedence so site tokens are defaults and explicit
component-local values/responsive fallbacks retain their accepted meaning.
Include default/reset-to-ocean/system/balanced/regular/md/sm behavior. Define
and test accessible semantic foreground/background roles for primary/secondary/
ghost under all advertised palettes rather than copying a light-theme text
color onto an incompatible background. Prove the declared AA role contrast
numerically from actual computed colors, not the string `accessibility_class`.
Do not add raw CSS input, inline caller style, remote fonts or new token types.

Use actual browser computed-style assertions for palette, typography, width,
spacing/gap, radius/shadow, local/responsive precedence and resets. Preserve
PR77 component semantics. Strategic reproducer:
`/tmp/slaif-078-theme-review-FDKCkn/css.mjs`.

## 4. V2: real Agent mutation to SAME workspace visual result

Current public Agent acceptance PATCHes/replays/reads theme; current computed
browser proof changes a separate HUMAN workspace via Editor. Connect the real
human-issued Agent capability, public Agent theme PATCH and its SAME workspace's
authorized preview/Render/browser result. Reuse the existing public NGINX
acceptance/preview path. Do not owner-seed the theme outcome or switch to a
different workspace and call it equivalent. No Objective081 exact-workspace
Puck selection feature is needed or authorized.

Prove changed themes for representative values in all four groups, public
canonical and other workspace/site unchanged, private no-store/noindex preview,
and actual Agent service restart/reconnect retaining theme/version/idempotent
replay. Creating another in-process ASGI client is not a process restart.
Retain existing human Editor/Puck controls, permissions, save/reset and shared
normalized renderer proof. Add no publication/lifecycle authority.

## 5. Diagnose the recorded Firefox failure without weakening evidence

Historical run34367041990/job102518331881 failed desktop-firefox
`responsive-admin-keyboard-read-states-and-logout`, auth.spec.ts79,
browser-response category. Q's later Compose passes do not identify that failed
request. Inspect retained failure evidence and determine the exact endpoint/
status/cause. Repair a concrete product/fixture/race defect minimally if found;
if transient infrastructure is demonstrated, record that evidence and a
successful targeted rerun. No blanket response suppression, lost failure
artifacts, skipped Firefox, weaker assertion or blind retry-until-green policy.

## Verification, truth and closure

Run focused repaired DB/migration/authority/concurrency and Web/browser tests
first, schema/OpenAPI drift, and all required current-head CI. Expensive existing
CI can supply full matrix/Compose coverage; avoid redundant full local reruns
when focused evidence and the same required CI already cover the unchanged
substrate. Every claimed criterion names a real assertion and boundary.
Report leftover failures/unproven cases honestly; COMPLETE requires the actual
bounded theme contract, not all numeric078 and not generic suite counts.

Update current API docs: `docs/API.md` still claims unconditional
theme-tokens:write for PATCH, despite the changed-value policy. Reconcile current
README/API/testing/MVP/increment ledgers and the whole PR description to actual
theme behavior and proof, while preserving historical audit/report evidence.
Mark PR77 accepted/merged, PR79 only pending strategic acceptance until merge,
numeric078 stillPARTIAL with global regions/page-style/catalog deferred.

The cumulative diff is60paths,+6450/-595, primarily one cross-runtime theme
contract plus generated OpenAPI/migrations/tests/OAP. This is a closure boundary:
report production/migration/test/generated/docs counts separately and add no
further semantic family. No global-region/header-footer/page-style/catalog,
media/MCP/exact-workspace Puck/lifecycle/publication/reconstruction/cleanup,
dependency upgrade, exception or gate weakening. Routine safe setup belongs to
the existing coder's passwordless-sudo VM, not the human.

## Publication and synchronization discipline

Commit exact order and active078-r, scoped repairs/tests/current docs on PR79
only. Publish `oap/reports/078-r-close-theme-render-and-final-evidence.md` as the
last report-only SELF child of a literal pushed implementation SHA. Include
PR/branch/base/head, files/size, each remaining criterion, exact tests/checks,
scope/risks and honest skips/failures. Lint Markdown before publication.
Never merge, enable auto-merge, replace the coder or create another PR.

The human explicitly classified the earlier responseOK as out-of-band, not Q
completion. Q was genuinely delivered only after the same control signal was
resent23:28:29CEST and consumed as4f4b. After publishing this report, send exact
responseFIFO OK and wait with an ACTUAL byte-reading/validating control listener.
Opening the descriptor with `exec 3< control.fifo` alone is not a reader and
previously discarded the control message. Preserve a real read handle across
waits; accept only ASCII OK, rereadactive and the unique order after receipt.
Do not create another order or signal a report before its remote publication.
