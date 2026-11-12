# 083-8-w report: repair ten newly measured High tuples (PARTIAL)

- Order: `oap/orders/083-8-w-repair-new-high-packages.md` (226L, 14950B,
  SHA `1efa4f7d3243115de3ba7324c7b91a60b427004ca1e6786ca144d4039612bf0a`)
- Mode: AMEND_EXISTING_PR
- Status: PARTIAL
- Repo: ulfe-lmi/slaif-agent-site
- PR: <https://github.com/ulfe-lmi/slaif-agent-site/pull/112> (open)
- Remote head branch: `oap/083-8-a-qualify-public-whole-session`
- Base: main `40cd172109a22ef5f342589b59a4293f35379651`
- Starting remote SHA (Sv): `0b919de6512fe0c5237ef3430bfb42d6df3e9bba`
- Implementation SHA (Iw): `14facd0ff69d6c83a3b50a871ccd5307f74e5d2e`
  (tree `f3abc7bd34cb9e10f736b1b3325bc731cf3af925`, sole parent Sv)
- Report publication commit: SELF
- Pushed commits: Iw (implementation; 9 paths) and SELF (this report only)

## Changes in Iw (9 paths: 7 source + order + active)

W repaired the ten newly measured High tuples with exact source pins
plus a protected APT bootstrap:

- `apt=2.8.4ubuntu0.1` + `libapt-pkg6.0t64=2.8.4ubuntu0.1`
  (CVE-2026-109518, 4 tuples): `infra/apache/Dockerfile` and both
  stages of `services/browser-worker/Dockerfile`.
- `libexpat=2.10.0-r0` (CVE-2026-113351 / CVE-2026-115506 /
  CVE-2026-117610 / CVE-2026-118370, 4 tuples):
  `infra/nginx/Dockerfile`.
- `musl=1.2.5-r24` + `musl-utils=1.2.5-r24` (CVE-2026-107891,
  2 tuples): `infra/postgres/Dockerfile`.

Protection scheme: command-local `-o Acquire::Retries=0` on every APT
invocation that can download packages before fixed APT is installed
(the updates, the first protected installs, and the three early real
purges, with the option trailing the target list); fixed
apt/libapt-pkg are installed first, with installed-version
assertions, before later package downloads. The post-fix builder
purge and both `apt-get -s` simulations are unchanged, and the exact
purge-marker guard in `tools/supply_chain/policy.py:829-844` is
intact. `supply-chain/policy.json` carries the exact sorted install
arrays. `tests/packaging/test_oci_contract.py` (253 to 323 lines, no
new methods) extends the existing per-image assertions: bootstrap
ordering (update precedes first install; both pins in that first
install; both installed-version checks in the full bootstrap window)
in all three affected stages, pinned musl/musl-utils/libexpat
checks, and the worker purge-option counts. `docs/SUPPLY_CHAIN.md`
(419L) adds the source-change-not-measured-build distinction and
keeps the four backend SQLite High findings as a separate explicit
assessment.

## Accepted High baseline (main 40cd; exact 12 six-tuples)

Field order per receipt: image, vulnerability_id, package, version,
type, purl. Exact data and binding from
`root-accepted-High-baseline-six-tuples.json`:

```json
{
 "exact_accepted_High_12": [
  ["browser-worker","CVE-2025-3887","gstreamer1.0-plugins-bad","1.24.2-1ubuntu4","deb","pkg:deb/ubuntu/gstreamer1.0-plugins-bad@1.24.2-1ubuntu4?arch=amd64&distro=ubuntu-24.04&upstream=gst-plugins-bad1.0"],
  ["browser-worker","CVE-2025-3887","libgstreamer-plugins-bad1.0-0","1.24.2-1ubuntu4","deb","pkg:deb/ubuntu/libgstreamer-plugins-bad1.0-0@1.24.2-1ubuntu4?arch=amd64&distro=ubuntu-24.04&upstream=gst-plugins-bad1.0"],
  ["browser-worker","CVE-2026-84782","libssl3t64","3.0.13-0ubuntu3.12","deb","pkg:deb/ubuntu/libssl3t64@3.0.13-0ubuntu3.12?arch=amd64&distro=ubuntu-24.04&upstream=openssl"],
  ["browser-worker","CVE-2026-84782","openssl","3.0.13-0ubuntu3.12","deb","pkg:deb/ubuntu/openssl@3.0.13-0ubuntu3.12?arch=amd64&distro=ubuntu-24.04"],
  ["postgres","CVE-2026-53612","libuuid","2.41.4-r0","apk","pkg:apk/alpine/libuuid@2.41.4-r0?arch=x86_64&distro=alpine-3.23.5&upstream=util-linux"],
  ["postgres","CVE-2026-53613","libuuid","2.41.4-r0","apk","pkg:apk/alpine/libuuid@2.41.4-r0?arch=x86_64&distro=alpine-3.23.5&upstream=util-linux"],
  ["postgres","CVE-2026-53614","libuuid","2.41.4-r0","apk","pkg:apk/alpine/libuuid@2.41.4-r0?arch=x86_64&distro=alpine-3.23.5&upstream=util-linux"],
  ["postgres","CVE-2026-76642","libuuid","2.41.4-r0","apk","pkg:apk/alpine/libuuid@2.41.4-r0?arch=x86_64&distro=alpine-3.23.5&upstream=util-linux"],
  ["postgres","CVE-2026-78408","libuuid","2.41.4-r0","apk","pkg:apk/alpine/libuuid@2.41.4-r0?arch=x86_64&distro=alpine-3.23.5&upstream=util-linux"],
  ["postgres","CVE-2026-78410","libuuid","2.41.4-r0","apk","pkg:apk/alpine/libuuid@2.41.4-r0?arch=x86_64&distro=alpine-3.23.5&upstream=util-linux"],
  ["postgres","CVE-2026-85091","zlib","1.3.2-r0","apk","pkg:apk/alpine/zlib@1.3.2-r0?arch=x86_64&distro=alpine-3.23.5"],
  ["web","GHSA-68fv-2mgg-jv7q","source-map-js","1.2.1","npm","pkg:npm/source-map-js@1.2.1"]
 ],
 "accepted_main": "40cd172109a22ef5f342589b59a4293f35379651",
 "accepted_synthetic_merge": "22dd43103dd0b6f820d26dbb9a65df94abad9cfa",
 "artifact_id": 13115895888,
 "artifact_ZIP_sha256": "9b78c1629cf9dc81c52179629a1b35a71ab35ac9eb32122456ee020df2835f44",
 "artifact_payload_checksums_verified": 53,
 "source_receipt_sha256": "a8d0db1d1a63fa24fbfdd6bdbac5662f5f4b2e380cf65fb481293790fe55d85d"
}
```

## Forecast versus actual (prewrite; all pass)

- Complete formatted seven candidates were built before any source
  write; aggregate forecast: W delta +174/+174 (MAX 180), 39-path
  totals 6227 default / 6223 minimal (HARD 6250, vs main), doc5
  forecast 324 (HARD 500), four-file family frozen 3599 (vs Sg).
- Actual after apply, re-measured on the worktree at Iw, per file
  (add/del) versus Sv: `docs/SUPPLY_CHAIN.md` 26/9,
  `infra/apache/Dockerfile` 11/2, `infra/nginx/Dockerfile` 4/1,
  `infra/postgres/Dockerfile` 6/1,
  `services/browser-worker/Dockerfile` 23/10,
  `supply-chain/policy.json` 10/1,
  `tests/packaging/test_oci_contract.py` 70/0; delta 174/174;
  39-path totals 6227/6223; family 3599/3599; git status exactly the
  7 modified paths; readback and modes verified.
- doc5 (docs/FOUNDATION_INTEGRATION.md, docs/TESTING.md,
  docs/SUPPLY_CHAIN.md, oap/INCREMENTS.md, oap/MVP-PROGRESS.md):
  direct diff versus D18 `d18b6e4c9423f61de99b516be90619bf2ab5d3e0`
  is 320 default / 320 minimal (ROOT c72465). The prewrite forecast
  of 324 was a conservative estimate derived from the candidate
  base; the applied result is 320/320 (within HARD 500).

## Local verification at Iw source

Outcomes as actually preserved (pre-commit WIP byte-equivalent to
Iw; no clean-Iw rerun):

- `uv run --frozen ruff check tests/packaging/test_oci_contract.py`:
  All checks passed (native 0).
- `uv run --frozen ruff format --check
  tests/packaging/test_oci_contract.py`: 1 file already formatted
  (native 0).
- packaging suite, three invocations (exact history preserved):
  - 80c10f, 23:33:44Z, piped `| tail -3`: 72 tests with two errors
    (`FileNotFoundError: 'node'` in
    test_browser_archive_extractor.py); the PATH was incomplete
    (missing the pinned Node dir); the unittest native exit was NOT
    preserved through the pipeline (pipeline native 0).
  - 427698, 23:34:06Z, bare on the same incomplete PATH: native 1,
    the same two missing-node errors.
  - 946791, 23:34:31Z, bare with the pinned Node PATH: 72 tests OK,
    native 0 (the credited result). The two failures were
    invocation/PATH artifacts, not product test failures; no
    further retry.
- `python -m unittest discover -s tests/supply_chain -p
  'test_*.py'`: 46 tests OK (native 0).
- `python tools/compose/verify.py --root .`: compose-policy: OK
  (native 0).
- `python -m tools.supply_chain.policy validate`:
  supply-chain-policy: OK (native 0).

## CI and artifact at Iw (current, dated; source checkpoint)

- Initial observation 2026-11-10T23:40:06.191219Z: 25 check-runs
  (10 success, 1 neutral CodeQL, 14 in_progress).
- Terminal observation 2026-11-10T23:54:37.028254Z (gh native 0):
  30 check-runs = 29 success + 1 failure. The failure is "Compose
  and edge packaging", step 8: control-readiness-fixture FAILED
  stage=wrong-role operation=await-readiness reason=timeout. The
  wrong-role stage has two await-readiness calls; exact phase and
  root cause remain unproved. This is distinct from the earlier
  media-console and Agent-API readiness failures. On this run:
  Supply-chain evidence SUCCESS (job 130209254805, artifact
  13814167417,
  supply-chain-evidence-bc9ea15f67288ca57d4475fe5aad2eb2161ba281),
  CodeQL SUCCESS (42925034988), and browser runtime/image policy,
  full Compose browser E2E, public-agent-acceptance, and
  public-agent-restart passed.
- Iw artifact audit (ROOT e40f64, independent): all ten targeted
  image/package/CVE findings absent at any severity (including
  related IDs), with seven measured exact fixed
  image/package versions; Critical0/ignored0/exceptions0 in all six
  images; prior 61 IDs absent including related; High comparison
  versus the accepted 12: 15 total (11 retained, 1 removed, 4 new
  backend sqlite-libs). Eight separate Medium findings with the same
  four libexpat CVEs on Ubuntu libexpat1 (Apache/worker) are
  unchanged from Sv; the ten targeted W rows were different
  image/package combinations. This is targeted repair evidence, not
  full six-image qualification.
- The Compose failure is outside W source scope: no retry, no
  test/policy weakening, no source expansion, no manual rerun or
  cancel. CI and artifact facts are current as of the dated
  observations and are distinct from the source-change facts above:
  source pins are not a measured build or scan.

## Process qualifications

- Wrong-ref push: the first Iw push (call 459aa3, `git push
  origin HEAD`) followed the local alias branch name and created
  remote branch `oap/083-8-j-execution` at Iw while PR 112 remained
  at Sv. Corrected by the explicit refspec fast-forward `git push
  origin HEAD:refs/heads/oap/083-8-a-qualify-public-whole-session`
  (0b919de..14facd0, native 0). The alias ref is retained for
  strategic reconciliation and was not deleted.
- Packaging three-invocation erratum as recorded in the local
  verification section.
- Constructor pre-failures before any source write (invocation
  artifacts, not product test failures): a test-file escape-anchor
  mismatch (repaired with line-derived blocks); one malformed
  scratch worker with a duplicated `purge -y purge -y nodejs`
  (rebuilt correctly; the official APT argument parser processes
  options after non-option arguments, so the trailing option form is
  valid); a corrupted peer policy.json candidate (invalid JSON plus
  unrelated reflows; rejected and never used); the doc candidate was
  built from the peer base after byte review.
- Prior q/r/s/t/u/v process qualifications are preserved by
  reference to the immutable round transcripts committed with the
  active W order (oap/orders + oap/reports), not recopied here.

## Limitations and acceptance gates

- W is a source pin/structure change only. It does not itself prove
  the installed inventory, CVE absence, a successful build, or
  security qualification.
- Acceptance requires: the current final implementation AND this
  SELF report to pass the full 30 checks (20 strict + 10 PostgreSQL
  children); the complete six-image evidence artifact with the ten
  targeted finding IDs absent at any severity (including related
  IDs) and the measured exact fixed runtime versions; separate
  private qualification; and ROOT review and merge.
- The four backend SQLite High findings remain a separate explicit
  assessment, outside W.
- WHOLE/LOCAL6 remain INERT/NOT_RUN (/tmp/oap-083-8-j/whole-j.sh
  624L, hash prefix 31dc9107; /tmp/oap-083-8-j/local6-j.sh 243L,
  hash prefix 12a9f36e).
- No zero-vulnerability, MVP, release, merge, cause-fixed, or
  six-image-pass claim.

## Confirmations

- No secrets, credentials, or private artifact URLs in this report
  or in the diff.
- No production access; no new PR; no merge or auto-merge; no
  force/reset/rebase/stash.
- No source change beyond the nine Iw paths; no Docker, local
  browser, or image probes under W; no private WHOLE/LOCAL6 work.
