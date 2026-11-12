# OAP 083-8-s report: diagnose-browser-policy (PARTIAL)

- Report ID: `083-8-s`
- Order: `oap/orders/083-8-s-diagnose-browser-policy.md`
- PR mode: `AMEND_EXISTING_PR`
- Disposition: `PARTIAL` (diagnostic implemented and locally
  verified; increment not accepted; final CI and runtime gates
  pending)

## Order and implementation identity

- Order sha256:
  `482f9e9ee181ff0bbd7679958cdeea6311c0c66fe7de2cd320e09e748fb92f2c`
  (180 lines, 11032 bytes)
- Repo: `ulfe-lmi/slaif-agent-site`
- PR: #112 [`OPEN`](https://github.com/ulfe-lmi/slaif-agent-site/pull/112)
- Remote head branch: `oap/083-8-a-qualify-public-whole-session`
  (local alias `oap/083-8-j-execution` is not the GitHub head)
- base main: `40cd172109a22ef5f342589b59a4293f35379651`
- Starting remote SHA (pre-round): Sr
  `b65cac9a37a478064d3f84fa1a4e9005e6e56085`
- Literal implementation SHA (Is):
  `e26920533d208c3e2b218cbec3bf061bff98db6f`
- Is tree: `98a81c16900c14138aaaf793e8b1674c05098ed3`
  (sole parent Sr; 4 files changed, 226 insertions, 12 deletions)
- `Report publication commit: SELF` (convention: final
  report-only commit, sole parent Is)
- Pushed commits: implementation Is (bare push
  `b65cac9..e269205`, direct last command, no force or pipe).
  Implementation commit Is was pushed; report-only publication
  uses SELF
- Remote verification: ls-remote and API PR head both
  `e269205...`; ROOT independent full review (c65876, native 0,
  17:40:55.858790Z): full remote leaf maps 1170->1171, decoded
  four GitHub blob bytes + hashes equal worktree/canonical,
  every other mode/type/blob identical; receipt
  `root-Is-independent-remote-checkpoint-review.json` in
  `/tmp/oap-083-8-s-control/`

## Exact changes (4 paths in Is)

- `tests/e2e/observation.ts` modified, 195 to 199 lines, +11/-7
  - sha256:
    `0ad0f85cbc443ecd4f58aded5266f4dd262a585eb00a2c396bf1b19a2f40e34f`
- `tests/contracts/e2e-observation.test.ts` modified, 274 to 304
  lines, +34/-4
  - sha256:
    `656a8246d23ba036a7eb0100ff181db6a43227d36e42deaf99c85b841ab6bb60`
- `oap/orders/083-8-s-diagnose-browser-policy.md` added, 180 lines
  (exact canonical bytes, order sha256 above)
- `oap/active` modified, 8 bytes `083-8-s` + LF
  - sha256:
    `ea5ffdee265b8adacd5c78b002684372dba18f70ea67e3b5beb807cff0ea45a7`

## Source change (test diagnostics only)

The combined family label `csp-permissions-policy` is replaced by
three fixed labels mapping exactly to the existing prefix
predicates:

- `policy-refused` <- `text.startsWith("Refused to ")`
- `policy-csp` <- `text.startsWith("Content Security Policy")`
- `policy-permissions` <- `text.startsWith("Permissions policy violation:")`

Exported names `ConsoleMessageFamily` and
`classifyConsoleMessageFamily` preserved. No new predicate,
dynamic label, captured group, or captured output. Original
classifiers, exports, failure verdicts, `expectConsoleClean` /
`toEqual([])`, and the reporter 300-char cap unchanged.
Pre-change grep baseline: the old label occurred only in the
two changed source files; after the change the source label is
removed, and the immutable transcript retains the history.
`media-publication.spec.ts` consumes the family classifier
without asserting the label string.

New contract cases (`e2e-observation.test.ts`):

- hostile/private-suffix redaction variants for each of the three
  shapes; the loop asserts results contain no secret/token/credential
- near-prefix lookalikes that stay `other`: lowercase CSP text,
  `Refused  to` (double space), missing colon,
  `Content Security Polices`
- three policy-form cases expecting `other-browser-error` added to
  the "keeps the original message verdicts" test

## Source caps (actual, computed, prewrite-asserted)

- 24-path cumulative vs main40cd (22-path inventory + the two
  diagnostic files; only the exact order/report/active paths
  excluded, never whole `oap/`): **5890 default / 5886 minimal**
  (HARD 6000)
- four-file family vs Sg `89ab5ec85273ebad10f9c6963b98811cdf992c54`:
  **3599** (HARD 3600); byte-frozen this round (worktree == Sr)
- five-doc vs D18 `d18b6e4c9423f61de99b516be90619bf2ab5d3e0`:
  **285** (HARD 500); the five bounded product docs are
  unchanged this round (Is's only doc path is the added order)

## Local verification (four standing commands)

Execution checkout, pinned toolchain: Node v24.22.1, pnpm 11.22.0,
Vitest 4.1.10, Prettier 3.9.6, Next.js 16.4.1 build.

1. `pnpm lint` - direct native exit 0 (own session 51049)
2. `pnpm format:check` - inner `NATIVE_RC=0`; "All matched files
   use Prettier code style!"
3. `pnpm typecheck` - inner `NATIVE_RC=0` (9 workspace projects +
   root + `tests/e2e` tsc)
4. `pnpm test` - inner `NATIVE_RC=0` (own session 53940): full
   build of all projects; packages scope-catalog 8/8,
   component-catalog 8/8, browser-tool-contracts 24/24,
   composition-schema 19/19 (3 files); apps/web `node --test`
   32/32; services/browser-worker unit 22/22; vitest
   `tests/contracts/*.test.ts` 3 files / 36 tests passed (includes
   `e2e-observation.test.ts` with the new cases)

Process qualification: commands 2-4 used a trailing
`; echo NATIVE_RC=$?`; the outer tool native is masked, so pass is
proved by the explicitly printed inner `NATIVE_RC=0` plus complete
success summaries, not by outer 0 alone. No reruns.

Subject qualification: the four commands ran while the two changed
files' bytes were exactly the Is blobs (worktree blobs
`cca7e67d...` and `8f5bec48...`) with all other files at Sr:
source-equivalent to Is, not clean-Is reruns.

Non-fatal pre-existing apps/web test warning:
`MODULE_TYPELESS_PACKAGE_JSON` for bounded-collection-filter.ts.

## GitHub CI (official, subject Is; no rerun or cancel)

Dated single-read check-run observations:

- post-push (~17:35Z): 25 present, 12 success, 13 in_progress,
  0 failed (historical snapshot)
- ROOT independent 17:40:55.858790Z: 25 present, 19 SUCCESS,
  6 pending, 0 failed (historical snapshot)
- final-state 17:49:35.730465Z (executor) and
  17:48:58.209296Z (ROOT independent, e5858c): 30 runs,
  28 SUCCESS, 1 FAILURE, 1 in_progress, 0 pending
- terminal-state 18:10:40.459709Z (executor), ROOT
  independently confirmed 18:12:27.224452Z: all 30 runs
  terminal: **28 SUCCESS, 2 FAILURE, 0 pending**

Failures at Is (executor/primary 21 read no raw logs; the
causes below come from ROOT independent RAM-only reviews):

- **Supply-chain evidence**: job/check-run `130005618845`,
  run `42866355039`, head `e269205...` (Is)
- **Compose and edge packaging**: job `130005618783`

### Supply-chain evidence: cause proved (ROOT independent review)

- Receipt `root-Is-supply-pinned-package-failure-review.json`
  (ROOT RAM gh native 0; full log 242515 bytes / 2767 lines,
  sha256 `ccfa60b795bc94196c79f6f05c43d682e90c803207dcf71691d82ea51f269db6`):
  APT reports the pinned `apache2`, `apache2-bin`,
  `apache2-data`, `apache2-utils` at `2.4.58-1ubuntu8.17`
  unavailable.
- All four pin pairs validated against `infra/apache/Dockerfile`
  and `supply-chain/policy.json`; the pin is also referenced in
  `tests/packaging/test_oci_contract.py`.
- The first apache build exhausted 3 attempts; build exit 100;
  step native 1.
- No source-policy ERROR or critical-vulnerability finding was
  proved; the failure prevents complete 6-image qualification.
- Official noble SECURITY lists `2.4.58-1ubuntu8.18` with
  matching dependencies: `.18` amd64 `apache2` and
  `apache2-bin`/`apache2-utils`, `apache2-data` confirmed by
  ROOT official archive HEAD 200 at 18:30:40.811646Z; the
  noble-updates data page still lists `.17`. Receipt
  `root-Apache18-official-package-availability.json` in
  `/tmp/oap-083-8-s-control/`; no signed install/build proof.
- Pin availability is identified but unrepaired: no pin/source/
  test edit in this S round; any bounded repair belongs to the
  next order (ROOT-issued after formal S closure).

### Compose and edge packaging: cause identified (ROOT RAM review)

- ROOT independently verified 18:23:42.532171Z: job
  `130005618783`, run `42866355039`, head Is; failed step 8
  "Run clean deployment, topology, edge, and failure smoke".
- Complete RAM-only log (gh native 0, 344303 bytes / 3644 lines,
  sha256
  `51527391aedba29e9e824cc8c90c95015b6d1d73de6beb15330096cc64ba9e17`):
  all four Apache packages at `2.4.58-1ubuntu8.17` unavailable,
  each with 2 occurrences, first at lines 3592..3595; source
  validated. Receipt
  `root-Is-Compose-pinned-package-failure-review.json`.
- Both current CI failures are Apache build/package
  availability; identified but unrepaired in this round.
- The original browser-policy cause (len-79/HTTPS metadata)
  remains unknown. No fix, pass, or new browser-recurrence
  inference.

## Process qualification: raw build-log output incident

- Peer 17 actual `5d20c3` printed an unfiltered build-log
  excerpt despite the no-raw-line/URL instruction; the output
  was retained in the actor journal and ROOT observation (not
  RAM-only overall).
- ROOT `d66ae3` stopped that output path; ROOT's independent
  RAM review emits only validated public package/version/source
  fields.
- The incident is preserved; no deletion; no global NOFILES or
  no-raw-output claim.
- ROOT Escape 18:27:53.194 ended a stalled model editing turn
  (same healthy CLI; TEMP bytes/inode unchanged); resumed
  18:28:11.898. Not a crash or source failure.

## Constructor process facts

Pre-source-write constructor failures (private helper; no repo
mutation in any):

- `1c34f8`: TypeError (dead conditional string splice)
- `78963a`: SyntaxError (escaped-quote literal; nothing executed)
- `19fae1`: OSError EINVAL (invalid `O_DIRECTORY` create flag for
  the scratch dir)
- `a64624`: successful construction write (native 0)

API artifact note: after the successful bare push `bb7381`, the
REST commit JSON has no top-level `tree` field (`bf8096` KeyError);
corrected access `e63da9` read `commit.tree`. The stronger byte
proof is ROOT's full remote 1170->1171 leaf-map review with
decoded blob bytes + hashes equal to worktree/canonical (c65876,
native 0); REST returned no blob contents fields.

## Errata and prior-round references (no history rewrite)

- q report `oap/reports/083-8-q-qualify-frozen-lifecycle-source.md`
  (PARTIAL): cap-forecast bypasses f811b0/c65104 and NULL-turn
  errata stand as recorded (q errata remain q).
- r report
  `oap/reports/083-8-r-finish-bounded-runtime-qualification.md`
  (PARTIAL): masked decode ad4e53, late canonical copy, and
  missing TEMP pre-inode errata stand as recorded (r errata
  remain r); WHOLE/LOCAL6 constructed-inert, not run. The r
  effd83 unrequested extraction / false NOFILES stays qualified
  per the active S order.
- No global "NOFILES" claim for this round: source writes (the two
  test files), API artifacts, and candidate scratch DID occur in S.

Private inputs remain INERT and NOT RUN:
`whole-j.sh` 624L (sha256 `31dc9107...`) and
`local6-j.sh` 243L (sha256 `12a9f36e...`).

## Remaining gates (unchanged)

- Is remains failed (30 terminal: 28 SUCCESS / 2 FAILURE);
  the future repaired implementation and the final SELF report
  require current successful 30; the unchanged failed Is is
  never rerun or relabeled
- Runtime qualification per full r order (WHOLE/LOCAL6 not run)
- Current SELF report commit at publication
- Full product architecture/privacy/acceptance requirements
- ROOT independent review and verified merge (executor never merges)

## Confirmations

- No merge or release/MVP; original browser cause remains
  unknown and no cause-fixed claim
- No zero-vulnerability claim (push-time remote notice referenced
  13 dependabot findings on the default branch; not assessed here)
- No new PR; PR112 amended only
- No allowlist/ignore/skip/xfail, mock, timeout, retry, or
  relaxation of any check
- No raw console payload, credential, or production access in
  this report; S changed test diagnostics only - a future pin
  repair belongs to the next order, and no dependency, CI,
  lock, or product-doc byte changed in Is
