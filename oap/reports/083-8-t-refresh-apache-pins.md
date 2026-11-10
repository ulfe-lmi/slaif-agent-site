# OAP report 083-8-t: Apache pin refresh 2.4.58-1ubuntu8.17 to .18 (PARTIAL)

- Order ID: 083-8-t
- Order: `oap/orders/083-8-t-refresh-apache-pins.md` (SHA256 `890a18d5049e7b74e0d3ac1bd340be4cac1fb22b9c1347cafcea1de582fbbceb`)
- Active: `oap/active` = `083-8-t` (8B, SHA256 `4156b77766dc85590c8602a74a1cddb3ac6027d3e857c916a87b5768d1de2542`)
- Mode: AMEND_EXISTING_PR
- Status: PARTIAL

## Identity

- Repo: `ulfe-lmi/slaif-agent-site`
- PR: [#112](https://github.com/ulfe-lmi/slaif-agent-site/pull/112) - OPEN, unique for increment 083-8
- Remote head branch: `oap/083-8-a-qualify-public-whole-session` (local alias `oap/083-8-j-execution` is not the GitHub head)
- Base: `main` `40cd172109a22ef5f342589b59a4293f35379651`
- Pre-push remote head: Ss `c535f587de098b9415fdad4fe3d1eccdd5e37584`
- Implementation SHA (literal): It `93bf5485e78e91d259ef804eb680b9f886592783`, tree `db69a0d685d9bcaa2b6e3f93d6edd0877e8705f5`, sole parent Ss
- Report publication commit: SELF (sole parent It; changes only this report)
- Pushed commits: `c535f58..93bf548` (bare push, native 0), then SELF (this report)

## Exact change

12 literal pin replacements `2.4.58-1ubuntu8.17` to `2.4.58-1ubuntu8.18` (4 per file, +4/-4 each) in 3 source files:

- `infra/apache/Dockerfile` - new blob `55f77e911aad9da81f37e03d3697e470f860d6d911132e6f83ecd338ea24b4d0` (1484B)
- `supply-chain/policy.json` - new blob `ad0fa275be209490870a472ab879ebacf0396650e3db650a85b28172c6936f03` (10290B)
- `tests/packaging/test_oci_contract.py` - new blob `1cf44b569bcd3d97594139502cd49ca4af378a44cc0b7d6b98b944f0a8b19082` (10485B)

Transcript files in the same It commit: `oap/active` (to `083-8-t`) and the exact t order (176L). It is exactly 5 paths; all other mode/type/blobs identical (ROOT independent review 55f09f).

## Source budget (vs `main` 40cd)

- 27 source paths: 5914 default / 5910 minimal, under 6000. Method: 22-path inventory (`root-Ir-cumulative-scope-review.json`) + 2 S diagnostic files + 3 T files; only exact order/report/active excluded, never whole `oap/`.
- 40 transcript paths exact.
- HARD3600 four-file family: 3599 unchanged (vs Sg `89ab5ec8...`).
- Five-doc family: 285 unchanged (vs D18 `d18b6e4c...`; HARD 500). No product doc edits.

## Local verification (each run once, native 0; subject Ss plus the 3 WIP pin files, byte-equivalent to It)

- `python -m unittest discover -s tests/packaging -p 'test_*.py'`: 72 OK (actual call abee76, native 0)
- `python -m unittest discover -s tests/supply_chain -p 'test_*.py'`: 46 OK (actual call 38541c, native 0)
- `python tools/compose/verify.py --root .`: compose-policy OK (actual call 668020, native 0)
- `python -m tools.supply_chain.policy validate`: supply-chain-policy OK (actual call 994d54, native 0)

Setup/deps: existing pinned local toolchain (project venv; Node 24.22.1 pinned path; pnpm 11.22.0); no new dependencies, no installs, no Docker/runtime/probe. No reruns; no other suites run this round.

## GitHub CI at It (naturally triggered; no rerun/cancel)

- ROOT independent snapshot 2026-11-10T18:54:21.213740Z: 25 present = 9 SUCCESS + 15 pending + 1 CodeQL neutral (neutral is not PASS).
- Executor early snapshot 2026-11-10T18:53:12Z: 25 present = 3 success + 16 in_progress + 5 queued + 1 CodeQL neutral.
- Executor final snapshot 2026-11-10T19:03:59.479780Z: 30 present = 28 SUCCESS + 1 FAILURE + 1 IN_PROGRESS. Failure: `Supply-chain evidence` (job 130052016651, completed 19:02:40Z); in progress: `Compose and edge packaging` (job 130052016762); both workflow run 42879554323, head It.
- ROOT-proven cause of the failure (RAM-only safe anchored record): unexpected Critical CVE-2026-4738 in backend supply evidence; no APT-unavailable or build-failed markers (unlike the Is Apache pin failures). Package and fix not yet known; no suppression, exception, or CVE fix under T; diagnosis and any next order are owned by ROOT.
- CI at It is NOT all green; no successful image build, no full qualification, no Critical-0 claim.

## Honest process facts

- A first PR description PATCH used `-F description=@file`, which GitHub silently ignored (`description` is not a PR field; the body is `.body`); a blank `.description` is not verification. Corrected with `-F body=@file`; actual `.body` bytes verified equal to the body file by direct Python JSON parse (native 0) after each of the two final body corrections (final body 2257B, SHA256 `1e977bd7fe10d4a695b0030190c06c26422690b9f7648fea96c7010fa564c302`).
- Candidate construction wrote 3 private candidate scratch files (one per source file) under the private control dirs before the formal source writes; candidate bytes pre-matched ROOT receipt `root-T-exact-candidate-review.json`. No global NOFILES or RAM-only claim.
- Prior-round process qualifications preserved by precise reference, not rewritten: q errata (prewrite forecast-cap bypasses f811b0/c65104, NULL turns; no retrocredit), r errata (ad4e53 masked decode, late canonical, missing TEMP pre-inode, effd83), S errata (fd6f02/f2c542 tool failures corrected 71d34a, publication draft inode 12226571 to TEMP 12226575, peer 5d20c3 unfiltered build-log excerpt incident stopped by ROOT d66ae3, model-turn interruption 18:27:53/18:28:11 not a crash) - see the active T order and the immutable q/r/S reports.
- Historical Is CI final: 30 terminal = 28 SUCCESS + 2 FAILURE (Supply-chain + Compose), both caused by Apache `.17` pin availability (ROOT-proved, RAM-only logs). This T refresh restores exactly those pins; official `.18` availability was ROOT-verified (4 package pages HEAD 200) but that is not a tested build.
- The original browser-policy failure cause (S scope) remains UNKNOWN; no cause-fixed or browser-recurrence claim.

## Not done / unaccepted

- No acceptance, merge, release, or MVP; increment 083/8 unaccepted.
- Acceptance gates per the T order remain open: current full 30-check CI (20 strict checks + 10 PG children) all green at It, full 6-image artifact/security qualification, private WHOLE/LOCAL6 runtime qualification (separate ROOT order), strategic satisfaction, ROOT-only merge.
- No Docker, no runtime, no setup in this round; WHOLE/LOCAL6 private inputs INERT/NOT_RUN (`whole-j.sh` 624L `31dc9107...`, `local6-j.sh` 243L `12a9f36e...`).
- The It Supply-chain failure is not diagnosed beyond the ROOT CVE-2026-4738 finding; no guessed fix applied.

## Confirmations

- Scope: only the 3 pin files plus order/active transcript; no dependency, doc, or product change.
- No secret/credential exposure; no production system touched; no raw console payload or credential-bearing URL in this report or the PR body.
- No extra PR, no merge, no force-push, no CI rerun/cancel, no new control reader.
- `COMPLETE`/`OK` never means accepted; strategy alone independently reviews and merges.
