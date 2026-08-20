# OAP Coding-Agent Report — 010-c

## Work order

- Identifier: `010-c`
- Work-order file: `oap/orders/010-c-null-safe-setup-proof-function.md`
- Numeric objective: `010`
- PR mode: `AMEND_EXISTING_PR`
- PR result: `AMENDED_EXISTING_PR`

## Status

COMPLETE

## Executive summary

PR `#15` now closes the database-side NULL bypass in the unmerged `009_001`
initial-setup completion function. The proof guard explicitly rejects a NULL
expected generation, NULL presented digest, and any digest whose length is not
exactly 32 bytes. Generation and digest equality now use PostgreSQL
`IS DISTINCT FROM`, so NULL can no longer make an inequality expression
evaluate to an unhandled SQL NULL.

No signature, object, relation, grant, dependency, application operation, or
intended behavior changed. The row lock, initialized/stored-token/expiry
checks, constant `P0001` database failure, application-side
`secrets.compare_digest`, transaction, owner, fixed search path, `PUBLIC`
revoke, and exact Control execute grant remain intact.

One new direct-function regression uses the actual `slaif_control` role after
issuing a generated fake setup token. NULL generation, NULL digest, 31-byte
digest, 33-byte digest, wrong 32-byte digest, and stale generation each return
SQLSTATE `P0001`. After every call, the complete owner-read snapshot is byte-
for-byte/value-for-value unchanged: zero users, zero administrator assignments,
NULL initialization time, and the original digest, issue time, expiry, and
generation. The ordinary typed adapter then consumes the same valid token,
creates exactly one administrator, initializes, and clears setup material.

The single permitted PostgreSQL invocation passed the full 7-test local-
identity set in 12.30 seconds, including all existing success, replay,
concurrency, uniqueness rollback/retry, cancellation, OIDC, grant, and denial
coverage. A packaged-source assertion protects the exact null-safe guard. All
affected local static/package/repository checks passed. The single GitHub
generation passed all 20 checks, with PostgreSQL 14–18 green and zero open
objective-branch code-scanning alerts. No rerun or correction was used.

No session, route, UI, Compose, OIDC flow, site, membership, capability,
publication, or other planned behavior was started. Server-side sessions
remain planned for 010-d; HTTP/UI/NGINX/Compose/E2E closure remains planned for
010-e.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: `15`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- PR state at report time: `OPEN`
- Draft at report time: `false`
- Mergeable at report time: `MERGEABLE`
- Merge state at report time: `CLEAN`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`
- Base branch: `main`
- Starting and final remote base SHA:
  `d4d1c7b7fd27ad2245f0b1224792a252d5274b5c`
- Head branch: `oap/010-installation-local-auth`
- Starting remote/report head:
  `f1abade214bbb10c951d9e089ff63e23f574b5cf`
- Implementation commit pushed:
  `b0f6515a3efe802bde7fa7cb18ec28f134dbf77f` —
  `Harden initial setup proof checks`
- Literal 010-c implementation head:
  `b0f6515a3efe802bde7fa7cb18ec28f134dbf77f`
- Report publication commit: SELF
- Remote PR head after report publication: SELF
- Implementation-head first parent:
  `f1abade214bbb10c951d9e089ff63e23f574b5cf`
- Implementation diff: 5 files, 296 insertions, 4 deletions
- New PR created this round: no
- Existing PR amended this round: yes
- Objective-010 PR count: exactly one
- Force push performed: no
- Merge performed: NO
- PR closed: NO
- Auto-merge enabled: NO

GitHub was reconciled before editing and immediately before the implementation
commit. The branch remained at the exact 010-b report head named by the order;
PR `#15` remained open, non-draft, and the unique PR for the required objective
branch. PRs `#12` and `#13` were not acted upon.

## Changes made

### Exact SQL correction

The existing completion function retains its signature and object identity.
Only the proof portion of its `IF` failure guard changed. It now includes:

```sql
OR p_expected_generation IS NULL
OR p_presented_digest IS NULL
OR pg_catalog.octet_length(p_presented_digest) IS DISTINCT FROM 32
OR installation.setup_token_generation
     IS DISTINCT FROM p_expected_generation
OR installation.setup_token_digest
     IS DISTINCT FROM p_presented_digest
```

This precedes every insert/update. Explicit input NULL and length checks make
the accepted proof shape clear. `IS DISTINCT FROM` supplies null-safe equality
for generation and digest. Stored digest presence, database-clock expiry, and
initialized-state checks remain ahead of the write. The same row is still
locked with `FOR UPDATE`; failure still raises only SQLSTATE `P0001` and
`initial setup failed` inside the trusted function. No dynamic SQL exists.

The application's primary comparison remains the 010-a setup-token helper,
which validates token shape, computes SHA-256, and calls
`secrets.compare_digest`. The database comparison remains only a second
invariant/race guard in the same Control transaction.

### Direct adversarial regression

The PostgreSQL regression issues a generated fake token, captures the complete
installation/identity snapshot, creates one valid production-profile fake
password hash, and calls the completion function directly while set to the
actual `slaif_control` role. It independently covers:

- NULL expected generation with the correct digest;
- current generation with NULL digest;
- current generation with a 31-byte digest;
- current generation with a 33-byte digest;
- current generation with a wrong 32-byte digest; and
- stale generation with the correct digest.

Each call is asserted to reach the function's constant `P0001` failure rather
than merely failing privilege resolution. After every call, the test compares
the complete snapshot to the original tuple, proving no user/admin insert, no
initialization, and no token field/generation mutation. It never prints the
proof, hash, or database error.

After all six failures, the existing typed Control adapter uses the valid token
and succeeds. The final snapshot proves one user, one administrator,
non-NULL initialization, unchanged generation, and NULL digest/issued/expiry.
The other six tests in the same integration file continue to prove exact
objects/grants/denials/OIDC, ordinary atomic success, invalid/expired/revoked/
replay behavior, exactly-one concurrency, uniqueness rollback/retry, and
cancellation rollback.

### Static/package regression

The existing foundation/package contract now asserts that the packaged
migration source contains both explicit input NULL checks, the null-safe
32-byte length check, and both `IS DISTINCT FROM` proof comparisons. It also
asserts that the prior nullable `<>` comparisons do not exist. Existing source
assertions continue to prove exactly two tables/two functions, fixed search
path, security definer, and Control-only grant.

## Files changed before report publication

- `oap/active`
- `oap/orders/010-c-null-safe-setup-proof-function.md` (new)
- `services/backend/src/slaif_agent_site/db/alembic/versions/009_001_local_identity.py`
- `services/backend/tests/integration/test_local_identity.py`
- `services/backend/tests/unit/test_foundation_contract.py`

These are exactly the five authorized implementation/order paths. No
documentation clarification was necessary because intended behavior and the
documented defense-in-depth contract did not change. This report is the sole
additional path in its mandatory report-only commit.

## Governance and artifact integrity

- `AGENTS.md` SHA-256:
  `dbf75301405937815d65093da30d2ca38fd04e9f8ed198cf56239adc1764e462`
- `OAP-COMMUNICATION-coding-agent.md` SHA-256:
  `e6150d6efb5a64e7f8af29b00514776972d4f98a0632281ddc260110c6374604`
- `ARCHITECTURE.md` SHA-256:
  `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- `SECURITY.md` SHA-256:
  `ec327af34d13406b560f75834d8bbda685f81dad17fd400cce0c5b6b8df4e23c`
- Activated 010-c order SHA-256:
  `75998d30ba6312be6c94cbaffcf0a2571f5bf30cf1121e2d27bc84a20d19dc20`
- Preserved 010-a order SHA-256:
  `f0ed7175b183483940d14c1cd4cd207864f2110e945f54485d1ec982c0c7bd26`
- Preserved 010-a report SHA-256:
  `efe9e2d5770d322393b39dec3597001dbc33d6d1b76c4f2a82a40d9c53a0946e`
- Preserved 010-b order SHA-256:
  `b548023ef90eda5f08b888fae5c2c417be1e077d52530a0995c79dbb18180748`
- Preserved 010-b report SHA-256:
  `90d77eda65395d0a0ca696fbb24fccc1f5d0a3e71a3b677918a2d184b429a588`
- Active pointer bytes: exactly `010-c\n` (`30 31 30 2d 63 0a`)

No narrower applicable instruction file exists. Governance and every prior OAP
order/report remained unchanged. The activated order and active pointer were
committed byte-for-byte as supplied by the strategic model.

## Attempt and generation ledger

### Activation and elapsed budget

- Strategic artifact timestamp/activation basis:
  `2026-08-18T02:19:06Z`.
- Implementation committed: `2026-08-18T02:22:06Z`.
- Implementation-head CI completed: `2026-08-18T02:27:08Z`.
- Activation through authoritative green checks: 8m02s, within the 20-minute
  target and 30-minute hard stop.

### Local static/package attempt

- Affected Ruff format: passed; 3 files left unchanged.
- Affected Ruff lint: passed.
- Canonical strict mypy: passed with no issues in 76 source files.
- Affected compile: passed.
- Directly affected packaged migration/static test: 9 passed in 1.11s.
- Repository policy and diff checks: passed.
- No local correction was required.

### PostgreSQL integration invocation 1 of 1

- Exact argv: `uv run --frozen pytest -q
  services/backend/tests/integration/test_local_identity.py`
- PostgreSQL: existing local 16.14 service with generated disposable fixture
  databases and fake roles/secrets.
- Result: 7 passed in 12.30 seconds.
- Direct proof cases: NULL generation/correct digest, current generation/NULL
  digest, 31-byte digest, 33-byte digest, wrong 32-byte digest, and stale
  generation/correct digest all returned `P0001`.
- Unchanged-state proof after each: original installation snapshot exactly
  equal, including zero identity/admin counts and unchanged initialization,
  digest, issue, expiry, and generation values.
- Valid typed path after all failures: passed; one user/admin, initialized,
  token material cleared.
- Fixture cleanup: passed; disposable databases and fake login roles removed.
- Retry or second PostgreSQL invocation: none.

### GitHub check generation 1 of 1

- Implementation SHA: `b0f6515a3efe802bde7fa7cb18ec28f134dbf77f`
- CI run `32091587480`: success; `2026-08-18T02:22:16Z`–
  `2026-08-18T02:27:08Z` (4m52s).
- CodeQL run `32091587368`: success; `2026-08-18T02:22:16Z`–
  `2026-08-18T02:23:28Z` (1m12s).
- All 20 check runs: success.
- Workflow rerun: none; zero were authorized.
- Second implementation commit/check generation: none; prohibited by order.

Caps used: 1 of 1 implementation commit/check generation, 1 of 1 focused
PostgreSQL invocation, and 0 workflow reruns.

## Acceptance-criteria evidence

### Criterion 1 — amend the unique existing PR once

- Result: PASS
- Evidence: one normal implementation commit amended the existing objective
  branch and triggered one check generation. PR `#15` remains the sole open,
  non-draft objective PR with exact title/base/head. No extra PR, force push,
  merge, close, auto-merge, rerun, or unrelated action occurred.

### Criterion 2 — null-safe proof guard and exact privileges

- Result: PASS
- Evidence: migration/static/runtime evidence proves explicit NULL generation,
  NULL digest, and exact 32-byte checks plus `IS DISTINCT FROM` comparisons.
  Object/signature/owner/search path/row lock/failure/grants are unchanged;
  GitHub PostgreSQL 14–18 passed.

### Criterion 3 — direct adversarial calls cannot mutate

- Result: PASS
- Evidence: all six required direct calls ran under actual `slaif_control`,
  reached `P0001`, and were followed by equality of the full original snapshot:
  no user, no administrator, no initialization, and no token-state change.

### Criterion 4 — valid typed path remains atomic

- Result: PASS
- Evidence: after all direct failures, the ordinary adapter path validated the
  token through the unchanged application `compare_digest`, invoked the same
  completion transaction, created one user/admin, initialized, and cleared all
  token material. Existing replay/concurrency/rollback/cancellation tests also
  passed in the same sole invocation.

### Criterion 5 — no other behavior or contract changed

- Result: PASS
- Evidence: diff/path checks show only the existing migration guard, direct
  regression, static assertion, and strategic artifacts. No object, signature,
  relation, dependency, documentation, role, product source, session, route,
  UI, Compose, or planned feature changed.

### Criterion 6 — checks, alerts, and immutable protocol

- Result: PASS through report publication.
- Evidence: all 20 implementation-head checks passed in the single generation;
  open objective-branch code-scanning alerts are zero. This report records the
  literal implementation head and is the final SELF report commit.

## Local verification

- `uv run --frozen ruff format
  services/backend/src/slaif_agent_site/db/alembic/versions/009_001_local_identity.py
  services/backend/tests/integration/test_local_identity.py
  services/backend/tests/unit/test_foundation_contract.py`: PASSED — 3 files
  left unchanged.
- `uv run --frozen ruff check` on the same three files: PASSED.
- `uv run --frozen mypy`: PASSED — no issues in 76 source files.
- `uv run --frozen python -m compileall -q` on the same three files: PASSED.
- `uv run --frozen pytest -q
  services/backend/tests/unit/test_foundation_contract.py`: PASSED — 9 passed
  in 1.11 seconds; includes packaged migration/offline graph/static guard.
- `uv run --frozen pytest -q
  services/backend/tests/integration/test_local_identity.py`: PASSED — 7 passed
  in 12.30 seconds; sole PostgreSQL invocation.
- `uv run --frozen python tools/check_repository.py`: PASSED —
  `PASS repository policy`.
- `git diff --check` and staged diff check: PASSED.
- Exact allowed-path, active/order SHA, prior-artifact SHA, branch/head/parent,
  PR identity, sole-PR, and clean-worktree checks: PASSED.
- Local supply-chain/image/SBOM/Grype gate: NOT RUN — explicitly forbidden;
  GitHub supply-chain evidence passed.
- Local Compose smoke/configuration: NOT RUN — explicitly forbidden and no
  Compose file changed; GitHub Compose/edge packaging passed.
- Local full Python/PostgreSQL matrices: NOT RUN — explicitly forbidden;
  GitHub Python 3.12–3.14 and PostgreSQL 14–18 passed.
- Local Node/Markdown/Playwright: NOT RUN — explicitly forbidden; GitHub Node
  contracts and Markdown passed.

No failed, skipped, pending, unavailable, or not-run item above is represented
as passing local evidence.

## GitHub CI / required checks

- CI run: `32091587480` — SUCCESS
- CodeQL run: `32091587368` — SUCCESS
- Implementation head checked:
  `b0f6515a3efe802bde7fa7cb18ec28f134dbf77f`
- Analyze (actions): SUCCESS — 38s
- Analyze (javascript-typescript): SUCCESS — 1m00s
- Analyze (python): SUCCESS — 50s
- CodeQL aggregate: SUCCESS — 3s
- Compose and edge packaging: SUCCESS — 2m44s
- Dependency review: SUCCESS — 7s
- Detect supported languages: SUCCESS — 4s
- Foundation PostgreSQL 14: SUCCESS — 54s
- Foundation PostgreSQL 15: SUCCESS — 49s
- Foundation PostgreSQL 16: SUCCESS — 53s
- Foundation PostgreSQL 17: SUCCESS — 55s
- Foundation PostgreSQL 18: SUCCESS — 54s
- Markdown: SUCCESS — 8s
- Mermaid: SUCCESS — 47s
- Node contracts: SUCCESS — 1m04s
- Python 3.12 quality and package: SUCCESS — 33s
- Python 3.13 quality and package: SUCCESS — 30s
- Python 3.14 quality and package: SUCCESS — 34s
- Repository policy: SUCCESS — 6s
- Supply-chain evidence: SUCCESS — 4m48s
- Totals: 20 successful, 0 failed, 0 cancelled, 0 skipped, 0 pending
- All required implementation-head checks green: YES
- Open objective-branch code-scanning alerts: 0
- Workflow reruns: 0
- The report-only SELF commit may trigger fresh checks. Those future results
  are not claimed here; the strategic model must independently verify them.

The successful implementation-head supply-chain artifact is:

- Artifact ID: `9308588239`
- Name:
  `supply-chain-evidence-efcea3d178311c89748c0f9d2e905ca0d494b024`
- Size: 1,705,087 bytes
- Created: `2026-08-18T02:27:04Z`
- Expires: `2026-09-01T02:27:03Z`
- Expired at report time: `false`

## Local setup / dependencies

- Existing frozen uv environment used; no dependency or lockfile changed.
- Existing local PostgreSQL 16.14 service used with disposable fixture
  databases and generated fake roles/secrets.
- New package, system installation, or `sudo`-level setup: none.
- Durable setup/configuration change: none.
- Production system, data, credential, account, or service accessed: none.

## Documentation impact

No documentation changed. This repair restores the already documented
database defense-in-depth behavior and does not alter the intended contract,
operator workflow, readiness, limitation, or future-round claim.

## Safety and scope confirmations

- Unrelated feature/refactor work: no.
- Allowed implementation/order paths: exactly five, all named above.
- Activated order or `oap/active` authored/modified by coding agent: NO; both
  strategic artifacts were committed byte-for-byte.
- Earlier OAP artifact edited: NO; 010-a and 010-b orders/reports retain the
  recorded SHA-256 values.
- Real secret, setup token, digest, DSN, password hash tied to a real secret,
  database error, private URL, or production data printed or committed: no.
- Test proof material: generated fake values only and never printed.
- Application constant-time comparison weakened or removed: no.
- Argon2, transaction, lock, expiry, failure, ownership, search path, `PUBLIC`
  revoke, or Control-only grant weakened: no.
- Function, relation, grant, dependency, or parameter added: no.
- Session, cookie, CSRF, recent-auth, route, UI, OIDC flow, site, membership,
  capability, publication, Compose, or planned feature added: no.
- PostgreSQL invocation cap exceeded: NO — exactly 1.
- Implementation/check-generation cap exceeded: NO — exactly 1.
- GitHub workflow rerun: NO — none authorized.
- Local forbidden broad supply-chain/image/Compose/matrix/Node/browser run: NO.
- Destructive reset/clean/checkout, broad prune, force push, extra objective PR,
  merge, close, or auto-merge: NO.
- PR `#12` or `#13` acted upon: NO.
- Report-publication commit changes only this report file: yes.

## Known limitations / blockers

- None within activated 010-c scope.
- This security repair does not make authentication browser-usable. Sessions
  remain absent until an authorized 010-d; HTTP/UI/Compose/E2E remains absent
  until an authorized 010-e.
- `COMPLETE` means the requested remote security state and evidence exist. It
  does not mean strategic acceptance and does not authorize this coding agent
  to merge.

## Recommended strategic follow-up

Independently verify this SELF report commit and first parent, the five-line
null-safe SQL proof guard, direct `slaif_control` NULL/length/wrong/stale cases,
unchanged snapshots, typed valid success, the single local/CI attempt ledger,
20 green checks, zero alerts, exact allowed paths, and preserved 010-a/010-b
artifacts. The strategic model alone decides whether to accept the repair or
activate 010-d on PR `#15`; no merge is authorized by this report.
