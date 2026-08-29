# OAP Work Order — 072-p

## Objective

Continue Objective 072 on PR #66. Diagnose the remaining Web→Render browser
preview 404 with fixed-vocabulary secret-safe stages, repair only the proven
boundary, and close the Next route-manifest reproducibility failure by semantic
JSON canonicalization. Use one targeted runtime diagnosis and one final broad
verification; no retry loop. Do not add public artifact retrieval or merge.

## Verified state

- Amend only PR #66 / `oap/072-browser-worker-real-playwright`; no new PR.
- Start at report-only head `74cb99e3ec31cb2c9284190977792e300d59f51e`;
  its sole parent is implementation `63ebf6eff247b9ce24de6d8dadb9bd8cc0037d4c`.
  Main remains `082f2359b0c4d59b692580d17992c35d46183b12`.
- Python/TypeScript/Web route canonicalization is implemented and focused tests
  pass, but real dispatcher navigation still returns bounded
  `BROWSER_NAVIGATION_HTTP_404` for canonical `/s/demo`.
- Public human preview, site resolution and all other Compose stages pass. The
  remaining failure can occur at context resolution, token verification,
  consume-authorize, COW validation, reauthorization or projection query; the
  current public 404 intentionally does not distinguish them.
- Supply-chain now fails earlier because paired Next builds produce different
  bytes for `.next/app-path-routes-manifest.json` at identical size. Existing
  diagnostics show exact path/hashes but not whether JSON semantics differ.
- Preserve the exact 41-entry `.64` exception and issue #67 through
  `2026-09-04`; any new unexcepted finding fails closed.

## 1. One safe targeted diagnosis

- Add internal-only fixed stage vocabulary for browser preview processing:
  `context`, `token-binding`, `authorize-consume`, `cow-context`,
  `authorize-recheck`, `projection-query`, `success`. Log only stage and fixed
  outcome under the existing request correlation; never token, nonce, IDs,
  route/query, authority, DB locator, payload, artifact or exception text.
- Preserve identical public non-leaking 404/status bodies. Human preview and
  canonical rendering must not emit browser stages.
- Run one targeted clean-stack browser dispatch request—not the full nine-
  project suite—and capture the exact last stage. Also compare the two Next
  manifest files as parsed JSON in a disposable location, reporting only
  `semantic-equal|semantic-different` and bounded differing JSON-key paths.
- If the stage or semantic difference is not isolated by this one attempt,
  stop and report `PARTIAL`; do not launch another broad diagnostic.

## 2. Minimal proven repairs

- Repair only the identified browser boundary. Preserve exact token/DB route,
  site/workspace/run/evidence/bytes/duration/nonce binding, one-time consume,
  shared workspace lock, COW validation, 404 non-leakage and canonical-content
  isolation. Do not bypass a failed stage or broaden accepted inputs.
- For the Next manifest, normalize only deterministic JSON serialization when
  parsed structures are semantically equal: recursively sort object keys and
  preserve array order/values. A route/key/value/addition/removal/type change
  must still fail with bounded path/hash evidence. Do not exclude the file,
  ignore arbitrary JSON, or weaken reproducibility.
- Add focused regressions for every changed stage and manifest behavior,
  including semantic-different failure and absence of secrets/IDs in logs.

## 3. Final acceptance

- After focused tests, run exactly one complete clean supply-chain execution and
  exactly one clean Compose regression. Compose must prove public NGINX create,
  `QUEUED -> RUNNING -> COMPLETED`, real `.64` Chromium COW overlay, PNG plus
  heading/structure summaries, atomic DB metadata, two-run isolation,
  Agent/worker restart recovery, hostile-network/credential/cleanup invariants,
  canonical unchanged, and public artifact bytes still unavailable.
- Supply-chain must pass paired reproducibility, all six SBOM/scans, 41 visible
  excepted and zero unexcepted Critical findings, licenses/notices and checksums.
- Run directly affected Python/Node/Web/worker/Render tests, full quality gates,
  repository/packaging policy, Markdown/Mermaid and every fresh GitHub check.
  No unchanged reruns; report attempts/timing/failures/skips literally.

## Scope and workflow

Only safe browser-preview stage observability, exact identified Web/Render/DB
boundary, reproducibility normalizer/tests/docs, strategic transcript. No
migration/grant unless the existing function itself is proven defective and a
forward migration is strictly necessary; no dispatcher redesign, worker runtime/
network/store, exception expansion, dependency, public retrieval, GC/source/
review/promotion, second PR, merge, auto-merge or release.

Commit/push unchanged order and `oap/active`, then repair. Publish exactly
`oap/reports/072-p-diagnose-and-close-preview-404.md` as report-only child with
literal implementation parent and `Report publication commit: SELF`; signal
exact FIFO `OK`.

Report exact safe failing stage/root cause/fix; manifest semantic result and
normalization; targeted/final run counts and timings; E2E/artifacts/restarts;
tests/CI; exception status; files/migration if any/SHAs; no extra PR and no
merge. Objective 072 remains `PARTIAL` pending public artifact retrieval and
final review.
