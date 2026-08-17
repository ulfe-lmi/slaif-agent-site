# PostgreSQL foundation integration

SLAIF Agent-Site adopts the non-yanked PyPI release
`agent-cow-postgresql==0.2.0` as its generic PostgreSQL copy-on-write
foundation. This document records the qualified dependency and bootstrap
boundary; it does not describe a runnable Agent-Site service.

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

## Current limitations

The product schema/role/bootstrap baseline now exists, but it contains no
domain table and no online connection. The foundation cannot harden an empty
COW schema, so the clean marker remains deliberately unsafe; see
[database bootstrap](DATABASE_BOOTSTRAP.md). Capability authorization,
immutable review snapshots, product concurrency policy, publication, Compose
packaging, and public APIs remain unimplemented. Tests use only disposable fake
credentials and databases.
