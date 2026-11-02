# OAP 083-9-c execution report: Python security prerequisite (backend 3.12.16 pin, worker seven-package purge), closed PARTIAL at implementation Fc

## 0. Header facts

- Round: 083-9-c of unresolved numeric objective 083, semantic
  increment 083/9, mode `AMENDED_EXISTING_PR`. Closed PARTIAL at
  implementation Fc by ROOT direction (2026-11-02, after Fc
  input/CI qualification and before the fresh Fc ALL31). Not
  accepted; not merged. `NEEDS_NEXT_ORDER`: ROOT-directed
  follow-up round on the same PR113 for the fresh final ALL31 and
  the final SELF six-image CI.
- Order: `oap/orders/083-9-c-python-security-prerequisite.md`
  (291 lines, 18217 bytes, content SHA256
  `f3ad2aab7a855402976d6c4ec94b2bbc47a4890a4b1f34bc7e71af5793edc738`),
  committed byte-exact at Pc and unchanged through Fc; activated
  2026-11-01T19:47:44.954787Z with one exact control OK (2 bytes
  `4f4b`, no LF) retained by the b-round next-control reader
  (PID 3116467).
- PR: `AMENDED_EXISTING_PR` #113
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/113>, state
  OPEN (verified 2026-11-02T00:14:09Z before publication), base
  main `d18b6e4c9423f61de99b516be90619bf2ab5d3e0` (D18), head
  branch `oap/083-9-a-remediate-node-brotli-runtime`, worktree
  `/home/janezp/codex-work/slaif-agent-site-083-9-a`, canonical OAP
  root `/home/janezp/codex-work/slaif-agent-site/oap`.
- Round-start head: SELFb `7e2c40f1282088b3ba725e2cb1fc65c487f30c4e`
  (b report commit, sole parent Fb
  `8802e6abe8af76935ae862b42239a9504cf2e35d`).
- Pushed commits this round (no amend, force-push, or rebase):
  - Pc `641745bede6df8176e26533044b3ee912a5b666e` (source checkpoint; sole parent SELFb; tree `c8809c218b071bd6fc2ab4800c16a81e2ede3eed`)
  - Pc1 `4ab01a75baca25815d37e4b9521bfcba7c51598a` (invalid `dpkg-query -a` removal; sole parent Pc; tree `92297c58cd393db344dd1f3a3e48410596957c5f`)
  - Fc `e4ec49038a663a228615adf3c7825bf18ba35465` (durable docs; sole parent Pc1; tree `4ff7da101957b3c3a572fb37beef75d880030e07`)
- Literal implementation SHA (Fc):
  `e4ec49038a663a228615adf3c7825bf18ba35465`.
- Report publication commit: SELF (this report; sole parent literal
  Fc `e4ec49038a663a228615adf3c7825bf18ba35465`; sole new path this
  report).
- Status: PARTIAL - N3 UNMET (fresh Fc ALL31 NOT_RUN), N5 PENDING
  (final SELF fresh six-image CI not run). N1, N2, N4, N6 MET.

## 1. Source state: exact scoped changes versus D18

Twenty-four tracked paths differ from D18 at SELF: seventeen source
paths plus seven transcript paths (`oap/active`, the three round
orders, the three round reports; this report is the seventh
transcript). Source gross 586 (516+/70-) versus planning 400 / hard
600 - reserve 14 at closure; ROOT approved prospective reserve use
for the named guard/policy/test/smoke/docs units. Fc itself changed
only the three approved docs (7+/5-).

Source paths (numstat versus D18):

- `README.md` 4+/3-
- `apps/web/Dockerfile` 3+/3-
- `docs/CONFIGURATION.md` 1+/1-
- `docs/DEPLOYMENT.md` 5+/5-
- `docs/LICENSE_POLICY.md` 1+/1-
- `docs/SECURITY.md` 8+/2-
- `docs/SUPPLY_CHAIN.md` 57+/18-
- `oap/INCREMENTS.md` 3+/2-
- `oap/MVP-PROGRESS.md` 2+/2-
- `services/backend/Dockerfile` 3+/3-
- `services/browser-worker/Dockerfile` 127+/8-
- `supply-chain/browser-worker-critical-matrix.json` 60+/0-
- `supply-chain/policy.json` 21+/6-
- `tests/packaging/test_oci_contract.py` 64+/3-
- `tests/supply_chain/test_policy.py` 104+/4-
- `tools/compose/smoke.sh` 3+/3-
- `tools/supply_chain/policy.py` 50+/6-

Transcript paths (numstat versus D18): `oap/active` 1+/1-;
`oap/orders/083-9-a-node-brotli-security-prerequisite.md` 299+/0-;
`oap/orders/083-9-b-browser-security-prerequisite.md` 363+/0-;
`oap/orders/083-9-c-python-security-prerequisite.md` 291+/0-;
`oap/reports/083-9-a-node-brotli-security-prerequisite.md` 464+/0-;
`oap/reports/083-9-b-browser-security-prerequisite.md` 487+/0-; this
report (added at SELF).

Frozen through Fc (ROOT input review): all image COPY inputs,
Dockerfiles, pins, and invocation sites unchanged Pc1->Fc; README
and web inputs unchanged since P1 (the 112 web input leaves are
blob-equal P1->Fc); critical matrix history (8 history objects +
65 findings) byte-exact; `uv.lock`, `pnpm-lock.yaml`, and CI
workflows unchanged; PR111 no-system-pip semantics preserved.

## 2. N1 - bounded single PR (MET)

- Exactly one PR (#113), amend-only rounds; 24 final paths within
  the 24-path maximum; source gross 586 within hard 600; no
  dependency, lock, or CI changes; no new production dependencies;
  foundation remains registry-only `agent-cow-postgresql==0.2.0`;
  architecture invariants preserved.

## 3. N2 - backend 3.12.16 pin and worker seven-package purge (MET at source)

Backend `services/backend/Dockerfile` (both build stages):

- Base digest-pinned `python:3.12.16-alpine3.23@sha256:a4ad86fc2eaa4f9a5c3153776c9fb56e502dbd8e23dfa855d164308f376a6dd2` (amd64 manifest `fe32c943235f1c5748d1106dbdfa25d206355c1be1ae1e167444a7ff9dfa9422`; config SHA256 `25a4a11db3b8db1541f61a67461c1d27aff87b4dd8b9e4effd8a5e258f3c8f71`; Python layer SHA256 `977e4cb8a93576029766a4c29c04e12492e5a1c89fe321c2143ce04f63dfd521` / diffID `45d6ee087647b8bbccd1f9abd64b38d07fbb12f6dc296ac392a4bca863916281`; config-declared upstream tarball SHA `b5796915dc45ff745cfb4e990a7e7c93d6f546328a102ce31448d69ebc37575c`) - inert authenticated registry-layer evidence, ROOT-reviewed, not executed.
- Official 3.12.16 is the October 25 2026 security release fixing CVE-2026-115557 (python.org release metadata).
- ensurepip retained; the existing installer-removal stages apply to the new base (system pip 25.0.1 dist-info, bundled wheel, `pip3`/`pip3.12` scripts); the final layer `51fe24216672b494fbcf8c0117b7bb85596bfab4c3cdc466946b3ba9e2aa5158` shows 8 tar entries including `usr/local/bin/pip -> pip3`, no whiteouts, and no later pip/ensurepip overlay; the OpenSSL 3.5.9-r0 overlay is carried over.

Worker `services/browser-worker/Dockerfile` (both build stages):

- Purges exactly seven packages: `python3`, `python3-minimal`, `libpython3-stdlib`, `python3.12`, `python3.12-minimal`, `libpython3.12-stdlib`, `libpython3.12-minimal`. The four versioned packages at 3.12.3-1ubuntu0.15 carry the retained Medium CVE hits (CVE-2026-115557, CVE-2026-111497); the three defaults are 3.12.3-0ubuntu2.1.
- Fail-closed gate: locale-fixed `apt-get -s` operation-row simulation parsed with the actual APT operation vocabulary; accepts only the exact seven `Purg` removals with exact multiplicity; rejects any `Inst`/`Conf`/`Remv`/other operative row; pre-removal version assertions; post-removal `dpkg-query -W` known-record query without a package selector (fourth-column status `ok not-installed` with the dpkg leading space, or record absent; no invented field), full healthy installed-inventory absence, `python3*`/`libpython3*` executable-path absence under `/usr` and `/opt`, and an `sh -exc` smoke guard; no autoremove, no force, no Essential override.
- Policy/tests: `tools/supply_chain/policy.py`, `supply-chain/policy.json`, `tests/packaging/test_oci_contract.py`, `tests/supply_chain/test_policy.py`, plus the candidate-10 critical-matrix history entry (old history objects preserved byte-exact).
- Ubuntu Noble `python3.12` upstream status "Needs evaluation" (not fixed/unaffected) is preserved in docs/matrix as a bounded absence of proof, not a fixedness claim.
- Pure in-memory synthetic verification (not product runtime): the ROOT-approved 70-line input (SHA256 `cf5d7a9cffc03d9fd65a7f4677c3aa72f437b63c88adbf0e43ccc27bcee3296d`) executed once against owned fixtures; nine benign cases with actual awk natives as expected (0 valid/multiset-mismatch/empty; 1 `Inst`/`Conf`/`Remv`/foreign; 2 intentional absent input); `outside_purg` fixture 8 rows (7 valid + 1 foreign); terminal 0; RAW Dockerfile byte SHA plus HEAD/branch bound. Scope is the awk program and the Dockerfile expected-set declaration against the independent seven-name set - actual APT, Docker, and full-image behavior NOT_RUN.
- The two purge awk program bodies are byte-identical Pc->Pc1 (program SHA256 `7f96b7d82eb06f988f2cc2070db7587ecd8672b130cf45e8a8058ba362448f9d`), so the synthetic proof carries through Pc1 and Fc.

## 4. N3 - fresh final ALL31 (UNMET; NOT_RUN)

- The order requires one fresh ALL31 (exact 31 commands, argv and
  order per the c order) at clean final Fc under
  `/tmp/oap-083-9-c/all31.sh` (planning 120 / hard 160 natural
  lines).
- NOT_RUN at Fc. In-memory drafts were submitted to ROOT review
  (the displayed 160-line draft was ROOT-measured 7490B / SHA256
  `d31e6cac95f4ce5c8d8831359773d8d1bdde18b8bd3b79e6623ec59fd845fb81`);
  none approved, none written, none executed; no runner file
  exists.
- ROOT directed (2026-11-02) that a prospective follow-up round
  will simplify this verification; c closes PARTIAL on this
  criterion.

## 5. N4 - local runtime proof (MET at literal Pc1, carried to Fc)

- Runner `/tmp/oap-083-9-c/verify-python.sh`: 400 natural lines /
  22628 UTF-8 bytes, SHA256
  `7628c71b168f14a2dedf0a53d1501fc4759a90ca26468d45bd754be94556a673`,
  ROOT full-read approved (receipt
  `/tmp/oap-083-9-c/root-runtime-input-review-r2-approved.json`);
  O_EXCL exclusive write plus byte-exact readback; exactly one
  bare `bash` invocation (actor 54229), launched
  2026-11-01T22:56:25.518Z, terminal 2026-11-01T22:59:04.456Z,
  actual terminal native 0.
- Source identity: START and true END after cleanup, both at
  branch `oap/083-9-a-remediate-node-brotli-runtime`, head Pc1
  `4ab01a75baca25815d37e4b9521bfcba7c51598a`, tree
  `92297c58cd393db344dd1f3a3e48410596957c5f`, clean; no
  AFTERSETUP marker exists in this runner (setup/phase logs are
  separate); ABORT never fired. Windows: setup 600s / phase
  5400s / cleanup 600s monotonic caps, kill grace 5s.
- 32 bounded commands, all actual native 0; 37 retained log files
  (32 command streams + `probe.log` + `source-identity.log` +
  `summary.txt` + 2 create-id files) in
  `/tmp/oap-083-9-c/verify-python/logs`, ROOT independent full
  read with hashes (receipt
  `/tmp/oap-083-9-c/root-Pc1-runtime-independent-review.json`,
  including its parser erratum).
- Preflight: host verifier Python exactly 3.13.18; Docker
  ServerVersion 29.1.3; healthy image/container inventories;
  exact-absent prechecks.
- Builds (native 0), both `linux/amd64`, OCI
  `org.opencontainers.image.revision` label equal Pc1; durable
  fsynced create IDs recorded before start:
  - backend `slaif-agent-site-backend:083-9-c-pc1` -> image `sha256:b2355a9b8279d094ad8e103e6d4255bece590ad64e07b7ba3085931a60a671d2`, createID `b1bc1d886dea29cf49b98a9876915dfb2e31a542600bffeb159bf69cae53c933`
  - worker `slaif-agent-site-browser-worker:083-9-c-pc1` -> image `sha256:1ad6bf85fd8fca3f3bdab8c7c2042043d9ec3679987b8a304955b94a52a61691`, createID `e2359128edd1f17801cee3785e697b2cd74bd853f2484f096c5e43e74577798d`
- Container metadata (both): `10001:10001`, `Mounts=[]`,
  `NetworkMode=none` (the Docker built-in `none` entry recorded as
  observed, never deleted, never claimed empty),
  `NoNewPrivileges=true`, `CapDrop=[ALL]`, 768MiB / 256 PIDs / 1
  CPU.
- Backend oracle (exec native 0): `Python 3.12.16`;
  `/usr/local/bin/python3.12` SHA256
  `bbe1110dea5ad4c33d3a74cac9ba40e3a8c0831b17d18aba7431fd4931bdfaa7`
  /14000B; `libpython3.12.so.1.0`
  `2fe59cf55db8e8df22868010bbaa0132edba4924dc0275f979fc1453263f3af9`
  /7236608B; `_ssl.cpython-312-x86_64-linux-musl.so`
  `0eed52ea8e6d390243d12e8a6e3cd7e06a015283be69132820ddf880d8815727`
  /226816B - each equal to the authenticated upstream base-layer
  measurement (receipt
  `/tmp/oap-083-9-c/root-python-binary-expected-hashes.json`; inert
  base facts, this run is the runtime comparison); OpenSSL
  3.5.9 29 Sep 2026; benign `ssl` import OK (behavioral cert
  rejection NOT_RUN; `_ssl` byte identity is the upstream SPKI
  denylist implementation identity only); venv python resolves to
  the system interpreter; foundation 0.2.0 with `direct_url.json`
  absent; six health-only `--check` OK; pip artifacts absent;
  ensurepip retained.
- Worker oracle (exec native 0; 506 healthy inventory rows): Node
  `v24.22.1` `/usr/local/bin/node` SHA256
  `e32e2d16081cf644f88392934288086e7662529d0d43277c34f7aad2207cfafb`
  /126879696B (glibc worker build; the P1 web/musl Node fact is a
  distinct P1 observation); LICENSE
  `5888dbb9a1d2b18f2c3e6c5f6af1b39de658372b402a0577b002777f14c62ace`;
  `libbrotli1=1.1.0-2ubuntu0.1` installed; brotli roundtrip OK
  (27 bytes) plus `process.versions.brotli=1.2.0`; ldd native 0
  with full output (no libbrotli line in node's own linkage =
  observation only, not static-linkage proof); NodeSource full
  formatted inventory with `nodejs` absent; 15 tool paths absent;
  single-browser tree; Chrome for Testing 156.0.8078.80 chrome exe
  SHA256
  `1bcad71ad1bff85955db13c6d8dd9f32374934d5a5cb079b526c46fb51f9bd97`;
  seven python packages with dpkg status `ok not-installed` (leading space) or record absent; python
  executable paths absent.
- Cleanup (natives 0): stop -> terminal `Running=false
  ExitCode=137` (sleep entrypoint under `stop -t 5`, distinct from
  the oracle exec native 0) -> rm -> name plus full-ID absence ->
  rmi -> image absence; no owned volumes or networks.
- Fc carry: Fc changed only the three approved docs; all image
  inputs/Dockerfiles/pins/invocations unchanged Pc1->Fc (ROOT
  input review), so the literal Pc1 runtime proof and the P1 web
  carry qualify at Fc; no fictional Fc runtime run is claimed.

## 6. N5 - final SELF six-image CI (PENDING; not run)

- Required at final SELF: all 20 strict correct-app required
  contexts plus all 10 actual PG children success, and a fresh
  six-image security/licensing/packaging CI at final SELF. A
  report cannot prove its own future SELF CI; the final SELF is a
  fresh report-only commit whose fresh checks are the mandatory
  gate before acceptance.
- Observed intermediate facts (not acceptance), receipts under
  `/tmp/oap-083-9-c/`:
  - `root-Fc-20plus10-success.json`: Fc all 30 checks success (20 strict required, including CodeQL, plus 10 PG children), ROOT full-read 2026-11-01T23:36:01.976895Z; CI merge revision `76856d6237d1e7e1208ce65a160231bc1ca35858`, parents D18+Fc, tree Fc.
  - `root-Fc-six-intermediate-review.json`: Fc six-image artifact 13105512072 qualified INTERMEDIATE: 8213315B, ZIP SHA256 `70186efcf109ebf5f157698671641035ac0e07d0093eb517dd5b394e414ba4b3`; all 53 payload checksums plus 18 index bindings verified; all six images with loaded-copy/repro/licenses present, license values equal Pc1; Critical 0 / ignored 0 / exceptions 0; 12 retained High / 0 new (4 browser-worker: CVE-2025-3887 `gstreamer1.0-plugins-bad` + `libgstreamer-plugins-bad1.0-0` 1.24.2-1ubuntu4, CVE-2026-84782 `libssl3t64` + `openssl` 3.0.13-0ubuntu3.12; 7 postgres: `libuuid` 2.41.4-r0 under CVE-2026-53612/53613/53614/76642/78408/78410 plus `zlib` 1.3.2-r0 CVE-2026-85091; 1 web: GHSA-68fv-2mgg-jv7q `source-map-js` 1.2.1); the 31 forbidden full tuples (29 old Chrome + CVE-2026-115557 + CVE-2026-111497) absent across all six images at any severity; Grype DB built 2026-11-01T06:20:12Z, age 16.966h at validation, checksum `sha256:d0e1af9e6491440e1a671d0a0aafc32c5c7cb5cda787dcec3482799ef298f31c`.
  - Backend shows no Critical at Fc (3.12.16); the worker python debs are purged (their four Medium hits are gone from worker).

## 7. N6 - docs and truthfulness (MET at closure)

- `docs/SECURITY.md`: durable acceptance wording - acceptance of
  the final implementation commit requires fresh required checks,
  a fresh local runtime probe, and the current six-image CI at the
  final gates (replaces the interim "pending final
  re-qualification" phrasing).
- `oap/INCREMENTS.md` / `oap/MVP-PROGRESS.md`: the 083/9 labels
  now read "Node, Brotli, Chrome, and Python runtime security
  prerequisite"; `docs/DEPLOYMENT.md` python row updated to
  3.12.16 with bounded Noble status wording; `docs/SUPPLY_CHAIN.md`
  documents the pin/purge history (candidate-10 entry, Syft commit
  `2293641e3bd628a01bb37639318d62c0ebe89b39` corrected to the
  actual 40-hex value).
- P1 qualification remains dated/intermediate; no future Fc/SELF
  pass is claimed; history (orders/active/reports/matrix)
  byte-exact; no historical edits.

## 8. Affected checks (actual, source phase)

- Ruff `check` plus `format --check` on the actual broader CI
  scope (`services/backend tests/repository tests/packaging
  tests/supply_chain tools migrations`), patched CPython 3.13.18
  host toolchain: 351 files, native 0.
- `tests/packaging`: 49/49 pass, native 0.
- `tests/supply_chain`: 46/46 pass, native 0 (includes the two
  new round-c negatives and the repaired temp fixture).
- `tools/supply_chain/policy.py validate`: native 0.
- `sh -n` outer plus exact extracted `sh -exc` inner literal:
  native 0.
- Fc affected Markdown: the three changed docs,
  `markdownlint-cli2@0.23.2` native 0 (0 issues; tool
  sanity-verified per erratum 4).
- Precision: the broader affected checks ran on pre-commit source
  bytes later published exactly as Pc1; Fc changed only the three
  docs (Markdown is the Fc affected check). No unchanged-gate
  reruns. The corrected host `dpkg-query -W` producer native 0 is
  a host/syntax check, not post-purge/runtime proof.

## 9. CI history (actual, preserved)

- Pc `641745bede6df8176e26533044b3ee912a5b666e`: run 41353729409
  FAILED - `Supply-chain evidence` job 124989214689 and `Compose
  and edge packaging` job 124989214710; actual root cause:
  unsupported `dpkg-query -W -a` in the post-purge known-record
  gate (native 2) after the pre-removal version check and the real
  purge had both succeeded; diagnostics artifact 13102866521
  retained.
- Pc1 `4ab01a75baca25815d37e4b9521bfcba7c51598a`: GREEN - run
  41355156975 plus CodeQL 41355156985, artifact 13102853565, merge
  revision `6907609877890f4b5b2ff18f3a12118658c95d6c`; raw six
  scans: Critical 0 / ignored 0 / exceptions 0, 12 retained High /
  0 new, CVE-2026-115557 plus CVE-2026-111497 plus the 29 old
  Chrome findings absent across all six images.
- Fc `e4ec49038a663a228615adf3c7825bf18ba35465`: all 30 checks
  success (section 6).

## 10. Local setup and provenance

- Patched CPython 3.13.18 built locally in disposable scratch from
  official fixed source (source XZ SHA256
  `abb0102e6d4ae027509bcb82327d9dd85515b44a3ba8ad538cfc5e9847029f68`,
  GZ `99dbc847fb6a3fb26358370fb4c591215864116ebb584f2b89ab0b74c51dfa2a`,
  verified against python.org release metadata before build);
  build receipt 2dd58e: BUILD_DONE, build-exit 0, Python 3.13.18,
  GCC 15.2.0, OpenSSL 3.5.5; installed at
  `/tmp/oap-083-9-c/py31318/install` and used as the host verifier
  and affected-check toolchain (uv 0.12.5 venv selected 3.13.18,
  44 frozen packages).
- Node v24.22.1 (`/tmp/oap-083-9-a/verify/node-v24.22.1-linux-x64`,
  approved for the Markdown checks); pnpm 11.22.0; Docker 29.1.3.
- The b-round older 3.13.14 observations remain historical (an
  early uv venv stayed at 3.13.14; caught; 3.13.18 re-selected
  with full-stream receipts).

## 11. Forward errata (c; carried without historical edits)

1. Session c65a2d: the rm -rf style deletion of a scratch target was rejected at 2026-11-01T20:32:14Z; the same target was then removed via `shutil.rmtree` at 2026-11-01T20:32:27Z (recorded as fact; any "no deletion workarounds" statement is scoped to post-containment actions only).
2. An earlier "399-line" verify-python summary had no tool receipt (journal gap); unsupported and not retroactively approved; superseded by the actual 400-line receipt (SHA256 `7628c71b168f14a2dedf0a53d1501fc4759a90ca26468d45bd754be94556a673`).
3. The first runner write-step extraction (glob-wide scan) hit a prose `NATURAL_LINES=400` string and self-aborted (native 1, nothing written); corrected to the receipt-bound approved file.
4. `markdownlint-cli2@0.23.2` prints "0 issues in 0 files" when no file has issues (the summary counts issue-bearing files); issue detection was verified via a synthetic bad file (3 issues, native 1); per-file runs report "Linting: 1 file".
5. The failed CI run 41353729409 belongs to Pc (not Pc1); the Pc1 green run is 41355156975.
6. Worker ldd: the absent libbrotli line in node's own linkage is an observation, not standalone static-linkage proof.
7. Container `ExitCode=137` at cleanup is the sleep entrypoint under `stop -t 5`, distinct from the oracle exec native 0.
8. A claimed ALL31 draft parse receipt (8670B / SHA `14c105c5...`) was not observed / unsupported; the actual displayed 160-line draft was ROOT-measured 7490B / SHA256 `d31e6cac95f4ce5c8d8831359773d8d1bdde18b8bd3b79e6623ec59fd845fb81`; no draft was approved or executed.
9. The in-memory report draft said "reserve 16" at gross 586; the actual reserve is 14 (600-586).
10. All b forward errata (P1 and Fb each 1120 leaves, SELFb 1121; the three-path delta is Fb-vs-P1 only; backend fix.versions includes 3.12.16/state fixed; the good==bad helper wrote unchanged bytes before asserting; host Node came from the xz archive; raw-ns/ROOT wire authoritative for subsecond time) remain in the b report without historical edits.

## 12. Known limitations

- Normal path exercised only (32 commands / 37 logs;
  abort/error/timeout-kill paths implemented but not exercised; no
  cancellation test); no all-path or all-cleanup guarantee.
- No zero-vulnerability, all-severity, or privacy claims; coverage
  is the CI six-image evidence only.
- Local container metadata is observation-only (network none,
  read-only, caps dropped, no-new-privileges, finite limits);
  product browser confinement is evidenced by the current CI
  smoke, not re-claimed locally.
- Upstream byte facts are authenticated inert base-layer
  measurements (registry evidence, not an executed image); the
  runtime comparison is the Pc1 run.
- `_ssl` byte identity is the upstream SPKI denylist
  implementation identity only; behavioral cert rejection
  NOT_RUN.
- The Pc1 runtime is intermediate evidence carried to Fc by
  proven-identical inputs (ROOT input review); the fresh Fc ALL31
  is NOT_RUN (N3).
- ALL31 drafts remain untested conversation data.

## 13. Confirmations

- No real secrets or credentials in this round's source diff or in
  this report; the retained probe streams were fully ROOT-read and
  contain command output and inventory data, not credentials
  (proven scope only).
- No production/deployment/credential work; no external
  exploitation; no trust/network/mount widening; no telemetry or
  hosted-service additions.
- No scan suppression, exceptions, or severity downgrades; no
  unchanged-gate reruns.
- No extra PR; no self-merge/automerge/bypass; PR #112 remains
  OPEN ON HOLD / INACTIVE (083-8-j resumes only by ROOT after 113
  accepted/merged and remote main verified).
- No numeric-083 completion / 084 advance / MVP /
  release-qualification claims; P1-P7 / I1-I8 and the full product
  evidence remain mandatory.

## 14. Close wire (protocol)

- This report publishes as the report-only SELF: sole parent Fc,
  sole new path this file. Sequence: same-TEMP
  `markdownlint-cli2@0.23.2` under Node 24.22.1 (native 0, 1
  file, 0 issues) -> TEMP fsync plus hash/inode -> atomic rename
  -> parent-directory fsync -> post-hash -> byte-exact canonical
  copy under the canonical OAP root -> byte equality -> report-only
  commit (sole parent Fc, one file) -> bare push -> remote
  head/parent/path/byte verification -> exactly one 2-byte `OK`
  response (no LF, no FIFO fsync, no replay) -> exactly one
  byte-retaining next-control reader with actual handle/PID.
- The actual OK/reader wire receipts are delivered in the close
  message, not in this immutable report.
