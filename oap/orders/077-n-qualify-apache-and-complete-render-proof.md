# OAP Work Order — 077-n

## Objective and verified state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`558d7dcb97188410edd566986ae2264e65f48a1d`, whose sole parent is blocked
077-m implementation `d09d7b97e43dd93f0238f87aa9f25ac5c3ff8a35`. Remote
`main` remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

Accept 077-m's verified locale/redirect/page-delete repair for progression, not
the round/objective. Resolve its Apache package blocker through the authorized
official Debian fallback and supply the exact Render evidence still absent.
Do not start dynamic `{slug}` behavior.

## 1. Qualify the official Apache Debian Trixie image

Apache 2.4.68 remains current GA. The official Alpine 3.24 image cannot install
the current Grype-fixed `libcurl`, APR-util and OpenSSL package set together;
no vulnerability exception is authorized.

Qualify this current Docker Official Image fallback:

```text
docker.io/library/httpd:2.4.68-trixie
sha256:979c38c2228d28c2edfd45c6e27dcee1c7b4a101a5526721ae8ece454e89e99e
```

The observed linux/amd64 manifest is
`sha256:570743f3adc135cc48a0b10c4ee893dc9c948ea1d1e59550fa8f8af6e35048be`
and declares `debian:trixie-slim`; independently reverify all metadata before
committing.

- Rebuild the Apache reference edge from that immutable index and translate
  only the package/module-enablement commands required for Debian while
  preserving the exact Apache config, non-product edge semantics, labels,
  reproducibility and multi-platform contract.
- Apply available fixed Debian security packages in a deterministic build;
  do not pin known-vulnerable packages, mix distributions, download arbitrary
  binaries, or use an unverified mutable source.
- Update supply-chain policy, package override facts, deployment/supply-chain
  docs, repository/packaging tests, SBOM expectations and attribution to the
  exact qualified source/final image.
- Require two reproducible builds, `httpd -t`, NGINX-vs-Apache parity, Compose/
  edge behavior, complete SBOM/license inventory, and the current Grype DB with
  zero unexcepted Critical findings on the final image.
- Remove the now-unsuccessful Alpine 3.24 Apache pin/facts cleanly. Do not alter
  the other independently pinned Alpine images merely for uniformity and do
  not create/extend any vulnerability exception or weaken the scanner/gate.

If the exact Trixie build still reports an unfixable Critical, exhaust only
official maintained 2.4.68 Debian package updates or a reproducible build from
the verified Apache 2.4.68 release artifact on a maintained fixed Debian base.
If no qualified zero-Critical artifact exists, report exact packages/CVEs/fixed-
version availability as a genuine blocker; do not substitute an exception.

## 2. Prove coherent Render snapshots, not only authorization locks

077-m cites earlier Render tests, but no test currently pauses after the new
canonical/preview repeatable-read snapshot is established, commits a structural
write, and checks the entire projection. Add deterministic real-PostgreSQL
production-path tests for both canonical and authorized preview:

- establish the Render transaction snapshot with an actual query;
- pause through an event/barrier, never a timing sleep;
- concurrently commit an Editor/public Agent page+locale+navigation/redirect
  change through its intended API and transaction;
- resume Render and prove its page, selected/default locales, navigation
  labels/order/targets, redirect decision, composition/theme/bindings all come
  from one complete before-state; a fresh render sees the complete after-state;
  no mixed projection is permitted; and
- prove an independent site/workspace remains isolated.

Instrumentation may wrap a production query stage to expose a deterministic
event; it may not mock the database, transaction, COW overlay, authorization,
route resolution, mutation, or projection result.

## 3. Prove cancellation, pool cleanup and durable restart

For canonical and human preview, cancel an in-flight Render only after its
transaction/COW context exists. Prove:

- transaction rollback/closure and pool return;
- no lingering `app.session_id`/operation context;
- preview connection isolation resets to the configured default;
- no DB write/audit/quota/idempotency residue;
- a subsequent authorized render succeeds on the same pool; and
- service/app stop and fresh start still resolve the same durable workspace
  overlay while canonical remains unchanged.

For a browser credential cancelled after its one-time authorization is consumed,
prove exactly one consume event and fail-closed replay; cancellation before
consumption must not consume it. Never make a one-time credential reusable by
rolling back an already durable security event unless the existing contract
explicitly does so.

## 4. Make the browser structure genuinely Agent-created

The current expanded browser test still owner-inserts locale/pages and directly
updates the COW page. It proves browser binding but not the ordered public
Agent→browser→Render workflow.

A real human-issued capability with the required page/locale/navigation/
redirect/read and `preview:inspect` scopes must, through public Agent FastAPI
handlers:

1. create the non-default locale, nested localized pages, localized navigation
   and any redirect used by the case;
2. request the bound browser preview run through the public Agent operation;
3. let the normal internal worker/control path claim/authorize the run and issue
   the run-bound credential; and
4. render that exact nested route through the internal browser-credential
   boundary, proving expected page/effective route/locale/navigation, site/
   workspace/route binding, no capability/browser token projection, exactly one
   consumption, replay denial, and canonical/second-workspace isolation.

Owner SQL may create identities/canonical fixtures, coordinate the worker and
assert state. It may not create/update the claimed workspace structure or
manufacture the public Agent browser request.

## 5. Close the remaining locale-graph race/cancellation proof

Keep migration 053's safe redirect target resolution and locale wrappers, but
add the exact missing coupled cases rather than citing adjacent older tests:

- Agent default-locale switch racing Editor/Agent redirect creation or page
  route mutation under the shared structural lock; and
- cancellation after a tentative default switch but before graph/audit
  completion, followed by same-key retry.

Only coherent serializations may commit. Invalid graph loses with stable 409;
valid graph wins with exact row versions. The loser/cancelled operation leaves
zero locale/page/navigation/redirect/quota/idempotency/audit/COW residue.
Canonical, other workspace and other site remain unchanged.

Preserve 077-l's locale-hidden navigation fix, all five exact public redirect
statuses/locations and preview headers, 077-m's valid/invalid switch and page
delete/restore proof, migration round trip/grants, Render corruption matrix,
one-time browser authority, Agent OpenAPI/route-policy continuity, and all
074–076/077 behavior.

## Verification and boundaries

Run focused Apache build/SBOM/scan/reproducibility/parity; Render snapshot/
cancellation/restart/browser; locale race/cancellation tests; full Agent/
Editor/Render/bootstrap integration; migration/privilege tests; Python quality/
unit/integration; Node contracts; PG14–18; repository/Markdown/Mermaid; clean
Compose public acceptance and complete supply-chain evidence; then all current-
head CI. Push before observing CI and repair only in-scope failures. No pending,
skipped, superseded or inferred result is a pass.

No dynamic `{slug}`/collection detail; no new Agent semantic route beyond the
existing browser request; no 078 composition/design/Puck; no media/MCP/freeze/
review/promotion/source/sweep/076; no architecture/historical-order/report/
general-refactor/production/release change; no exception or issue closure.
Preserve Chrome `152.0.7977.82` and the empty exception set. GitHub issue #67
stays open until Objective 077 is merged to verified `main`.

Commit this exact order and `oap/active` unchanged, push only the existing PR
branch, create no PR, and never merge/auto-merge. Publish exactly
`oap/reports/077-n-qualify-apache-and-complete-render-proof.md` as the final
report-only child of a literal implementation SHA with
`Report publication commit: SELF`. Include exact Apache source/final digests,
packages, CVE before/after, reproducibility/SBOM/license/parity; exact snapshot
barriers and before/after fields; cancellation stage/pool/session/credential
state; restart result; public Agent-created browser sequence; locale race and
rollback evidence; commands/counts/skips/current checks; no scope/secret/extra
PR/merge/exception; remaining dynamic/final 077 scope; and strongest reason not
to accept. Do not claim an item from an adjacent old test.

`PARTIAL`/`BLOCKED` requires a concrete external or technical blocker with
exact attempted evidence. Do not return because tests/Compose/CI are long. No
post-report push. Signal exact FIFO `OK`, then wait for strategic review.
