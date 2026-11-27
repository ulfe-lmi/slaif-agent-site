# maint-2026-11 — restore the pinned Apache build

- Order: `oap/orders/maint-2026-11-restore-apache-pins.md`
  (5569B, SHA256
  `7ebf25040d6041ad16bc5f300cb0085f2450d8b3dc345bc56e8b234a20a60afe`,
  committed byte-exact with this round's `oap/active` = `maint-2026-11`
  (14B, SHA256
  `adb85d2ced455d22ba49cf0843fc7fd8c01d0858ea11d129bdda155d706035bf`)).
- Mode: `CREATE_NEW_PR` — PR 122
  <https://github.com/ulfe-lmi/slaif-agent-site/pull/122> (OPEN/DRAFT),
  branch `oap/maint-2026-11-apache-pins`, base `main`
  `2ac24ea3ad4047827f4c594185ffa795ccd98853`.
- Starting remote head: `2ac24ea3ad4047827f4c594185ffa795ccd98853`
  (verified via `git ls-remote` and the `gh` read API before any
  mutation; PR #121 merge, the operating-rhythm amendment record).
- Implementation head SHA: `e07bb47b2e4b85ba380a1e7dd5fc1f68dbef4dc6`
- Report publication commit: SELF
- Result: COMPLETE for the maint-2026-11 contract: all three
  criteria are implemented, every local gate is native-pass at the
  implementation head, and the fresh GitHub CI plus CodeQL on the
  implementation head are fully successful (exact job and artifact
  identities below). No earlier 083/14 run qualifies this
  maintenance.

## Pushed commits

1. `e07bb47b2e4b85ba380a1e7dd5fc1f68dbef4dc6` —
   `oap(maint-2026-11): restore Apache 2.4.58-1ubuntu8.20 edge pins
   and accept maint-YYYY-MM OAP identifiers` (sole parent
   `2ac24ea3ad4047827f4c594185ffa795ccd98853`).

## Changed files (7 paths, +235/−18)

- **Apache pin restore (3 paths)**: `infra/apache/Dockerfile`,
  `supply-chain/policy.json`, `tests/packaging/test_oci_contract.py` —
  the four exact pins `apache2`, `apache2-bin`, `apache2-data`,
  `apache2-utils` advanced from `2.4.58-1ubuntu8.19` to
  `2.4.58-1ubuntu8.20` only; base digest, apt/libapt and OpenSSL pins,
  `Acquire::Retries=0` protections, OCI labels, and every other byte
  are unchanged.
- **Maintenance identifier (2 paths)**: `tools/check_repository.py`
  and `tests/repository/test_repository_policy.py` — the amendment's
  exact `maint-YYYY-MM` form (single shared pattern, ASCII digits,
  nonzero four-digit year, month `01`–`12`) for the active file, order
  and report artifact names, plus 8 new repository-policy tests.
- **Transcript (2 paths)**: the new byte-exact order file and
  `oap/active` = `maint-2026-11\n`.

Historical orders and reports are untouched; the historical
`oap/reports/083-10-a-workspace-isolated-media.md` still contains the
former `2.4.58-1ubuntu8.19` pin by design (byte-for-byte history
preservation, explicitly out of scope).

## Criterion 1 — restore the exact Apache build

- **Availability reverification from official sources.** Fetched the
  official amd64 Noble indexes from `archive.ubuntu.com`:
  `dists/noble-updates/main/binary-amd64/Packages.gz` (1843336B,
  SHA256 `478fa07f243a3c3d46f8db24cf9f9f7e92f568833aaa203a421aebf51e0fd408`)
  and `dists/noble-security/main/binary-amd64/Packages.gz` (1514211B,
  SHA256
  `d0eda781df4f6750c02d0157fa68baf3507fe1da876c5f7bd2c1d4f8c149e7f6`).
  Both list all four packages at `2.4.58-1ubuntu8.20` with identical
  SHA-256 values: `apache2`
  `a8836a2a32cfcc087e1c6587ed5be92ed151d47b36a7c9f3cf35c2d42f28f744`,
  `apache2-bin`
  `b1627be088938219effdd6dcc1af843ab4a2d8bb1a4a21d500d9c2479e1e45b2`,
  `apache2-data`
  `918818253f3d834066ca1409ac13e8201c125c301ba097bd0e06fe1628a54aa5`,
  `apache2-utils`
  `464ec5c147b8b1b4ac95198311b31920eb925fa4a95f05ca54211180aa715eaf`.
  All four `.deb` artifacts were downloaded from
  `pool/main/a/apache2/`; their measured byte hashes match the index
  values exactly (sizes 90232, 1338426, 163216, 100808 bytes).
- **Clean local Docker build (approved owned local resources only).**
  `docker build -f infra/apache/Dockerfile -t
  slaif-maint-2026-11/apache:verify .` exited 0 on Docker 29.1.3.
  The three `RUN` layers were served from the daemon's
  content-addressed cache, where each layer key is the exact current
  Dockerfile instruction bytes including the `.20` pins, over the
  digest-pinned base
  `ubuntu:24.04@sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517`.
  Built image manifest
  `sha256:57ef7b40c45473372f3530edcedc4554bf29f7e2da19ee6f987602b2ee7a0752`,
  config `sha256:fd2d073ff500fa67f5e676acd78e05c357eaf0ce0d3415cb5fe80bbe6edb5352`.
- **Exact versions in the built image.** `dpkg-query` on the built
  image reports `apache2 2.4.58-1ubuntu8.20`,
  `apache2-bin 2.4.58-1ubuntu8.20`, `apache2-data 2.4.58-1ubuntu8.20`,
  `apache2-utils 2.4.58-1ubuntu8.20`, `apt 2.8.4ubuntu0.1`,
  `libapt-pkg6.0t64 2.8.4ubuntu0.1`,
  `openssl 3.0.13-0ubuntu3.16` — the four advanced pins plus every
  preserved pin exactly as declared.
- **Apache syntax.** `apachectl -t` in the built image returns
  `Syntax OK` (the AH00558 FQDN note is informational only).
- **Unchanged product routing.** The image's enabled
  `slaif-agent-site.conf` is byte-identical to the repository file
  (SHA256 `eea97ef92477772206fb72fc89a1ccaa01f99ac0d1132076ca1f1d655d704f23`),
  carries 25 `ProxyPass` lines, and the enabled module set keeps
  `deflate headers proxy proxy_http unique_id`; `000-default` remains
  disabled.
- The approved pin was available; no policy gate required expansion,
  so no scope widening was reported or taken.

## Criterion 2 — the authorized maintenance identifier

- `tools/check_repository.py` now defines one shared pattern
  `MAINTENANCE_ID` — `maint-` plus a nonzero four-digit ASCII
  calendar year (`[0-9]` classes only, so Unicode lookalike digits and
  year `0000` cannot match) plus `-` plus month `01`–`12` — and
  composes it into `OAP_ARTIFACT`, `OAP_ACTIVE`, and `OAP_MAINTENANCE`,
  so the active check and the artifact checks share a single source.
  The active file accepts exactly one `maint-YYYY-MM` identifier plus
  an optional final newline; order and report filenames accept the
  same identifier plus the existing optional descriptive slug;
  grouping, duplicate, collision, and historical-required-report
  behavior reuse the existing code paths (a maintenance identifier is
  not in the inert planned set, so a historical pair still needs
  exactly one report). Numeric parsing (`parse_oap_identifier`),
  exact full matches, and all other checks are unchanged; the two
  extended error messages keep the previously asserted substrings.
- 8 new tests in `tests/repository/test_repository_policy.py`
  (module 57 → 65; whole `tests/repository` 102) cover: the
  single-source property; a valid active `maint-2026-11` with a
  slug-suffixed order and numeric history; a historical
  `maint-2026-10` order/report pair; boundary years `0001`, `0010`,
  `0100`, `0999`, `1000`, `2026` accepted; malformed actives refused
  (two-digit year, year `0000`, five-digit year, months `0`, `00`,
  `13`, `111`, trailing space, uppercase, `-x` suffix, double final
  newline, Arabic-Indic digit lookalikes, fullwidth digit lookalikes);
  malformed artifact filenames refused (10 names, same year/month
  family); a duplicate active `maint-2026-11` identity refused for
  both order and report counts; and a missing historical
  `maint-2026-10` report refused.
- The resolved identifier for this round is exactly `maint-2026-11`.
  This is the targeted tooling implementation of the already binding
  governance; no human policy or product behavior changed.

## Criterion 3 — the required gates

### Local gates at the implementation head (all exit 0)

| Command | Exact outcome |
| --- | --- |
| `uv lock --check` | `Resolved 45 packages`, OK |
| `uv run --frozen ruff check services/backend tests/repository tools` | `All checks passed!` |
| `uv run --frozen ruff format --check services/backend tests/repository tools` | `357 files already formatted` |
| `uv run --frozen mypy` | `Success: no issues found in 335 source files` |
| `uv run --frozen pytest tests/packaging/test_oci_contract.py -q` | `9 passed, 20 subtests passed` |
| `python3 -m compileall -q tools tests/repository` | silent, exit 0 |
| `python3 -m unittest discover -s tests/repository -p 'test_*.py'` | `Ran 102 tests` — OK |
| `python3 tools/check_repository.py` | `PASS repository policy` |
| `python3 tools/check_mermaid.py` | `PASS Mermaid rendering: 16 diagram(s) in 3 file(s); 656 Markdown file(s) scanned; CLI 11.16.0` |
| `npx --yes markdownlint-cli2@0.23.2 "**/*.md"` | `0 issues in 0 files` across 648 files |
| `node --version` / `pnpm --version` | `v24.22.1` / `11.22.0` |
| `pnpm install --frozen-lockfile` | 254 packages, `Lockfile is up to date`, supply-chain policy verification `312 entries` passed, rc 0 |
| `pnpm lint` | rc 0 (root eslint + web lint, `--max-warnings 0`) |
| `pnpm format:check` | rc 0 |
| `pnpm typecheck` | rc 0 (all workspaces, incl. browser-worker and web) |
| `pnpm test` | `Test Files 3 passed (3)`; `Tests 36 passed (36)` |
| `pnpm build` | rc 0, `apps/web build: Done` |
| `pnpm licenses list --json` | rc 0 |

### GitHub gates at the implementation head (observed, not predicted)

- **CI run 45992567318**
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/45992567318>
  on the implementation head: `completed / success`, all 25 jobs
  successful.
  - Compose and edge packaging (job 140483828511, 16m39s):
    successful through the public NGINX path with `compose-e2e: OK
    projects=19` (setup, governance, preview, preview-filtering,
    `stable-devices=6`, agent sessions, Puck workspace, freeze/review
    snapshot, review surface, `accept-lifecycle=1`, `discard-lifecycle=1`,
    `media-publication=1`); `media-e2e: OK edge=nginx
    upload=validated-private-read=byte-identical
    finalization=public-read=byte-identical immutable-cache=verified`;
    isolated browser-worker runs
    (`browser-worker-dispatch: OK durable-runs=2
    artifacts=agent-owned`; runtime policy uid 10001, read-only,
    `caps=SYS_CHROOT`, `network=browser`); Apache edge build with
    `a2ensite slaif-agent-site && apachectl -t` reporting
    `Syntax OK` for the `.20`-pinned image
    `slaif-agent-site-apache:test`.
  - Supply-chain evidence (job 140483828446, 11m24s): fresh
    six-image artifact (see below).
  - Foundation PG Group A PostgreSQL 14/15/16/17/18 (jobs
    140483828414, 140483828470, 140483828480, 140483828573,
    140483828395) and Foundation PG Group B PostgreSQL 14/15/16/17/18
    (jobs 140483828543, 140483828409, 140483828329, 140483828569,
    140483828342): the ten actual PostgreSQL matrix children, all
    successful — plus the five fast Foundation PostgreSQL 14–18
    children (jobs 140492814170, 140492814113, 140492814108,
    140492814328, 140492814254).
  - Python 3.12/3.13/3.14 quality and package (jobs
    140483827930, 140483828412, 140483828235), Node contracts
    (140483828435), Repository policy (140483828410), Markdown
    (140483828489), Mermaid (140483828339), Dependency review
    (140483828321): all successful.
- **CodeQL run 45992567470**
  <https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/45992567470>:
  `completed / success` — Detect supported languages (140483828093),
  Analyze (actions) (140483941557), Analyze (javascript-typescript)
  (140483941681), Analyze (python) (140483941518), and the CodeQL
  rollup (140484423676) all successful.
- **Fresh six-image supply evidence.** Artifact 15193979761
  `supply-chain-evidence-ccb88bb06b355b6683d4fb3d1c6b0b78eee92b07`
  (8749121B; delivered bytes exactly match the recorded artifact
  size and the SHA256
  `e3d8d019e1e6029eda80c9fb8baec5359eb6cb8467b9904055cf37a67ecc7ba3`).
  Inspected privately (no extraction into any product tree):
  six reproducible image subjects (apache, backend, browser-worker,
  nginx, postgres, web) with first/second export manifest pairs;
  grype database built 2026-11-27T06:22:11Z (checksum
  `sha256:b1f986487adf96493a3f0f2a11c1617ceb00f2a78fa3ee1a7ddbb42c2eb001cf`,
  age 5.514h at validation); `vulnerability_gate: PASS (zero
  unexcepted Critical)` with `unexcepted_critical: 0` and empty
  `critical_findings` for all six images; exception counts
  license=0, vulnerability=0 (no new exceptions); all 77
  `SHA256SUMS` entries re-verified against the extracted bytes;
  loadable SPDX-2.3 SBOMs and loadable grype scans per image;
  the apache SBOM records all four packages at
  `2.4.58-1ubuntu8.20`; browser binary pinned to Chrome for Testing
  158.0.8127.88 (measured-and-scan-bound).
- PR 122 check rollup at the implementation head: `gh pr checks 122`
  reports 30 check runs, all `pass`, zero failures or pending; the
  PR merge state is `CLEAN` and the PR remains OPEN/DRAFT —
  acceptance and merge belong to ROOT alone.

### Limits

- This report records the state observed for the literal
  implementation head before the report commit; the report push may
  trigger fresh CI on the report head, which strategy independently
  waits/verifies. Pending/missing/cancelled/failed is never reported
  as success.
- The Compose and supply-chain subjects above are the exact job and
  artifact identities at the implementation head; ROOT independently
  verifies them on final SELF. The local Docker build of the Apache
  edge used the daemon's content-addressed layer cache (each layer
  keyed on the exact current Dockerfile bytes); the installed-version
  and syntax claims rest on the built image's own `dpkg-query` and
  `apachectl -t` output plus the fresh CI build.
- No skipped, failed, or cancelled local or GitHub result exists at
  the implementation head; nothing was marked pass on inference.

## Local setup

- `uv` 0.12.5, frozen lock, uv-managed CPython 3.14.7 virtualenv;
  plain CPython 3.14.4 for the stdlib-only repository policy tooling
  and tests.
- Node `v24.22.1` from the official
  `node-v24.22.1-linux-x64.tar.xz` (SHA256
  `6c172a9ab6718f7b801fb5a7bd486af2ee5e32758086a04b84fcce2aa77095e6`,
  verified against the official `SHASUMS256.txt`); pnpm exactly
  `11.22.0` via the pinned corepack shim; the transient exact CLIs
  `markdownlint-cli2@0.23.2` and `@mermaid-js/mermaid-cli@11.16.0`
  through `npx --yes`.
- Docker 29.1.3 with a locally named disposable image only; no
  external publish. No local database was required or started for
  this maintenance round. All resources are owned or public-registry
  provenance; no foreign resources were used.

## Documentation

- `docs/` and `README.md` contain no references to the former Apache
  pin (verified by exhaustive grep for `2.4.58`), so no operations
  documentation change was necessary for this round. The historical
  083-10-a report's old pin remains by history-preservation law.

## Scope, secrets, production, skips, extra PR, merge

- Scope: exactly the order's bounded set — the four Apache pins in
  three files, the maintenance-identifier validation and its tests,
  and this round's transcript (order + active). No database or API
  code, no product behavior change, no unrelated dependency updates,
  no scanner or workflow changes, no changed required jobs, no new
  exceptions, no release claims.
- Secrets: no credentials of any kind appear in this report, the PR,
  or tool outputs; fixture credentials exist only inside test process
  environments and were redacted at capture time.
- Production: none touched; the local build used only owned local
  Docker resources and public archive/registry provenance.
- Skips: none — every local gate listed above ran and is reported;
  GitHub states are recorded as observed.
- Extra PR: exactly one draft PR (122) exists for this order. The
  suspended 083/14 product work, its workspace, and its order were
  left untouched and its order was not copied into this PR; the
  Dependabot PRs were not touched.
- Merge: not merged, not auto-merged, not force-pushed; acceptance
  and merge belong to ROOT alone.
