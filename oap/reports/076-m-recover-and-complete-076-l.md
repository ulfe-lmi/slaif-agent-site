# OAP Report — 076-m execution-control recovery

ID: 076-m  
Order: `oap/orders/076-m-recover-and-complete-076-l.md`  
Result: COMPLETE FOR THE 076-L SUBSTANTIVE SLICE  
Delivery: HUMAN-AUTHORIZED_STRATEGIC_AMENDMENT_OF_EXISTING_PR

Repository: `ulfe-lmi/slaif-agent-site`  
PR: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72) (OPEN)  
Base: `main` (`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`)  
Branch: `oap/076-agent-model-content-semantics`  
Starting report head: `65027b93fa8e3931bf3f3a4641d336cfaeea5bea`  
Implementation head SHA: `9127cd33bb1791fcd78a877cc39992b8e079ee5e`  
Report publication commit: SELF

## Execution-control diagnosis and authority

The human explicitly authorized the strategic model to implement this bounded
recovery directly and instructed that no agent be run without separate
approval. No coding agent was launched, queued, resumed, or signaled for this
implementation; there were zero FIFO readers throughout the implementation.

The accessible 076-l Codex transcript proves the failed turn used
`gpt-5.6-luna` at high reasoning despite the coding constitution requiring Sol/
xhigh. Its last request used about 277K of a 475K context window, so exhaustion
was not the cause. After reading `oap/active` and the order, it committed the
transcript, authored PARTIAL, pushed, and signaled without inspecting source,
running Git/DB/tool diagnostics, editing production code, or running a test.
No external blocker was reported. Later automatic resumes created two
simultaneous control-FIFO readers in the same session. Strategic diagnostics
proved the branch/head, shell, full filesystem authority, passwordless sudo,
uv 0.12.5, PostgreSQL 16 client/server and port 5432 were healthy. The cause was
therefore a model/session execution-control pathology plus premature voluntary
termination, not the work-order scope or a technical PostgreSQL blocker.

## Production implementation

- Revision `044_001_agent_resource_constraints.py` now replaces only
  `content.slaif_agent_content_type_create(uuid,text,jsonb,text,jsonb)` while
  preserving its exact signature, row shape, `SECURITY DEFINER` owner boundary,
  fixed search path, trusted COW/site check, unchecked semantic delegate, and
  Agent runtime grant.
- The replacement reads constraints only through the owner-only typed helper,
  denies keys outside a nonempty `allowed_type_keys`, and enforces non-NULL
  `max_content_types` against ACTIVE types visible through the current COW
  overlay.
- Count plus insert is serialized with
  `pg_advisory_xact_lock(hashtextextended(workspace_id ||
  '_content_type_create', 994))`, where workspace ID comes only from trusted
  `app.session_id` after validation.
- PUBLIC and every non-Agent product role are revoked from the replacement;
  only `slaif_agent_runtime` receives EXECUTE. Runtime still cannot execute the
  resource helper or read protected base/change/control state.
- 044 downgrade restores the exact pre-044 guarded wrapper behavior and grant,
  then removes the helper. Upgrade→downgrade→upgrade was executed in the real
  integration test.

## Executable proof

The focused PostgreSQL test uses the existing fully migrated product-role/COW
fixture and proves:

- direct runtime allowed-key success and disallowed-key denial;
- exact sequential maximum;
- two distinct runtime connections/operations racing one remaining slot yield
  exactly one commit and one stable DB denial;
- losing attempts leave no additional COW reviewer operation;
- two concurrent Agent HTTP requests yield exactly one 201 and one 409/429,
  one visible type, one durable idempotency row, and one semantic audit row;
- other workspaces cannot see the mutations and canonical base remains
  unchanged;
- runtime cannot execute the helper; and
- downgrade restores the original wrapper/grant and removes the helper, while
  re-upgrade restores enforcement and helper isolation.

Verification history:

- Initial focused run: failed before PostgreSQL because SQLAlchemy interpreted
  a colon-bearing lock namespace as a bind parameter; fixed with a colon-free
  fixed namespace.
- Second focused run: failed because asyncpg rejects combined `REVOKE; GRANT`
  prepared statements; split into separate Alembic operations.
- Third focused run: all production/race/isolation behavior passed; the test's
  PUBLIC ACL assertion incorrectly treated PUBLIC as a role name; replaced by
  the repository-standard `aclexplode(... grantee=0)` proof.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -k content_type_create_resource_limits_are_db_serialized -q`
  — `1 passed, 5 deselected in 7.89s` after the residue assertions were added.
- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -q`
  — `6 passed in 39.92s`.
- Ruff check — passed; Ruff format check — passed.
- `uv run --frozen mypy` — passed, 241 source files.
- `python tools/check_repository.py` — `PASS repository policy`.
- `git diff --check` — passed.

## GitHub and scope

At implementation publication, PR #72 was open, mergeable, and UNSTABLE only
because all 16 newly triggered CI/CodeQL checks were queued; none was claimed
successful. No check was rerun. No type update/delete, field wrapper, audit/
quota coupling, OpenAPI/API shape, other entity, dependency, CI workflow,
architecture, prior transcript, production system, or release claim changed.
No second PR, merge, agent process, FIFO signal, real secret, capability,
cookie, or production credential was used. Objective 076 remains open beyond
this completed recovery slice.

Report publication commit: SELF
