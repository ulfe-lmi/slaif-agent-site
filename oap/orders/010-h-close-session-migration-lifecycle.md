# OAP Work Order — 010-h

## Objective

Amend PR `#15` to close the single remaining `010_001` migration-lifecycle
defect, then obtain successful local and PostgreSQL 14–18 execution of the
complete human-session proof. Add the missing revoke-function downgrade and no
new behavior.

## GitHub objective state

- Numeric objective: `010`
- Execution round: `010-h`
- PR mode: `AMEND_EXISTING_PR`
- Existing PR: `#15`
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/15>
- Required branch: `oap/010-installation-local-auth`
- Base branch/current main: `main` /
  `c37da1e26ee7dad38545511ca7c2e07c63adcff9`
- Required starting PR/report head:
  `4d05eb07f7984b5d538833e003af630a018c5b91`
- `010-g` implementation head:
  `e133a090b7271983679ce5369f9c4155bdb2c89a`
- Required title:
  `[OAP 010] Establish secure installation and local authentication`

PR `#15` is the unique objective PR. No new PR, rebase, force-push, merge,
close, auto-merge, or unrelated action.

## Verified defect and bounded scope

Revision `010_001` creates five Control-only session functions, including:

```text
control.slaif_revoke_human_session(text, bytea, bytea)
```

Its current `downgrade()` drops the inspect, two finalize, and create functions
but omits the revoke function before dropping `control.user_session`. Rebuild
therefore leaves the function behind and upgrade fails with
`DuplicateFunctionError`. GitHub run `32398206626` independently reproduces
this on PostgreSQL 14–18. The session test is now present in every matrix job
but cannot execute past rebuild. Compose recovery at `010_001` is already
green and must remain unchanged.

Manual implementation changes are limited to:

```text
services/backend/src/slaif_agent_site/db/alembic/versions/010_001_human_session.py
services/backend/tests/unit/test_foundation_contract.py
services/backend/tests/integration/test_database_bootstrap.py  # only if exact lifecycle assertion is needed
oap/active
oap/orders/010-h-close-session-migration-lifecycle.md
oap/reports/010-h-close-session-migration-lifecycle.md
```

Do not edit session runtime semantics, integration fixtures, CI workflow,
Compose tooling, docs, dependencies, routes, UI, or any adjacent feature unless
an executable post-fix result exposes a directly related lifecycle assertion
that cannot be corrected inside the paths above. Report any such blocker
instead of expanding scope.

## Hard execution budget

- Target: 20 minutes; hard stop: 35 minutes.
- Fresh bootstrap/rebuild plus focused session PostgreSQL invocations: 2 max.
- Implementation commits/check generations: 1 before report.
- Workflow reruns: 0.
- Local Compose, supply-chain/image, Node, browser, broad matrices: 0.

## Requirements

1. Drop `control.slaif_revoke_human_session(text, bytea, bytea)` in deterministic
   dependency-safe downgrade order before dropping `control.user_session`.
2. Keep all five create/owner/revoke/grant inventories exact and keep downgrade
   symmetrical. Add/retain a static regression that would fail if any created
   function lacks its exact drop.
3. Run a fresh upgrade→downgrade/rebuild→upgrade lifecycle and prove no stale
   function/relation/grant remains and privilege validation is safe.
4. Run the complete corrected `test_human_session.py` and require it to reach
   and pass every safe/state-changing/CSRF/substitution/expiry/recent-auth/
   touch/race/cancellation/role assertion from `010-g`.
5. Preserve the inspect → application constant-time compare → finalizer/revoke
   transaction order, current PostgreSQL matrix wiring, Compose `010_001`
   recovery, all prior artifacts, and absence of HTTP/UI/adjacent features.
6. Push one implementation generation and require every one of the 20 checks
   on the report head to succeed with no rerun.

## Verification required

Prepare the one-line lifecycle fix and static assertion before using the DB
attempt. Run affected Ruff/format/mypy/compile/static/unit/repository checks,
then at most two invocations covering fresh bootstrap lifecycle plus
`test_human_session.py`. Run explicit changed-doc lint only if a Markdown file
changes, exact path/prior hashes, no conflict markers, and `git diff --check`.

Do not run local Compose, full matrix, supply-chain/image, Node, or browser.
GitHub executes the already-updated PostgreSQL 14–18 session proof and the
unchanged full 20-check gate once. No rerun.

## Safety, workflow, and report

Use disposable PostgreSQL and fake data only; expose no secret/digest/password/
cookie/DSN/private URL. Preserve governance, architectures, OAP history,
setup/identity/session role separation, and all earlier tests.

Amend only the existing branch with one implementation commit, then atomically
publish exactly:

```text
oap/reports/010-h-close-session-migration-lifecycle.md
```

The final report-only `SELF` commit must parent the literal implementation
head. Report exact migration diff; create/drop symmetry; successful lifecycle
and complete session result; all five matrix jobs and 20 report-head checks;
attempt count; paths/hashes/skips; no-rerun/no-new-PR/no-merge state; and
`Report publication commit: SELF`.
