# OAP Work Order — 077-v

## Objective and frozen PR state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`6891cf26f7ff5d498fe5561ccfae3ea13826d101`, whose sole parent is 077-u
implementation `ec04054d8b1f319ec04b79307c4c670350c00df5`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

PR #74 is feature-frozen. This round repairs only defects introduced or left
unproved by 077-u while finishing the already-activated 077-t contract. Do not
add Objective-077 feature scope. Strategy will perform the final hostile audit
and truth-ledger reconciliation after this repair.

## 1. Restore true public/preview renderer and CSS parity

077-u replaced the Next preview page with a manual Route Handler that calls
`renderToReadableStream` on a bare HTML document. It uses the trusted React
component implementation, but it bypasses the application layout, emits no
site/global stylesheet reference, hard-codes `<html lang="en">`, and uses a
generic title. That violates the architecture's invariant that canonical and
active preview use the same component tree and CSS and that only render context
differs; it also makes the non-default-locale acceptance claim incomplete.

Repair the preview response so it simultaneously:

- uses the same trusted renderer and effective site CSS as canonical output;
- emits the actual selected normalized locale in the HTML `lang` attribute and
  a bounded page-derived title/metadata rather than hard-coded English state;
- remains server-rendered, private/no-store/noindex and CSP-compatible, without
  inline unsafe CSS/JS;
- does not serialize workspace/site/page/item/view/node/translation UUIDs,
  capability/browser/human credentials, projection JSON or Next Flight route
  metadata into the response body;
- preserves human-session and exact one-use run-bound browser-preview access,
  redirects/status codes/query normalization, edge headers and restart behavior;
  and
- does not create a divergent second component implementation or CSS contract.

Choose the smallest architecture-consistent implementation. If a stable public
renderer stylesheet is used, canonical and preview must both consume the same
versioned source/artifact so drift tests fail. Do not solve this by relaxing the
UUID/secret negative or by adding `unsafe-inline` to CSP.

Add executable Web/Playwright/Compose assertions for default and `sl-SI`
dynamic pages that check actual stylesheet loading and representative computed
renderer layout/style, correct `lang`, correct localized content, zero internal
UUID/credential/Flight leakage, and identical trusted component classes between
canonical and preview where canonical fixture equivalents exist. Source-text
regex alone is not proof of CSS delivery.

## 2. Preserve and interrogate browser evidence; remove broad cleanup

`_run_dynamic_news_edge_journey` currently treats browser-run state
`COMPLETED` as sufficient, then directly deletes `audit.browser_event`, browser
records, and finally executes:

```text
find /var/lib/slaif/browser-artifacts -mindepth 1 -maxdepth 1 -delete
```

That can delete unrelated run artifacts, masks durable evidence from later
checks, and does not prove that the browser observed the dynamic page.

Replace it with bounded evidence handling:

- after the public Agent request reaches `COMPLETED`, use the public capability-
  bound Agent artifact list/retrieve interface to inspect the exact run;
- require its heading/structure evidence to be bound to the requested dynamic
  route/site/workspace/target and to demonstrate the expected trusted page
  title/content without secrets or foreign identifiers;
- prove wrong run/artifact/workspace/capability access and replay are denied by
  the established public/focused interfaces;
- preserve immutable browser audit/event and artifact metadata for the test run
  until normal disposable-Compose teardown; and
- remove direct audit deletion and any broad filesystem deletion. If a test
  count assumed zero artifacts, make it scope its assertion to its own fixture
  baseline/delta rather than erasing other evidence.

No product retention/GC feature is in scope. Test teardown may destroy the
entire already-disposable Compose project/volume at the existing outer boundary,
not selectively falsify application history inside the running system.

## 3. Make fallback and cancellation evidence real

### Localized fallback

077-u renders selected and default translations that both exist; it does not
prove fallback. Through existing public Agent translation operations, remove or
otherwise make the selected-locale translation absent and prove the valid
non-default dynamic route uses the explicit default-locale value. Then prove
that absence/invalidity of required output after fallback makes the whole route
404/fail closed. Preserve localized filter/sort denial.

### Preview COW cancellation and token semantics

The new cancellation test calls `service.canonical`; it never enters
`_repeatable_read_cow`, never authenticates a human/browser preview, and checks
no quota/idempotency/audit state. Replace or supplement it with deterministic
real-PostgreSQL preview cancellation after the dynamic route/detail/translation
snapshot is established:

- exercise the actual human preview COW path and show cancellation rolls back/
  closes the transaction, clears session/operation context, returns the pool
  connection reusable, leaves canonical/workspace data intact, and changes no
  capability mutation quota, Agent idempotency row or semantic audit row;
- exercise the actual run-bound browser-preview path at the same boundary and
  prove its separately committed one-use authorization semantics precisely
  (including the expected retry denial), without leaking the token; and
- prove a later newly authorized render succeeds.

Use `asyncio.Event`, transaction/advisory-lock barriers or equivalent exact
signals; no timing sleep is correctness evidence.

The 077-u race test also mutates canonical base tables directly. Keep it as a
supplemental repeatable-read corruption proof if useful, but add at least one
deterministically ordered dynamic preview-versus-production-Agent HTTP mutation
case so the claimed COW/locking/public mutation interaction is real. Assert the
complete before/after result and durable mutation/audit/idempotency state, not
only an allowed status set.

## 4. Continuity, verification and report

Preserve 077-u's database query-bound fix, stale-definition rejection,
non-default route fix, static CollectionDetail compatibility, public Agent News
fixture, route/status/isolation/restart behavior, exact OpenAPI/route-policy
continuity, migration 055/056 downgrade behavior, and all existing page/locale/
navigation/redirect locks and COW isolation.

Run focused preview HTML/CSS/locale/privacy tests, browser artifact public API
and denial tests, localized fallback tests, preview COW/browser cancellation,
and production Agent mutation race tests. Then run the complete current 077
gates: PG14-18; Python quality/unit/integration; Node lint/format/typecheck/test/
build/license; repository/Markdown/Mermaid; clean Compose/public NGINX/Web/
browser/restart; all six zero-Critical supply-chain evidence; and all current-
head GitHub checks. Required pending/skipped/superseded results are not pass.

Do not add composition/design/Puck 078, media 079, MCP 080, Agent-workspace Puck
081, freeze/review/promotion 082+, source/sweep 087, new public Agent routes,
dependencies/images/exceptions/primitives/operators/architecture, or general
cleanup. Preserve Chrome `152.0.7977.82`, empty vulnerability exceptions and
open GitHub issue #67. Do not edit historical orders/reports or final MVP truth
ledgers in this repair.

Commit this exact order and `oap/active` unchanged, amend only PR #74, create no
PR and never merge. Publish exactly
`oap/reports/077-v-repair-preview-parity-evidence.md` as a report-only child of
the literal implementation SHA with `Report publication commit: SELF`.
Report exact CSS/lang/HTML/privacy evidence; browser artifact list/retrieval,
binding/denial and retained audit evidence; fallback cases; preview COW and
browser-token cancellation state; production Agent race barriers/final state;
commands/counts/skips/current checks; scope/no-secret/no-extra-PR/no-merge; and
the strongest remaining reason not to accept Objective 077.

Do not return early for ordinary implementation/test/CI failure or task size.
`PARTIAL`/`BLOCKED` requires a concrete external outage or unresolved product/
architecture decision. No post-report push; signal exact FIFO `OK`, then wait.
