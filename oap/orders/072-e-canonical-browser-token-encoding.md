# OAP Work Order — 072-e

## Objective

Continue Objective 072 on PR #66 with one narrow acceptance correction. Make
the `sbp1` browser-preview verifier reject non-canonical base64url encodings,
including alternate final signature characters whose discarded pad bits decode
to the same HMAC bytes. Preserve the completed 072-d route, privilege, COW,
credential-binding, secret, and queued-run architecture. Do not implement the
worker, dispatcher, Playwright, or artifact bytes, and do not merge.

## Verified current state

- Numeric objective: `072`; round: `072-e`.
- Mode: `AMEND_EXISTING_PR`; amend only PR #66 on
  `oap/072-browser-worker-real-playwright`. Create no new PR.
- Begin from verified remote 072-d report head
  `c3fc8dda348396e91b349d669f5d674915ffea36`; its sole parent is
  implementation head `d5bb47107d45435c5bd02973c6b7f0f47622b474`
  and its sole changed path is
  `oap/reports/072-d-agent-browser-routes-and-preview-credential.md`.
- Remote main remains
  `082f2359b0c4d59b692580d17992c35d46183b12`; PR #66 is open,
  non-draft, and mergeable. All 20 implementation-head checks passed. Reconcile
  the live report-head checks before mutation.
- The bounded 072-d implementation is genuine and retained: real
  capability-authenticated Agent run routes, migration 036 Render authority,
  run-bound HMAC credential, Web/Render header path, COW recheck, isolated key
  mounts, and real PostgreSQL/Compose evidence.
- Strategic review reproduced one precise defect. A token with canonical final
  signature character `0` can be changed textually to final character `1`;
  both forms decode to the same 32-byte signature, and the current verifier
  accepts the altered form. The earlier test failure was therefore useful
  evidence of missing canonical-encoding enforcement, not merely a defective
  tamper test.
- This alias does not bypass the persisted nonce digest, durable run binding,
  or workspace isolation. It nevertheless violates 072-d requirements for
  canonical serialization, immutable token representation, and rejection of
  malformed encodings.

## Bounded correction

Change only the shared browser-preview credential verifier and its directly
relevant tests or exact documentation if documentation needs factual
clarification.

Require every decoded base64url component to have one canonical unpadded text
representation. After strict bounded decoding, re-encode the bytes with the
existing canonical encoder and require an exact string match. Apply this to the
header, payload, and signature components. Preserve strict duplicate-key JSON,
fixed header facts, constant-time HMAC byte comparison, token size/lifetime,
all claim validation, expected binding, and stable non-secret error behavior.

Add deterministic regression proof that:

- a freshly issued canonical token still verifies and the existing stable
  vector remains unchanged unless repository evidence proves the vector itself
  was wrong;
- changing only unused final signature pad bits yields a distinct textual token
  that decodes to the same signature bytes but is rejected by the verifier;
- non-canonical header and payload component encodings are rejected even when a
  test recomputes an otherwise valid HMAC over those altered component strings;
- ordinary significant signature tampering, replay authority, expiry, route,
  site, workspace, run, evidence, artifact, and duration binding behavior remain
  unchanged; and
- failures reveal no token, key, nonce, binding, SQL, or role material.

If exact base64url canonicality cannot be enforced by this local verifier change
without changing the token contract, stop and report rather than redesigning
the credential.

## Explicit non-goals

Do not change Agent or Render HTTP routes, public response shapes, HMAC
algorithm, key format or mounts, token prefix/header/claims, TTL or clock skew,
nonce digest/consumption, migration 036, database functions or grants, COW
session behavior, capability authentication, quotas, idempotency, worker code,
Compose topology, dependencies, lockfiles, CI policy, or prior OAP artifacts.

Do not add dispatcher/claim wiring, Playwright, browser binaries, artifact
storage or retrieval, network confinement, source crawling, responsive sweep,
review/promotion/publication, another PR, or merge. Numeric Objective 072 remains
PARTIAL after this correction.

## Acceptance and verification

- The exact reproduced `0` to `1` final-character alias and all equivalent
  non-zero discarded-pad-bit variants fail with the stable credential error.
- Canonical tokens and the deterministic vector continue to pass.
- Header, payload, and signature base64url canonicality is proven directly;
  HMAC comparison remains constant-time for canonical signatures.
- No runtime authority, schema, route, secret distribution, dependency, or
  worker behavior changes.
- Focused credential tests pass, including the new canonicality regressions.
- Run frozen Ruff formatting/checking and Mypy for the touched Python scope,
  the full backend unit/repository suite, repository policy, and Markdownlint.
  Run any additional directly affected test scope discovered during the change.
- Push one bounded implementation commit and require every fresh GitHub check
  for that exact implementation SHA to be successful before report
  publication. Record any failure, retry, skip, or not-run result honestly.

Commit and push the exact strategic 072-e order and active bytes unchanged on
PR #66, then the bounded verifier/tests correction. Publish exactly
`oap/reports/072-e-canonical-browser-token-encoding.md` as one report-only child
with `Report publication commit: SELF` and a literal 40-hex implementation
parent. Report status remains `PARTIAL` for Objective 072 while stating whether
the 072-e correction is complete. Verify remote parent/path/head, signal exact
FIFO `OK`, and do not merge.

The report must state PR/base/branch/all SHAs; the exact alias reproduction and
post-fix rejection; canonical header/payload/signature proof; unchanged vector,
TTL, nonce, route/COW/privilege/secret/worker boundaries; files and dependency
state; every local and CI result; no extra PR; and no merge.
