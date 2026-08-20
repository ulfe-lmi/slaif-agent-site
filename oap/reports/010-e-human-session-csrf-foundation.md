# OAP Coding-Agent Report — 010-e

## Work order

- Identifier: `010-e`
- Work-order file: `oap/orders/010-e-human-session-csrf-foundation.md`
- Numeric objective: `010`
- PR mode: `AMENDED_EXISTING_PR`
- PR result: `AMENDED_EXISTING_PR`

## Status

PARTIAL

## Executive summary

Implemented the bounded server-side opaque human-session and CSRF foundation.
The change adds migration `010_001`, Control-only lifecycle functions, typed
token/policy/service helpers, privilege inventory, focused tests, and the
required persistence/security documentation. No HTTP route, UI, NGINX,
Compose, OIDC, MFA, site, membership, capability, publication, or audit-event
surface was added. The resolver SQL ambiguity found by the focused integration
test was corrected before publication.

The implementation was pushed once. The focused PostgreSQL test was run twice
(the order maximum): both runs failed before the correction with the diagnosed
`public_id` ambiguity, so the correction could not be rerun under the order's
database-invocation cap. GitHub CI subsequently failed because the pre-existing
database-bootstrap relation inventory assertion was not updated for the new
`control.user_session` table (all PostgreSQL versions); Compose packaging also
failed. This report therefore truthfully remains `PARTIAL` and requests a
strategic continuation for the required repair and verification.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: `#15` — <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- State: `OPEN`, non-draft, `MERGEABLE`, merge state `UNSTABLE`
- Base/head: `main` / `oap/010-installation-local-auth`
- Starting remote `main` SHA: `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Starting remote PR head: `f34bd92462173c3d70c923576a2f2f1cb8d5b882`
- Implementation head SHA: `1d74623e069515bb9a8574ed0bf58d64a77fb9c2`
- Report publication commit: SELF
- No merge, force-push, auto-merge, close, or extra PR performed.

## Changes

- Added `control.user_session` migration with opaque versioned public IDs,
  256-bit secret/CSRF digests, expiry/revocation fields, owner-only table,
  and least-privilege `slaif_control` grants.
- Added SECURITY DEFINER create/resolve/revoke functions with fixed
  `pg_catalog` search path, active-user checks, idle/absolute/recent-auth
  policy, row locking, touch throttling, and idempotent revoke.
- Added typed token parsing, constant-time digest helper, frozen session and
  cookie policies, masked representations, and ControlDatabase service wiring.
- Added unit/integration coverage, privilege/repository contract updates, and
  the authorized authentication/configuration/database/operations docs.

## Acceptance evidence

- Unit session/foundation/config/database tests: **58 passed**.
- Ruff format/check: **passed**.
- Mypy: **passed** (80 files).
- Compileall, repository unittest: **passed** (50 tests).
- Repository policy: **passed**.
- Explicit changed-document Markdownlint: **passed** (5 files).
- Focused PostgreSQL integration: **2 attempts, both failed** before the SQL
  ambiguity correction; no third invocation was made.
- Migration lifecycle CI: PostgreSQL 14–18 **failed** on the unchanged
  expected relation list missing `control.user_session`.
- Other CI jobs: Python 3.12/3.13/3.14, Node, Mermaid, Markdown, dependency
  review, repository policy, supply-chain evidence, and CodeQL **passed**;
  Compose and edge packaging **failed**. CI run `32394634119`; CodeQL run
  `32394634113`; no reruns.

## Hashes and protocol evidence

- Activated order SHA256: `e64198d2ece1687b575714affc3f5b9ea4f1f6caa9f633e1c83b8f409747a2`
- Root `AGENTS.md`: `29742029b3896bc9b2106742ad6f1f4a029b1831737ff23a9d2fc4258a2b580d`
- `OAP-COMMUNICATION-coding-agent.md`: `ffa3e2bf7998c1274543dc76f22f4b19655d2d209fdbde2a020eff8fa47d83b8`
- `ARCHITECTURE-for-agents.md`: `af25568ac371bba2716ecc512f06a940dbc0c25211aba6ccd6e5cee5e5cf0580`
- Full `ARCHITECTURE.md` source hash (not loaded): `813f57c3f10f7fdb05c88807399fbcf8dd50f1c61871ce833a379467344e02fa`
- Prior 010-d order/report hashes preserved: order
  `9f799d9675af516eb188001c161a29aa4d2aea22245e726ddcdba35f8614c5dd`,
  report `6d820e3013c5ae6c8d4009631714b78d9fb722e748f14f14e3292131e134806f`.

## Scope and safety confirmations

- Exactly one existing objective PR amended; no extra PR.
- No production credentials, secrets, capability tokens, cookies, or private
  URLs committed or printed.
- No production systems accessed; no destructive action performed.
- Broad local Compose, browser, image, full DB matrix, and Node suites were not
  run because the order explicitly prohibited them; GitHub gates are recorded.
- Report publication is the only remaining commit and must change only this
  file; its first parent will be the implementation SHA above.

## Limitations / requested continuation

Repair the CI relation inventory (and resulting Compose failure), then rerun
the required focused PostgreSQL and CI verification in a new activated
continuation order. The resolver correction is present in the implementation
head but lacks a permitted post-correction local integration rerun.
