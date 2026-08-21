# OAP Work Order — 012-d

## Objective and exact state

Amend objective-012 PR #24 to close one disposable-test isolation gap: the
membership fixture precondition must reject any pre-existing user account, and
the post-E2E assertion must prove the database contains exactly the two fixed
OIDC fixtures plus the one setup-created LOCAL Platform Administrator.

- Numeric objective: `012`; round: `012-d`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#24](https://github.com/ulfe-lmi/slaif-agent-site/pull/24)
- Base/head: `main` / `oap/012-membership-rbac`
- Required starting remote head:
  `b87626cb732279605400b011c5a51e085b7ac0b4`
- 012-c implementation parent:
  `46dc01c239b482bbf6cb5fc82eb14737c715a91c`
- Verified state: open, ready/non-draft, mergeable, no reviews/threads; correct
  report-only head/parent; all 20 current-head checks successful.

Fetch and verify this exact PR/head. Amend only PR #24; never create a PR,
merge, close, auto-merge, or workflow-rerun.

## Authorized files and repair

```text
tools/compose/smoke.sh
tests/packaging/test_compose_smoke_contract.py
oap/active
oap/orders/012-d-fixture-account-isolation.md
oap/reports/012-d-fixture-account-isolation.md
```

No product, backend, schema, migration, API, Web, Playwright, Compose topology,
docs, dependency, lock, image, or prior OAP artifact may change.

Before fixture insertion, strengthen the existing fixed transaction precondition
to fail if **any** row exists in `control.user_account`, not merely a row with
one of the fixed UUIDs. Retain the uninitialized-installation, no-administrator,
no-membership, collision-safe INSERT, fixed OIDC values, and no-overwrite rules.

After E2E, strengthen the owner-side assertion to prove the complete account
inventory is exactly:

```text
2 ACTIVE OIDC fixture accounts:
  fixed expected IDs/issuer/subjects/display names
  NULL local username/normalized username/password hash/email
  no Platform Administrator assignment

1 ACTIVE LOCAL account:
  the setup-created account
  non-NULL local identity/password fields
  exactly the sole Platform Administrator assignment

total user_account rows = 3; no other identity/account row
```

Do not print IDs, usernames, hashes, or credentials. Preserve all membership,
restart, secret, recovery, and cleanup assertions. Extend the static packaging
test to require the any-user precondition and exact-total/classification query,
and to prevent regression to checking only the two fixed IDs.

## Verification and workflow

Target 8 minutes; hard stop 20 minutes. Run:

```text
sh -n tools/compose/smoke.sh
uv run --frozen ruff check tests/packaging/test_compose_smoke_contract.py
uv run --frozen ruff format --check tests/packaging/test_compose_smoke_contract.py
python -m unittest tests.packaging.test_compose_smoke_contract
git diff --check
```

Inspect the exact SQL/static-test diff. Do not run local Compose, Playwright,
Node, PostgreSQL, images, Mermaid, or SBOM. Push one implementation generation
after local green; inspect the one complete GitHub generation, including real
Compose. No second generation or workflow rerun. Report `PARTIAL` if any check
is not successful at the hard boundary.

Commit this order and `oap/active` byte-identically. Atomically publish exactly:

```text
oap/reports/012-d-fixture-account-isolation.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
the exact pre/postcondition changes, five local passes, PR/head/draft, all 20
checks, skips/hashes, and explicit no-new-PR/no-rerun/no-merge. Signal exact
FIFO `OK` only after report and claimed remote state exist.
