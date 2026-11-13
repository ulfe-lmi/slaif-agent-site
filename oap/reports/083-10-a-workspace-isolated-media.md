# OAP Coding-Agent Report — 083-10-a

## Work order

- Identifier: 083-10-a; work-order file `oap/orders/083-10-a-workspace-isolated-media.md`; numeric objective 083, increment 10 (round a)
- PR mode: CREATED_NEW_PR

## Status

COMPLETE (all 30 required check runs on implementation head 65e0f162f7762c911fc116a58e64b31be3ed95b0 SUCCESS as observed, terminal 10:34:14Z: 20 named/app + 10 actual PG children, no failed/missing/pending; full 19-project public-NGINX Compose PASS including media-publication and the six stable pairings plus the full smoke; fresh six images Crit 0 / ignored 0 / exceptions 0; CodeQL success. Report published atomically at the SELF commit whose first parent is the literal implementation SHA; the report-only SELF push may trigger fresh CI, truthfully pending at wire time. No merge or product acceptance is claimed; strategy alone reviews/merges.)

## Executive summary

Implements workspace-isolated media (platform migration 077): the existing
COW-enabled media asset tables are re-routed — the existing online human/
agent registration and metadata/reference functions now write the
workspace-owned content COW view with trusted server-owned
site/workspace/operation context, and publication-derived metadata/public-
status mutation moved into the actual reviewer transaction with foundation
promotion, site revision, promotion audit, workspace/job success and cache
outbox. Acceptance publishes exactly the reviewed referenced media closure
(page composition media references plus typed media/document field
references in all supported base/localized scalar and list modes, compared
as UUID identity), promotes unreferenced assets as canonical PRIVATE, and
leaves already-public digests with their prior authorization; unreferenced
pre-copied orphans are unserved and no physical byte-GC is claimed. The ten
SELECTED media regression modules (four new module files plus six existing
modules with corrected oracles) are wired unfiltered into foundation CI
Group B for every PG14..18 child (45+Q+M, 66 M cases per child) with the
matching repository CI oracle and a bounded 30-minute Group B child budget
(Group A and all other timeouts unchanged). The E2E media-publication spec
is restructured around three real freeze/review/accept cycles with a
run-unique valid PNG fixture, full-closure manifests (1/1/4 assets), lawful
ACTIVE hostile contexts, and per-workspace audit bindings; frozen-review-
parity gains the bounded A4 pending/unserved/cross-workspace assertions;
review-surface fixture expectations are made faithful to the genuine new
pending media COW operation (eight-operation timeline, added Media assets
diff card), and the discard-lifecycle expectations are made faithful to
pending-only media leaving no canonical base row after a real discard.
The compose driver's shared HUMAN preview workspace seed now carries the
076 version facts its materializer requires (their absence
deterministically caused the 73e4 FREEZING helper timeout), and the
review helper now surfaces an actual freeze-job terminal failure before
the workspace-status deadline. The round closed with the qualified
foundation 0.2.1 (public registry release carrying the composite-FK
pairing fix that caused the 87d0/9f accept failures) integrated under
exact pin/lock/guards with a real HUMAN mixed-FK page regression, the
compose smoke fixture fully isolated (dedicated 0340 ACTIVE workspace
seeded after all 19 browser projects), and the browser-worker Chrome
for Testing pin corrected to 157.0.8103.78 targeting the observed
Critical CVE-2026-126859.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: #116 (URL: `https://github.com/ulfe-lmi/slaif-agent-site/pull/116`),
  state OPEN (draft during the round; marked ready after report
  publication)
- Base branch: main @ starting remote SHA d888b37ffe3b3685c3743dd054a953e148d6dbf2 (verified unchanged at branch creation and before the first push); head branch oap/083-10-a-workspace-media-isolation
- Implementation head SHA: 65e0f162f7762c911fc116a58e64b31be3ed95b0 (pushed heads in order: d57e5c1, e6aa904, afe89b5, 73e4c3e, 87d03ea, 831dcf9, e00e6bc, 9f6b3e8, ca4bc19, 14f6f77, 33dddac, 65e0f16 = current pushed head; parent 33dddacc535c3f76c9412bcef400fee75985e0a4, tree c682ab1e379a400b398f7043bc82b4cbd8a65157; ROOT verified the 13 changed blobs of the 65e0f16 delta byte-exact against the frozen review index; re-verified as remote HEAD at publication)
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commits pushed before report: 14
  (23d091f implementation; b84595a review-surface fixture-fidelity
  repair after the 23d0 Compose failure; d57e5c1 discard-lifecycle
  fixture-fidelity repair after the b845 Compose failure; e6aa904 media-
  publication boolean-concat fixture fidelity + Apache .19 pin
  maintenance after the d57e Compose/Supply-chain failures; afe89b5
  supply-chain policy manifest .19 sync after the e6aa run terminated;
  73e4c3e media-publication per-actor workspace status observation after
  the e6aa Compose agent-only detail-GET 404; 87d03ea compose driver
  version-facts seed + freeze-job failure diagnostics after the 73e4
  Compose FREEZING helper timeout; 831dcf9 bounded diagnostic-only
  review-worker failure logging + sanitized CI collection after the
  87d0 Compose accept-job REVIEW_JOB_STALE_AT_BUDGET terminal failure;
  e00e6bc sanitizer lint repair after the 831 Node-contracts lint
  failure; 9f6b3e8 fixed reviewer-step markers to localize the 42883
  region; ca4bc19 error-only fixed reviewer-step state (no healthy-path
  spam); 14f6f77 qualified foundation 0.2.1 integration + real HUMAN
  mixed-FK page regression; 33dddac smoke agent-browser fixture
  isolation (dedicated 0340 ACTIVE preview workspace); 65e0f16 Chrome
  for Testing 157.0.8103.78 security pin + 0340 seed moved after all 19
  browser projects); report parent = implementation SHA
- Push form note: the 87d03ea push used `git push origin
  oap/083-10-a-workspace-media-isolation` (output piped to tail) rather
  than the order literal `git push -u origin
  HEAD:refs/heads/oap/083-10-a-workspace-media-isolation`; ROOT
  independently verified the remote destination and head bytes were
  exact (tree 0eb01aa02e0e200db8572f614ce85c37851cdbd4, both changed
  blobs matching the reviewed bytes); no undo/replay/rebase performed.
  The 14f6f77 push used the branch name `git push origin
  oap/083-10-a-workspace-media-isolation` (output piped to tail); ROOT
  independently verified the exact remote PR destination/head. The order
  literal `git push -u origin
  HEAD:refs/heads/oap/083-10-a-workspace-media-isolation` was restored
  for all subsequent pushes (ca4bc19, 33dddac, 65e0f16); the 65e0f16
  push completed rc 0 with the remote ref ls-remote-verified.
- New PR this turn: yes (#116); amended existing: no; merge performed: NO

## Changes made

- `077_001_workspace_isolated_media` migration: re-routes existing online
  media registration/metadata/reference functions to the existing COW
  content view with server-owned context and lifecycle lock; publication-
  derived mutation into the reviewer transaction with least-authority
  product helpers; direct 077->076 downgrade refuses fail-closed with the
  marker ratchet preserved; media_asset was already COW-enabled — no
  re-COW, no private pending-row guard clone; v2 snapshot format, exact
  keys/versions and retained historical reads unchanged.
- `media_service/finalize.py`, `review_worker/accept_job.py`,
  `bootstrap/service.py`, `content_model/service.py`, `db/privileges.py`:
  referenced-closure finalization from the promoted state; UUID identity
  semantics in the 077 publicize guard (canonical and compact spellings
  accepted and compared as UUID); least-authority grants so runtime/
  editor/control/media processes gain no canonical publication authority.
- Tests: four NEW module files (test_media_workspace_isolation,
  test_media_workspace_existing_assets, test_media_workspace_migration_
  preservation, test_media_workspace_privileges) plus the six existing
  modules completing the ten selected CI M modules (test_media_service,
  test_media_security_lifecycle, test_real_human_accept,
  test_real_human_discard, test_freeze_review_snapshot,
  test_human_agent_editor_workspace), media-service isolation corrections (canonical
  0 / pending 1 in own workspace, same-site B 404, real freeze/discard with
  retained frozen exact bytes and honest orphan existence/no-GC), real
  accept/discard closures incl. NEW-pending A5 and after-both A6 rollback
  with exact pending-row preservation and public orphan 404, eight-module
  historical phase-fidelity closure (076 historical phase, one-way 077
  current head), three-test typing corrections (test-only annotations/
  patch.object, no production export change), test_foundation_ci oracle for
  the ten unfiltered M modules and the Group B 30-minute budget.
- CI: `.github/workflows/ci.yml` Group B (all five PG14..18 children) gains
  the exact ten-module unfiltered M command after the unchanged 45+Q
  selection; Group B child timeout-minutes 15 -> 30 (bounded orchestration
  budget correction for the expanded exact selection; Group A and all other
  timeouts, names, matrices, argv, order and aggregate guards unchanged).
- Packaging pin maintenance (bounded live-mirror correction): the four
  exact Apache pins move 2.4.58-1ubuntu8.18 -> 2.4.58-1ubuntu8.19 in the
  three mirroring sites (infra/apache/Dockerfile install pins,
  tests/packaging/test_oci_contract.py literals, supply-chain/policy.json
  manifest) after the live Ubuntu noble-updates index superseded .18 for
  all four packages (d57e Supply-chain job: apt exit 100, three attempts);
  official index evidence independently recorded by the peer; no other
  pin, origin, guard, base or dependency changed; the fresh CI APT build
  validates signed repository trust and installed versions.
- E2E: media-publication.spec.ts three real cycles + run-unique PNG +
  full-closure manifests + audit bindings + ACTIVE-context hostile suite;
  frozen-review-parity.spec.ts +136 lines of bounded A4 assertions;
  review-surface.spec.ts fixture fidelity for the genuine pending media
  COW operation (timeline 8 with one media_assets:upsert; Media assets
  added-1 card with the fixture asset id); discard-lifecycle.spec.ts
  fixture fidelity for pending-only media (discarded asset asserts
  canonical base count 0 and media_asset_changes count 0 in both the
  fresh-site and post-accept cases; every other lifecycle assertion
  unchanged); media-publication.spec.ts renders its five
  status|published|hash oracles with an explicit
  `CASE WHEN published_at IS NOT NULL THEN 't' ELSE 'f' END` because PG
  boolean-to-text concatenation renders 'true'/'false' (exposed by the
  first runtime pass of the never-before-run media-publication project);
  the expected public|t / private|f literals are unchanged and bare-
  boolean SELECT oracles elsewhere still render 't'/'f' and are
  untouched); workspace status observation is now per-actor — the AGENT
  cycles keep the positive human HTTP detail oracle (038
  slaif_human_agent_workspace_get is explicitly scoped to
  actor_type='AGENT', so a 404 there stays a genuine failure), while the
  HUMAN preview-workspace cycle observes status through the test fixture
  SQL (no generic authorized HTTP status read exists: both the detail
  and list control reads are agent-only, while freeze/review/accept are
  actor-agnostic).
- Compose driver (87d03ea): tools/compose/e2e.sh now seeds the shared
  HUMAN preview workspace with the exact 076 six-pin version-facts
  literal at creation (shell-escaped inside the double-quoted psql
  argument; the retained first bare-quote attempt produced invalid JSON
  and was corrected, with the docker argv-capture stub proving psql
  receives the exact valid JSON as a single -c argument); the 076
  materializer otherwise rejects the column default '{}' with
  REVIEW_WORKSPACE_VERSION_UNKNOWN, the deterministic cause of the 73e4
  FREEZING helper timeout; no other seed/role/site/UUID/overlay
  changes. The media-publication waitForReview helper now first polls
  the passed freeze.job_id for a terminal review_job state and fails
  with the actual persisted job error if the freeze job FAILED, before
  any workspace-status poll; consistency/state/deadline oracles
  unchanged.
- Qualified foundation 0.2.1 (14f6f77; 2026-11-13 prospective source
  correction, byte-exact supplement transcript committed): the corrected
  upstream composite-FK pairing fix shipped as public registry release
  0.2.1 and was integrated by exact pin
  `agent-cow-postgresql==0.2.1` (wheel 315f5172506076f5…/108551B, sdist
  6556d567eaa1f449…/110560B, registry URLs and digests verified), bounded
  uv.lock delta (foundation block + root specifier only),
  FOUNDATION_VERSION + strict guards (tools/check_repository.py,
  tools/supply_chain/policy.py, supply-chain/policy.json), fixture and
  marker anchors, current docs + strategic mirrors, NOTICE, regenerated
  THIRD_PARTY_NOTICES.md and sbom.json (the SBOM regeneration also
  repairs pre-existing stale certifi 2026.10.19 / next 16.4.1 inventory
  rows already present in the unchanged locked inputs — honest stale
  inventory repair, no new dependency). Registry-only per dependency
  law: no Git/editable/local SDK input; all 36 installed files
  verified matching the qualified wheel bytes.
- Real HUMAN mixed-FK page regression (14f6f77; PEER-authored,
  source-reviewed, test_real_human_accept.py SHA cf199671): one new real
  HUMAN Editor pending-page -> dependencies() -> freeze -> real accept ->
  canonical title/revision/promotion-audit/outbox case through public
  HTTP, with the exact audit.human_editor_mutation oracle and canonical
  title still original before accept; all 59 pre-existing non-import
  module AST nodes unchanged; 17 PASS/121.02s focused local PG18.
- Compose smoke fixture isolation (33dddac): the restructured
  media-publication E2E cycles terminate the shared parity preview
  workspace (0301) in ACCEPTED, so capabilities bound to it no longer
  authenticate — the silent smoke agent-browser-phase failure after all
  19 projects in 14f6f77. e2e.sh seeds a dedicated still-ACTIVE HUMAN
  preview workspace (0340, same site/admin, pinned 076 six-pin
  version-facts constructor literal, no pending content) and smoke.sh
  binds its two browser capabilities to it; compose smoke contract + CI
  oracle suites re-verified (52 tests / 305 subtests PASS). No oracle
  weakening, no lifecycle bypass, no reactivation of 0301.
- Chrome for Testing 157.0.8103.78 security pin (65e0f16; 2026-11-13
  security source correction, byte-exact supplement transcript
  committed): 157.0.8103.50 -> 157.0.8103.78 (official CfT Stable feed
  revision 1717349, same executable path) targets the observed Critical
  CVE-2026-126859 from the 14f6f77 browser-worker raw scan; verified
  archive SHA256
  9223832977a13db3646201b1341c1f9cf08afa3ceae92540116d7b0c062364fb
  (203266906B) and binary chrome SHA
  f60cb86024464df9740504a1584b605c2b3cf107625ff11e1da22c875c1627e8 with
  actual `chrome --version` = 157.0.8103.78 native 0. Exact
  version/URL/hash literals in the browser-worker Dockerfile,
  tests/packaging/test_oci_contract.py, tools/supply_chain/policy.py,
  supply-chain/policy.json, tools/compose/smoke.sh version guard, and
  current docs (README, CONFIGURATION, DEPLOYMENT, SECURITY,
  SUPPLY_CHAIN, LICENSE_POLICY) with truthful 083-10-a attribution and
  dated .50 history preserved; no other pin/dependency/base-image/
  threshold changed; vulnerability-exceptions.json still empty.
  Patched-image scan PASSED on the fresh 65e0f16 CI run (Crit 0 / ignored 0 / exceptions 0; CVE-2026-126859 absent including related IDs).
- Compose driver seed timing (65e0f16, 33dddac Compose failure repair):
  the 0340 seed moved from before the browser projects to after all 19
  browser projects (immediately before the final compose smoke; the
  compose-e2e OK marker still reports 19). Seeded early, 0340 (newer,
  same site) could steal the headerless human resolver's fixture
  binding for the actual browser projects — the 33dddac PREVIEW-project
  theme/header assertion failures (expected meadow received ocean;
  expected minimal received institutional). No production resolver or
  oracle change.
- Docs: API/OPERATIONS/SECURITY/TESTING and README media isolation,
  private/public authorization and cache distinctions, unserved-orphan
  qualification, 083-8-z closure corrections; oap/INCREMENTS.md and
  oap/MVP-PROGRESS.md 083-10 entries with corrected 083-8-z closure
  attribution.

## Files changed

91 paths (82 modified + 9 new) — 8047 insertions(+), 1428 deletions(-),
9475 gross cumulative at 65e0f162f7762c911fc116a58e64b31be3ed95b0 from
base d888b37f (`git diff --stat`-verified): grouped per the ROOT frozen
publication index — production/config 14 paths (774 gross: ci.yml,
infra/apache/Dockerfile, pyproject.toml, uv.lock, foundation.py,
bootstrap/content-model/privileges sources, media_service database +
finalize, review_worker accept_job + worker, browser-worker Dockerfile,
supply-chain/policy.json); docs/governance 21 (417: README,
CONTRIBUTING, NOTICE, AGENTS.md, ARCHITECTURE-for-agents.md, 10 docs,
oap ledger 2, strategic-instructions 4); generated inventory 2 (16:
THIRD_PARTY_NOTICES.md, sbom.json); activated transcript 2 (268:
oap/active, order); migration 1 (365: 077_001); tests/evidence/policy/
tooling 51 (7635: 39 backend test modules, 4 E2E specs, packaging +
repository policy suites, compose drivers, diag-sanitize.mjs,
policy.py, check_repository.py).

## Acceptance-criteria evidence

### A1

- Unique fresh PR #116 from verified remote main d888b37f on the required
  branch; order + active committed byte-exact unchanged; no other PR or
  prior report/order changed; dependabot PRs 105/114/115 untouched.

### A2

- Baseline RED preserved at /tmp/oap-083-10-a-baseline-red/runs/attempt3/
  (pytest-run3.log f1066995, a2-baseline-red-human.json 6d2867ad,
  a2-baseline-red-agent.json 9078fc9e, file-identities.txt 35cd66d8,
  test-diff-attempt3.txt ba27ffac; ROOT independent review): 2 FAILED /
  14.43s / native 1 on the original M run — human+agent uploads 201,
  same-site workspace B served 200 exact bytes and canonical base was
  independently recorded 1 PRIVATE (the premature-canonical defect); the
  B-404 assertion failed and the subsequent canonical-0 check did not
  execute; public 404 was an unasserted sanity read. Attempts R1/R2 were
  distinct setup failures and are retained separately. After the fix:
  real HTTP + real COW pending writes in A with canonical and same-site B
  unchanged, fresh pending assets AND edit/delete of existing canonical
  assets, cross-site/scope/role/state/idempotency/quota denials, no-op
  dedupe (test_media_workspace_isolation, test_media_workspace_existing_
  assets, test_media_service corrections; actual local PG18 PASS receipts
  retained, e.g. pg18-existing-canonical-3 4 PASS/40.91s native 0 after two
  retained fixture-failure runs — those fixture failures are NOT product
  RED and are labeled as such).

### A3

- Human Editor PATCH/DELETE of an agent-uploaded asset inside its AGENT
  workspace (the lawful human-on-agent editor selection is separate from
  the agent capability, which derives the agent workspace) with correct-
  workspace read vs same-site/canonical denial, proper audit families and
  transaction atomicity; actual PG18 PASS (a3 run retained; the wrapper-1
  tail observation is preserved as an afterfact copy, not relabeled).

### A4

- Through public NGINX (CI Compose job): pending private media private
  preview, freeze with the actual worker, immutable descriptors/inventory/
  digest, frozen reads stable after lawful edits/discard/promotion
  cleanup, private/public/cross-site/substitution denials, six stable
  engine pairings via the freeze-parity project; 23d0 Compose run failed
  at the review-surface project before freeze/accept/media (stale seven-
  operation fixture oracle, actual 8 rows) — retained honestly; the
  b84595a Compose run then PASSED review-surface (3 cases), freeze-review-
  snapshot (4 cases), frozen-review-parity (six stable pairings) and
  accept-lifecycle (2 cases) before failing at discard-lifecycle (two
  cases expected `private|t` canonical base state for the NEW pending
  asset after real discard, received empty — correct under 077, where a
  pending-only asset leaves no canonical base row; the d57e5c1 repair
  asserts canonical base count 0 and media_asset_changes count 0 for the
  discarded asset, keeping every other lifecycle assertion); the d57e5c1
  Compose run then PASSED every project through discard-lifecycle (all 3
  cases, including both repaired fixtures) before failing at the never-
  before-run media-publication project, cycle-1 oracle (line 915):
  expected `public|t|<digest>` vs actual `public|true|<digest>` with the
  digest and public status correct — PG renders boolean-to-text
  concatenation as 'true'/'false' (verified on owned PG18: bare boolean
  SELECT renders 't'/'f'), a fixture presentation error, not a product
  defect; fixed with explicit CASE WHEN in all five analogous oracles
  (e6aa904). The e6aa904 Compose run then PASSED every project before
  media-publication and failed inside media-publication at a
  workspaceStatus GET expected 200, received 404 (line 191); the log
  does not mark which cycle (stage unknown: the driver suppresses the
  call-site stack and all upstream projects consumed real time, so no
  per-cycle attribution is claimed). Source-supported deterministic
  cause (not a runtime trace): the human control detail GET is
  agent-only (038 slaif_human_agent_workspace_get,
  actor_type='AGENT'), and the shared parity preview workspace is HUMAN
  (driver-seeded), so that helper cannot lawfully observe the HUMAN
  workspace status. Fixed in 73e4c3e with per-actor status observation
  (AGENT keeps the HTTP oracle, HUMAN uses the fixture SQL). The
  73e4c3e Compose run then PASSED review-surface (3), freeze-review-
  snapshot (4), frozen-review-parity (six stable pairings, cleanup
  94103ms), accept-lifecycle (2) and discard-lifecycle (3), and failed
  at media-publication (line 241:38) at the 4-minute helper deadline
  while the workspace status was still FREEZING (stage unknown).
  Deterministic source cause: the compose driver seeded the shared
  HUMAN preview workspace without version_facts (076 column default
  '{}'), which the 076 materializer rejects with
  REVIEW_WORKSPACE_VERSION_UNKNOWN (freeze job
  SNAPSHOT_VALIDATION_FAILED), so the workspace could never leave
  FREEZING; fixed in 87d03ea by seeding the exact 076 six-pin version
  facts at creation, plus the minimal freeze-job FAILED diagnostic in
  the helper. The 87d03ea run's
  media-publication accept failure (REVIEW_JOB_STALE_AT_BUDGET) is the
  42883 composite-FK branch, corrected by the qualified foundation
  0.2.1 in 14f6f77; the 14f6f77 Compose run then PASSED all 19 public-
  NGINX browser projects — including the full media-publication project
  (three real freeze/review/accept cycles, hostile tail, audit bindings,
  final public checks) and the A4 six stable pairings (cleanup
  71206ms) — and all follow-up checks through agent-browser-http:OK,
  before a silent exit 1 in the smoke agent-browser phase (smoke.sh:1115
  marker; the workspace-lifecycle mismatch repaired in 33dddac). The
  33dddac Compose run FAILED earlier at the PREVIEW project (human-
  editor-theme expected --meadow received --ocean; global-regions
  expected --minimal received --institutional — the early-seeded 0340
  stealing the headerless human resolver's fixture binding), so no
  19-project PASS is claimed for 33dddac; the 65e0f16 seed-timing move
  is proven by the 65e0f16 Compose run: FULL 19 public-NGINX browser
  projects PASSED including the full media-publication project and the
  six stable pairings, plus the previously-failing smoke agent-browser
  phase — the full 19-project/A4/A5 browser PASS now exists. Local static source green
  on the final subject (prettier explicit 0; typecheck/lint wrapper 0
  with the direct natives piped to tail and unretained, re-proved by
  the current CI).

### A5

- Real freeze/review/accept with the real review worker publishes metadata/
  reference effects and public status atomically matching the approved
  frozen media and bytes; NEW pending assets public only after committed
  acceptance; existing canonical assets keep prior authorization; discard
  leaves canonical/other workspaces/retained bytes intact; accept/discard/
  replay/idempotency honest; same-hash concurrent proposals safe
  (test_real_human_accept module 17 PASS/121.02s focused local PG18 on the current input — 16 PASS/97.41s on the pre-0.2.1 input; the new HUMAN mixed-FK case included; direct pytest native piped tail/UNRETAINED, wrapper 0;
  E2E cycles 1-3; E2E accept-lifecycle both cases PASS in the failed
  b84595a Compose run — real accept through public NGINX — while the
  media-publication project was not reached in that run).

### A6

- Final strongest proof (test source 9fa7baeec): injected failure at the
  real media-mark/promotion boundary with actual worker/reviewer/COW
  transaction — both real effects reach the guarded point before forced
  rollback (observed sequence witness), exact pending rows preserved
  (before/after equality), no partial canonical media/content/revision/
  promotion audit/success/outbox commit, public pre-copied orphan 404
  despite object existence, no false collection (pg18-a6-exact-1.log
  f8b3282c: 1 PASS/9.96s/direct 0/wrapper 0). An earlier 8.49s run
  (33569142) is a distinct limited subject and is retained/qualified as
  such, not the final witness.

### A7

- Actual privilege tests (direct/inherited overgrants detected, legacy
  canonical creator confined, least authority) + fresh/upgrade/migration
  refusal: 076->077 normal upgrade preserves genuine media/v2 (migration-
  preservation module 1 PASS/16.43s native 0, peer real PG18, credited for
  byte-identical integrated inputs), direct 077->076 downgrade refuses
  without effects, fresh head install cases (test_database_bootstrap 33
  PASS/401.45s native 0 incl. focused; three retained earlier failure
  runs).

### A8

- Local current gates on the final subject (65e0f16 inputs where the
  changed files apply): uv lock --check, ruff check/format 0, mypy 0
  errors on the current input (native 0 to log), unit 788 PASS +
  repository unittest 90 OK (direct unittest native piped/unretained,
  actual OK summary retained), control-database integration 4
  PASS/42.92s, real-accept module 17 PASS/121.02s (includes the new
  HUMAN case; focused wrapper 0, direct pytest native UNRETAINED via
  tail), 10 process --check all CHECK_OK native 0, compileall,
  check_repository PASS, policy validate + notices --check,
  check_mermaid 16/16, markdownlint 0 (630 files); Node (frozen
  install, lint, format:check, typecheck, test — 36 contract cases
  across the private scaffolding packages, a subset of the full package
  test surface — build) with direct natives masked by tail in the first
  chain (qualified) and complete pnpm licenses list --json captured to
  file (native 0, 249 packages parsed). On the 65e0f16 touched inputs
  specifically: packaging 9 PASS + 20 subtests, supply-chain 46 PASS +
  27 subtests, repository policy 0, ruff check/format 0, 6 changed
  Markdown files linted 0 issues, repository unittest 90 OK, bash -n
  both compose drivers — direct pytest/unittest natives UNRETAINED
  (piped tail, wrapper rc 0), no receipt-only rerun. The earlier-head
  gates above (878 PASS/33.17s unit+repository, Node full chain,
  licenses) remain the qualified record for the unchanged inputs.
- FULL current backend DB: ACTUAL full backend PG18 integration run
  384 PASS / 3298.61s / 0 failures (finished 09:22Z) on the 14f6f77
  input — owned ::1:5432 PG 18.6 (target PID/datadir/uid re-verified
  immediately before), explicit PGHOST/PGPORT/PGUSER/PGPASSWORD fixture
  env, --ignore for the untracked private probe (no tracked test
  excluded); direct pytest native UNRETAINED (output piped to tail,
  wrapper 0). Backend Python inputs are unchanged from that run's head
  through 65e0f16 (only compose driver scripts, browser-worker, docs and
  policy pins changed since), so the run remains the qualified local
  full-DB evidence for the current head; the earlier 383-PASS
  pre-typing subject (pg18-integration-full-3.log 1088f0d7) and the
  17-failed full-2 are retained as history. CI is NOT a duplicate 383:
  foundation Group A runs 85 selected regressions and Group B runs
  45+Q+M (66 M cases) per child; the mandatory current 20 named + 10
  actual PG children validate the exact head separately.
- Fresh full Compose through public NGINX with real fixtures/cleanup, 19
  Playwright projects, six stable pairings and fresh six images: CI
  Compose job on the implementation head (23d0 FAILED at review-surface;
  b84595a PASSED through accept-lifecycle then FAILED at discard-
  lifecycle; d57e5c1 PASSED through discard-lifecycle then FAILED at
  media-publication boolean-concat oracle, with Supply-chain failing on
  the withdrawn .18 pin; e6aa904 FAILED at policy/supply-chain before
  APT and at media-publication workspace-status 404; 73e4c3e PASSED
  review/freeze/frozen-parity/accept/discard and Supply-chain fresh six
  images (0 Critical/40 High, artifact 14002186883) then FAILED at
  media-publication line 241:38 FREEZING helper timeout; 87d03ea PASSED
  review/freeze/frozen-parity(six pairings)/accept/discard then FAILED at
  media-publication with the ACTUAL accept-job terminal failure
  REVIEW_JOB_STALE_AT_BUDGET (worker error reason not retained in that
  run; the 831dcf9 diagnostic delta captured the first witness and
  subsequent runs/bounded probes identified the cause: foundation SDK
  composite-FK 42883 in reviewer.dependencies, corrected by the
  qualified 0.2.1 in 14f6f77); the 14f6f77 run PASSED all 19 public-
  NGINX browser projects incl. media-publication and the A4 six stable
  pairings, then FAILED the smoke agent-browser phase (silent exit 1 at
  smoke.sh:1115 after agent-browser-http:OK — workspace lifecycle,
  repaired in 33dddac) with Supply-chain FAILING the Critical
  CVE-2026-126859 browser-worker finding (job 131786750642 / artifact
  14023083058, repaired in 65e0f16); the 33dddac run FAILED at the
  PREVIEW project (0340 resolver interference, repaired in 65e0f16
  seed timing) with Supply-chain FAIL (job 131804162576, exact
  diagnostic unread); 65e0f16 PASSED: full 19 public-NGINX browser
  projects incl. media-publication + six pairings + full smoke (agent-
  browser phase included) and fresh six images Crit 0 / ignored 0 /
  exceptions 0 (CVE-2026-126859 absent); qualified partial evidence
  retained at every earlier head).

## Local verification

Environment: owned disposable PG18 at ::1:5432 (trust, fake credentials),
uv 0.12.5 frozen env, Node v24.22.0 + pnpm 11.22.0 (frozen lockfile, 254
packages), Playwright browsers from prior rounds. Logs under /tmp/oap-
083-10-a-impl/ retain headers/source hashes and direct natives where
noted (full SHA256 index in the round journal):

- `uv lock --check`: PASSED (py-static-1.log)
- `uv run --frozen ruff check ...`: PASSED
- `uv run --frozen ruff format --check ...`: PASSED
- `uv run --frozen mypy`: PASSED (322 source files, 0 errors after the
  reviewed 3-test typing delta)
- `uv run --frozen pytest services/backend/tests/unit tests/repository -q`:
  PASSED 878 + 29 subtests / 33.17s / native 0 (predates CI budget change)
- 10x `python -m slaif_agent_site.<svc> --check`: all CHECK_OK native 0
  (process-prep-1.log)
- `python -m compileall -q tools tests/repository`: PASSED
- `python -m unittest discover -s tests/repository -p 'test_*.py'`:
  PASSED 90 / native 0 (process-prep-1.log, pre-budget-change subject);
  after the budget change: `python -m unittest tests.repository.
  test_foundation_ci` 19 OK + discover 90 OK (direct natives piped,
  actual OK summaries retained; the first line-based YAML edit attempt
  failed its assertion before any write, and its 19-OK ran on the old
  15-minute subject, not the new 30)
- `python tools/check_repository.py`: PASSED
- `python tools/check_mermaid.py`: PASSED 16 diagrams/3 files, CLI
  11.16.0, direct 0 (mermaid-2.log) after two retained npx tooling
  failures (process-prep-1/prep-2)
- pinned markdownlint-cli2 0.23.2 on changed docs: PASSED 0 issues
  (prep-2.log)
- `pnpm install --frozen-lockfile`: PASSED (node-install-2.log, 254
  packages, native 0; first attempt failed with `corepack: command not
  found`, native 127, retained — node-install-1.log)
- `pnpm lint`: node-gate-2.log records actual LINT 1 (one unused `cycle2`
  binding in the restructured E2E spec, exact node retained); bounded fix
  then `pnpm lint` PASSED direct 0 (node-lint-3.log)
- `pnpm format:check` / `pnpm typecheck` / `pnpm test` / `pnpm build` /
  `pnpm licenses list --json`: PASSED (node-gate-2.log natives 0)
- Focused re-checks on the late subjects (e6aa904..87d03ea): prettier
  --check on the changed TS spec explicit 0; typecheck and lint wrapper
  0 with each command piped to tail (no pipefail), so their DIRECT
  natives are unretained (wrapper-only proof, honestly qualified; the
  current CI provides the authoritative lint/typecheck proof); one
  prettier attempt that included the .sh compose driver failed on the
  unsupported parser (tooling failure, retained) and the TS-only
  re-check ran separately as corrected.
- Focused PG18 (subjects in round journal): hist15 15 PASS/125.37s
  native 0; typing8 8 PASS/112.65s native 0; media-service corrected
  2 PASS/146.03s native 0; real-human-accept module 16 PASS/97.41s
  native 0; existing-canonical 4 PASS/40.91s native 0 (after two retained
  fixture-failure runs); fieldref RED pg18-fieldref-red-1 (a45ed6de): the
  all-reference-modes case is the meaningful real-worker RED (MEDIA_
  PUBLICIZE_NOT_REFERENCED P0003 at the actual 077 publicize, server log
  independently observed/retained by ROOT) while the first single-asset
  case failure was a fixture unpack error — retained and distinguished;
  corrected 077 (5929) two cases PASS/16.83s native 0 (fd5f0d28);
  bootstrap module 33 PASS/401.45s native 0 (three retained earlier
  failure runs); migration-preservation 1 PASS/16.43s native 0 (peer real
  PG18, credited for byte-identical inputs); agent HTTP four historical
  cases 4 PASS/63.19s native 0; A5 2 PASS/18.16s native 0; A6 final
  1 PASS/9.96s direct 0/wrapper 0.
- FULL backend PG18: full-1 launch NOT CONFIRMED (headers-only 1155B log
  01b14568 retained; launcher defect recorded, no full-PASS claim);
  full-2 17 FAILED/365 PASSED/2313.28s native 1 (7998d327; all 17 causes
  traced and resolved via the eight-module historical closure, discard
  round-trip fix and two media-service isolation assertion corrections);
  full-3 383 PASS/3308.37s native 0 (1088f0d7) on the pre-typing subject —
  qualified exactly as stated in A8.
- Diagnostic delta (831dcf9) focused verification: ruff check/format
  PASSED, mypy 322 files PASSED, unit test_media_public_core +
  test_review_worker 42 PASS/3.49s native 0; node --check and bash -n
  PASSED; collector stub harness (merged stdout+stderr, 4 accepted
  fixture lines / 10 rejected unsafe lines incl. class-only and
  outcome-only fragments) exact-expected output native 0 (proof-3/4/5
  logs; the earlier wrong-expectation-order native 1 is retained as
  history). One EXPLICIT owned-::1:5432 budget regression under the
  first exclusive lease (test_real_human_accept.py::test_accept_worker_
  retryable_rollback_and_budget; PGHOST=::1 PGPORT=5432 PGDATABASE=
  postgres, target PID 3397505/owned datadir re-verified immediately
  before): 1 PASS/9.07s direct native 0, zero slaif_test_% databases and
  no live test children after fixture teardown (release receipt
  c7312798). The 831 Node contracts job then FAILED on five new-file
  ESLint findings (no-useless-assignment, process no-undef x4); the
  bounded sanitizer-only fix (node:process import + unassigned ok) is
  verified locally (ESLint/Prettier/node --check/collector proof all 0)
  and is pushed only after the useful 831 jobs terminate.
- Current-subject focused gates (ca4bc19..65e0f16, log-qualified): full
  backend PG18 384 PASS/3298.61s (direct pytest native UNRETAINED,
  piped tail; wrapper 0; explicit owned ::1:5432 fixture env; --ignore
  private probe, no tracked test excluded); unit 788 PASS/31.09s +
  repository unittest 90 OK (direct natives piped/unretained, actual OK
  summaries retained); control-database integration 4 PASS/42.92s and
  real-accept module 17 PASS/121.02s (focused wrapper 0, direct
  natives UNRETAINED); mypy 0 on the current input (native 0 to log);
  ruff check/format 0; 10 process --check; compileall; check_repository;
  policy validate + notices --check; check_mermaid 16/16; markdownlint 0
  (630 files); Node frozen install/lint/format:check/typecheck/test
  (36 contract cases)/build (direct natives masked by tail, qualified)
  and complete pnpm licenses list --json to file (native 0, 249
  packages). On the 65e0f16 touched files: packaging 9 PASS/20
  subtests, supply-chain 46 PASS/27 subtests, repository policy 0,
  ruff 0, 6 changed Markdown files 0 issues, bash -n both compose
  drivers, compose smoke contract + CI oracle 52 tests/305 subtests —
  direct pytest/unittest natives UNRETAINED (piped tail), no
  receipt-only rerun of passing subjects.

## GitHub CI / required checks

- CI run 43331837905 on implementation commit 23d091f (observed): 25
  jobs, 24 success / 1 fail. Success: Dependency review, Foundation PG
  Group A PostgreSQL 14/15/16/17/18, Foundation PG Group B PostgreSQL
  14/15/16/17/18 (8m55s-14m6s, within the new 30-minute budget),
  Foundation PostgreSQL 14-18 aggregators, Markdown, Mermaid, Node
  contracts, Python 3.12/3.13/3.14 quality and package, Repository
  policy, Supply-chain evidence. Fail: Compose and edge packaging
  (6m42s) — review-surface.spec.ts timeline count expected 7 / received
  8 (stale fixture oracle; the driver stopped before the freeze/accept/
  media projects, so no 19-project/A4/A5 browser PASS claim from that
  run).
- CodeQL run 43331838187 on the same head (observed): 5 check entries —
  Analyze (actions), Analyze (javascript-typescript), Analyze (python),
  Detect supported languages and the CodeQL app — all success.
- 23d0 total: 30 check runs, 29 SUCCESS / 1 FAIL (Compose); the failed
  head's failure stands and is retained.
- CI run 43335287908 on implementation commit b84595a (observed): 25
  jobs, 24 success / 1 fail. All 10 actual PG children success (Group A
  5m33s-7m25s; Group B 8m25s-14m16s, within the new 30-minute budget);
  all static/quality/supply-chain jobs success. Fail: Compose and edge
  packaging (9m03s) — review-surface (3 cases), freeze-review-snapshot
  (4 cases), frozen-review-parity (six stable pairings) and accept-
  lifecycle (2 cases) all PASSED (qualified partial A4/A5 runtime
  evidence); failure at discard-lifecycle.spec.ts lines 515/852 (expected
  `private|t` canonical base state for the NEW pending asset after real
  discard, received empty — correct 077 semantics, stale fixture oracle);
  the driver stopped before the media-publication project, so no
  19-project/A5 browser PASS claim from that run either.
- CodeQL run 43335287919 on b84595a (observed): 4 jobs, all success.
- b845 total: 30 check runs, 29 SUCCESS / 1 FAIL (Compose); the failed
  head's failure stands and is retained.
- CI run 43337913043 on implementation commit d57e5c1 (observed): 25
  jobs, 23 success / 2 fail. All 10 actual PG children success (Group A
  7m05s-9m44s; Group B 8m11s-11m49s, within the 30-minute budget). Fail 1:
  Compose and edge packaging (10m44s) — review-surface (3 cases), freeze-
  review-snapshot (4 cases), frozen-review-parity (six stable pairings),
  accept-lifecycle (2 cases) and discard-lifecycle (3 cases, including
  both repaired fixtures) ALL PASSED; failure at the never-before-run
  media-publication project cycle-1 oracle (line 915, `public|t|` vs
  actual `public|true|`, digest identical — boolean-concatenation
  presentation, not a product defect). Fail 2: Supply-chain evidence
  (8m26s) — pinned Apache 2.4.58-1ubuntu8.18 no longer on the live
  noble-updates index (apt exit 100, three attempts, all four packages);
  the Python reproducibility stage passed before it; no valid six-image
  artifact or vulnerability-gate PASS is claimed from that run.
- CodeQL run 43337913011 on d57e5c1 (observed): 4 jobs, all success.
- d57e total: 30 check runs, 28 SUCCESS / 2 FAIL (Compose, Supply-chain).
- CI run 43341034745 on implementation commit e6aa904 (observed): 25
  jobs, 22 success / 3 fail. All 10 actual PG children success. Fail 1:
  Repository policy (23s) and Fail 2: Supply-chain evidence (18s) — both
  at the policy stage before any APT/image work: supply-chain/policy.json
  still listed .18 while the Dockerfile pinned .19 (the third mirroring
  site missed by the first pass; afe89b5 syncs it, verified locally by
  the full repository-policy command sequence). Fail 3: Compose and edge
  packaging (8m32s) — every project through media-publication cycles 1-2
  PASSED; failure at the cycle-3 HUMAN preview workspace status read
  (agent-only detail GET 404; source cause above; fixed in 73e4c3e).
- CodeQL run 43341034720 on e6aa904 (observed): 4 jobs, all success.
- e6aa total: 30 check runs, 27 SUCCESS / 3 FAIL (policy, supply-chain,
  Compose).
- CI run 43345301738 on implementation commit 73e4c3e (observed): 25
  jobs, 24 success / 1 fail; all 10 actual PG children success. Fail:
  Compose and edge packaging — review-surface (3), freeze-review-
  snapshot (4), frozen-review-parity (six stable pairings, cleanup
  94103ms), accept-lifecycle (2) and discard-lifecycle (3) ALL PASSED;
  media-publication failed at line 241:38 at the 4-minute helper
  deadline while the workspace status was still FREEZING (stage
  unknown; deterministic cause the unpinned version_facts seed, fixed
  in 87d03ea); no full 19-project/A4/A5 PASS from that run. Supply-chain
  evidence SUCCESS on this head: fresh six images, 0 Critical / 40
  High, artifact 14002186883 (.19 pins validated end-to-end).
- CodeQL run 43345301733 on 73e4c3e (observed): 4 jobs, all success.
- 73e4 total: 30 check runs, 29 SUCCESS / 1 FAIL (Compose); the failed
  head's failure stands and is retained.
- CI run 43349630176 on implementation commit 87d03ea (observed): 25
  jobs, 29 success / 1 fail; all 10 actual PG children success. Fail:
  Compose and edge packaging - review-surface (3), freeze-review-
  snapshot (4), frozen-review-parity (six stable pairings, cleanup
  56391ms), accept-lifecycle (2) and discard-lifecycle (3) ALL PASSED;
  media-publication FAILED with `Error: accept job FAILED:
  REVIEW_JOB_STALE_AT_BUDGET` (an actual accept-job terminal failure,
  new in this head; the specific failing cycle/actor is not individually
  marked in the official log and is not claimed; the worker reason was
  not retained in that run and no source guess is labeled as it for
  87d0; the 831dcf9 diagnostic push targets exactly this observability
  gap, and its witness plus bounded owned-runtime probes identified the
  cause - see the 831dcf9/9f6b3e8 entries below); no full
  19-project/A5 PASS from that run.
- CodeQL run 43349630131 on 87d03ea (observed): 4 jobs, all success.
- 87d0 total: 30 check runs, 29 SUCCESS / 1 FAIL (Compose); the failed
  head's failure stands and is retained.
- CI run 43360645729 on implementation commit 831dcf9 (observed): 30
  check runs, 28 SUCCESS / 2 FAIL. FAIL Compose and edge packaging:
  media-publication line 353:13 accept-job REVIEW_JOB_STALE_AT_BUDGET,
  its diagnostic log retaining the first witness (three
  phase=reviewer-tx class=UndefinedFunctionError sqlstate=42883 plus
  retry/budget lines). FAIL Node contracts: the lint failure repaired in
  e00e6bc. All 10 actual PG children, Supply-chain (fresh six images),
  Node-free quality jobs and CodeQL 43360645685 success; the 831 failed
  head stands and is retained.
- CI run 43363801051 on implementation commit 9f6b3e8 (observed): 30
  check runs, 29 SUCCESS / 1 FAIL (Compose and edge packaging only);
  media-publication failed the same confirmed branch (ROOT-decoded
  accept job 60d7d9c0: operations START -> dependencies START ->
  phase=reviewer-tx UndefinedFunctionError sqlstate=42883 observed on
  the first attempt and part of the second before the 60-line official
  log cap; terminal error REVIEW_JOB_STALE_AT_BUDGET records retry-
  budget exhaustion; the x3 full sequence is from the 831dcf9 local
  raw log, not from 9f);
  all 10 actual PG children, Node contracts, Supply-chain and CodeQL
  43363801156 success.
- CI run 43395948298 on implementation commit 14f6f77df82625b2b962c34954e971c4126c73f9 (observed): 30
  check runs, 28 SUCCESS / 2 FAIL. All 10 actual PG children success;
  CodeQL 43395948376 success. FAIL 1: Compose and edge packaging (job
  131786750842) — ALL 19 public-NGINX browser projects PASSED, including
  the full media-publication project and the A4 six stable pairings
  (cleanup 71206ms); every follow-up check through agent-browser-http:OK
  passed, then a silent exit 1 at the smoke.sh:1115 marker (the new
  media-publication cycles terminate the shared 0301 preview workspace
  in ACCEPTED, so the smoke phase's capability inserts into that
  workspace no longer authenticate — workspace lifecycle, repaired in
  33dddac). FAIL 2: Supply-chain evidence (job 131786750642, artifact
  14023083058) — raw scan found Critical CVE-2026-126859 in the
  browser-worker image's Chrome 157.0.8103.50 (fixed 157.0.8103.78;
  official CfT feed + Google desktop Linux release confirmed); the other
  five images 0 Critical / 0 ignored. The 14f6f77 failed head stands
  and is retained.
- CI run 43401195165 on implementation commit 33dddacc535c3f76c9412bcef400fee75985e0a4 (observed): 30
  check runs, 28 SUCCESS / 2 FAIL; all 10 actual PG children success;
  CodeQL 43401195145 success. FAIL 1: Compose and edge packaging (job
  131804162958) — failed at the PREVIEW project before media-
  publication: human-editor-theme expected renderer-theme-palette--
  meadow received --ocean; global-regions expected header--minimal
  received --institutional. Source cause: 0340 seeded BEFORE the
  browser projects (same site, newer created_at) could steal the
  headerless human resolver's fixture binding; repaired in 65e0f16 by
  seeding 0340 after all 19 projects. FAIL 2: Supply-chain evidence
  (job 131804162576) — failed; the exact diagnostic was not read
  (retained as an observed failure). The 33dddac failed head stands and
  is retained.
- CI run 43408367550 on implementation commit 65e0f162f7762c911fc116a58e64b31be3ed95b0 (observed): 30 check runs, 30 SUCCESS / 0 FAIL (started 10:20:23Z, terminal 10:34:14Z) = 20 required named/app checks + 10 actual PG children, no failed/missing/pending. All 10 actual PG children success (Group A + Group B PostgreSQL 14-18, 4m50s-11m10s, within the 30-minute budget) plus the five Foundation PostgreSQL 14-18 aggregators; CodeQL 43408367543 success. Compose and edge packaging (job 131828256658, 13m48s) FULL 19 public-NGINX browser projects PASSED, including the full media-publication project (three real freeze/review/accept cycles, hostile tail, audit bindings, final public checks) and the frozen-review-parity six stable pairings (cleanup 60913ms); the smoke agent-browser phase (previously silent exit 1) PASSED through agent-browser-http: OK, browser-worker-dispatch, artifact public/negative/restart/outage checks, control-readiness (6 induced failures / recovery clean) and the final compose-smoke OK — the dedicated 0340 fixture seeded after all 19 projects behaves as designed. Supply-chain evidence (job 131828256600) SUCCESS: fresh six images, Crit 0 / ignored 0 / exceptions 0 (actual current totals 2905 findings: High 39 / Medium 2686 / Low 151 / Negligible 17 / Unknown 12; the earlier 40-High / 1978-finding / 2026-11-12 DB figures are historical, not current); vulnerability DB built 2026-11-13T06:20:21Z (checksum 7776d82a5be335571ee9aa77093375659ceaae3fe324b9ed4ba2ba94abbaa36e, age 4.209h at scan); checksummed evidence artifact 14028583911 (8427984B, SHA256 0b38e9acaeb8bd835d54e2a01c4d315389c46828d5ccb8d43612501dd579abc4) under the synthetic 9f28816062e9c2b8cd7564f93289484b01a3b36d identity. ROOT v2 native-0 audits: 77 payload hashes / 18 index bindings / 6 config manifest labels / 12 exports / 9 changed backend source bindings; all 36 qualified 0.2.1 wheel image file hashes verified (SDK 0.2.1, MIT); Chrome .78 exe SHA f60cb8602446… / archive 9223832977a1… source and image bindings; 6 same-side Syft/Grype bindings (9452 locations); target CVE-2026-126859 ABSENT including related IDs (one Chrome Medium CVE-2015-1239 and the 39 High overall retained, no suppression, no zero-vuln claim); selected non-OCI package/license/attribution/supplier deltas ONLY the exact SDK 0.2.0->0.2.1 and Chrome 157.0.8103.50->157.0.8103.78 version locators; all six extracted license text sets equal the 9f head. Proofs (control folder): root-65e0-six-image-structural-audit.json 6007B SHA 9c17722695979863b69d28298ffeff84c593e572191409fd1750f0d0b71a443a; root-65e0-qualified-sdk-browser-and-source-bindings.json 11022B SHA 321e0bede0614c9f1ccea42bf5fd18ff6e29edd87b0e94d10d5b44571b2f0b4b. Critical test inputs verified byte-equal to the 14f6 head: media-publication 2741L/105659B SHA ab4f9b1b5d59…, frozen-review-parity 3258L/131933B SHA a0801f02d267…, test_real_human_accept 3612L/153083B SHA cf199671… (three unconditional acceptCycle calls at lines 938/1664/1876); the local 384 full run's backend input is unchanged. The current head is fully green as observed; the report-only SELF commit pushed with this report may trigger fresh CI (truthfully pending at wire time permitted; strategy waits/reviews). No merge or product acceptance is claimed.
- ROOT CAUSE CONFIRMED (not a source guess): pinned foundation
  agent-cow-postgresql 0.2.0 agentcow.get_cow_dependencies pairs
  composite-FK columns by constraint name only (no ordinal mapping);
  product 042 composite FKs page/navigation_item/redirect (site_id
  uuid, locale text) -> site_locale(site_id uuid, tag text) yield the
  cross-pair equality uuid=text in the dynamic EXECUTE -> 42883 inside
  reviewer.dependencies() whenever a session has pending
  page/navigation_item/redirect changes (physical site_locale_changes
  existence suffices). Bounded owned-runtime probes under the exclusive
  ::1:5432 lease reproduce it through public APIs only (editor
  slaif_page_update route: actual operator uuid=text extracted from the
  caught error; L2 agent slaif_agent_page_update route:
  class=UndefinedFunctionError sqlstate=42883,
  signature=operator:uuid=text); the real Compose input is the e2e.sh:113
  pending 'Compose preview overlay' page in the shared HUMAN preview
  workspace accepted by cycle3 (spec L1876). Evidence: /tmp/oap-083-10-a-
  control/primary-42883-cause-confirmed-evidence.txt. Fix/qualification
  path awaits ROOT selection; no architecture or pin change initiated.
- All required green at publication: YES — CI 43408367550 on 65e0f162f7762c911fc116a58e64b31be3ed95b0: 30/30 check runs SUCCESS (20 named/app + 10 actual PG children), no failed/missing/pending, observed terminal 10:34:14Z; CodeQL 43408367543 SUCCESS. Compose full 19 PASS + six pairings + full smoke; Supply-chain fresh six images Crit 0 / ignored 0 / exceptions 0 (2905 total findings: 39 High / 2686 Medium / 151 Low / 17 Negligible / 12 Unknown); CVE-2026-126859 absent including related IDs.
- Report-only commit may trigger fresh checks; strategy verifies SELF.

## Local setup / dependencies

- uv 0.12.5 frozen environment (no lock changes); Node v24.22.0 + pnpm
  11.22.0 via corepack-cached exact versions (--frozen-lockfile honored,
  no ignore-scripts); owned disposable PG18; pinned
  markdownlint-cli2 0.23.2 and transient Mermaid CLI 11.16.0 per repo gate
  definitions; no NEW production dependencies — only version changes of
  two existing qualified artifacts (foundation agent-cow-postgresql
  0.2.0 -> 0.2.1 from the public registry, Chrome for Testing pin
  157.0.8103.50 -> 157.0.8103.78), each under a prospective own-mistake
  source correction with byte-exact supplement transcripts; no private
  SDK dependency introduced (the media closure work uses only existing
  product interfaces).
- Actual setup/tooling deviations, retained honestly (no compensation
  cleanup of old evidence):
  - 11:54..12:15: five containers + their network were removed from the
    foreign host engine (recorded in /tmp/oap-083-10-a-impl/docker-
    boundary/engine-evidence.json; mounts/storage/prior-workload impact
    UNKNOWN). That foreign host engine was NOT an approved owned test
    engine for this round; the specified actual contacts/mutations and
    UNKNOWN impacts are preserved above (incl. the 12:18:07 containerd
    restart and the 22:55 peer default `ps` scope incident); no
    compensating cleanup was performed, and no blanket never-used claim
    is made.
  - apt NEEDRESTART handling actually restarted containerd at 12:18:07
    (workload impact UNKNOWN); a foreign PG18 (main, 5433) was started.
  - 22:55: a peer default-Docker `ps` / home / tool-cache / private-SDK
    source read was a read-only scope incident — no mutation observed, no
    impact claimed, corrected in follow-up.
  - npx wrapper incident: a `printf >` write followed the current
    /tmp/oap-083-10-a-impl/bin/npx symlink into the OLD 083-8-h tool tree,
    creating a 147B wrapper there (9afee951, 23:41:10); the current
    private wrapper was atomically replaced in impl/bin; the old-tree new
    file is retained, no compensating cleanup, no old-tree approval or
    impossible reconstruction claim.
  - node-install-1 corepack absence (127), prep-1/2 npx absences
    (check_mermaid native 1), full-1 unconfirmed launch, a3 wrapper-1
    afterfact copy, and all retained pre-fix failure runs are recorded
    above with their exact causes.
- Scoped private QA (peer) uv frozen all-groups/build evidence is credited
  where used; the current CI package builds are separate subjects.

## Documentation

- docs/API.md: media isolation + public route contract, private byte
  response cache scoping, PATCH (pending COW metadata update) vs reference
  DELETE (tombstone) accuracy.
- docs/SECURITY.md: unserved-orphan qualification (digest with no canonical
  public authorization), private/staging/artifact denial vs approved
  anonymous public digest reads, immutable storage directories not exposed
  as static (byte responses edge-proxied to the media service).
- docs/TESTING.md: fresh-pending public 404 bound to previously-unpublished
  digests; 077 privilege module 076 historical phase; ten selected media
  modules unfiltered in EACH Group B child (five executions); media-
  publication project scope vs the six stable pairings supplied by the
  freeze-parity project; migration preservation module attributed to its
  actual 076->077 normal upgrade test.
- docs/OPERATIONS.md, README.md, oap/INCREMENTS.md, oap/MVP-PROGRESS.md:
  media isolation behavior and 083-8-z closure corrections at all four
  mutable sites.
- docs/SUPPLY_CHAIN.md, docs/DEPLOYMENT.md, docs/CONFIGURATION.md,
  docs/SECURITY.md, docs/LICENSE_POLICY.md, README.md: Chrome for Testing
  157.0.8103.78 current pin with truthful 083-10-a attribution (dated
  083-8-v .50 history preserved), archive SHA-256 and scan-coverage
  statements; docs/DATABASE_BOOTSTRAP.md current marker paragraph
  corrected to the actual current Alembic head (077_001);
  docs/FOUNDATION_INTEGRATION.md current rows only (historical 0.2.0
  sections preserved); docs/TESTING.md prospective 0.2.1 note
  (historical 083/8 claims preserved); AGENTS.md and ARCHITECTURE-for-
  agents.md current pin + prospective maintenance notes;
  oap/strategic-instructions/ byte-exact supplements (foundation 0.2.1
  qualified source correction; Chrome 157.78 security source
  correction).

## Safety and scope confirmations

- Unrelated files changed: no (all 91 paths serve the order or the
  qualified corrections; grouping above).
- Production secrets accessed: NO; production systems accessed: NO.
- Required tests skipped/not run: no local skips; remote CI states as
  observed (never passed while pending).
- Scope deviation: the order's planning footprint (4..8 test paths,
  1000..2500 substantive lines) was exceeded in test-heavy size (51
  test/evidence/policy/tooling paths, 7635 gross lines at 65e0f16) and
  was explicitly reassessed in the ROOT packets during the round (incl.
  the cumulative 91-path / 9475-gross exception covering the qualified
  foundation 0.2.1, the Chrome .78 Critical repair and the fixture
  closure); the bounded Group B 15->30-minute child budget
  correction was an authorized orchestration correction for the expanded
  exact selection, not a test or gate weakening. No non-goal touched:
  no D5/complete-083 claims, no byte-GC, no new routes/roles/deps/
  manifests, no product read-model feature.
- Extra objective PR: NO; coding-agent merge: NO.
- Activated order/active edited: NO (committed byte-exact).
- Report commit changes only this report: yes (verified staged diff).

## Known limitations / blockers

- A4/A8 public-boundary runtime (fresh Compose through public NGINX, 19
  Playwright projects, six stable pairings, six images) is supplied by the
  current CI Compose job; the 23d0 run failed at review-surface; the
  b84595a run passed through accept-lifecycle then failed at discard-
  lifecycle; the d57e5c1 run passed through discard-lifecycle then
  failed at media-publication (boolean-concat oracle) with Supply-chain
  failing on the withdrawn .18 pin; the e6aa904 run failed at
  policy/supply-chain before APT and at media-publication workspace-
  status 404; the 73e4c3e run passed review/freeze/frozen-parity/
  accept/discard with Supply-chain fresh six images (0 Critical/40
  High) and failed at media-publication line 241:38 FREEZING helper
  timeout (unpinned version_facts seed, fixed in 87d03ea); the 87d03ea
  run PASSED through discard-lifecycle then FAILED at media-publication
  with the actual accept-job terminal failure
  REVIEW_JOB_STALE_AT_BUDGET (stage/cause unknown after container
  cleanup; bounded diagnostic-only logging pushed in 831dcf9 as the
  first witness - no source guess claimed as root cause for 87d0); the
  831dcf9 run (28/30) captured that witness and the 9f6b3e8 run (29/30,
  Compose only) confirmed the branch; cause identified as the foundation
  SDK composite-FK 42883 (evidence: primary-42883-cause-confirmed-
  evidence.txt), corrected by the qualified foundation 0.2.1 in
  14f6f77; the 14f6f77 run then PASSED all 19 public-NGINX browser
  projects incl. media-publication and the A4 six pairings before
  failing the smoke agent-browser phase (silent exit 1, workspace
  lifecycle — repaired in 33dddac) with Supply-chain failing the
  Critical Chrome CVE-2026-126859 (repaired in 65e0f16); the 33dddac
  run failed at the PREVIEW project (0340 resolver interference —
  repaired in 65e0f16 seed timing) with a second Supply-chain failure
  (exact diagnostic unread); qualified partial evidence retained at
  every earlier head; the 65e0f16 run PASSED 30/30 with the fresh full-
  19 public-NGINX evidence and the patched-image six-image scan (Crit 0
  / ignored 0 / exceptions 0; CVE-2026-126859 absent including related
  IDs); local static source green on the final subject
  (prettier explicit 0; typecheck/lint wrapper 0 with the direct
  natives piped to tail and unretained — the current CI re-proves them;
  one prettier attempt over the unsupported .sh driver file failed as
  tooling and is retained).
- Local FULL PG18 DB credit is qualified exactly as recorded (pre-typing
  383 PASS subject + reviewed 3-test-only delta equivalence + 8 focused
  typed PASS); CI is the selected-regression validation (A 85 / B 45+Q+M),
  not a duplicate full suite.
- Review-surface runtime for the repaired fixture expectations
  (b84595a) PASSED all 3 cases in the failed b84595a Compose job and
  again in the d57e5c1, e6aa904 and 73e4c3e Compose jobs; discard-
  lifecycle runtime for the d57e5c1 repair PASSED in all three later
  jobs; media-publication runtime fully PASSED in the 14f6f77 Compose
  run and again in the 65e0f16 Compose run (three real cycles, hostile
  tail, audit bindings, final public checks — the full 19-project suite
  green on 65e0f16).
- Tooling deviations above (containerd restart, foreign engine incident,
  npx wrapper) have unknown workload impacts recorded; no compensating
  cleanup performed.

## Recommended strategic follow-up

- 65e0f16 CI verified: all 10 PG children success, Compose public-
  NGINX 19-project suite fully PASSED including the media-publication
  project and the A4 six stable pairings, fresh Supply-chain six images
  with the Chrome 157.0.8103.78 pin (Crit 0 / ignored 0 / exceptions 0;
  CVE-2026-126859 absent), CodeQL success — 30/30 check runs SUCCESS as
  observed. The report is published atomically (report-only commit
  SELF, parent 65e0f162f7762c911fc116a58e64b31be3ed95b0); its push may
  trigger fresh CI, truthfully pending at wire time. Strategy/ROOT
  independently reviews and merges; no merge or product acceptance is
  performed by coding.
