# OAP Work Order — 077-f

## Objective and verified PR state

Repair one concrete 077-e regression in bootstrap downgrade atomicity. Amend
only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), branch
`oap/077-agent-site-structure-semantics`, base `main`; no new PR and no merge.
Required starting remote report head:
`502f8856c3f40d96c5084086a4bb91a4490c74a3`, whose sole parent is 077-e
implementation `c56d535f312b724639a83078eb243c1a1747eed5`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

Preserve all valid 077-a through 077-e work. This is not navigation/redirect/
locale/Render expansion and not a general bootstrap redesign.

## Exact defect

`bootstrap.service.downgrade` now commits the public
`agentcow.postgres.disable_cow_schema` transaction before invoking Alembic.
Migration 049 performs its `route_template`/`deleted_at`/`PAGE_*` audit
compatibility preflight only afterward. Therefore a normal product-bootstrap
downgrade of a database containing 049-only page state can:

1. successfully disable the entire content COW schema;
2. enter migration 049 downgrade;
3. fail with `049_DOWNGRADE_PAGE_DATA_PRESENT`; and
4. leave the current installation at revision 049 but with COW disabled and
   runtime hardening/readiness no longer intact.

The 077-e report's direct-migration test does not prove the product bootstrap
failure path and its claim that incompatible data refusal leaves hardening
usable is therefore incomplete.

## Required repair and evidence

- Before any public COW disable call or other mutation, the product bootstrap
  downgrade path must inspect the current migration state and run the exact
  known 049 compatibility preflight through public application relations:
  active/pending workspace operations, non-null page route templates,
  tombstones, and PAGE semantic-audit rows. If incompatible, return one stable
  operator-facing `BootstrapStateError` and change nothing.
- Keep migration 049's own defensive preflight for direct Alembic invocation.
  Do not restore private foundation relation/function names or bypass the
  public `disable_cow_schema` path.
- For a compatible database, bootstrap may transactionally call the public
  foundation disable API and proceed through the existing Alembic downgrade.
  Preserve expected owner/role/privilege behavior and the tested 048→049
  re-upgrade path.
- Handle a failure between public disable and successful migration completion
  explicitly. At minimum, known validation/preflight failures must occur before
  disable. For later Alembic/tool failure, either safely restore/reconcile COW
  hardening or fail readiness with a precise documented operator recovery; do
  not claim atomic rollback where separate committed transactions make it
  impossible. Never silently leave long-running runtime services ready against
  an unprotected content schema.

Add a focused real-PostgreSQL product-bootstrap test that creates each 049-only
state class and calls the actual `downgrade(settings)` entry point. For every
denial, assert before/after equality of Alembic revision, COW enabled state,
privilege/hardening validation, content/audit data, functions, workspace
operations and readiness marker. Instrument or monkeypatch the public disable
call to prove it was not invoked. Then prove a compatible database uses the
public disable path, downgrades, re-upgrades, reconciles/hardens, and preserves
compatible data.

Run focused bootstrap/migration/privilege tests, complete integration and
repository/unit regressions, Python quality, PG14–18, Markdown/Mermaid, Node,
and clean Compose only if the bootstrap path affects its acceptance. Inspect
all required current-head CI. Preserve Chrome `152.0.7977.82`, the empty
vulnerability-exception set, and existing supply-chain policy.

## Non-goals and report

No page API/route behavior beyond this downgrade safety repair; no Agent locale
CRUD, navigation, redirect, dynamic Render, composition/design/media/MCP/
review/promotion/source/sweep or 078+ behavior. No dependency/image/exception/
architecture/historical artifact/general refactor/issue closure/production
access. Do not reopen 076.

Verify/update only PR #74 and its branch. Commit this exact order and
`oap/active` unchanged with the bounded repair/tests/docs, push, create no PR,
never merge or enable auto-merge, and repair only in-scope CI failures.

Publish exactly
`oap/reports/077-f-make-page-downgrade-preflight-atomic.md` as a final
report-only child of the literal implementation SHA with `Report publication
commit: SELF`. Include exact commit/files; before/after failure-state evidence;
proof public disable was not called on incompatible state; compatible public
disable/downgrade/re-upgrade proof; readiness/privilege behavior; exact tests/
checks/skips; no private foundation dependency/scope drift/new PR/merge/
exception/secret confirmation; and remaining Objective 077 scope.

`PARTIAL`/`BLOCKED` requires a concrete external/technical blocker with exact
attempted evidence. Do not return early because tests or CI are long. No
post-report push. Signal exact FIFO `OK`, then wait for strategic review.
