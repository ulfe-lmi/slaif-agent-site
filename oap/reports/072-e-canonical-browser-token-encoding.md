# OAP Coding-Agent Report — 072-e

## Work order

- Identifier: `072-e`; numeric objective: `072`.
- Work-order file:
  `oap/orders/072-e-canonical-browser-token-encoding.md`.
- PR mode: `AMENDED_EXISTING_PR`.

## Status

PARTIAL

The bounded 072-e canonical-base64url correction is complete and verified.
Numeric Objective 072 remains PARTIAL because the browser dispatcher, worker
execution, Playwright worker dependency/image, artifact bytes/retrieval,
network confinement, source tools, and browser execution E2E remain deferred.

## Executive summary

Corrected the `sbp1` verifier so each strictly decoded header, payload, and
signature base64url component must round-trip to its exact canonical unpadded
text. This rejects alternate discarded-pad-bit spellings that decode to the
same bytes while preserving the fixed HMAC algorithm, constant-time comparison
for canonical signatures, token facts, stable vector, TTL, expected bindings,
and all runtime authority.

Deterministic regression proof reproduces the strategically reported final
signature character `0` changed to `1`; `1`, `2`, and `3` are distinct strings
that decode to the same 32-byte signature. The old verifier accepted them and
the new verifier rejects all three. Re-signed non-canonical header `A`→`B` and
payload `Q`→`R` component aliases likewise decode to the same bytes but now
fail before parsed facts can authorize preview.

No route, schema, migration, function/grant, key format/mount, nonce behavior,
COW path, dependency, worker behavior, or documentation changed. The focused
and full required local gates passed, the directly affected real PostgreSQL
Render-preview test passed, and all 20 fresh implementation-head GitHub checks
completed successfully.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`.
- PR: #66, <https://github.com/ulfe-lmi/slaif-agent-site/pull/66>.
- PR state at report drafting: `OPEN`, non-draft, `MERGEABLE`, merge-state
  `CLEAN`.
- Base branch: `main`; head branch:
  `oap/072-browser-worker-real-playwright`.
- Starting remote objective head:
  `c3fc8dda348396e91b349d669f5d674915ffea36`.
- Starting authoritative remote main:
  `082f2359b0c4d59b692580d17992c35d46183b12`.
- Implementation head SHA:
  `eb5c7d51fcbeee98251c63f427fdb806db6a0ac1`.
- Report publication commit: SELF.
- Remote PR head after report publication: SELF (literal derived and verified
  after publication).
- Implementation commit pushed before report:
  `eb5c7d51fcbeee98251c63f427fdb806db6a0ac1`
  (`fix(browser): reject noncanonical preview tokens`).
- Report parent must equal implementation SHA: yes; verified after publication.
- New PR this turn: no. Existing PR amended: yes. Merge performed: NO.

## Changes made

### Canonical component decoding

- Added one private verifier helper that calls the existing strict bounded
  decoder, re-encodes the resulting bytes with the existing canonical unpadded
  base64url encoder, and requires exact string equality.
- Applied that helper to exactly the `sbp1` header, payload, and signature
  components.
- Left the key-file decoder and key format unchanged. The signer already emits
  canonical components and was not changed.
- Left `hmac.compare_digest(signature, expected_signature)` in the same
  canonical-signature path. Significant canonical signature differences still
  reach constant-time byte comparison and fail.
- Newly recognized non-canonical components raise the same stable non-secret
  `BrowserPreviewCredentialError` message, without token, key, nonce, binding,
  SQL, or role material.

### Deterministic regression proof

- Extended the fixture issuer with an optional deterministic nonce while
  preserving the original default vector.
- Added strict test helpers to decode, re-sign, and locate same-byte
  non-canonical pad-bit aliases.
- Added a fixture token whose canonical 32-byte HMAC signature ends in `0`.
  Replacing only that character with `1`, `2`, or `3` produces three distinct
  textual signatures that decode to the exact same bytes; every alias now
  fails.
- Added a significant signature-bit change proving ordinary HMAC tampering
  still fails.
- Added an otherwise valid re-signed header component with canonical final
  character `A` changed only in discarded bits to `B`; both strings decode to
  the same accepted header JSON bytes, but the alias now fails.
- Added an otherwise valid re-signed payload component with canonical final
  character `Q` changed only in discarded bits to `R`; both strings decode to
  the same claim bytes, but the alias now fails.
- Existing deterministic token SHA-256 remains
  `133725d1ed391c0c36dafee52c5cfa9b92ef0dbd731eccf8447eeb7da54593db`.

## Files changed

- Verifier:
  `services/backend/src/slaif_agent_site/browser_preview_credentials.py`.
- Direct regression tests:
  `services/backend/tests/unit/test_browser_preview_credentials.py`.
- Strategic transcript committed unchanged:
  `oap/orders/072-e-canonical-browser-token-encoding.md` and `oap/active`.
- Documentation changed: none; existing credential documentation remains
  factually correct.
- Dependency and lock files changed: none.
- Migrations, schemas, routes, HTTP response shapes, privileges, Compose,
  secrets, and worker files changed: none.

## Acceptance-criteria evidence

### Criterion 1 — Exact signature-alias rejection

- Result: PASSED.
- Deterministic nonce `00000000000000000000000000000005` produces a token
  whose canonical signature ends in `0`.
- Changing only that character to `1`, `2`, or `3` creates a different textual
  token in each case while strict decoding produces the same original 32-byte
  HMAC.
- Before the fix, the exact focused regressions failed because the verifier
  accepted the `…1` alias and the other same-byte forms. After the fix, all
  aliases raise the stable credential error. A significant signature change
  still fails through the unchanged HMAC verification boundary.

### Criterion 2 — Header/payload/signature canonicality

- Result: PASSED.
- Signature canonicality is directly proven by all three non-zero discarded
  pad-bit variants of canonical final character `0`.
- Header proof re-signs an altered component whose last character is `B`
  instead of canonical `A`; payload proof re-signs `R` instead of canonical
  `Q`. Each pair decodes byte-for-byte identically, so valid HMAC recomputation
  cannot hide the non-canonical representation.
- Exact re-encoding fails the alias before header/claims validation. Freshly
  issued canonical components still verify.

### Criterion 3 — Existing credential behavior preserved

- Result: PASSED.
- Existing tests continue to prove fixed version/algorithm/key/audience,
  duplicate-key rejection, maximum size/lifetime, future/expiry denial,
  signature/key mismatch, and capability/site/workspace/run/route/target
  expected bindings.
- The stable vector, token prefix/header/claims, 60-second maximum TTL,
  five-second skew, nonce digest, key identifier, and stable errors are
  unchanged.
- Canonical signature HMAC comparison remains `hmac.compare_digest` over exact
  32-byte values.

### Criterion 4 — Runtime boundaries unchanged

- Result: PASSED by bounded diff and regression evidence.
- Agent/Render/Web routes and response shapes, migration 036 and every database
  function/grant, capability/idempotency/quota state, nonce consumption, shared
  lock and COW recheck, secret initializer/mounts, and Compose topology have no
  diff.
- The directly affected real PostgreSQL Render browser-preview integration test
  passes, preserving overlay/canonical isolation and one-time authority.
- Browser worker remains health-only, DB-less, key-less, without Playwright,
  dispatcher, artifact volume/bytes, or execution route.

## Local verification

- Pre-fix reproduction:
  `uv run --frozen pytest services/backend/tests/unit/test_browser_preview_credentials.py -k noncanonical -vv`:
  expected FAILED — 2 failed/11 deselected. The signature test showed the exact
  `…0`→`…1` same-byte token was accepted; the header test showed the re-signed
  same-byte alias was accepted. No product test was suppressed.
- Post-fix focused credential command:
  `uv run --frozen pytest services/backend/tests/unit/test_browser_preview_credentials.py -vv`:
  PASSED — 13 tests in 0.10 seconds.
- `uv run --frozen ruff format --check services/backend/src/slaif_agent_site/browser_preview_credentials.py services/backend/tests/unit/test_browser_preview_credentials.py`:
  PASSED — 2 files already formatted.
- `uv run --frozen ruff check services/backend/src/slaif_agent_site/browser_preview_credentials.py services/backend/tests/unit/test_browser_preview_credentials.py`:
  PASSED.
- `uv run --frozen mypy`: PASSED — 216 source files.
- `uv run --frozen pytest services/backend/tests/unit tests/repository`:
  PASSED — 473 tests in 15.40 seconds.
- `uv run --frozen pytest services/backend/tests/integration/test_render_browser_preview.py -q`:
  PASSED — 1 real PostgreSQL integration test in 6.30 seconds.
- `python tools/check_repository.py`: PASSED.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: PASSED — 233
  Markdown paths discovered, zero issues reported.
- `uv lock --check`: PASSED — 45 packages resolved; no lock change.
- `git diff --check`: PASSED.
- Local full backend integration, Node, PostgreSQL 14–18 matrix, Compose, and
  supply-chain commands: NOT RUN locally because this bounded verifier-only
  order required the focused real Render integration plus the named local
  gates. Their complete fresh GitHub equivalents ran and passed below. No
  required local command was skipped.

## GitHub CI / required checks

State observed for implementation head
`eb5c7d51fcbeee98251c63f427fdb806db6a0ac1`: all 20 reported checks completed
successfully; all required checks green at drafting: yes.

- `Repository policy`: SUCCESS.
- `Node contracts`: SUCCESS.
- `Python 3.12 quality and package`: SUCCESS.
- `Python 3.13 quality and package`: SUCCESS.
- `Python 3.14 quality and package`: SUCCESS.
- `Foundation PostgreSQL 14`: SUCCESS.
- `Foundation PostgreSQL 15`: SUCCESS.
- `Foundation PostgreSQL 16`: SUCCESS.
- `Foundation PostgreSQL 17`: SUCCESS.
- `Foundation PostgreSQL 18`: SUCCESS.
- `Compose and edge packaging`: SUCCESS.
- `Supply-chain evidence`: SUCCESS.
- `Markdown`: SUCCESS.
- `Mermaid`: SUCCESS.
- `Dependency review`: SUCCESS.
- `Detect supported languages`: SUCCESS.
- `Analyze (actions)`: SUCCESS.
- `Analyze (python)`: SUCCESS.
- `Analyze (javascript-typescript)`: SUCCESS.
- `CodeQL`: SUCCESS.

The report-only SELF commit may trigger fresh checks; strategy independently
verifies SELF.

## Local setup / dependencies

- Used exact existing uv 0.12.5 and the frozen Python environment.
- The directly affected integration test used the repository's disposable local
  PostgreSQL fixture and fake credentials.
- No sudo, package installation, production credential, production system/data,
  hosted service, account-bound runtime, or external write was needed.
- No production/test dependency, Python/Node lock, signing key format, HMAC
  algorithm, token contract, or runtime image changed.

## Documentation

No documentation change was needed. Existing documentation already states that
the token is canonically serialized and strictly verified; the implementation
now enforces that statement for every base64url component.

## Safety and scope confirmations

- Unrelated files changed: no.
- Production secrets accessed: no. Production systems/data accessed: no.
- Token fixture, key fixture, and nonce are deterministic fake values. No real
  token, key, nonce, capability, cookie, DB URL, or binding was printed or
  committed.
- Required tests skipped/not run: no. The expected pre-fix failure and every
  local not-run scope are recorded above; all fresh required GitHub checks ran.
- Scope deviation: no. No route, schema, migration, function/grant, TTL,
  nonce/replay, key/mount, COW, worker, Compose, dependency, or documentation
  behavior changed.
- Extra objective PR: NO. Coding-agent merge/auto-merge/close: NO.
- Activated order/active edited by coding agent: NO; exact strategy-authored
  bytes were committed unchanged.
- Earlier migrations/orders/reports edited: no.
- Report commit changes only this report: yes (verified after commit).

## Known limitations / blockers

- Browser worker remains a health-only, DB-less stub without signing key,
  Playwright, browser binary, dispatcher input, artifact storage, or execution
  route.
- Durable runs remain truthfully `QUEUED`; production token minting awaits the
  future trusted dispatcher, and artifact byte retrieval remains 404.
- Network confinement, source crawling, responsive sweep, browser execution
  E2E, publication, and artifact GC remain deferred.
- Numeric Objective 072 therefore remains PARTIAL by order. The bounded 072-e
  correction is complete with no blocker.

## Recommended strategic follow-up

Strategy may independently verify the exact alias rejection and decide whether
a later same-PR Objective 072 order should proceed to the confined dispatcher,
real Playwright worker, and private artifact-byte boundary. Coding makes no
next-order, acceptance, merge, or release decision.
