# Strategic review: Objective 078/2 theme increment

Audited source: PR79 head `e89ff37ee3debc69d9c780d746ec4b098ceb4318`, report-only
SELF child of `b89ef7bce4026db8377c782e2c6bfa13ce5cc8c1`. Verified main/base
`3cae3d6cef2a92e7068856d21bc9a47b8190c22e`; branch
`oap/078-2-site-theme-tokens`. Verdict: REJECT current completion claim; repair
the finite findings below. No new theme/global feature scope is authorized.

## Independently confirmed findings

### D1: trusted SQL accepts invalid null-valued tokens

Migration065 `_validate_sql` uses `->> NOT IN (...)` without explicit scalar
non-null checks. SQL three-valued logic bypasses the IF for JSON null. Strategic
real-PostgreSQL probe called `content.slaif_agent_theme_update` as
`slaif_agent_runtime` with palette `{"preset":null}`: returned palette null,
version2, then independent workspace read confirmed it persisted. Public
Pydantic rejection does not repair this trusted-boundary violation.

### D2: read-authorized no-effect contract not implemented

Strategic public-HTTP/real-PostgreSQL probe used `theme:read` without write and
PATCHed unchanged default ocean at expected version1: returned403, not ordered
200/no effect. `agent_http.update_theme`, route policy and migration065 all
require `theme-tokens:write` before change classification. The order explicitly
requires changed-value authority and exact conditional OpenAPI metadata.

### D3: shared helper regression and non-exact downgrade

Migration065 reconstructs `slaif_agent_resource_constraints` but drops existing
060 validation, including bounded arrays, typed array elements, route-prefix
and delete-enabled type checks. Its downgrade substitutes another abbreviated
helper without the original lifecycle/expiry/site/user and validation checks.
The legacy theme wrapper restoration is also hand-rewritten, not exact metadata/
definition restoration. The claimed round-trip test checks only data values;
it neither snapshots nor compares prior function definitions, owners, ACLs or
volatility. New theme support must not weaken unrelated trusted resource policy.

### D4: theme-specific hostile/concurrency evidence is missing

Only three theme integration tests were added. The race uses `asyncio.gather`
without a deterministic database barrier or proof that both transactions contend.
No theme-specific direct-runtime invalid mutation matrix, cancellation/rollback,
first-materialization versus existing-row race, or the complete ordered negative
authority/lifecycle/quota/isolation matrix exists. The read-purity test's bare
`SELECT count(*)` has no FROM and is always1, so it cannot prove no theme row was
created. General pre-existing integration totals do not prove these new paths.
CI still selects `-k component`, so these theme DB tests are not matrix-wired.

### V1: global theme overrides accepted component-local semantics

Independent Chromium rendering using the production stylesheet confirmed:
theme grid gap lg overrides explicit local gap none at desktop and mobile-sm
at mobile: both compute24px instead of0px/8px. A meadow-themed ghost Button
computes solid green background instead of transparent. Theme selectors have
higher specificity than existing local/responsive selectors. Repair precedence,
default/reset behavior and accessible palette/variant contrast; test actual
computed styles and preserve the accepted PR77 semantics.

### V2: public Agent theme-to-same-workspace preview proof absent

The new public Agent acceptance only PATCHes/replays/reads theme. The new
computed-style browser test changes a separate HUMAN workspace through Editor.
Together they do not prove an Agent theme mutation visibly renders in that
same Agent workspace. Connect the actual issued capability's workspace to the
existing authorized preview/browser path, without implementing Objective081's
exact-Agent-workspace Puck feature or owner-seeding the expected outcome.

## Actually executed CI failures

Final report-head run34367041990 has18success/2failure:

- PostgreSQL15 job102518332029:
  `test_agent_component_concurrent_creates_before_anchor_are_serialized` fails
  with `expected 2 structural lock waiters, got 1`. The helper uses a fixed
  500-iteration unscoped pg_locks poll; diagnose actual readiness/lock graph,
  never reduce expected contention or hide the test.
- Compose job102518331881: desktop-firefox
  `responsive-admin-keyboard-read-states-and-logout` fails at browser-response,
  auth.spec.ts line79. Preserve response-failure evidence and diagnose the
  concrete request before any minimal repair. No browser/gate skip or broad
  suppression. Other device projects and new theme browser scenario passed.

## Control and scope decision

This is not the former no-production-work executor pathology: substantial theme
implementation exists. The concrete control failure is evidence overclaiming
and reuse of the old deferred patch without satisfying changed 078-p criteria.
Future reports must map each claimed criterion to actual named theme assertions;
generic suite counts and schema existence are not negative/runtime proof.
Keep original078-p report immutable and publish corrections prospectively.

078-q owns D1–D4 trusted theme boundary/migration/proof and the PostgreSQL race
failure. V1–V2 and concrete Firefox closure are reserved for the following
bounded rendering/evidence round, not further feature scope. Do not merge until
all findings and current-head gates close. PR size55files,+5044/-590 includes
generated OpenAPI and tests; no global regions/page-style/catalog expansion may
accumulate in this increment. Existing coding agent only.
