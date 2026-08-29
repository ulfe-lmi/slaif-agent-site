# OAP Report — 072-o

- Order: `072-o-canonical-preview-route`
- Result: `PARTIAL`
- Delivery: `AMENDED_EXISTING_PR`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66) (OPEN)
- Base: `main` at `082f2359b0c4d59b692580d17992c35d46183b12`
- Branch: `oap/072-browser-worker-real-playwright`
- Starting remote SHA: `92d385c70321cf09eb2beb561860c2a211560d5f`
- Implementation SHA: `d8489d1a56a80ecc78b0b152040e04a2df297cb5`
- Report publication parent: `d8489d1a56a80ecc78b0b152040e04a2df297cb5`

## Delivered

Canonical preview routes now remove trailing slashes from non-root paths while
preserving `/`, safe percent-encoded spelling, and sorted canonical queries in
both Python and TypeScript. Agent/DB/token/worker request digests and the Web
preview boundary use the same canonical bytes; Web now uses the shared internal
workspace contract package and canonicalizes reconstructed Next paths before
Render binding. Worker and Python digest vectors were updated accordingly. The
internal Web workspace dependency is pinned as `workspace:0.0.0`, satisfying
the repository supply-chain policy without introducing a hosted or mutable
package source.

Added parity coverage for root, trailing-slash, query-order, Unicode/encoding,
and hostile-route behavior. The 072-m immediate terminal diagnostics remain
unchanged. No migration, grant, dispatcher redesign, worker runtime/network,
exception, public artifact, or publication behavior changed.

## Evidence

- Python browser-contract, credential, worker-client, and Render integration tests passed.
- TypeScript browser-tool-contracts (24 tests), Web surface (9 tests), and browser-worker (10 tests) passed.
- Full local Python ruff, format, mypy, unit, repository, and packaging gates passed before the final digest-vector correction; focused rerun passed after it.
- Clean Compose regression reached the dispatcher restart marker but still failed with bounded `BROWSER_NAVIGATION_HTTP_404` on run `af2ffee8-ec28-4a13-9c15-8cd83044b679`; no real `COMPLETED` artifacts were claimed. This remaining defect is outside the route-byte mismatch repaired here and is left for the next bounded order.

The exact 41-entry Chrome `.64` temporary exception and issue #67 remain
unchanged through `2026-09-04`; no new findings or scope were added. Objective
072 remains `PARTIAL` pending the remaining preview E2E defect and public
artifact retrieval.

## CI and safety

Fresh GitHub checks for the final report head are required after push; the
known Compose failure is recorded literally. No extra PR, merge, auto-merge,
release, production access, credential/cookie exposure, or artifact-byte
publication occurred.

Report publication commit: SELF
