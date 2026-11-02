# OAP 083-8-i execution report: cohesive lifecycle capture, closed PARTIAL with exact WIP preserved

## 0. Header facts

- Round: 083-8-i of semantic increment 083/8 (closed PARTIAL by strategic
  decision; increment not concluded); CLOSURE_ONLY continuation of the
  G2/G5/G6 verification closure; AMEND_EXISTING_PR mode.
- Order: `oap/orders/083-8-i-cohesive-lifecycle-capture-and-fresh-gates.md`
  (304 lines, 19839 bytes, content SHA256
  `60867959d8a044e403862cd8e83631fe0ce6c7b8a6218c718cf64a126fb58b50`,
  blob `9f70b585c1ba9e8e08504d8e255c211dedfdba3e`); activated
  2026-10-30T00:45:08.949618Z after the same complete TEMP lint/fsync/atomic
  order+active publication; one exact control OK (2 bytes `4f4b`, no LF,
  native 0; writer close 2026-10-30T00:45:09.054551Z) consumed by the
  existing primary control wrapper 782980/child 782982, which retained
  `/tmp/oap-083-8-h/next-control-signal.bin` and its `.native` sidecar and
  was verified absent at report preparation.
- PR: `AMENDED_EXISTING_PR` #112
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/112>, state open
  (verified at round start and at report preparation); branch
  `oap/083-8-a-qualify-public-whole-session`; base main
  `d18b6e4c9423f61de99b516be90619bf2ab5d3e0` (unchanged this round).
- Starting remote SHA (Sh): `6b77175735ec5a2954fb922933dbcfe81a40a6d1`
  (h report-only SELF; verified as remote branch head and PR API head at
  round start).
- Literal implementation SHA (Ii):
  `5bf6c3dfc0ef3ab277eaf279c8d2db3a7888eb64` (tree
  `081b3cf99e36bb6891ec72f67163e7857b8404e7`; sole parent Sh; committed
  2026-10-30T01:46:35Z). Explicitly an UNTESTED PARTIAL WIP preservation
  commit - not the final tested Ii envisaged by i acceptance; no quality
  gate, test, or runtime was run against it.
- Report publication commit: SELF (this report; sole parent literal Ii).
- Pushed commits this round: Ii (verify.py WIP + exact i order + active)
  and SELF (report-only, sole new path).
- Status: PARTIAL (ROOT strategic decision; not accepted; not merged).

## 1. Source state: exact 264-line WIP preserved

- Exactly three allowed paths were staged and committed:
  `tools/compose/verify.py`, the i order, `oap/active`. Human files
  `.codex/`, `CODEX-SESSIONS.md`, `codex.sh` remain untracked, untouched,
  and uncommitted.
- `tools/compose/verify.py` versus Sg: +264 added / -0 removed. At Ii the
  path is 100755 blob `5bdaaadbfa71910965ae632b6f81e1da3060b83f`, file
  SHA256 `78bcde4583971f0c0ab681e0deb7373c219881e1229eeb972b840413df96441d`,
  44758 bytes, 1170 lines.
- The other three allowed paths are byte-identical to Sg at Ii:
  `tools/compose/smoke.sh` (1355L/73203B),
  `tests/packaging/test_compose_smoke_contract.py` (189L),
  `docs/TESTING.md` (415L). No test, doc, helper, staging, or runtime write
  occurred this round.
- The WIP (static, unapplied-to-behavior, unexecuted, untested) is a
  cohesive private evidence I/O core inserted between `_fail` and
  `validate_config`, plus `import stat` and `import time`: stable
  safe-error helper; id/integer/safe-relpath validators; componentwise
  directory-fd opener (every component `O_DIRECTORY|O_NOFOLLOW`, public
  ancestors allowed, final directory euid-owned 0700); all-fd close helper;
  exclusive 0600 receipt writer with strict `utc/time_ns/record` envelope;
  strict JSON duplicate-key/nonfinite hooks; private flat receipt reader.
  No CLI dispatch, no `__main__` change, `main()` unchanged; the import
  remains inert and the new private definitions are unused by existing
  code.
- Construction happened in two measured stages versus Sg: (1) a 250-line
  core, (2) the ROOT-ordered finite repairs (+14 lines, total 264):
  `from None` in the safe-error helper; writer record-dict validation;
  strict serialization (`allow_nan=False`; safe `TypeError`/`ValueError`/
  `RecursionError` handling); safe UTF-8 handling; the 1 MiB size bound
  enforced before any leaf is created or written; euid-owner check added to
  the leaf fstat gate alongside type/mode/size.
- Only static inspection occurred, on the actual host interpreter: AST
  parse and line-length check (no line over 88). Not run: Ruff, pytest,
  unittest, affected checks, ALL31, any runtime, any Docker or quality
  gate.
- WIP limitations, preserved as unaccepted (no new Unicode framework or
  test requirement was added during this closure):
  - `from None` suppresses displayed exception chaining; it does not erase
    in-memory `__context__`.
  - Default `ensure_ascii=True` escaping means actual lone-surrogate input
    refusal cannot be claimed without tests.
  - The reader duplicate-key/nonfinite/UTF-8/size refusals and the writer
    serialization guards are untested at this time.
- The remaining complete four-path work (verify.py collectors/helper/audit/
  CLI, smoke.sh opt-in wiring including the 27 helper sites, meaningful
  test additions, docs/TESTING.md section) is forecast at approximately
  2040 gross added+removed lines versus Sg: an unmeasured natural-line
  estimate without packing. It is not a complete candidate, not proof of an
  unavoidable lower bound, and not a cap violation; the actual preserved
  264 lines are under HARD 1800. No force-fit, packing, or proof deletion
  occurred; the complete patch does not exist and is not claimed.

## 2. I1-I8 status this round

### I1 Scope/budget and remote identities - PARTIAL

The preserved WIP is within the four allowed files and under HARD 1800;
order/active bytes are exact. A complete-candidate remote identity cannot
exist (no complete candidate was formed); the Ii identity is recorded in
section 1.

### I2 Deterministic pre-disposal capture - NOT IMPLEMENTED

No collector, helper, CLI, smoke wiring, or runtime; the I/O core is inert
and unused by any path.

### I3 Test meaning and affected/ALL31 at Ii - NOT RUN

No test changes; no Ruff/pytest/unittest/affected/ALL31 execution. The old
30 Sg checks are old-source results on the g implementation, not Ii gate
proof.

### I4 Fresh WHOLE - NOT RUN

No WHOLE runner, no Docker action, no scratch input written
(`whole-i.sh` was never created).

### I5 Fresh LOCAL6 - NOT RUN

No LOCAL6 execution; `local6-i.sh` was never created.

### I6 Unaffected I_f carry - only within original qualified subjects

Q80/FULL363/P7 carry remains bound only to the exact original qualified
subjects and their identity/scope gates (g report); nothing relabeled to
Ii; no new carry asserted.

### I7 Final SELF CI - no acceptance

Ii CI is fresh/pending at publication; Sh CI observed 28 success + 2
failure (section 3); no check passing is claimed anywhere.

### I8 Immutable report/publication/FIFO - per section 5

This report; the publication, verification, and FIFO steps are stated
prospectively where not yet executed, with actual receipts to follow in the
closure message.

The original P1-P7 acceptance criteria and all full-product requirements
remain preserved by reference (order section "Acceptance, truthful
reporting and synchronization"); nothing narrowed.

## 3. CI as actually observed

- Sh `6b771757` (observed 2026-10-30T01:47Z via the GitHub API, read-only):
  30 check runs - 28 completed/success, 2 completed/failure:
  - Supply-chain evidence (run `40981094419`, job `123821259915`), failed
    2026-10-30T00:50:01.741Z: web Node 24.14.1 CVE-2026-111497 (Critical),
    native 1. Scan artifact 12945032923 (11213308B, SHA256
    `fcd9e822cbe67b67a54c837d6fe66d9f759e45f63fae586bc429118e76235139`,
    38 members) was streamed independently by ROOT.
  - Compose and edge packaging (run `40981094419`, job `123821259675`):
    media-publication final console tuple, source other / message
    other-browser-error / len 79 / https; root cause UNKNOWN. Console-clean
    assertions and redaction were not weakened, and this is not labeled
    infrastructure.
- Browser-worker Node 24.18.1 and Ubuntu libbrotli1 `1.1.0-2build2`
  (Medium in the artifact; fixed in `1.1.0-2ubuntu0.1`) need bounded
  assessment/remediation; "no Critical in that scan" does not mean
  unaffected. No suppression, ignore, or vulnerability exception was added.
- The official Node security release 2026-10-21 fixes affected 24.x at
  24.22.1; scanner firstObserved 2026-10-29 is not a publication date. The
  fix is outside this four-file/no-dependency order and was not applied
  here.
- Ii `5bf6c3d`: fresh CI pending at publication; nothing claimed.

## 4. Strategic closure record

- ROOT closed i PARTIAL by strategic decision
  (`/tmp/oap-083-8-i/root-close-i-partial-for-node-prerequisite-decision.txt`):
  no further collector/helper/CLI/smoke/test/doc piece in i; no Node/Brotli
  patch or CI rerun within this order; the exact 264-line WIP is preserved
  as static review input only, with no code/test acceptance.
- PR112 remains OPEN ON HOLD (inactive) after this round: not abandoned,
  not accepted. ROOT will author a separate bounded 083-9 Node/Brotli
  security PR from verified main; only one active execution increment at a
  time (083/8 inactive while 083/9 runs); 083/8 resumes only by ROOT's next
  same-PR order after security main is verified. Numeric 083 and the full
  product remain unresolved; no advance to 084. This applies the
  human-approved semantic-increment/PR amendment; no mixed Node family
  enters the public qualification PR; no historical cap waiver (h 500 and
  i 1800 stand as recorded).
- The original full product remains unresolved and preserved: immutable
  effective net pending U, true causal closure, complete Agent 025 /
  Editor 028-069 / human Media 030 audits, exact committed==U and no
  Pending INSIDE actual reviewer, durable timeline/resource diff after
  cleanup, drift/conflict/history/multisnapshot/stale tabs/original
  first-touch; Full-U conservative grouping remains UNAPPROVED and browser
  evidence is not a fake COW operation. Then the D5-approved sequence
  (direction approved 2026-09-20; no new human permission gate invented
  here): 084 conflictsafe, 080 real MCP, 085 News, 086 destructive, 087
  source-sweep, 088 reconstruction, 089 expiry/revoke/cancel/retention/
  BYTEGC/recovery, 090 restore, 091 full hostile MVP, plus human-approved
  release criteria; all 18 fields, common forms, reviewer-without-create,
  phone+desktop, truthful discovery/nav, actual Apache HTTP, FREEZING
  recovery/leases/retained media/backups. No qualification-only,
  preview-only, or narrower release-completion substitution. No product
  completion claim.

## 5. Procedure, publication, and remote proof

Done this round (actual receipts retained under `/tmp/oap-083-8-i/`):

1. One complete TEMP prepared inside `oap/reports/` on the same
   filesystem: `.083-8-i-cohesive-lifecycle-capture-and-fresh-gates.temp.md`;
   exact repository markdownlint CLI 0.23.2 `--no-globs` on the SAME
   complete TEMP: native 0, one file, zero issues (every edit re-linted).
2. Pre-hash/UTC/raw time_ns/inode/size of the closed TEMP; explicit file
   fsync; same-inode atomic rename to the sole report path;
   parent-directory fsync; post-rename SHA256 verified equal to the linted
   TEMP.
3. The Ii source-preservation commit (section 0) was pushed; post-push
   `ls-remote` verified the remote branch head equals Ii.
4. The Sh CI observation (section 3) was made via the GitHub API,
   read-only, at the stated time.

To be executed before the single response OK (prospective at this commit;
actual receipts reported in the closure message):

1. Report-only SELF commit: sole parent literal Ii
   `5bf6c3dfc0ef3ab277eaf279c8d2db3a7888eb64`, sole new path this report;
   pushed to the PR branch.
2. Explicit remote proof: the actual PR API head SHA compared with SELF and
   rechecked if stale; SELF sole parent Ii; sole report path present;
   remote report bytes/hash equal to the linted TEMP; PR112 still open with
   base main `d18b6e4c9423f61de99b516be90619bf2ab5d3e0` and unmerged.
3. ONE exact ASCII OK (2 bytes `4f4b`, no LF) written to the verified
   response FIFO (inode 4470112; ROOT sole i response reader
   12870/PID785048) and the writer closed; no replay; the old h readers
   16402 and 92598 are not polled.
4. Exactly ONE byte-retaining next control reader (tool-owned long-lived
   session; full bytes + EOF + native retained separately) on control FIFO
   inode 4470111; its handle/PID/path reported to ROOT.

Forward h precision errata (carried without editing h): the h report's
pre-response branch proof was exact SELF, but the actual PR API then printed
the earlier Th `8231c7b0e14faf3abba425398698de22d0760857`, not SELF; ROOT
independently verified the current PR head later; that comparison is not
claimed to have passed pre-wire. In this round the actual PR head is
explicitly compared with SELF and rechecked if stale before signaling. The
h wire/next-reader publication steps were prospective at h commit time; the
actual h response EOF was 2026-10-30T00:40:15.179036Z. The initial rm-based
reader attempt was rejected before execution; a nohup reader disappeared
and one verified replacement waited; no control replay. The broad h
no-write/read-only-scratch wording applied only to no product patch/no gate
execution: the earlier unauthorized text copies and the later required
local Node/lint/publication writes remain factual. Secret claims are
qualified to inspected scope; universal forensic absence is never inferred.
All original deviations are retained.

## 6. Limitations and unresolved criteria

- I1-I8 are unresolved as stated above; the complete four-path patch,
  affected checks, fresh ALL31/WHOLE/LOCAL6, and final SELF CI all remain
  pending under a later order.
- The approximately 2040-line unmeasured estimate exceeds planning 1400 +
  reserve 400 and HARD 1800 at natural line counts; continuation needs a
  ROOT scope/budget decision (bounded scope split across sequential bounded
  increments, an explicit budget order, or scope reduction). No force-fit
  or proof drop was attempted.
- Node 24.14.1 Critical CVE-2026-111497 (and the pending Node 24.18.1 /
  libbrotli1 assessments) is a prerequisite handled by the separate bounded
  083-9 security PR; the packaging job failure root cause remains UNKNOWN.
- The 264-line WIP is untested, statically preserved code; acceptance and
  merge are ROOT's alone.

## 7. Confirmations

- Scope: this round's commits change only `tools/compose/verify.py` (WIP),
  the i order, and `oap/active` (Ii), plus this report (SELF). No other
  source, test, doc, dependency, lock, CI selector, authority, or
  infrastructure change. `.codex/`, `CODEX-SESSIONS.md`, `codex.sh`
  preserved untouched. No new branch/PR, no merge, no auto-merge, no
  reset/force/amend/rebase/clean/deletion of preserved history or human
  files.
- Secrets: none in any artifact; no capability, cookie, DB URL, setup
  credential, or private-artifact content; the WIP was never executed or
  connected to Docker.
- Production: untouched.
- Local setup: Node v24.22.0 (official nodejs.org dist tarball, SHA256
  verified against SHASUMS256-v24.22.0.txt) at
  `/tmp/oap-083-8-h/node-v24.22.0-linux-x64/bin` with markdownlint-cli2
  0.23.2 via npx, disposable round scratch; no product dependency or lock
  change.
- Docs: `docs/TESTING.md` is unchanged this round; the preserved WIP is
  inert, so no product behavior change required documentation.
- Tests: none run; no all-passed claim; no check-passing claim.
- No release, no acceptance, no merge, no next-objective advance.
