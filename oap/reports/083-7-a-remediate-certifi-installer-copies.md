# OAP Coding-Agent Report — 083-7-a

## Work order

- Identifier: 083-7-a (numeric objective 083, increment 7, round a); work-order file `oap/orders/083-7-a-remediate-certifi-installer-copies.md` (358 lines, sha256 `3937f725521c780d7b63af2af13ef1fab38262cf000e461117ffba3597e939ff`)
- PR mode: CREATED_NEW_PR

## Status
PARTIAL

## Executive summary
Round 083-7-a (CERTIFI_INSTALLER_COPY_REMEDIATION, new PR #111 from verified main
`df307a955c5c39276fa34934395c7c2c1372ac1e`) is closed honestly PARTIAL at root
direction of 2026-10-26T05:15Z. K1 (exact patched certifi 2026.10.19 lock +
attribution) and K2 (before-change baseline export, inventory, probes) are
complete with actual evidence. The K4 guard source is committed in full, but K4
is PARTIAL: the raw both-directory-spellings test proof is deferred to 083-7-b
(preserved losslessly), and the guard negative/anchor cases are proven only on
manually built manifests, not on a synthetic-TAR-to-`rootfs_manifest`-to-guard
pipeline (narrow proof only; root is reviewing a minimal adapter for b). The
implementation hit the 500 hard cap at 502 (root-measured), was preserved, and
was restored to a coherent 466 gross by deferring the 36-line raw-DR work unit;
502 is not retroapproved and no cap waiver exists. Per root PARTIAL decision, NO
docs edits and NO runtime/build/probe/ALL31/WHOLE/LOCAL6 gates were run in a:
K3, K5, K6 are NOT RUN and K7 is pending at publication. Final b will require
fresh complete K3-K8 at the final b source. Advisory #17 remains OPEN; no
acceptance, remediation completion, or release claim is made.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site` at `/home/janezp/codex-work/slaif-agent-site`
- PR: #111 <https://github.com/ulfe-lmi/slaif-agent-site/pull/111> — OPEN
- Base/head branches: `oap/083-7-a-remediate-certifi-installer-copies` -> `main`
- Starting remote SHA (required verified main): `df307a955c5c39276fa34934395c7c2c1372ac1e`
- Implementation head SHA: `a4eb2a759783fe4bdb2651561f54859ceb1bca7e`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal verified via GitHub after push; recorded privately)
- Implementation commits pushed before report: `5000b099718ddff694bffca739b372e578612f02` (root-published order+active bytes, commit J) and `a4eb2a759783fe4bdb2651561f54859ceb1bca7e` (implementation, 6 files); report parent = implementation SHA
- New PR this turn yes (created during activated round); amended existing NO; merge performed NO

## Changes made

- `uv.lock`: certifi block only, 3+/3-: exact 2026.10.19 (wheel
  `42d35340cc5b9ba78e818ddbff0c5b1c2b779de448a340fd1b989f5fa8670e1b`, sdist
  `035c1e85572b141bf1c3a3eff0e33a8eb74917522f2559075ff8d2fea780a1ae`), all other
  locked artifacts/graph entries unchanged; `uv lock --check` native 0
- `services/backend/Dockerfile`: +8, comment plus `RUN rm` of the measured
  system-pip copies (pip package, `pip-25.0.1.dist-info`, the three
  `usr/local/bin` pip command entries) and the measured `ensurepip`
  `_bundled` bootstrap wheel, as root, before `USER 10001`; no base/APK/scanner
  change
- `tools/supply_chain/evidence.py`: 117+/4- — `IMAGE_PREFIXES` for `backend`
  gains the three measured system scopes; `_prefix_matches` fixed (directory
  prefix = normalized exact-parent OR slash-descendant; file prefix = exact
  only, lookalikes excluded); new `backend_installer_guard` (mandatory fixed
  backend manifest path, required coverage prefixes, real directory anchors
  incl. `opt/slaif`, `opt/slaif/.venv`, site-packages, `slaif_agent_site`,
  `opt/slaif/migrations`, `usr/local/bin`, ensurepip dir, system site-packages
  dir; entrypoint anchors incl. `opt/slaif/bin/initialize-local-secrets.py`;
  rejects pip code root+subtree, `pip-*.dist-info`, the
  `(?:^|.*/)_vendor/certifi` fragment rule, `ensurepip/_bundled` pip wheels,
  `usr/local/bin` pip commands, duplicate paths); guard runs in BOTH
  `finalize_bundle` and `validate_bundle` (after checksum verification) plus an
  index image-name coverage check (incomplete/duplicated index fails)
- `tests/supply_chain/test_evidence.py`: 329+/0- — K4 guard/collector tests as
  scoped in the PARTIAL handoff (see K4)
- `supply-chain/policy.json`: 1+/1- — certifi PURL key only,
  `pkg:pypi/certifi@2026.10.19`; license/source fields, allowlists and all other
  reviews unchanged
- `THIRD_PARTY_NOTICES.md`: 1+/1- — regenerated with the existing tool after
  frozen sync; only the certifi version row drifted; `notices --check` native 0
  (components=298)
- No docs changes in a (root-directed deferral to b); no other identities touched

## Files changed
Uniform `git diff --minimal --numstat` vs `df307a955c5c39276fa34934395c7c2c1372ac1e`:

| path | + | - | gross |
| --- | --- | --- | --- |
| `THIRD_PARTY_NOTICES.md` | 1 | 1 | 2 (separate generated-attribution identity, cap 10) |
| `services/backend/Dockerfile` | 8 | 0 | 8 |
| `supply-chain/policy.json` | 1 | 1 | 2 |
| `tests/supply_chain/test_evidence.py` | 329 | 0 | 329 |
| `tools/supply_chain/evidence.py` | 117 | 4 | 121 |
| `uv.lock` | 3 | 3 | 6 |

Five-implementation-identity gross: 8 + 2 + 329 + 121 + 6 = **466** (hard cap 500).

## Acceptance-criteria evidence
### K1 — exact patched certifi 2026.10.19 lock and attribution: COMPLETE

- Official GHSA-6q48-6c7w-9gw2 affects `>=2019.03.09,<2026.10.19`; patched
  2026.10.19. Root re-opened advisory #17 on 2026-10-26; artifacts re-verified
  from PyPI before locking: both 2026.10.19 artifacts non-yanked (upload
  2026-10-20T02:24Z), wheel/sdist sha256 as in `uv.lock` above; a newer
  2026.10.23 also exists on PyPI, so the exact pin `certifi==2026.10.19` was
  mandatory (`uv lock --upgrade-package certifi==2026.10.19`), no whole-lock
  update. Advisory satisfaction proved with `packaging.Version` (root-qualified
  receipt), never lexical comparison.
- License: actual old (2026.7.22) wheel, new wheel, and new sdist `LICENSE`
  members are BYTE-IDENTICAL, 989 bytes, sha256
  `e93716da6b9c0d5a4a1df60fe695b370f0695603d21f6f83f053e42cfc10caf7`, MPL-2.0;
  terms unchanged, so the already-approved certifi component/license family is
  retained; only the PURL key changed. No new license family/exception/allowlist.
- All other locked artifacts and dependency-graph entries unchanged (the 3-line
  lock diff is the certifi block only); foundation `agent-cow-postgresql` 0.2.0
  pins/artifacts untouched.

### K2 — before-change baseline, export and probes: COMPLETE

- Before any tracked edit, the accepted-main backend image
  `sha256:3bf5e87ac0345b6111a30d24a977d6aae89efd4d059bc2a587a2159e18325db1`
  (the actual 083/6 f1/f2/WHOLE2-selected backend; provenance = prior qualified
  image + root-proved builder-input carry chain I24a->f35 exact 4 OAP names and
  f35->df307 exact 2 tests + 2 docs + 7 transcripts; NOT claimed rebuilt at
  df307) was exported RAW at 2026-10-26T04:09:15Z: `baseline-rootfs.tar`
  120216576 bytes, sha256 `cb1d66aa468e243efb5c7485e0e82b0684c62357c9829a22ebecb47be9b1e856`,
  RETAINED, 641 inventory entries with original TAR modes/kinds/links/digests.
- Measured affected copies confirmed in the before image: installed
  `pip` 25.0.1 (`site-packages/pip` + `pip-25.0.1.dist-info` +
  `usr/local/bin/pip|pip3|pip3.12`), `pip/_vendor/certifi`, `ensurepip` module
  with the single `_bundled/pip-25.0.1-py3-none-any.whl`, and
  `ensurepip/_vendor/certifi`.
- Probes: the 04:12 pair ran WITHOUT `-I` and is preserved as LIMITED
  (non-isolated) positive evidence only. ONE corrected before pair at
  04:16:23Z used explicit measured interpreters with `-I`
  (`/usr/local/bin/python3.12` system; `/opt/slaif/.venv/bin/python` app),
  `--network none --read-only`, native exit 0 for both, at the immutable image,
  before tracked edits (root-verified empty git status 04:18): positive
  before-presence of system pip/app packages established.
- Errata preserved: first inventory JSON (sha256
  `79ddd806aa38805addd2b7a3cd9914bf72bb5486a095f29a37280a46bb18573e`) has a
  wrong `system_pip_distinfo.root` label (helper bug); corrected
  `baseline-inventory-v2.json` (sha256 `8a259dc000d27e5a78dea75b07a3985a1e818c7723a4a931237fd1e26b97c96f`)
  plus erratum note retained; an early provenance note citing a nonexistent
  `services/backend/uv.lock` was retracted, corrected note uses the actual root
  `uv.lock` and the full Dockerfile `COPY` input list.
- Source audit (K3 precondition): ZERO pip/ensurepip invocations in
  `services/backend/src`, `tools/compose`, `compose.yaml` — absence of observed
  invocation is bounded, not universal proof.

### K3 — effective runtime absence of installer copies: NOT RUN in a

- The Dockerfile removal is committed, but per the root PARTIAL decision no
  image build, after-probes, or functional checks were run in a. Required
  after-evidence (specific `importlib.metadata.PackageNotFoundError` for pip,
  `find_spec("pip") is None`, ensurepip module still present, app-venv
  positives incl. `agent-cow-postgresql` 0.2.0, file-level absences, all bound
  to the actual fresh image ID) will run fresh at the final b source. No
  STOP-before-removal condition was observed (no supported flow needs the
  installer per the source audit).

### K4 — permanent scoped fail-closed guard: PARTIAL (source complete, proof narrow)

- Committed source (evidence.py) implements the ordered guard in BOTH
  `finalize_bundle` and `validate_bundle` on the checksummed manifest, with the
  coverage/anchor/reject rules above; no new index/schema fields.
- Valid NARROW proof (unit level, manually built manifest documents):
  installed pip, partial vendor removal, retained dist-info metadata,
  ensurepip and venv `_vendor/certifi` fragments, bootstrap wheel, pip command
  entries all rejected; missing directory/entrypoint anchors (incl.
  `initialize-local-secrets.py`), symlink-as-directory forgery, stale
  coverage prefixes, duplicate paths rejected; non-backend image scoping
  passes; standalone system `certifi` correctly passes. `validate_bundle`
  rechecks after a tampered manifest with recomputed checksums, and an
  index-coverage-evasion index (duplicate image entry) fails.
- Valid collector proof from synthetic TAR (no guard in this path):
  file-prefix lookalikes excluded, parent-anchor + slash-descendant inclusion,
  existing file scopes preserved.
- NOT proven in a (both explicitly PARTIAL):
  1. Raw both-directory-spellings proof (`opt/slaif` vs `opt/slaif/` raw USTAR
     headers genuinely differ before collection) — the 36-line work unit was
     preserved and is deferred to b (see Cap section).
  2. Pipeline coverage: the guard negative/anchor cases run on MANUALLY BUILT
     manifests, not on synthetic TAR -> `rootfs_manifest` -> `backend_installer_guard`.
     No test feeds a collected real-TAR manifest into the guard. Root is
     reviewing a minimal adapter for b; not authorized in a.
- The 43-test/27-subtest pass therefore does NOT establish every K4
  requirement; it is narrow proof of the guard decision logic and of
  collector prefix semantics separately.

### K5 — one-time before/after same-collector preservation: NOT RUN in a

- Before raw TAR retained (`cb1d66aa...`); after export + same-collector
  comparison and two-build reproducibility deferred to the final b source.
  Historical lower OCI layers still contain removed bytes; no layer-purge or
  raw-OCI-identity claim.

### K6 — fresh committed-I full local gates: NOT RUN in a

- ALL31 (clean isolated worktree, human3 excluded), broader CI lint scopes,
  FULL backend integration (historical expected 347 incl. coherent RC7) on
  isolated PG18, literal WHOLE `slaif0835`, and LOCAL6 were all NOT RUN in a
  per the root PARTIAL decision. No carried old local pass is claimed; all of
  these are mandatory fresh at the final b source.

### K7 — fresh final report-only S CI: PENDING at publication

- Report-only S triggers fresh checks: all 20 required names + 10 actual
  PG14..18 children, unchanged five argvs / 85+45 per PG / 15m budgets, actual
  CI Compose whole, fresh six-image artifact/provenance/Critical0/noignored/
  empty exceptions and inherited-High full-tuple review; ruleset 20934043 /
  apps 15368 except CodeQL 57789. All are honestly PENDING at this
  publication; root independently waits/reviews. No unchanged rerun-until-green.

### K8 — honest docs/attribution, report, protocol: PARTIAL

- Docs intentionally NOT updated in a (root-directed; the 083/7 ledger lines in
  `docs/SUPPLY_CHAIN.md`, `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md` defer to
  b). Attribution (policy PURL, regenerated notices) IS updated as ordered.
- This report is the full immutable record; protocol steps below. Advisory #17
  remains OPEN (default-branch alert state only after merge; no dismiss/
  suppress); test-lock remediation and installer-copy removal are separate
  measured claims; no OS/browser trust-store, all-files-absence, global-TLS,
  or release claim. Numeric 083 remains PARTIAL.

## Cap violation and recovery (exact)

- Order cap: 500 gross across the five implementation identities. Pre-correction
  measured 465; root-ordered K4 corrections (the raw-both-directory-spellings
  test and its helper, two actual-vendor-path negative cases, the
  standalone-certifi-pass assertion, the missing-initializer negative) netted
  the gross to 502.
- Root measured the violation at 2026-10-26T04:50:15Z: Docker 8 + policy 2 +
  tests 365 + evidence 121 + lock 6 = **502 > 500**. 502 is unapproved WIP, NOT
  retroapproved; no cap waiver exists.
- Preservation FIRST (root-ordered): `/tmp/oap-083-7-a/preserved-502-20261026T045655Z`
  (mode 700/600): full `git diff --minimal` patch sha256
  `704b6e82f4c83c28294273dc2635d6014f4e9b1e45170f3de34b0afcb98eb909`, numstat,
  raw status, HEAD/branch, and SHA-verified copies of all 6 changed files
  (502 test file sha256 `903b8e8c72cf973c01c96ec4677e8e2b51df28876eb4287eae805177afdb5d4f`).
- Recovery: the 36-line raw-DR work unit (helper 15L + raw loop 19L + 2
  separator blanks; test def line kept) removed from the test file by
  byte-guarded line-range edit; five-identity gross restored to **466** with
  headroom 34. No 2-line packing, no proof deleted: every other K4 test proof
  (vendor fragments, standalone pass, initializer negative, anchors,
  lookalikes, parent anchor, tamper rechecks) remains in a.
- Deferred work unit (lossless): `/tmp/oap-083-7-a/future-b-test-patch-20261026T050229Z.patch`
  (2135 bytes, sha256 `0a1fbaae9d49b228cac0e280b2cf102b67608dbbeb17442e5f5d8c25216838d8`);
  round-trip proven: applying it to the A2 test file reproduces the preserved
  502 test file BYTE-IDENTICAL (sha256 `903b8e8c...`, patch exit 0). Honest
  consequence: b with this unit returns to exactly the 502 test state, so b
  requires the prospective cap decision (root has indicated 550 for the same
  five paths); no claim that 502 complies is made here.
- tarfile source anchors for the raw-spelling claim (for b and this report):
  uv Python 3.13.14 `tarfile.py` writer `TarInfo.get_info` appends `/` for
  DIRTYPE at line 1028; reader `TarInfo.frombuf` strips it at line 1347; host
  Python 3.14 at lines 1035 / 1354.

## Preserved failure ledger (all native, no omission)

- 04:12 before-probe pair WITHOUT `-I`: preserved as LIMITED non-isolated
  evidence, superseded by the 04:16:23Z isolated pair (native 0 both).
- 04:13 wheel-member inspection script: KeyError, native exit 1 (actual LICENSE
  is under `dist-info/licenses/LICENSE` per member list); preserved.
- Baseline inventory v1 `system_pip_distinfo.root` label defect; erratum + v2
  preserved (hashes above).
- Early WIP: ruff E501 violations (scratch log), 4-test `populate()` failure
  against the first guard draft, tarfile raw-header size-field bug in a 04:46
  scratch probe; all superseded, logs retained in scratch.
- Preserve-script slip: one chmod made preserved directories mode 600
  (untraversable); corrected to 700/600 and re-verified (`sha256sum -c` all OK).
- A2 build-script assertion failures (three, all in scratch before any tracked
  write): wrong boundary index, wrong expected-needle string, and a range that
  would have deleted the kept test def line; caught by the build script's own
  guards; the tracked file was written only after all guards passed.
- The 502 cap violation itself (root-measured) and the forecast/manifest
  citation erratum below.

## Erratum (future-patch path citation)

- Root-flagged; confirmed. The ACTUAL preserved work-unit file is
  `/tmp/oap-083-7-a/future-b-test-patch-20261026T050229Z.patch` (WITH trailing
  Z; sha256 `0a1fbaae9d49b228cac0e280b2cf102b67608dbbeb17442e5f5d8c25216838d8`).
  Two scratch documents cited `...050229.patch` WITHOUT the Z (a file that does
  not exist): `cap-stop-forecast-final-20261026T050400Z.md` section 3 and the
  RECOVERY CROSS-REFERENCES block of the 502 PRESERVE-MANIFEST. Originals
  preserved unchanged; correction recorded in
  `/tmp/oap-083-7-a/erratum-future-patch-path-20261026T051000Z.txt`.

## Local verification

- `uv run --frozen pytest tests/supply_chain -q` (committed A2 source): PASSED — 43 passed, 27 subtests passed, native exit 0
- `uv run --frozen pytest tests/supply_chain -q` (502 WIP baseline, pre-restore): PASSED — 43 passed, 27 subtests passed, native exit 0
- `uv run --frozen ruff check tests/supply_chain/test_evidence.py tools/supply_chain/evidence.py` (both states): PASSED — native exit 0
- `uv run --frozen ruff format --check` (both files, both states): PASSED — native exit 0
- `uv lock --check`: PASSED — native exit 0
- `python tools/check_supply_chain_policy.py` / policy validate: PASSED — native exit 0
- notices `--check` after frozen sync: PASSED — native exit 0, components=298
- K3 after-probes, K5 same-collector comparison, ALL31, broader CI lint scopes, FULL integration, literal WHOLE, LOCAL6: NOT RUN in a (root-directed PARTIAL scope)
- future-b patch round-trip (A2 + patch == preserved 502 test file, byte-identical): PASSED — native exit 0

## GitHub CI / required checks

- Implementation head `a4eb2a759783fe4bdb2651561f54859ceb1bca7e`, observed at
  report drafting (2026-10-26T05:2xZ): 25 check-runs — 10 SUCCESS + 1 NEUTRAL
  completed, 14 IN_PROGRESS, 0 FAILURE. Not yet terminal; no claim made.
- Report-only SELF commit triggers fresh checks; all K7 checks PENDING at
  publication; strategy verifies SELF independently.
- All required green at drafting: NO (in progress at drafting)

## Local setup / dependencies

- uv 0.12.5, project venv Python 3.13.14, Node v24.22.0, pnpm 11.22.0 (lint
  tooling only this round), Docker for the K2 export/probes on the owned
  accepted-main backend image only; frozen locks throughout; no package
  installs, no dependency changes beyond the ordered certifi block; no
  production/protected/foreign systems or credentials touched.

## Documentation

- NOT updated in a per root PARTIAL decision; the three ordered doc identities
  (`docs/SUPPLY_CHAIN.md`, `oap/INCREMENTS.md`, `oap/MVP-PROGRESS.md`) remain
  unchanged and defer to b. Regenerated `THIRD_PARTY_NOTICES.md` certifi row is
  the only attribution text change.

## Safety and scope confirmations

- Unrelated files changed: NO — exactly the six ordered paths; only untracked entries are the preserved human files (`.codex/`, `CODEX-SESSIONS.md`, `codex.sh`), untouched
- Production secrets accessed: NO; production systems accessed: NO
- Required tests skipped/not run: YES — K3/K5/K6 gates NOT RUN in a per explicit root PARTIAL direction (final b requires all fresh); no test/source/config/timeout/selection weakening; no carried old local pass
- Scope deviation: YES, authorized — docs omitted in a per root direction; cap 502->466 recovery per root direction (no waiver; prospective b cap is root-owned)
- Extra objective PR: NO (single PR #111); coding-agent merge: NO
- Activated order/active edited: NO
- Report commit changes only this report: YES (sole path, sole parent = implementation SHA)

## Known limitations / blockers

- K4 raw-DR-spellings proof and TAR-to-collector-to-guard pipeline coverage are NOT qualified (deferred / root reviewing adapter for b); K4 is PARTIAL
- K3/K5/K6 NOT RUN in a: the committed Dockerfile removal is not yet proven effective at runtime; no all-files-absence, layer-purge, unreachability, or trust-store claim
- Advisory #17 OPEN; image-bytes finding (pip 25.0.1 vendors certifi 2024.08.30, ensurepip wheel identical bytes) predates this lock change and is addressed by the removal, but post-merge default-branch alert state is unverified
- b at the preserved unit measures 502 gross; a prospective cap decision (root-indicated 550) is required before b source work
- Scratch-only limits: original image modes recoverable from the RETAINED raw TAR; 04:12 probes non-isolated; no runtime DB/browser state exists from a (nothing was run)

## Recommended strategic follow-up

- Activate 083-7-b on the same PR #111 with the prospective five-path cap
  (root-indicated 550): apply the preserved raw-DR unit, add the minimal
  TAR->collector->guard adapter under root/secondary review, then run the
  fresh complete K3-K8 (build + after-probes, same-collector before/after,
  ALL31, FULL, WHOLE, LOCAL6, docs, final S) at the final b source.
