# PostgreSQL foundation integration

SLAIF Agent-Site adopts the non-yanked PyPI release
`agent-cow-postgresql==0.2.0` as its generic PostgreSQL copy-on-write
foundation. This document records the qualified dependency and bootstrap
boundary; the runnable
Agent-Site service itself (APIs, rendering, Compose stack) is documented by
the architecture and operations documents, and the current-limitation
reconciliation below is scoped to verified `main`
`d18b6e4c9423f61de99b516be90619bf2ab5d3e0` (2026-10-27, PR #111 accepted).

## Qualified release and artifacts

The locked distribution is installed from the public PyPI registry. Normal
development, CI, release, and deployment do not install it from Git, a direct
URL, a local path, or an editable checkout.

| Item | Qualified value |
| --- | --- |
| Distribution | `agent-cow-postgresql` |
| Version | `0.2.0` |
| Python declared by foundation | `>=3.10,<3.15` |
| Agent-Site Python range | `>=3.12,<3.15` |
| Downstream Python CI | 3.12, 3.13, 3.14 |
| Downstream PostgreSQL CI | 14, 15, 16, 17, 18 |
| License | MIT |
| Wheel | `agent_cow_postgresql-0.2.0-py3-none-any.whl` |
| Wheel SHA-256 | `c469d24700fabb93a58f464d3539a32e936097f93035a95f193062859546f5b1` |
| Source distribution | `agent_cow_postgresql-0.2.0.tar.gz` |
| Source SHA-256 | `eae8d434d2fc03c4faa08b44b4863fc8f8efb44ee33eaad3adc22e7eb96a062c` |

The separately qualified migration substrate is also registry-only and locked:

| Distribution | Version/license | Representative wheel SHA-256 | Source SHA-256 |
| --- | --- | --- | --- |
| Alembic | `1.19.1` / MIT | `b39018cb3d9413a19cbd54cf3c02ad33998641f0538eb77413a488a21c3e14be` | `e0fca0518118c78acc493e31bcb5402f190057aaf6df8b5b95ce94c4789cf648` |
| SQLAlchemy | `2.0.52` / MIT | `3b81b8363a919ce53453591cdb93702e6bd54ade6c4fa2f468fc053baee5ed89` | `5e2d46356ac2ccb7d268ab6c2319ac6a2b42f1b8d5fd8bd3d46855cd82abee97` |

The locked migration closure adds Greenlet `3.5.5` (MIT AND PSF-2.0),
Mako `1.4.1` (MIT), and MarkupSafe `3.0.3` (BSD-3-Clause). `uv.lock`
contains the exact hashes for every available artifact.

The base distribution declares no unconditional runtime dependencies. Its
SQLAlchemy extra declares SQLAlchemy and asyncpg; Agent-Site does not select
that extra. Agent-Site declares asyncpg directly for foundation/application
operations. Exact Alembic `1.19.1` and SQLAlchemy `2.0.52` are separately
approved only for metadata-free migration execution; they do not create an ORM
or a second application driver.

The package source and issue tracker are maintained at
[jpers1/agent-cow-postgresql](https://github.com/jpers1/agent-cow-postgresql).
It is a PostgreSQL-focused downstream of Trail's MIT-licensed
[agent-cow-python](https://github.com/trail-ml/agent-cow-python). Those links
are provenance and collaboration references, not build dependency sources.

## Public API boundary

Product code centralizes its qualified imports in
`slaif_agent_site.agent_state.foundation`. The module re-exports, without
wrapping, the following documented `agentcow.postgres` surface:

- setup and privilege controls: `deploy_cow_functions`, `enable_cow_schema`,
  `harden_cow_schema`, and `validate_cow_schema_privileges`;
- scoped driver integration: `asyncpg_cow_session` and
  `asyncpg_cow_reviewer`;
- operation and conflict inspection: `get_session_operations`,
  `get_operation_dependencies`, and `get_cow_conflicts`;
- typed session/reviewer surfaces and results: `CowSession`, `CowReviewer`,
  `PromotionResult`, `DiscardResult`, `CowConflict`, `CowConflictError`,
  `CowPostgresConfig`, and `CowPrivilegeValidation`.

Whole-session and selective promotion/discard are methods on the public
`CowReviewer` scope. The adapter does not change its transaction ownership or
the default fail-safe conflict policy. It contains no SQL, foundation storage
name, credential, product policy, or canonical-write compatibility option.
Product-specific authorization and safe invocation belong to later
Agent-State objectives.

## Semantic and authority boundaries

The foundation provides a logical live-base overlay. A workspace reads the
current canonical base plus the selected session's visible operations; it is
not a physical database branch or a snapshot copied at session creation. A
first-touch baseline supports conflict detection for modified rows and schema
state. Human review must still freeze an immutable product-owned review
snapshot before approval.

Ownership stays separated:

| Layer | Owns |
| --- | --- |
| Agent-Site | Sites, identities, content, composition, semantic APIs, rendering, browser/media behavior, and publication control. |
| Agent-State | Authorized site-bound workspaces, capabilities, operation/audit semantics, review snapshots, and safe promotion orchestration. |
| Foundation | Generic PostgreSQL overlay mechanics, operation ordering, conflict checks, promotion/discard primitives, and database privilege helpers. |

Foundation session and operation settings are context, not authentication.
Trusted application code must resolve an authenticated capability and select
the site, workspace/session UUID, and operation UUID. External agents must
never provide database credentials, reach `CowSession.native`, submit raw SQL,
or choose context that server code passes through unchecked.

### Review revision and first-touch baseline

A workspace records two different revision facts, and the review lifecycle
keeps them distinct:

- **Creation-time revision** — when a workspace is created, the current
  canonical site revision is recorded as the workspace's
  `base_site_revision`. It is provenance only; later site activity never
  overwrites it.
- **Review-time revision** — when the workspace is frozen, the trusted
  materializer locks the canonical site row in the same transaction that
  materializes the immutable snapshot (the workspace-then-site lock order
  the acceptance path shares, so a concurrent same-site publication
  serializes with the freeze) and the snapshot's `base_site_revision` is the
  revision captured in that locked read. A workspace created at revision A
  and frozen after an unrelated publication at revision B is reviewed
  against B, with coherent B-plus-overlay content and a byte-valid digest.

The first-touch COW baseline is the workspace's own conflict-detection
foundation, and freezing does not rebase or refresh it: touched rows keep
being compared against the original baseline, and a concurrent change to a
touched row still reports `BASE_ROW_CHANGED` at promotion. If another
workspace publishes after a freeze, the old snapshot remains unchanged and
viewable, and its acceptance is refused by the preflight gate with the
stable `SITE_REVISION_CHANGED` — the trusted stored revision is checked
against the locked current revision before digest re-validation, so the
stale-review reason is never obscured by re-materialized content. Increment
083/4 (migration `075_001`) delivers the freeze-time lock and preflight
ordering; the remaining complete-snapshot/render/operation/conflict closure
is tracked in `oap/MVP-CONTRACT-AUDIT.md`.

## Qualification gate

The reproducible local gate is:

```bash
uv --version
uv lock --check
uv sync --frozen --all-groups
uv run --frozen ruff check services/backend tests/repository tools migrations
uv run --frozen ruff format --check services/backend tests/repository tools migrations
uv run --frozen mypy
uv run --frozen pytest services/backend/tests/unit tests/repository
uv run --frozen pytest services/backend/tests/integration
uv build --out-dir /tmp/slaif-agent-site-distributions
python tools/check_repository.py
```

The unit gate checks installed metadata, Python compatibility, public imports,
the registry-only lock and exact hashes, adapter source, and wheel/sdist
contents and Apache-2.0 metadata. The generic integration gate retains its
disposable setup/runtime/reviewer test. A separate Agent-Site suite provisions
all exact roles and principals, migrates/rebuilds, reconciles foundation COW,
tests effective positive/negative privileges, injects failures/over-grants,
and proves cancellation/pool cleanup. CI runs both suites on PostgreSQL 14
through 18 and the quality/package gate on Python 3.12 through 3.14. Exact
execution evidence is preserved in the corresponding OAP report.

An upgrade must repeat the architecture qualification gate: verify non-yanked
PyPI metadata and license, regenerate `uv.lock` with the deliberately selected
version, audit both artifact hashes and dependencies, verify public API
compatibility, and pass every downstream Python/PostgreSQL/security/package
check. Dependabot output is a proposal, not qualification or acceptance.

### Recorded `0.2.0` local result

On 2026-08-17, exact uv `0.12.5` performed fresh frozen installs and the
unit/metadata/repository suite on CPython 3.12.3, 3.13.15, and 3.14.7. The
downstream integration suite passed independently against disposable
PostgreSQL 14, 15, 16, 17, and 18 instances. The product wheel and source
distribution contained only the backend package plus standard project/package
metadata, declared Apache-2.0, and retained the single exact production
foundation requirement. Final GitHub matrix and security-analysis results are
recorded in the immutable OAP execution report rather than inferred from this
local result.

## Public whole-session promotion qualification (083/8)

Increment 083/8 (in flight at `083-8-a`) configures, through the public
`agentcow.postgres` 0.2.0 API only, a qualification that asserts whether a
whole mixed-FK COW session can be committed after promotion has made
uncommitted effects, and rolled back completely when the terminal reviewer
window fails. The qualification is a GENERIC MECHANISM PROOF on an owned
disposable cluster: it does not qualify the actual public Agent/Editor/Media
HTTP surface, the freeze/accept worker, or the audit/revision/outbox product
families. Actual executed results and source IDs are recorded in the formal
OAP report, not declared here before execution.

- The fixture mirrors actual product table geometry (single-UUID primary
  keys with composite site-scoped UNIQUE constraints; DEFERRABLE INITIALLY
  IMMEDIATE composite FKs; composite UUID+TEXT and UUID+UUID references,
  including self-references) from migrations 016/020/021/022/023/040/042,
  and creates its own disposable database so the fixture setup role is the
  sole agentcow deployer there.
- P2 is configured to commit two whole deferred-FK sessions over
  representative model/field/item/translation/relation/page/composition/
  navigation/media families, asserting canonical absence and unchanged-seed
  oracles for every pending insert before approval, in-scope
  `operations()` inspection while still inside the reviewer body, and fresh
  post-scope inspections.
- P3 asserts empty-session no-op, same-value coalescence, repeated-write
  last-value, and insert/delete net-zero behavior. P4 asserts row-conflict
  refusal preserving pending state and the required genuine schema-conflict
  refusal (the physical base and the COW base diverge). P5 asserts the
  deferred physical two-table cycle commits, the non-deferred cycle is
  refused before promotion, dangling deferred states are refused at the
  SET-CONSTRAINTS-IMMEDIATE stage inside `commit_session`, and the
  write-time fail-closed refusal (SQLSTATE 22023) is distinct from
  promotion-time refusal. P6 asserts the terminal window: promotion effects
  exist in-transaction and are not committed from an independent
  connection; an escaped postcondition refusal, an actual task cancellation
  (positive `CancelledError`/`task.cancelled()` assertion), and a backend
  termination each roll the promotion back with no leaked transaction,
  locks, or nonempty stale COW context (frozen 0.2.0 semantics treat NULL
  and `''` as clean).
- CI is configured to run the module as the fourth exact pytest command of
  the Python integration job group B (the existing three commands, 45
  tests: component 24 + theme 9 + page-style 12, remain unchanged; group A
  85 unchanged) on PostgreSQL 14 through 18; actual per-version Q counts
  are reported evidence.
- P7 (composite-FK `dependencies()` characterization) is a separate
  scratch-only diagnostic outside this module and the CI selection: the
  whole-session commit path does not call the dependencies SQL, and the
  module keeps `dependencies()` out of pass/fail assertions. Its I_f
  scratch returned normally with four known pending operations and three
  relation pairs in the public `(depends_on, operation_id)` direction
  (`core.py` lines 1428..1440, `operations.py` lines 575..584); the
  printed `reversed_present=True` is a scratch artifact because its own
  expected-pairs block used the opposite convention, not an API reversal
  or a failed qualification, and no promotion or full-graph proof
  occurred in that diagnostic. The frozen 0.2.0 changes-table primary
  key is `(session_id, operation_id, ORIGINAL_PK...)`, so
  `ordinal_position >= 3` removes the two internal bookkeeping prefixes
  rather than skipping any original 1-2 column primary-key table, and
  the dirty-changes enumeration returns changes-table names. The
  composite-FK per-column/single-column UNION edge concern
  (`cow_sql_functions.py` lines 1745..1800) remains a bounded source
  lead, not an observed UUID/TEXT exception or a general graph verdict
  from P7. The I_f fixture has composite `(site_id, id)` foreign keys; a
  single UUID primary key is not a single-column foreign key. The
  executed scratch, orders, and reports are preserved unchanged.

Citation erratum: the order parenthetical "asyncpg.py478" cites the public
`asyncpg_cow_reviewer` manager, which actually lives at `safe_promotion.py`
line 478 in the frozen 0.2.0 wheel; the named public API is unchanged.
`CowPromotionRequestError` is intentionally NOT part of the product
re-export boundary in `slaif_agent_site.agent_state.foundation`.

## Current limitations

This section predates the domain schema, online connections, freeze/review,
human-approved publication path, and Compose packaging that exist at the
current verified `main` `d18b6e4c9423f61de99b516be90619bf2ab5d3e0` (their
source history spans increments both earlier than and later than
083/1-083/7; no per-increment attribution is claimed here); the residual
limitations below are what still apply at that revision. The foundation cannot harden an empty
COW schema; Agent-Site therefore publishes `EMPTY_SAFE` only after a separate
zero-object and zero-authority proof, while explicitly leaving foundation
hardening/validation false and not applicable. Any content object requires
the normal public foundation hardening path and `HARDENED`; see
[database bootstrap](DATABASE_BOOTSTRAP.md). Capability authorization and the
bounded Agent create/idempotency path use the foundation session API. Still
open at this revision: publication promotes canonical content only after
human approval through the existing narrow path, and its full product
safety closure remains unfinished (preview remains observational and does
not substitute for it); the missing immutable reviewed-U, complete product
semantic audit, and true closure with noPending/durable history and
re-review are product acceptance gaps tracked in
`oap/MVP-CONTRACT-AUDIT.md`; and the conservative-full-U generic operation
state remains UNAPPROVED (public operation inspection exists; pending-U is
not an unimplemented generic foundation state). Increment 083/8
additionally configures the generic whole-session promotion/rollback
mechanism qualification only; it does not close any of the product-surface
gaps above. Tests use only disposable fake credentials and
databases.
