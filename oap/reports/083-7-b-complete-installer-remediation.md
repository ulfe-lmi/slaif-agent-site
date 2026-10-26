# OAP Coding-Agent Report — 083-7-b

## Work order

- Identifier: 083-7-b (objective 083, increment 7); work-order file
  `oap/orders/083-7-b-complete-installer-remediation.md` (273L,
  SHA256 84a5477fc7c4b8563f8bd907bbf31b8c4aeef410227c8e2cfb17f24b318475fa),
  FULL-read; activated order 083-7-a
  (`oap/orders/083-7-a-remediate-certifi-installer-copies.md`, 358L,
  SHA256 3937f725521c780d7b63af2af13ef1fab38262cf000e461117ffba3597e939ff)
  FULL-read and preserved unchanged.
- PR mode: AMENDED_EXISTING_PR (SAME PR 111, no new PR).

## Status
COMPLETE (all B1-B8 local gates executed and evidenced at frozen I_b; fresh final-S CI honestly PENDING at publication per B7 - strategy waits/reviews before merge)

## Executive summary
Completed the deferred certifi installer-copy remediation at one frozen
implementation commit: (1) exact certifi 2026.10.19 test-lock target with
byte-identical LICENSE; (2) measured runtime pip installer-copy removal from
the backend image (pip package + dist-info, ensurepip bootstrap wheel, pip
command links) with builder/base/interpreter/stdlib/ensurepip-module/app-venv
preserved; (3) fail-closed merged-filesystem guard on BOTH finalize and
validate-bundle, completed with the preserved raw-directory-header unit and a
synthetic TAR -> collector -> guard adapter (B4); (4) same-collector BEFORE vs
AFTER full-coverage comparison proving exactly the intended 547-entry removal
and nothing else (B5); (5) fresh serial local gates at the frozen I: exact
ALL31, supply + CI lint, fresh I backend build + isolated SYSTEM/APP/FILES
probes, FULL 347 unfiltered integration on owned isolated PG18, literal WHOLE
slaif0835, LOCAL6 two-build six-image supply chain (B6); (6) docs reconciled
with accepted merge history and the finite a-report corrections (B8).
Original 600s frozen-review-parity timeout failure (postmerge main CI after
083/5 PR 107) cause remains UNKNOWN; this increment makes no new diagnosis of
it. Advisory 17 (certifi 2026.7.22) remains OPEN until root's postmerge
verification; no dismissal/suppression/closure claim.

## Authoritative GitHub state

- Repository: ulfe-lmi/slaif-agent-site; PR 111
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/111>, state OPEN,
  unmerged (merge performed NO by coding).
- Base branch main / accepted starting remote main
  `df307a955c5c39276fa34934395c7c2c1372ac1e`; head branch
  oap/083-7-a-remediate-certifi-installer-copies.
- Starting remote PR head at b activation:
  `e7b0c8255301641209f9361aa985c1d29b9aa480` (a report-only SELF, sole parent
  `a4eb2a759783fe4bdb2651561f54859ceb1bca7e`; exact handoff 05:16:48.731544Z,
  root independently verified 05:17:47Z).
- Implementation head SHA: b0538981eb70ca3593db71a54bddfb22d8f841a6
  (tree 431fa2eab08448f87956b9a43243fab6f5fd1578); pushed and remote-verified
  BEFORE any gate (remote PR head = I_b observed during this round).
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal derived via GitHub)
- Implementation commits pushed before report:
  `5000b099718ddff694bffca739b372e578612f02` (a activation: order + active
  exact bytes), `a4eb2a759783fe4bdb2651561f54859ceb1bca7e` (a implementation:
  five paths + notices), `e7b0c8255301641209f9361aa985c1d29b9aa480` (a
  report-only SELF, immutable), `b0538981eb70ca3593db71a54bddfb22d8f841a6`
  (b implementation: raw-DR unit, TAR->collector->guard adapter, 083/7 docs,
  b-order + active exact bytes). Report parent = implementation SHA.
- New PR this turn: NO. Amended existing: YES. Merge performed: NO.
- Related PRs: 107 (083/5) and 110 (083/6) are OAP accepted/merged history
  (not bot PRs); 109/108/105 are held bot PRs, untouched.

## Changes made
### Cap history (honest; no retroactive approval)

- a WIP crossed the five-path 500-gross cap to 502 before prospective
  authorization; root measured the violation at 04:50:15Z (Docker 8 + policy
  2 + tests 365 + tool 121 + lock 6). STOP; full unapproved WIP preserved
  (private /tmp/oap-083-7-a/preserved-502-20261026T045655Z/, patch
  SHA256 704b6e82f4c83c28294273dc2635d6014f4e9b1e45170f3de34b0afcb98eb909).
- Coherent recovery: the 36-line raw-directory-header test work unit
  (test lines 834-849 + 851-870) was deferred losslessly as
  /tmp/oap-083-7-a/future-b-test-patch-20261026T050229Z.patch (WITH Z;
  earlier forecast/manifest cited the nonexistent 050229.patch without Z -
  explicit erratum, no invented file); restored a footprint 466 + notices 2.
  Root independently byte-verified the restoration (only the 36 lines
  deferred; other files identical).
- b prospective hard cap 550 (five implementation paths only, replacing 500
  from b activation); actual final gross 524 (below cap, no crossing, no
  packing/deleting proof, no retroapproval implied).

### Cumulative grouped diff (uniform `git diff --minimal --numstat` vs
`df307a955c5c39276fa34934395c7c2c1372ac1e`), implementation identities
EXACTLY FIVE, gross 524 <= prospective cap 550:

- `services/backend/Dockerfile` 8/0: one RUN removing the measured pip
  package + `pip-25.0.1.dist-info`, the ensurepip bootstrap wheel
  `ensurepip/_bundled/pip-25.0.1-py3-none-any.whl`, and
  `/usr/local/bin/pip`, `pip3`, `pip3.12`; comment records scope (runtime
  image only; builder/base/interpreter/stdlib/app venv unchanged; ensurepip
  module retained).
- `supply-chain/policy.json` 1/1: ONLY the license_metadata_reviews key
  `pkg:pypi/certifi@2026.7.22` -> `pkg:pypi/certifi@2026.10.19`, same
  approved MPL-2.0 license and source; all other reviews/allowlists/scanners/
  exceptions unchanged.
- `tests/supply_chain/test_evidence.py` 387/0: a-round guard units retained +
  restored deferred 36-line raw-directory-header unit (byte-identical to the
  preserved 502-state patch unit; patch
  `/tmp/oap-083-7-a/future-b-test-patch-20261026T050229Z.patch`,
  SHA256 0a1fbaae9d49b228cac0e280b2cf102b67608dbbeb17442e5f5d8c25216838d8) +
  B4 synthetic-TAR->collector->guard adapter cases (healthy + negative
  entries reused, no duplicated case corpus; explicit directory case;
  fail-closed unknown kind).
- `tools/supply_chain/evidence.py` 117/4 (gross 121): fail-closed guard on
  BOTH finalize and validate-bundle; fixed backend manifest read
  unconditionally (no untrusted index path construction); image-name
  coverage / duplicate-apache rejection; initializer entrypoint anchor
  `/opt/slaif/bin/initialize-local-secrets.py`; ordered vendored-certifi
  fragment rejection across covered scopes (opt/slaif, SYSTEM
  site-packages, ensurepip, bin); preserved FILE exact-prefix and DIRECTORY
  normalized exact-parent/slash-descendant matching (sibling lookalikes
  excluded).
- `uv.lock` 3/3 (gross 6): ONLY the certifi package block
  2026.7.22 -> 2026.10.19 (sdist + wheel url/hash/size/upload-time); every
  other package/global metadata byte-identical vs df307; foundation 0.2
  registry hashes frozen.
Docs EXACTLY THREE, gross 54 <= 200:

- `docs/SUPPLY_CHAIN.md` 43/0 (removal/guard/representation/attribution
  evidence + lower-layer/scoped-CA/security limits, no future claims).
- `oap/INCREMENTS.md` 5/2 (ledger rows with actual gh-verified merge facts:
  PR106 `4bf74fdc8e74323045a7f8830cf393493e75fe0d` 2026-10-18T10:17:47Z,
  PR107 `f35ec75319afd966d02ee2b7b8cb1db1eb4cd144` 2026-10-25T20:30:05Z,
  PR110 `df307a955c5c39276fa34934395c7c2c1372ac1e` 2026-10-26T03:57:48Z).
- `oap/MVP-PROGRESS.md` 2/2.
Generated attribution EXACTLY ONE, 2 <= 10:

- `THIRD_PARTY_NOTICES.md` 1/1: certifi row 2026.7.22 -> 2026.10.19
  (PyPI / development, MPL-2.0, same source URL).
Increment transcript identities FIVE: a-order 358, a-report 341, b-order 273,
b-report (this report), active 1/1 (`083-7-b\n`, 8 bytes,
hex 3038332d372d620a). Final PR path count 14. No migrations, generated
contracts, workflows, other dependency/attribution/policy identities.

## Files changed
See grouped listing above; complete cumulative numstat:

```text
1 1 THIRD_PARTY_NOTICES.md
43 0 docs/SUPPLY_CHAIN.md
5 2 oap/INCREMENTS.md
2 2 oap/MVP-PROGRESS.md
1 1 oap/active
358 0 oap/orders/083-7-a-remediate-certifi-installer-copies.md
273 0 oap/orders/083-7-b-complete-installer-remediation.md
341 0 oap/reports/083-7-a-remediate-certifi-installer-copies.md
8 0 services/backend/Dockerfile
1 1 supply-chain/policy.json
387 0 tests/supply_chain/test_evidence.py
117 4 tools/supply_chain/evidence.py
3 3 uv.lock
```

plus this report only in the SELF commit.

## Acceptance-criteria evidence
### B1/K1 - exact certifi 2026.10.19 target

- Exact non-yanked PyPI certifi 2026.10.19: wheel 136464B SHA256
  42d35340cc5b9ba78e818ddbff0c5b1c2b779de448a340fd1b989f5fa8670e1b; sdist
  137598B SHA256 035c1e85572b141bf1c3a3eff0e33a8eb74917522f2559075ff8d2fea780a1ae
  (root-qualified; a-round K1 verification receipts under
  /tmp/oap-083-7-a/).
- Old/new wheel and new sdist LICENSE byte-identical 989B SHA256
  e93716da6b9c0d5a4a1df60fe695b370f0695603d21f6f83f053e42cfc10caf7; exact
  approved terms and target 19 kept (no silent move to latest 23); no new
  license family/exception.
- All-other-lock equality vs df307: ONLY the certifi block differs (numstat
  3/3; verified at frozen I by `uv lock --check` native 0 in ALL31 CMD01 and
  the cumulative diff above).
- Preserved a failure: 04:24:48Z package-version JSON query KeyError
  (releases key) then 04:24:57Z corrected package query native 0.

### B2/K2 - retained BEFORE evidence (no repeated baseline)

- Retained original TAR `/tmp/oap-083-7-a/baseline-20261026T040915Z/
  baseline-rootfs.tar` 120216576B SHA256
  cb1d66aa468e243efb5c7485e0e82b0684c62357c9829a22ebecb47be9b1e856 (re-verified
  this round); 641 inventory entries checked against original TAR
  kind/mode/link/hash (root receipt
  /tmp/oap-083-7-b/strategic-K5-expected-measured-removals.json: exactly 547
  unique expected removals = pip 533 + dist-info 10 + commands 3 + bootstrap
  wheel 1).
- Cached 083/6 backend image
  `3bf5e87ac0345b6111a30d24a977d6aae89efd4d059bc2a587a2159e18325db1`: actual
  manual image digest binds the content; OCI revision label = local. Source
  attribution is the controlled frozen build cwd/argv/observations plus
  root-proved builder-input equality by the immutable I24a->f35->df307 tree
  edges (receipts /tmp/oap-083-6-b/strategic-I24a-f35-A420-exact-carry-chain.json
  and /tmp/oap-083-6-c/strategic-c-F1-F3-cumulative-review.json) - NOT a
  literal-I rebuild label; not claimed rebuilt at df307.
- Errata retained: original v1 inventory
  (SHA256 79ddd806aa38805addd2b7a3cd9914bf72bb5486a095f29a37280a46bb18573e,
  245601B) had wrong `system_pip_distinfo.root` label
  (usr/local/lib/python3.12); corrected v2
  (SHA256 8a259dc000d27e5a78dea75b07a3985a1e818c7723a4a931237fd1e26b97c96f)
  derived metadata-only from the same retained TAR-derived JSON; the 10 entry
  paths/modes/hashes were always correct; erratum note
  /tmp/oap-083-7-a/baseline-20261026T040915Z/inventory-erratum-note-20261026T042434Z.txt.
- Actual isolated BEFORE pair 04:16:23..26Z native 0 both (system + app,
  explicit -I, at immutable 3bf, before tracked edits); older 04:12Z
  non-isolated positive pair retained as LIMITED (invoke -c without -I).
  No new before export/download/probe this round.
- Two before copies = unpacked SYSTEM `pip/_vendor/certifi` and the SAME
  package inside `ensurepip/_bundled/pip-25.0.1-py3-none-any.whl`; no actual
  top-level `ensurepip/_vendor/certifi` TAR entries exist - that path is a
  synthetic negative case, not a third measured copy (a-report correction,
  carried here).
- Preserved native inspection/probe failures from a (see Failures).

### B3/K3 - fresh I build + isolated after probes

- Fresh backend build at frozen I_b:
  `sha256:19e4ffcd1fdac874b7ad599ee4798f96a31cdcc014469e60b65f98dd24f78ea7`
  (created 2026-10-26T05:41:19.617602309Z; tag slaif0837b/i-b053898; build
  native 0; first attempt tag-uppercase native 1 preserved).
- Three strict probes, all `docker run --rm --network none --read-only`
  (no mounts/credentials/network/services), base64-embedded scripts, all
  native 0 at 05:42:21..26Z bound to actual image ID 19e4ffcd (receipts
  /tmp/oap-083-7-b/k3-I-b053898/; probe-summary.txt):
  - SYSTEM (`--entrypoint /usr/local/bin/python3.12 ... -I -c ... system`):
    interpreter_prefix /usr/local; isolated pass; find_spec pip absent PASS
    with SPECIFIC `importlib.metadata.PackageNotFoundError` for PIP
    (specific absence, not catch-all); find_spec ensurepip present; find_spec
    ssl present. Result PASS.
  - APP (`--entrypoint /opt/slaif/.venv/bin/python ... -I -c ... app`):
    interpreter_prefix /opt/slaif/.venv; isolated pass; 5 actual module
    imports pass (slaif_agent_site, agentcow.postgres, fastapi, asyncpg,
    uvicorn); foundation 0.2.0; `find_spec_certifi_app` independently
    recorded false (separate observation, not the specific-assertion
    target). Result PASS.
  - FILES (`--entrypoint /usr/local/bin/python3.12 ... -I -c ...`):
    6 installer paths ABSENT (pip, pip-25.0.1.dist-info, pip, pip3, pip3.12,
    ensurepip bootstrap wheel) / 6 anchors PRESENT (ensurepip/__init__.py,
    python3.12, app venv python, alembic.ini,
    bin/initialize-local-secrets.py, migrations).
- Root receipts: strategic-K3-selected-image-after-probe-review.json and
  strategic-actual-K3-K5-executor-call-index.json.
- LIMIT: OCI revision label local; source attribution = controlled frozen
  build cwd/argv/observations. RUN rm whiteouts do not purge historical
  lower OCI layer bytes (lower-layer bytes remain). No OS/browser trust-store,
  all-files-absence, or global-TLS claim.

### B4/K4 - permanent guard on BOTH finalize and validate-bundle

- Fixed backend manifest read unconditionally (guard never runs against an
  untrusted index-constructed path); image-name coverage + duplicate-apache
  replacement failure; initializer entrypoint anchor
  /opt/slaif/bin/initialize-local-secrets.py required; ordered vendored-
  certifi fragment rejection across covered scopes (actual
  `/_vendor/certifi` fragments; standalone certifi is NOT that fragment;
  standalone app dependency allowed; no all-wheel prohibition); measured
  covered scopes opt/slaif, SYSTEM site-packages, ensurepip, bin; no
  missing/renamed/forged-symlink-directory/vacuous-success cases; tampered
  backend manifest + recomputed checksums rechecks semantics; directory
  spelling: genuinely different raw directory x vs x/ headers (TarInfo.addfile
  normalizes DIRECTORY names, so identical headers via addfile are NOT proof -
  the actual raw headers are asserted to differ; source anchors: host
  CPython 3.14 tarfile.py get_info line 1035 / frombuf line 1354, UV
  Python 3.13.14 tarfile.py get_info line 1028 / frombuf line 1347).
- B4 adapter: backend_tar_doc serializes existing fixture entries to a
  synthetic TAR then collects through rootfs_manifest into the guard (reuses
  all current cases, no duplicated case corpus, no new index/schema/fields,
  no 100-line DRY refactor); pre-freeze WIP corrections landed and retained:
  fixture member size/payload consistency (payload b"synthetic-entry",
  member.size=len(payload); earlier hardcoded size 12 vs 15B payload
  truncation fixed), explicit directory case, fail-closed unknown kind.
  Root peer adjudication: B4 sound; manual-fixture size12/hash15 note
  non-blocking; no refreeze required.
- Native results at frozen I_b: `uv run --frozen pytest tests/supply_chain`
  -> 43 passed, 27 subtests passed in 0.78s, native 0 (SUPPLY_PYTEST_EXIT=0);
  `uv run --frozen ruff check services/backend tests/repository
  tests/packaging tests/supply_chain tools migrations` native 0;
  `uv run --frozen ruff format --check` same scope native 0 (351 files).
- Preliminary a-round units do not satisfy final-source gates; final I_b
  units above do (preliminary precommit 43+27 retained as history).

### B5/K5 - same collector BEFORE vs AFTER (full coverage)

- SAME collector `tools.supply_chain.evidence.rootfs_manifest(..., "backend")`
  at frozen I on: BEFORE retained original TAR (cb1d66aa..., 120216576B) and
  AFTER fresh export of image 19e4ffcd via owned unstarted container
  f97859b01aaca0bbd70670dd6a179475330488f01a9f90dcdbd11673b06e46a6
  (docker create/export/remove; EXPORT_EXIT=0):
  /tmp/oap-083-7-b/k5-I-b053898/after-rootfs.tar 112207872B SHA256
  2a59512f265401c6ee0882067141ae24467d63931a653e1d4b2c1e011a8f7828.
- Full-coverage result (k5-comparison.json,
  SHA256 45336855dc796395c3dca83f7e12a95539471345da43438889e02e598601f1e2):
  before 3428 unique covered paths -> after 2881 (= root's expected
  3428 - 547); only_in_before = EXACTLY the 547 expected removals;
  only_in_after 0; changed 0 (kind/mode/link/hash/size); result PASS.
  2858 opt/slaif paths + 23 system paths preserved; 27 dist METADATA/
  RequiresDist runtime venv graph equal (root independent review receipt
  strategic-K5-independent-full-TAR-and-venv-graph-review.json).
- Observed AFTER is the proof; root's expected set is corroboration only.
- LIMITS: scoped (covered scopes) not universal CA absence; normalized vs
  raw OCI identity explained; APP production certifi absent before; patched
  19 belongs to the dev/test lock (no APP dependency upgrade claim).
- Full fresh two-build/six-image reproducibility, inventory, license and
  vulnerability policy: LOCAL6 gate below (no earlier local security-gate
  carry).

### B6/K6 - serial local gates at SAME frozen I_b
All local runtime gates SERIAL at frozen I_b; clean isolated Git worktree
/tmp/all31-083-7-b-I (HEAD b053898 / tree 431fa2ea, exclude ONLY exact human
.codex/, CODEX-SESSIONS.md, codex.sh, left untouched); private parent umask
0077, literal gate child explicit 0022; immediate native child exits captured
before pipes/echo; every failure retained.

- ALL31 (exact 31 a-order argv/order, normative; no selection/timeout/plugin
  weakening): 31/31 native 0, overall 0, 05:31:56.011Z..05:37:47Z
  (summary.txt; full raw snapshot file EXACT 12 lines / 3 blocks
  START, PRE-COMMANDS, END; all status EMPTY / same b053898 / tree 431fa2ea).
  First launch unlaunched outer-redirect native 1 preserved as setup failure
  (shell redirection evaluated before inner mkdir; not concurrency).
  Root receipt strategic-ALL31-final-I-independent-review.json.
- Supply + CI lint: see B4 (native 0 at I_b).
- FULL 347 unfiltered backend integration on owned isolated PG18:
  PG container slaif-pg-0837b
  (1d6d5a68dab94eabdc1ad2f1f4a8009445141e127cb6e6bf16933ba757eb8657,
  postgres:18.6-alpine3.23 image sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f,
  created 05:45:49.777975028Z, NO host port, fake qualification credentials
  redacted in provenance).
  Runner c5e5e956290b1704d9c5c94345bf33597dac1e3b9f42200c49bad777f135ea03
  (started 05:50:08.576036711Z), base python:3.13-slim
  sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f,
  `--network container:<pg>`, read-only mounts of uv 0.12.5 binary + uv
  cache, rw worktree mount at same path. Actual test interpreter Python
  3.13.14 (uv-managed; pytest 9.1.1) - distinct from runner base image env
  PYTHON_VERSION=3.13.16 (kept distinct in evidence).
  Exact argv: `uv run --frozen pytest services/backend/tests/integration`
  with reporting-only additions `-rA --tb=short` (unfiltered selection
  preserved; no test filter).
  RESULT PASSED: collected 347 items; 347 passed in 3647.81s (1:00:47);
  0 failed / 0 error / 0 skipped / 0 xfailed / 0 xpassed (347 unique
  PASSED lines in the -rA section; 7 parameterized IDs contain spaces, all
  distinct). FULL_CHILD_EXIT=0 (native pytest child, immediate capture, no
  pipe); container State.ExitCode=0, StartedAt
  2026-10-26T05:50:08.576036711Z, FinishedAt
  2026-10-26T06:51:01.015613113Z, status exited, not OOM-killed.
  Coherent RC7 present and PASSED:
  test_075_001_round_trip_exact_restore_and_locked_materializer,
  test_076_001_round_trip_retained_v2_and_exact_restore (retained-v2-first)
  and test_075_001_v1_only_downgrade_roundtrip_disposable (separate v1-only);
  20 freeze_review_snapshot + 9 frozen_review_parity records PASSED.
  Raw START retained: HEAD b053898 / tree 431fa2ea / unfiltered status COUNT
  0 (launch.log FULL_WORKTREE_DIRTY_START=0; original
  live-provenance.json had an inverted-bool dirty_start field - original
  preserved byte-identical, explicit corrected erratum
  live-provenance-corrected.json, no new START invented). Actual raw END
  (finish.log, one-shot finalize): HEAD b053898 / tree 431fa2ea /
  `git status --porcelain=v1 --untracked-files=all` 0 lines (fully clean).
  Finalized log: 51689B,
  SHA256 a90bc6cd247aff6e2fb750be66a52a6078e93e2c544d3188d173d71a08b8a96c
  (root independently matched).
- WHOLE literal `sh tools/compose/smoke.sh slaif0835`:
  launched 06:54:47Z (literal child START; after FULL terminal 06:51:01Z)
  under owned session; hard serial prechecks passed (FULL container c5e5e956
  terminal/native 0; frozen b053898; no pre-existing slaif0835 containers;
  parent umask 0077, child explicit 0022).
  Setup failure retained: first harness launch (06:53Z, nohup under an exec
  session that terminated immediately) disappeared BEFORE any WHOLE child
  executed; launcher-native.txt 0B, launcher native status UNKNOWN (never
  captured), no log/sidecar produced; disappearance cause only suspected
  (process-group teardown) and not independently proven; only the half-
  created 0B umask artifact removed to permit the clean owned-session
  launch; this is a setup failure, NOT a failed WHOLE test attempt (no
  rerun, no zero-failure label).
  RESULT PASSED: 06:54:47.210Z..07:13:05.266Z, WHOLE_NATIVE_EXIT=0
  (07:12:55.684222Z). 40 `browser-e2e: PASSED project` records across 19
  projects (compose-e2e OK projects=19: setup, governance, preview,
  preview-filtering, stable-devices=6, agent-sessions=2,
  agent-workspace-puck=2, freeze-review-snapshot, review-surface,
  accept-lifecycle, discard-lifecycle, media-publication);
  frozen-review-parity-six-stable-pairings PASSED (phase=cleanup
  action=close, elapsed=139189ms - the historical 600s-timeout stage
  completed well within budget locally; original cause of the CI
  timeout remains UNKNOWN); packaging `Ran 49 tests in 0.479s OK`;
  media-e2e OK (edge=nginx upload=validated-private-read=byte-identical
  finalization=public-read=byte-identical immutable-cache=verified);
  public-agent-news-edge OK (canonical-isolation=byte-identical,
  html=uuid-token-flight-free); recovery: browser-artifact-recovery OK
  byte-identical, browser-worker-secret-recovery OK
  (missing=not-ready canonical=available restored=healthy),
  browser-signing-recovery OK (same), control-readiness-fixture OK
  (mount=isolated identity=exact failures=6 recovery=clean),
  render-locator-recovery restored render=healthy web=healthy
  nginx=healthy; footer compose-smoke OK (footer proof is the actual
  selected preview
  global-regions-render-canonical-defaults-and-editor-save-is-preview-scoped
  contract record with its source assertions - no invented separate
  literal footer OK marker).
  Fresh-container proof (watcher, 39262B): INITIAL project containers
  created 06:55:50-51Z for this WHOLE (none pre-existing, hard-verified);
  later actual recreations during the recovery stage carry later Created
  values retained in the same watcher file (container IDs/created values
  preserved, initial creation kept distinct from later recreation); actual
  resolved image IDs incl web: backend services
  sha256:3f084222ad90392b90a889b6e9bc23413d0e1396c06e7eca9ea5143002428ba3,
  web sha256:eefc9b0080253f2670b7ac39b79ef2ea03bd89945206c781f20f60cc91190cec,
  browser-worker sha256:61918b31f88a8c363c0e78a94968860e63bee5ec8ccfa6cca86d7dceb7ad9fbb,
  postgres sha256:368a3e0112da6ab5ef4c814811a59b9178b415eba96b66c3d02a95b8b53be310
  (nginx and remaining services in watcher file). Finalized log 64305B
  SHA256 60fa93d551770d91cc7f80539133c28db5924f4f88027767b847bfbcab9752e8;
  child umask 0022 recorded; parent 0077; raw start/end HEAD b053898 /
  tree 431fa2ea, clean excluding exact human3.
- LOCAL6 `GITHUB_SHA=b0538981eb70ca3593db71a54bddfb22d8f841a6 sh
  tools/supply_chain/run.sh /tmp/oap-083-7-b/local6-I-b053898/
  evidence-Ib-run1` (child umask 0022 / parent 0077):
  RESULT PASSED, pipeline native exit 0, 07:13:40.534Z..07:41:13.988Z
  (27.6 min). Two builds x six images (first/second); reproducibility OK
  (python-artifacts=2, next-build-id=d9d59585a08719fc301a29ec47f94e42,
  browser-output=source-contract). Actual six image IDs: backend
  sha256:db29669566104bfe954a2492dbbd045bdec851f36f31ba3f90f7ce6ff008000d,
  web sha256:7969a111e4f711fccf20a7157ea6f14312ffe0035c2ced8c9ca0c7ee1e7f1613,
  browser-worker sha256:0dc93f026b23dd8359ce90e92e009f73a242f02e70a8a8fb025e2219baa7a7e8,
  nginx sha256:c2d7c261923aeae3a3f5fcd1f52d23ff717520207875952973edd18acc073c2a,
  apache sha256:86b0e8b9e24fc6d9e10d71919898590edabc8da6099f28e0451c000ea75c5cbe,
  postgres sha256:1b8213303707087fd0dc83df7e756f77a4df02e4e054fccd74cb21fc311d7806.
  Pinned immutable scanner images: syft v1.51.0@sha256:678bfa565b60f747aac0f8e964fe5588a24445b8d0a480e91f6efd70020dfbb0,
  grype v0.117.0@sha256:ddf9e9f204049f3a4a0955ef70873cabab6a31432125ad4f20a490b54950a253;
  FRESH Grype vulnerability database updated to latest version in-run
  (root-verified: fresh DB built 2026-10-26T06:38:44Z, checksum
  214b59fb..., age 1.04h - distinct from the older Oct-25 DB used by the
  bI CI artifact).
  Scans (six Grype scan JSON + six text renderings over 6 unique images,
  not 12 independent scans): ALL six
  `gate: PASS (zero unexcepted Critical)`, Critical 0 x6, Critical
  exceptions 0 x6; raw `ignoredMatches: []` verified present in all six
  scan JSONs (not inferred from absent text lines); High 19 total across
  images (0/1/4/0/7/7, all labeled review evidence - inherited population;
  root's independent preliminary artifact review of the bI ZIP: 53
  checksums, 6 Critical 0, no ignored, exceptions EMPTY, 19 High same as
  110, six pip-related removals 5 Medium + 1 Low - preliminary only;
  final-S artifact required). supply-chain-policy OK; third-party-notices
  OK components=298; supply-chain-evidence OK images=6 critical=0 high=19;
  supply-chain-evidence-checksum OK; supply-chain-gate OK (guard
  finalize + validate on this evidence). Finalized log 106395B
  SHA256 8576e04c1e30f7991fff5a33d80c34a3e3a12ab0978d671e58beb3a7f0c266e0;
  raw start/end HEAD b053898 / tree 431fa2ea, clean excluding exact
  human3; chrome-for-testing 156.0.8078.47 zip sha256 verified in both
  builds; edge checks (apachectl -t Syntax OK / nginx -t) are existing
  configuration checks, NOT live Apache HTTP parity.
- Runtime/setup/cleanup/privacy: all routine setup executor-owned (no
  human setup/approval pause). Owned container dispositions (actual):
  FULL runner c5e5e956 retained STOPPED (Exited 0) as terminal evidence
  through and after the WHOLE precheck that inspected its
  terminal/native0 state; owned PG slaif-pg-0837b stopped
  2026-10-26T07:43:07Z (Exited 0) after all gates; read-only residual
  listing at 2026-10-26T07:42:59Z: slaif-runner-7b Exited (0),
  slaif-pg-0837b Up (pre-stop), NO slaif0835 containers and NO
  slaif0835/0837b volumes remained after the literal WHOLE teardown.
  No secrets in evidence (PGPASSWORD redacted in provenance); private
  evidence 077/0600.
- K3 build + probes and K5 comparison: see B3/B5 (serial, at I_b, before
  the browser/runtime gates).

### B7/K7 - fresh final-S CI (after S push)

- Required: FRESH all 20 required context names + all 10 actual PG14..18
  A/B children (unchanged five argv / 85+45 per PG / 15m budgets,
  aggregator always+needs), actual current CI Compose whole, six-image
  evidence artifact; strict 20934043 / current apps 15368 except CodeQL
  57789 / no bypass; no skipped/neutral/missing/failed/cancelled/pending
  substituted for success; fresh scanner Critical 0 / no ignored /
  exceptions EMPTY on the ACTUAL current six-image artifact; inherited High
  full 6-tuples compared against accepted 107/110 with legitimate removals
  explained (no invented counts or IDs); browser/CfT executable/archive/
  SPDX/Grype-input identity and all other existing pins preserved.
- SELF checks may honestly be PENDING at publication; root independently
  waits/reviews before merge. AT PUBLICATION: the fresh b-S report-only
  commit had just been pushed; its 30 fresh checks are NOT YET OBSERVED
  (honest PENDING - not predicted, not substituted by the current-I
  observation below).
- Current-I observation (NOT a b-S substitute): at 06:18:17.128Z, check-runs
  for I_b: 30/30 COMPLETED/SUCCESS (saved
  /tmp/oap-083-7-b/report/ci-observation-ib.json).

### B8/K8 - docs and finite a-report corrections

- Docs: as Changes made. Local `main` ref was initially inspected and found
  stale (214909); gh-verified actual merge facts then controlled the docs
  (not "never used" - corrected wording).
- Advisory 17 (certifi 2026.7.22, GHSA-6q48-6c7w-9gw2, open) remains OPEN
  until root's postmerge verification; no dismissal/suppression/manual
  closure or immediate-closure promise. Test-lock update and effective
  installer-copy removal are separate claims; OS/browser trust stores,
  other alerts, global TLS, and release remain unqualified.
- Finite a-report corrections (a report immutable and PARTIAL; no a-report
  rewrite): (1) CI observation placeholder "05:2xZ" -> actual
  call_a46a7319b404f3ca queried aI at 05:11:12.383Z, result
  05:11:13.023Z: 25 runs, 10 SUCCESS / 1 NEUTRAL / 14 IN_PROGRESS (historical
  observation, kept separate from fresh b I/S state; root PARTIAL direction
  preceded the 05:09:21Z implementation commit - no invented exact
  authorization time). (2) Two before copies clarification (synthetic
  negative, not a third measured copy) - carried in B2. (3) Local policy
  argv was `uv run --frozen python -m tools.supply_chain.policy validate`,
  not nonexistent tools/check_supply_chain_policy.py; notices argv same
  module with notices/--check. (4) Retained omitted failures: 04:24:48Z
  KeyError then 04:24:57Z corrected native 0; 04:34:18Z notices and
  notices --check native 1 for missing pnpm PATH while policy validate
  native 0; later corrected successes separately; initial a-report lint 23
  issues/native 1 then final SAME-file lint 0 at 05:16:01Z before
  publication 05:16:24Z. (5) Preliminary pytest piped through tail did not
  capture immediate child native status: marked UNKNOWN, not an all-native
  ledger or final-I run. (6) A2 native-0 checks preceded their 05:09:21Z
  commit: they ran on later-committed identical bytes, not freshly at I;
  version proof cites the actual semantic Version call and exact artifact
  metadata, with no nonexistent root execution attributed.

## Local verification
All commands executed at frozen I_b unless noted; exact argv per ALL31
summary.txt (31/31 native 0, overall 0).

- CMD01 `uv lock --check`: PASSED native 0
- CMD02 `uv sync --frozen --all-groups`: PASSED native 0
- CMD03 `uv run --frozen ruff check services/backend tests/repository tools`: PASSED
- CMD04 `uv run --frozen ruff format --check services/backend tests/repository tools`: PASSED
- CMD05 `uv run --frozen mypy`: PASSED
- CMD06 `uv run --frozen pytest services/backend/tests/unit tests/repository`: PASSED
- CMD07 `uv build --out-dir /tmp/slaif-agent-site-distributions`: PASSED
- CMD08-17 ten process smoke `--check` (control/editor/agent/render/mcp/
  media/review-worker/scheduler/media-gc/bootstrap): PASSED
- CMD18-26 nine frozen Node/TS commands (node --version, pnpm --version,
  pnpm install --frozen-lockfile, pnpm lint, pnpm format:check, pnpm
  typecheck, pnpm test, pnpm build, pnpm licenses list --json): PASSED
- CMD27-31 five preparation checks (compileall -q tools tests/repository,
  unittest discover -s tests/repository -p test_*.py, tools/
  check_repository.py, tools/check_mermaid.py, markdownlint-cli2@0.23.2
  **/*.md): PASSED
- B6 extra (same frozen I, CI scopes): `uv run --frozen ruff check
  services/backend tests/repository tests/packaging tests/supply_chain tools
  migrations` and `ruff format --check` same scope: PASSED native 0
- `uv run --frozen pytest tests/supply_chain`: PASSED 43 passed + 27 subtests,
  native 0
- K3 isolated probes SYSTEM/APP/FILES at image sha256:19e4ffcd: PASSED
  native 0 x3 (strict assertions)
- K5 same-collector BEFORE vs AFTER: PASSED (3428 -> 2881; exactly the 547
  expected removals; 0 added; 0 changed)
- FULL 347 integration (unfiltered, owned isolated PG18): PASSED -
  347 passed in 3647.81s, 0 failed/error/skipped, FULL_CHILD_EXIT=0,
  container ExitCode 0 (05:50:08.576Z..06:51:01.016Z)
- WHOLE literal `sh tools/compose/smoke.sh slaif0835`: PASSED -
  WHOLE_NATIVE_EXIT=0 (06:54:47.210Z..07:13:05.266Z); 40 browser test
  records / 19 projects / six pairings (139189ms) / 49 packaging /
  recovery / footer (compose-smoke OK)
- LOCAL6 two-build six-image `sh tools/supply_chain/run.sh
  /tmp/oap-083-7-b/local6-I-b053898/evidence-Ib-run1`: PASSED -
  pipeline native 0 (07:13:40.534Z..07:41:13.988Z); 6 images,
  critical=0, high=19 (inherited review-evidence population), raw
  ignoredMatches=[] in all six scan JSONs, exceptions empty;
  checksums/gate/finalize+validate OK

## GitHub CI / required checks

- State observed for implementation head I_b at 06:18:17.128Z: 30/30
  COMPLETED/SUCCESS (current-I observation only, saved
  /tmp/oap-083-7-b/report/ci-observation-ib.json); re-observed at
  2026-10-26T07:44:42.437Z (30/30 COMPLETED/SUCCESS; saved /tmp/oap-083-7-b/report/ci-observation-ib-requery.json).
- Fresh b-S checks: PENDING at publication (report-only commit triggers
  fresh checks; strategy verifies SELF; no substitution).
- All required green at drafting (implementation head I_b): YES, as
  observed (30/30 SUCCESS); this is NOT a claim for the fresh b-S set.

## Local setup / dependencies

- uv 0.12.5, Node v24.22.0, pnpm 11.22.0 (pinned tools); repository venv
  Python 3.13.14 (uv-managed); postgres:18.6-alpine3.23
  (sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f)
  owned container, no host port; python:3.13-slim
  (sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f)
  runner base; backend image built at I_b sha256:19e4ffcd...; no new
  PRODUCT dependency/service identities beyond the ordered certifi; owned
  disposable runtime/build installs and preparation (pinned uv 0.12.5 /
  Node v24.22.0 / pnpm 11.22.0 tooling, docker builds, owned postgres and
  runner containers) happened as described in this report; no product/lock
  authority change beyond the ordered certifi block.

## Documentation

- docs/SUPPLY_CHAIN.md (+43), oap/INCREMENTS.md (+5/-2), oap/
  MVP-PROGRESS.md (+2/-2), THIRD_PARTY_NOTICES.md (certifi row). Numeric 083
  and the full product remain PARTIAL; no release authorization.

## Safety and scope confirmations

- Unrelated files changed: NO (14 exact paths; cumulative diff above).
- Production secrets accessed: NO; production systems accessed: NO (fake
  local qualification credentials only, redacted in evidence).
- Required tests skipped/not run: NO - every required local gate at
  frozen I_b executed (exact ALL31 31, supply + CI lint, K3 build +
  3 isolated probes, K5 same-collector, FULL 347 unfiltered, literal
  WHOLE, LOCAL6 two-build six-image); the only not-yet-run set is
  the fresh b-S CI checks, honestly PENDING at publication (B7).
  Scope deviation: NO.
- Extra objective PR: NO. Coding-agent merge: NO.
- Activated order/active edited: NO (exact bytes committed).
- Report commit changes only this report: YES (sole path).
- PR 107/110 = OAP accepted/merged history (untouched); bot PRs 109/108/105
  HOLD (untouched).

## Known limitations / blockers
### Failures and deviations (complete, all preserved)

- a (round a, immutable PARTIAL report): 502 cap violation (unapproved WIP)
  -> preserved + coherent 466 recovery (see Cap history); 04:24:48Z
  package-version JSON KeyError then 04:24:57Z corrected query native 0;
  04:34:18Z notices/notices --check native 1 (missing pnpm PATH) while
  policy validate native 0; a-report lint 23 issues/native 1 then final
  SAME-file lint 0 at 05:16:01Z (publication 05:16:24Z); preliminary piped
  pytest native status UNKNOWN (piped through tail; not an all-native
  ledger); A2 native-0 checks on later-committed identical bytes (not
  freshly at I).
- b: pre-freeze B4 adapter WIP corrections (count assertion native 1;
  hardcoded member size 12 vs actual 15B payload b"synthetic-entry"
  silent-truncation risk) corrected before the final freeze; final I_b
  units native 0 (no source or gate effect; WIP preserved).
- b: K3 first build attempt tag-uppercase native 1 (preserved; corrected
  attempt native 0).
- b: ALL31 first launch outer-redirect native 1 (unlaunched; shell
  redirection evaluated before inner mkdir; preserved as setup failure).
- b: WHOLE harness first launch (06:53Z, nohup under an exec session that
  terminated immediately) disappeared BEFORE any WHOLE child executed;
  launcher-native.txt 0B, launcher native status UNKNOWN (never captured),
  no log/sidecar produced; disappearance cause only suspected
  (process-group teardown) and not independently proven; only the
  half-created 0B umask artifact removed to permit the clean owned-session
  launch. Setup failure, NOT a failed WHOLE test attempt; no rerun.
- b: FULL runner live-provenance dirty_start inverted-bool field (original
  JSON preserved byte-identical; corrected erratum JSON; actual start CLEAN
  per launch.log FULL_WORKTREE_DIRTY_START=0).
- b: scratch report-draft verification assertion native 1 (draft repeated
  the old 083-6-c active LF hex 3038332d362d630a instead of 083-7-b's
  3038332d372d620a) then corrected in scratch only; no source or gate
  effect.
- a: 04:13Z wheel-inspection KeyError native 1 (LICENSE lookup; actual
  LICENSE is under dist-info/licenses/LICENSE per member list; corrected
  comparison followed; preserved).
- Pending at publication (honest, not predicted): fresh b-S CI all 30
  (20 required + 10 PG children) + fresh six-image artifact for b-S;
  strategy/root waits and reviews before acceptance/merge.

### Limits (honest)

- Historical 600s frozen-review-parity global-timeout failure occurred in
  postmerge main CI after 083/5 PR 107; cause UNKNOWN; this increment makes
  no new diagnosis or claim about it.
- Lower OCI layer bytes of the removed installer paths persist in image
  history (RUN rm whiteouts); removal is effective-merged-filesystem scoped.
- Scoped CA-absence claim only (covered scopes / collector coverage), not
  universal; normalized vs raw OCI identity: image digest binds content,
  OCI revision label local - source attribution via controlled frozen
  cwd/argv/observations.
- Advisory 17 OPEN; fresh scanner Critical 0 on the current artifact is not
  a no-known-critical claim for other surfaces; OS/browser trust stores
  unqualified.

## Recommended strategic follow-up
No new feature/selection/trigger/lifecycle work is proposed from this
round. The certifi 2026.10.19 test-lock repair is THIS increment's
delivered work (B1/K1: uv.lock certifi block 2026.7.22 -> 2026.10.19,
test-group transitive only; no APP production dependency upgrade); no new
increment is proposed for it and no delivered claim is denied. After
accepted 083/7 and verified main, root's next public 0.2 qualification
remains INERT/unassigned until the actual final order. This report makes
no release, closure, or next-order claim.
