# OAP report 083-8-u: pin exact zlib 1.4-r0 in four images (PARTIAL)

- Order ID: 083-8-u
- Order: `oap/orders/083-8-u-fix-zlib-critical.md` (SHA256 `d135a87cbd3c38b48d244fb180a295f6d512a708ca323d07257fc3047f1d154b`)
- Active: `oap/active` = `083-8-u` (8B)
- Mode: AMEND_EXISTING_PR
- Status: PARTIAL

## Identity

- Repo: `ulfe-lmi/slaif-agent-site`
- PR: [#112](https://github.com/ulfe-lmi/slaif-agent-site/pull/112) - OPEN, unique for increment 083-8
- Remote head branch: `oap/083-8-a-qualify-public-whole-session` (local alias `oap/083-8-j-execution` is not the GitHub head)
- Base: `main` `40cd172109a22ef5f342589b59a4293f35379651`
- Pre-push remote head: St `a8a59b932bb1995af4a5a813fee7937d78d69c22`
- Implementation SHA (literal): Iu `80637450d628a7adcf7821987440dc748ede6953`, tree `7816c4118deab85df25f4ec3f2dd53e17070026a`, sole parent St
- Report publication commit: SELF (sole parent Iu; changes only this report)
- Pushed commits: `a8a59b9..8063745` (bare push, native 0), then SELF (this report)

## Exact change (six source files + order/active transcript, 8 paths)

Exact `'zlib=1.4-r0'` pin added for the measured Critical CVE-2026-4738 targets:

- `services/backend/Dockerfile` - SHA256 `5cbed888b8ef41c4080a9e752978c359bcc28e7f97104ab36a84f60c81243ab6` - apk pin in builder AND runtime stages
- `apps/web/Dockerfile` - SHA256 `5c18bcc6f2c39773dbbee755bed3d841f8888c251037e9227599eaef67e3bfaf` - apk pin in builder AND runtime stages
- `infra/nginx/Dockerfile` - SHA256 `db18ae759550a5542068b68ca1961d47a4340a6684cd3a1175cef121d0de2c7a` - v3.24 runtime pin + installed-version assertion (existing awk/test pattern)
- `infra/postgres/Dockerfile` - SHA256 `b06d91a95f528282b97248d75f4946fd46e0f759d483ca7ab9650284dc613e59` - v3.23 runtime pin + installed-version assertion
- `supply-chain/policy.json` - SHA256 `f028dc57fcb293fc38d6cf740c089afe3625df48fceef1a8a4eeca3b0323cdb4` - zlib entry in all four alpine install arrays (pinned Prettier 3.9.6 fragment formatting; unrelated bytes unchanged)
- `tests/packaging/test_oci_contract.py` - SHA256 `25cb645816e1938e271ff5954109bded11f7c7f63a7db69f7f90611ae3074cc6` - guards all four images, separate builder/runtime assertions for backend/web, existing test renamed `..._removed_and_zlib_pinned`

Preserved: base tags/digests, registries (v3.23; NGINX v3.24), other pins/removals, Apache .18 repair, labels/entrypoints/users, app deps/locks.

## Source budget (vs `main` 40cd)

- 31 source paths (27 + four Docker paths): 5959 default / 5955 minimal, under the 5974/5970 U caps (same overall HARD 6000); U delta 45/45, under MAX 60.
- Method: `git diff --numstat` vs `git diff --minimal --numstat` versus main, additions+deletions (ROOT It checkpoint receipt method).
- Erratum: first prewrite forecast (call bed3d8, native 0) printed 5963/5959 matching the first applied WIP (indent-duplicated policy splice); the corrected constructor (call aa498a, native 1) computed the indent-repair delta -4 but printed stale absolutes against the pre-U 5914/5910 baseline; final actual 5959/5955 (total delta 45) was then computed and asserted on the worktree (call 16c0e5, native 0). No retrocredit for the wrong absolute forecasts (root-U-test-and-forecast-evidence.txt).
- Four-file family 3599/HARD 3600 (vs Sg) and five-doc 285/HARD 500 (vs D18) unchanged.

## Local verification (each once; subject pre-commit WIP byte-equivalent to Iu; no clean-Iu rerun)

- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: 72 OK observed (call 32fac0); command piped to tail, pipeline native 0, unittest native NOT independently preserved
- `python -m unittest discover -s tests/supply_chain -p 'test_*.py'`: 46 OK, bare native 0 (call 559abb)
- `python tools/compose/verify.py --root .`: compose-policy OK, bare native 0 (call c12dee)
- `python -m tools.supply_chain.policy validate`: supply-chain-policy OK, bare native 0 (call 5326c9)

## GitHub CI at Iu (naturally triggered; no rerun/cancel)

- Observation 2026-11-10T20:18:33.723606Z, head Iu: 25 check-runs present = 5 SUCCESS + 3 FAILURE + 1 neutral + 16 in_progress.
- Formatting failures: Python 3.12/3.13/3.14 quality and package (run 42893858976; jobs 130101684687/130101684575/130101684725), step 6 "Lint and check formatting". ROOT RAM-only log review: lint all checks passed; one file would be reformatted: `tests/packaging/test_oci_contract.py`. Safe category: Python formatting failure, not a unit-test failure. No retry or manual rerun; pinned-formatter repair is owned by the next ROOT order.
- Supply-chain evidence job 130101684624 later completed FAILURE at the Critical gate because of the known browser-worker Chrome Criticals below (out of U scope), not the zlib targets.
- CI at Iu is NOT all green; no complete successful six-image qualification pipeline claimed.

## Targeted Iu repair evidence (ROOT artifact review, not full qualification)

ROOT-reviewed Iu artifact (run 42893858976, artifact 13799513970, 38 files, all 37 declared checksums verified; synthetic merge parents [main 40cd, Iu], canonical tree == Iu; receipt `root-Iu-six-image-zlib-proof.json`):

- actual zlib 1.4-r0 in ALL FOUR runtime inventories (raw and normalized Syft)
- CVE-2026-4738 absent at ANY severity, including related IDs, in all six raw Grype scans; ignored 0 in all six
- Critical 0 in five images; browser-worker retains the 29 exact It Chrome-for-Testing Critical IDs (package chrome 156.0.8078.80; fix 157.0.8103.38; official current Stable 157.0.8103.50) - out of U scope; separate V order after U closure

## Scope limits (honest)

- The pin repair plus targeted artifact evidence does not itself constitute full six-image qualification, High-risk tuple audit, private runtime qualification, or acceptance; no all-green or all-six-image Critical-0 claim (five-image Critical 0 is targeted measured evidence).
- Official v3.23 and v3.24 APKINDEX/secdb evidence (ROOT receipts) proves zlib 1.4-r0 exists and fixes CVE-2026-4738; ROOT did not cryptographically verify or install APKs.
- The original browser-policy failure cause remains UNKNOWN (S); no cause-fixed or browser-recurrence claim.

## Preservation and confirmations

- q/r/S/T reports and errata preserved by exact reference to the immutable reports and the active U order; no history rewrite, no global NOFILES/RAM-only claim.
- No Docker, no runtime, no setup in this round; WHOLE/LOCAL6 private inputs INERT/NOT_RUN.
- No app-dependency or lock change (OS apk pins only); no secret/credential exposure; no production system touched.
- No extra PR, no merge, no force-push, no CI rerun/cancel, no new control reader.
- Gates remain: full 30-check CI (20 strict + 10 PG children) green at the CURRENT final implementation AND SELF, full six-image artifact/security audit (CVE-2026-4738 absent at any severity, zlib 1.4-r0 in all four runtime inventories, Critical 0/ignored 0), private WHOLE/LOCAL6 qualification, ROOT-only merge.
