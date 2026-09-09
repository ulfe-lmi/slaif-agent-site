# OAP Execution Report — 078-f

## Identity and delivery

- Order: `078-f-prove-public-component-render-loop`
- Objective: `078`; round: `078-f`; mode: `AMEND_EXISTING_PR`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77), open, not merged
- Base: `main`
- Head branch: `oap/078-agent-composition-design-semantics`
- Starting remote head: `cf466626f9fdd5e940beed3567dca7aed2437edd`
- Implementation commit: `d8a292f7c7ebb8bc7bc42af84e4f36b8502be810`
- Implementation parent: `cf466626f9fdd5e940beed3567dca7aed2437edd`
- Report publication commit: `SELF`
- Pushed implementation commits: `d8a292f7c7ebb8bc7bc42af84e4f36b8502be810`
- Result: `COMPLETE` for this bounded continuation; Objective 078 remains open

## Exact bounded changes

- Extended `tools/compose/public_agent_acceptance.py` with the existing public
  NGINX component proof: human-issued L2 workspace/capability,
  exact OpenAPI/session/permissions/catalog reads, empty initial composition,
  nested `Section -> Container -> Heading` plus `RichText`, exact node GETs,
  content-only Heading PATCH, semantic before/after moves, dense ordering and
  positive versions, private four-artifact browser evidence, and Agent/
  Render/Web restart persistence.
- Added dependency-safe leaf/parent deletion, delete replay, canonical and
  observer isolation, lower-scope structure negatives, design-scope denial,
  foreign site/workspace/page/node/parent/sibling denial, stale/schema/raw
  order/idempotency negatives, mutation/delete/resource quota proofs, and
  durable audit/idempotency unchanged-state assertions.
- Classified component PATCH/move/DELETE actions in the existing semantic audit
  expectation helper, including request-digest defaults.
- Updated `tools/compose/smoke.sh` artifact baseline for the four additional
  component browser artifacts: 12 retained files / 6 retained artifacts,
  with the existing later `+12` runtime invariant preserved.
- Updated `docs/API.md`, `docs/TESTING.md`, `README.md`,
  `oap/MVP-PROGRESS.md`, and `oap/MVP-CONTRACT-AUDIT.md` to describe only the
  proven bounded component slice and preserve the open-PR/partial-MVP claims.
- Committed the exact immutable order and `oap/active` value `078-f`; no
  historical order or report was edited.

## Public workflow evidence

The final fresh clean run was:

```text
tools/compose/smoke.sh slaif071f20260908f
```

Terminal proof included:

```text
compose-e2e: OK projects=11 setup=1 governance=1 preview=1 stable-devices=6 agent-sessions=2 artifacts=disabled
public-agent-news-edge: OK workspace=0d6188af-6cfa-4ab0-b076-4200e4bebc3c routes=default,non-default detail=exact listing-sort=verified status-slug-translation=verified canonical-isolation=byte-identical restart=agent,render,web html=uuid-token-flight-free css=canonical-parity browser-artifacts=public-verified-retained authorization=one-use
public-agent-component-loop: OK workspace=753929f7-2020-43e3-a530-7006369565e9 page=2b8a4503-626a-4d5b-a6b1-f42033255764 tree=Section>Container>(RichText,Heading) initial=empty update=content-only move=before,after preview=human-nginx-html browser=real-private-4-artifacts restart=agent,render,web state=ids-props-hierarchy-order-versions delete=leaves-parents-replay-safe negatives=scope-design-foreign-stale-schema-idempotency quotas=mutation-delete resource=bounded canonical=unchanged observer=unchanged
public-agent-acceptance: OK workspace=24c7417e-c760-4bdc-8a9f-8ff5cdc8a8e5 types=2 fields=3 items=2 translations=1 relations=1 views=1 pages=1 components=1 locales=1 redirects=1 navigations=1 navigation-items=3 openapi=exact restart=verified nginx-outage=verified crud=public quotas=mutation-429,max-delete-429 dependency-delete=422 page-delete-restore=verified canonical-independence=verified render-restart=verified
public-agent-restart: OK workspace=743dd465-c1bc-491c-89cb-7f647f7fc74d capability=b704e15320b2431d agent-before=200 agent-after-restart=200 agent-after-revoke=401
browser-artifact-root-policy: OK retained-files=12 retained-artifacts=6 mode=0600 owner=10001
browser-artifact-runtime-policy: OK files=24 retained=12 new=12 mode=0600 links=1 credentials=absent
control-readiness-fixture: OK mount=isolated identity=exact failures=6 recovery=clean
compose-smoke: OK
```

The fresh project used isolated Compose volumes and was cleaned by the smoke
trap. Only NGINX was used as the public HTTP boundary. Owner SQL was limited to
neutral fixture setup and post-request audit/isolation inspection; component
mutations were performed through public Agent HTTP.

The human control flow issued the bounded L2 capability in memory. The proof
never printed or persisted capability, session, browser, worker, or service
credentials. Public HTML and browser artifact bytes contained no workspace,
site, page, component UUID, capability, preview credential, internal URL,
projection JSON, Next flight data, console error, or failed-request entry.

## Acceptance criteria and evidence

- Canonical OpenAPI bytes, session, permissions, catalog-v1, and initial empty
  page composition were fetched through the capability/public boundary.
- The nested Section/Container/Heading/RichText tree was created with semantic
  anchors only. Individual GETs matched the exact listed records.
- Heading content was updated through the L1-compatible content-prop scope;
  RichText was moved before Heading and Heading was moved through an after
  anchor. Sibling order was dense and versions were positive and exact.
- Authenticated human preview through public NGINX/Web rendered updated text,
  nested component markers, safe output, and no canonical route leakage.
- The normal Agent preview run reached the real browser worker and returned
  four private JSON artifacts: exact heading and structure evidence plus empty
  console and failed-request evidence. Same-key replay returned the same run.
- Agent API, Render API, and Web were restarted independently. Public Agent
  records and preview HTML retained IDs, props, hierarchy, order, versions, and
  rendered meaning after every restart.
- Leaves were deleted before parents. Reads/listing returned 404/absence,
  preview removed the components, and a replayed delete caused no second
  effect. Audit, idempotency, and COW operation expectations were exact.
- Lower-scope structure writes, design props, foreign substitutions, stale
  versions, invalid slot/type/nested schema/raw order, dependency deletion,
  idempotency mismatch, exhausted mutation/delete quotas, and the component
  resource budget failed with stable public errors and unchanged durable state.
- Canonical rendering, another workspace on the same site, another site, and
  site records remained unchanged before and after mutation, restart, and
  deletion. Revoked component capability writes returned 401.

## Verification

Local focused and repository checks:

- `python -m unittest discover -s tests/repository -p 'test_*.py'`: 58 passed
  (and the final full unit/repository gate: 531 passed).
- `python -m compileall -q tools tests/repository`, `sh -n
  tools/compose/smoke.sh`, `git diff --check`: passed.
- `python tools/check_repository.py`: `PASS repository policy`.
- `python tools/check_mermaid.py`: 16 diagrams in 3 files passed.
- `npx --yes markdownlint-cli2@0.23.2 "**/*.md"`: 0 issues in 422 files.
- Python gate: `uv lock --check`, frozen all-group sync, Ruff check/format,
  mypy, unit/repository pytest, integration pytest, and `uv build` passed;
  integration result was `195 passed in 1854.42s (0:30:54)`, and the unit/
  repository result was `531 passed` with one existing Starlette deprecation
  warning.
- Node gate: Node `v24.14.1`, pnpm `11.22.0`; frozen install, lint,
  format:check, typecheck, test, build, and license inventory passed.
- Final clean Compose smoke: `compose-smoke: OK`; the terminal summary above
  is the exact captured proof. The smoke wrapper does not emit a duration.

## GitHub authoritative state

At final inspection, PR #77 was `OPEN`, `isDraft=false`, `mergeStateStatus=CLEAN`,
and `headRefOid=d8a292f7c7ebb8bc7bc42af84e4f36b8502be810`. Current-head checks:

| Check | State |
| --- | --- |
| Repository policy | pass |
| Node contracts | pass |
| Python 3.12 quality and package | pass |
| Python 3.13 quality and package | pass |
| Python 3.14 quality and package | pass |
| Foundation PostgreSQL 14 | pass |
| Foundation PostgreSQL 15 | pass |
| Foundation PostgreSQL 16 | pass |
| Foundation PostgreSQL 17 | pass |
| Foundation PostgreSQL 18 | pass |
| Compose and edge packaging | pass |
| Supply-chain evidence | pass |
| Markdown | pass |
| Mermaid | pass |
| Dependency review | pass |
| CodeQL | pass |
| Detect supported languages | pass |
| Analyze (actions) | pass |
| Analyze (javascript-typescript) | pass |
| Analyze (python) | pass |

No required check was pending, skipped, failed, cancelled, or missing at final
inspection.

## Scope, safety, and remaining work

- No production component implementation, schema, dependency, architecture,
  security policy, acceptance criterion, historical artifact, or merge state
  was broadened or weakened.
- No extra PR was created. PR #77 was not merged or auto-merged.
- The bounded 078-f component data plane is proven at this source revision;
  Objective 078 remains partial because design/theme/global-region expansion,
  exact Agent-workspace Puck editing, media semantics, MCP, freeze/review,
  promotion/publication, reconstruction, cleanup, backup/restore, and final
  MVP evidence remain outside this order.
- Objective 070 is not implicated by this order. Objective 078/PR #77 may be
  declared complete for this round only when the strategic authority accepts
  this report and independently decides the open PR is ready for merge; the
  coding agent does not merge it.
