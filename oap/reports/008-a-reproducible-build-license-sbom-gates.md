# OAP Coding-Agent Report — 008-a

## Work order

- Identifier: 008-a
- Work-order file:
  `oap/orders/008-a-reproducible-build-license-sbom-gates.md`
- Numeric objective: 008
- PR mode: CREATED_NEW_PR
- Report drafted: 2026-08-17T20:17:27Z

## Status

COMPLETE

## Executive summary

Created the unique objective-008 pull request and added a self-hosted,
fail-closed supply-chain evidence gate without changing product behavior or
runtime topology. The new deterministic policy inventories frozen Python and
npm dependencies, exact GitHub Actions and OCI sources, reviewed application
licenses, separately classified attribution data, and OS/runtime licenses. It
generates the committed 185-component third-party notice from frozen inputs
and rejects drift, prohibited or unknown direct licenses, hosted SDKs,
mutable sources, malformed exceptions, and evidence leakage.

The implementation builds Python distributions twice and proves identical
wheel and sdist bytes. It gives Next.js a source-derived deterministic build
ID, compares complete normalized Web and browser-worker distribution
manifests, and compares application-file and package manifests from two clean
builds of all five project images. The precise contract does not claim equal
outer OCI image IDs: BuildKit creation metadata made all five IDs differ,
while every normalized in-scope file and package manifest was equal. Only
three exact Next.js encryption-bearing generated manifests are normalized;
their non-secret semantic content remains compared and every other distributed
file, including all installed `node_modules` paths, is hashed.

The CI job produces normalized SPDX 2.3 and symbol-aware Syft JSON SBOMs for
the backend, browser worker, Web, NGINX, Apache, and pinned PostgreSQL images.
Exact, digest-pinned Syft 1.51.0 and Grype 0.117.0 scanned all six SBOMs using
one recorded database. The final evidence reports zero Critical, 35 High, 106
Medium, 16 Low, one Negligible, and one Unknown-severity finding. Both
exception files remain empty. Unknown OS/runtime license metadata stays in the
inventory for human review and is not represented as permissive.

The final CI evidence artifact contains 52 secret-scanned files with a valid
SHA-256 manifest and 14-day retention. Its recorded Grype database was 13.897
hours old, below the 120-hour maximum. All 20 GitHub checks succeeded on the
implementation head's PR merge test, and zero open code-scanning alerts exist
for the branch. The complete existing Python, PostgreSQL, Node, repository,
Markdown, Mermaid, Compose/edge, packaging, and CodeQL gates remain green.

This report is the final repository mutation for the round. Checks on the
report-containing `SELF` head cannot be embedded in this immutable report;
they will be required to finish successfully, with zero open CodeQL alerts,
before the FIFO response is sent.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR number: 11
- PR URL: <https://github.com/ulfe-lmi/slaif-agent-site/pull/11>
- PR state at report time: OPEN
- PR readiness at report time: non-draft
- PR merge state at report time: CLEAN
- Required and actual PR title:
  `[OAP 008] Add reproducible supply-chain and SBOM gates`
- Base branch: `main`
- Head branch: `oap/008-supply-chain-build-gates`
- Starting authoritative remote/base SHA:
  `cc09342664a8ce60414474fd8d308ee459cd0dda`
- Implementation head SHA:
  `9c732921e6c04eb21bf385cdd5964055bd8ed3eb`
- Implementation commits pushed before the report commit:
  - `2a16bad429fdb0583400fe7bd89007b9207deda2` —
    `Add reproducible supply-chain build gates`
  - `9bb8d24232eded25fd108467ea978c2d8172703d` —
    `Avoid CodeQL URL sanitizer false positives`
  - `9c732921e6c04eb21bf385cdd5964055bd8ed3eb` —
    `Cover complete Web distribution reproducibility`
- Report publication commit: SELF
- Remote PR head after report publication: SELF (literal SHA derived from
  GitHub)
- Report commit first parent: same as Implementation head SHA
- Created a new objective PR this turn: yes
- Amended another objective PR this turn: no
- Other objective-008 PRs found: none
- Other open PRs found at final implementation review: none
- Merge performed: NO
- Auto-merge enabled: NO
- PR #5 or PR #7 modified: NO

## Changes made

### Machine-readable policy and deterministic notices

`supply-chain/policy.json` defines and schema-validates the application,
attribution, OS/runtime, registry, source, action, image, scanner,
vulnerability, exception, and evidence rules. It keeps these three conclusions
distinct:

```text
strict automatic application dependency gate
explicit data/font attribution review
container OS/runtime inventory and legal-review evidence
```

The policy rejects AGPL, SSPL, BUSL/BSL, Elastic License, Commons Clause,
noncommercial, field-of-use, source-available, and unknown direct application
licenses. It explicitly reviews current `CC-BY-4.0`, `0BSD`, and BlueOak
attribution categories, preserves unknown OS metadata for review, and makes no
legal-opinion claim.

The deterministic inventory covers 40 Python and 145 npm components and
regenerates `THIRD_PARTY_NOTICES.md` from frozen metadata. Every entry records
component, version, ecosystem/type, license or review state, provenance, and
attribution notes. Repeated generation is stable and CI rejects any committed
notice drift. `NOTICE` retains the project/foundation attribution and points to
the complete generated inventory.

Both exception files are empty arrays. Validation rejects missing identifiers,
versions/images, rationale, approver/reference, creation/expiry dates, or
bounded scope; it also rejects duplicates, wildcards, expired entries, and
overlong lifetimes. No coding-agent exception was created.

### Reproducibility contract

The reproducibility runner fixes `SOURCE_DATE_EPOCH=1704067200`. Two isolated
frozen Python builds produced these byte-identical artifacts:

- wheel: 61,964 bytes,
  SHA-256 `48f150dc706d8cbfb45deb69079630aecb620decd5bf9fa23186d201f1515acd`
- sdist: 48,242 bytes,
  SHA-256 `125577600e2ce5606faca1942fe878b4a4460841e25b6e98c541e83c40514dc7`

Next.js derives build ID `2bacf934cb57d50e0c10bb29dd9765a2` solely from
versioned source and lock inputs. The authoritative CI pair compared 1,149 Web
distribution files, including 1,035 `node_modules` paths. It normalized only
the preview keys in the prerender manifest and the encryption key in the
JavaScript and JSON server-reference manifests. The focused final-tree local
pair compared 1,250 files, including 1,136 `node_modules` paths; the count
varies across CI and local platforms because of platform-specific optional
packages, while each same-environment pair was identical. The browser worker
has no compilation output by design, so its exact three-file runtime source
manifest was compared twice.

All five project images were built twice from exact base digests. The backend,
browser worker, Web, NGINX, and Apache normalized application-file and package
manifests were equal between their two builds. Their outer image IDs differed
because of BuildKit-created layer/image metadata. That metadata is explicitly
outside this bounded contract; the implementation does not claim byte-equal
OCI manifests or IDs.

Generated OpenAPI/product contract artifacts are currently absent. The runner
rejects untracked build output, undisclosed exclusions, new Next.js encrypted
manifests, and omissions from the Web distribution. The ordinary Compose
command needs no human-supplied epoch, version, revision, or build ID.

### Exact image and scanner provenance

Every project Dockerfile has the seven required OCI labels. Compose supplies
honest local defaults while CI supplies the verified revision. All base inputs
use readable patch tags plus top-level immutable digests:

- Python `3.12.12-alpine3.23`:
  `sha256:2d91681153dd4b8cdb52d4fd34a17b9edbafa4dd3086143cfd4b6c3a84c1acb0`
- Node `24.14.1-alpine3.23`:
  `sha256:8510330d3eb72c804231a834b1a8ebb55cb3796c3e4431297a24d246b8add4d5`
- NGINX `1.29.7-alpine3.23`:
  `sha256:e7257f1ef28ba17cf7c248cb8ccf6f0c6e0228ab9c315c152f9c203cd34cf6d1`
- Apache `2.4.68-alpine3.23`:
  `sha256:4a15e9c73f25334bc03cfb3c692c9adfc103bb46ca89cee1f0b9a5fcbc7b21f6`
- PostgreSQL `18.6-alpine3.23`:
  `sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f`
- uv build image:
  `sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1`

The build-only scanners are:

- Anchore Syft 1.51.0, Apache-2.0, source commit
  `2293641e3bd628a01bb37639318d62c0ebe89b39`, image digest
  `sha256:678bfa565b60f747aac0f8e964fe5588a24445b8d0a480e91f6efd70020dfbb0`
- Anchore Grype 0.117.0, Apache-2.0, source commit
  `b5fa92bbcbef655497e3be840a2f718380e2cdd3`, image digest
  `sha256:ddf9e9f204049f3a4a0955ef70873cabab6a31432125ad4f20a490b54950a253`

The policy inventories ten exact full-SHA GitHub Actions, six OCI source
records, and both scanner commands. Scanners run only as transient build/CI
containers, are absent from the Python and npm locks, and are not runtime
dependencies.

### SBOM, vulnerability, and retained evidence

The final CI run generated and validated standard SPDX 2.3 JSON plus normalized
symbol-aware Syft JSON for all six required targets. The checksummed index maps
each image to its immutable source/base/revision identity, SBOM filename and
hash, package type/count, scan input hash, severity counts, and exception
applications. Expected packages and project files are present; forbidden
secrets, DSNs, keys, tokens, Docker sockets, host paths, and source binds are
absent.

Final normalized package inventories by PURL type were:

- Apache: 39 `apk`, one `generic`, one `oci` (41 packages)
- backend: 38 `apk`, one `generic`, one `oci`, 24 `pypi`, six unclassified
  (70 packages)
- browser worker: 18 `apk`, one `generic`, three `npm`, one `oci`
  (23 packages)
- NGINX: 64 `apk`, one `oci` (65 packages)
- PostgreSQL: 53 `apk`, one `generic`, four `golang`, one `oci`
  (59 packages)
- Web: 18 `apk`, one `generic`, 63 `npm`, one `oci` (83 packages)

Python dependency scopes were 23 production, nine development, two build, one
qualification, two quality, and three test. npm scopes were 16 production and
129 development. Browser binary inventory is correctly empty and the policy
will require an explicit inventory when a browser enters a later objective.

Grype database build time was `2026-08-17T06:19:33Z`; its recorded archive
checksum was
`sha256:b8aeae641b24bc403c2c247dd1f096e9b36b66f84e41cf42a690acab965e29ff`.
It was 13.897 hours old when final CI validation ran, within the policy's
120-hour maximum. No scan was skipped. Results were:

| Image | Critical | High | Medium | Low | Negligible | Unknown |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Apache | 0 | 5 | 23 | 0 | 0 | 1 |
| backend | 0 | 15 | 33 | 5 | 1 | 0 |
| browser worker | 0 | 3 | 9 | 5 | 0 | 0 |
| NGINX | 0 | 9 | 28 | 0 | 0 | 0 |
| PostgreSQL | 0 | 0 | 4 | 1 | 0 | 0 |
| Web | 0 | 3 | 9 | 5 | 0 | 0 |
| **Total** | **0** | **35** | **106** | **16** | **1** | **1** |

The source-controlled license and vulnerability exception counts are both
zero. OS/runtime packages with unknown license metadata remain visible:
Apache 3, backend 9, browser worker 2, NGINX 1, PostgreSQL 6, and Web 3. The
image hardening removed unused curl/libcurl from NGINX, Perl from Apache, and
npm from the Web runtime rather than suppressing Critical findings.

The successful CI artifact is:

- name:
  `supply-chain-evidence-51efe4427e54eaa63484f879f5d139631e47b130`
- artifact ID: `9299393549`
- workflow run: `32064183488`
- supply-chain job: `95492177704`
- PR merge-test revision:
  `51efe4427e54eaa63484f879f5d139631e47b130`
- size: 1,661,607 bytes
- created: `2026-08-17T20:13:25Z`
- expiry: `2026-08-31T20:13:24Z`
- retained files: 52
- checksum entries: all valid
- `SHA256SUMS` size: 4,767 bytes
- `SHA256SUMS` SHA-256:
  `c1d02729ee0b7f9b664ea2145b58a3d0b2deddb7bd527c3b1f76d1a3e9e602e3`

The pull-request workflow correctly records GitHub's ephemeral merge-test SHA
as its revision while the literal implementation head remains
`9c732921e6c04eb21bf385cdd5964055bd8ed3eb`. The artifact upload uses the
official upload-artifact action pinned at
`043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` with 14-day retention. Evidence
is a CI artifact only, not a release or publication.

## Files changed

The implementation changed 35 paths, with 5,147 insertions and 49 deletions:

- Workflow: `.github/workflows/ci.yml`.
- Policy and generated inventory: `supply-chain/policy.json`,
  `supply-chain/license-exceptions.json`,
  `supply-chain/vulnerability-exceptions.json`,
  `supply-chain/scanner-commands.txt`, `THIRD_PARTY_NOTICES.md`, and `NOTICE`.
- Reproducible builds and image metadata: `apps/web/Dockerfile`,
  `apps/web/next.config.mjs`, `services/backend/Dockerfile`,
  `services/browser-worker/Dockerfile`, `infra/nginx/Dockerfile`,
  `infra/apache/Dockerfile`, and `compose.yaml`.
- Supply-chain implementation: `tools/supply_chain/__init__.py`,
  `tools/supply_chain/policy.py`, `tools/supply_chain/reproducible.py`,
  `tools/supply_chain/evidence.py`, and `tools/supply_chain/run.sh`.
- Existing validators: `tools/check_repository.py`,
  `tools/compose/verify.py`, `tests/packaging/test_compose_policy.py`,
  `tests/packaging/test_oci_contract.py`, and
  `tests/repository/test_repository_policy.py`.
- New tests: `tests/supply_chain/test_policy.py`,
  `tests/supply_chain/test_reproducible.py`, and
  `tests/supply_chain/test_evidence.py`.
- Documentation: `README.md`, `CONTRIBUTING.md`,
  `docs/DEPLOYMENT.md`, `docs/OPERATIONS.md`,
  `docs/LICENSE_POLICY.md`, and `docs/SUPPLY_CHAIN.md`.
- Strategic transcript, committed exactly as activated: `oap/active` and
  `oap/orders/008-a-reproducible-build-license-sbom-gates.md`.
- This SELF publication adds only
  `oap/reports/008-a-reproducible-build-license-sbom-gates.md`.

`uv.lock` and `pnpm-lock.yaml` are byte-identical to the base commit. No
product/development dependency, runtime service, route, database object,
network, volume, port, credential, or product contract changed.

## Acceptance-criteria evidence

### Criterion 1

- Result: PASSED.
- Evidence: PR #11 is the sole objective-008 PR and the sole open PR. It is
  open, non-draft, CLEAN, based on `main`, uses the required branch and title,
  and contains the activated order/pointer plus this correlated report. No
  merge or auto-merge occurred.

### Criterion 2

- Result: PASSED.
- Evidence: two frozen clean Python builds produced identical wheel and sdist
  bytes and the exact hashes above. Same-environment Web pairs had identical
  normalized path/mode/size/hash manifests across every distributed file;
  only three named encryption-bearing Next.js values were normalized. The
  browser worker's complete three-file runtime manifest matched. All five
  image pairs had identical package and application-file manifests, while
  differing outer IDs and their BuildKit metadata boundary are explicitly
  recorded.

### Criterion 3

- Result: PASSED.
- Evidence: all six image targets have validated normalized SPDX 2.3 and Syft
  JSON SBOMs and checksummed index entries with exact image/base/revision
  identity and the package counts above. Tests prove expected OS, language,
  and application content is present and secrets/host data are absent.

### Criterion 4

- Result: PASSED.
- Evidence: exact digest-pinned Syft 1.51.0 and Grype 0.117.0 processed every
  required SBOM with the recorded 13.897-hour-old database. All six Critical
  counts are zero, all 35 High and other findings remain visible, no exception
  applied, and no scan was skipped.

### Criterion 5

- Result: PASSED.
- Evidence: application source/license policy accepts the frozen current
  dependency graph. Negative unit fixtures reject prohibited and unknown
  direct licenses, hosted/account SDK prefixes, telemetry defaults, mutable or
  disallowed registry/VCS/direct/local/editable sources, npm ranges/patches/
  links/workspace escapes and install scripts, mutable Actions/OCI references,
  and incomplete evidence.

### Criterion 6

- Result: PASSED.
- Evidence: OS/runtime aggregation and attribution data are classified apart
  from application dependencies. All current attribution obligations and
  foundation/upstream notice text are represented in the deterministic
  185-component inventory. Unknown OS metadata is highlighted for review, and
  neither policy nor documentation claims automated legal approval.

### Criterion 7

- Result: PASSED.
- Evidence: license and vulnerability exception files each contain zero
  entries. Negative tests enforce exact identifier/version/image, rationale,
  approver/reference, creation/expiry dates, bounded scope, uniqueness, no
  wildcard, current validity, and maximum lifetime.

### Criterion 8

- Result: PASSED.
- Evidence: every project image has all seven OCI labels; all base and scanner
  references are readable exact tags plus immutable digests. The full Compose
  clean-start/restart/failure smoke, topology, roles, secrets, CSP, request ID,
  edge syntax, and existing packaging policies passed. The accepted 15-service
  topology and one-command UX are unchanged.

### Criterion 9

- Result: PASSED.
- Evidence: final CI generated, validated, secret/path-scanned, and checksummed
  the complete 52-file evidence artifact, then uploaded it with an exact
  full-SHA official action and 14-day retention. All 20 current GitHub checks
  succeeded, and open repository/branch CodeQL alert count is zero.

### Criterion 10

- Result: PASSED.
- Evidence: the machine-readable policy and durable supply-chain, license,
  deployment, operations, README, contributing, notice, and generated-inventory
  documentation record the exact guarantees, limitations, update/exception
  procedures, provenance, scanner database policy, retention, and reproduction
  commands. They explicitly reject legal-certification, vulnerability-free,
  provenance-attestation, release, and production-readiness claims.

### Criterion 11

- Result: PASSED.
- Evidence: `oap/active` contains exactly `008-a`; the order and report names
  correlate uniquely; prior OAP artifacts are unchanged. This report-only
  SELF commit has literal implementation parent
  `9c732921e6c04eb21bf385cdd5964055bd8ed3eb`; its exact remote SHA and one-file
  delta will be verified before FIFO `OK`.

## Local verification

### Python matrix and distributions

For each of local Python 3.12.3, 3.13.15, and 3.14.7, the corresponding
interpreter ran the frozen environment and complete required commands:

```text
uv sync --frozen --all-groups
uv run --frozen ruff check .
uv run --frozen ruff format --check .
uv run --frozen mypy services/backend/src tools tests
uv run --frozen pytest services/backend/tests/unit tests/repository
uv build
```

Results for each version: sync passed; Ruff check passed; Ruff formatting
passed on 79 files; mypy passed on 60 source files; 134 unit/repository tests
passed; wheel and sdist builds passed. The separate two-build reproducibility
gate produced the identical hashes recorded above.

### Supply-chain tests and runners

```text
uv run --frozen python -m unittest discover -s tests/supply_chain -p 'test_*.py'
uv run --frozen python -m tools.supply_chain.reproducible \
  --output /tmp/slaif008-repro-fix
sudo -E sh tools/supply_chain/run.sh /tmp/slaif008-evidence-final-3
python -m compileall -q tools/supply_chain tests/supply_chain
sh -n tools/supply_chain/run.sh
```

Results: 29 supply-chain tests passed; the final-tree focused reproducibility
pair passed with the 1,250-file/1,136-`node_modules` Web manifest described
above; the local all-image runner produced six valid SBOMs and scans with zero
Critical and 35 High findings; compile and shell syntax passed. The local full
runner preceded the last fail-open manifest-coverage correction, but its image,
SBOM, and scanner code was unchanged. The authoritative final-tree all-in-one
result is the successful final CI run and downloaded artifact.

The standard-library negative suite covered every required policy rejection,
exception expiry/schema, normalized ordering, checksum tampering, notice drift,
missing image/SBOM, malformed scan data, stale database, Critical finding,
unknown/prohibited license, hosted SDK, mutable source/action/image, binary
secret markers, and path leakage. A binary invalid-UTF-8 fixture was accepted
when clean and rejected when a configured fake secret marker was present.

### Repository, package, and documentation gates

```text
uv run --frozen python -m unittest discover -s tests/repository -p 'test_*.py'
uv run --frozen python -m unittest discover -s tests/packaging -p 'test_*.py'
uv run --frozen python tools/check_repository.py
uv run --frozen python tools/compose/verify.py --root .
npx --yes markdownlint-cli2@0.23.2 '**/*.md' '#.venv/**' '#node_modules/**'
npx --yes @mermaid-js/mermaid-cli@11.16.0 --version
git diff --check
```

Results: 45 repository tests passed; 18 packaging tests passed; repository and
Compose static verifiers passed; 49 owned Markdown files had zero lint issues;
all 12 diagrams across two Mermaid-bearing documents rendered successfully
with Mermaid CLI 11.16.0 and `/snap/bin/chromium`; diff whitespace passed.

### Node contracts

```text
pnpm install --frozen-lockfile
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
pnpm build
pnpm licenses list --json --long
pnpm licenses list --prod --json --long
```

Results: frozen installation passed for 307 packages in ten projects; lint,
format, typecheck, all tests, build, and both license inventories passed. Test
counts included two Web tests, one browser-worker test, and two Vitest contract
tests.

### PostgreSQL 14 through 18

For each exact disposable `postgres:14-alpine` through
`postgres:18-alpine` fixture, the matrix ran the foundation integration suite
and complete bootstrap/privilege suite:

```text
uv run --frozen pytest \
  services/backend/tests/integration/test_foundation_postgres.py
uv run --frozen pytest \
  services/backend/tests/integration/test_database_bootstrap.py
```

Results on every PostgreSQL major: four foundation tests passed and 23
bootstrap/privilege tests passed. All five disposable containers were removed.

### Compose clean/restart/failure smoke

```text
sudo sh tools/compose/smoke.sh slaif007oap008final
```

Result: passed clean start, restart/recovery, deliberate bootstrap failure,
exact topology, role/privilege checks, edge headers, secret permissions and
leak scans, NGINX/Apache syntax, all 18 packaging tests, and cleanup. Temporary
containers, networks, volumes, images, and secrets created by the fixture were
removed without broad Docker pruning.

### Lock, transcript, scope, and secret verification

- `uv.lock` SHA-256 remained
  `025ba81b052cbc033dffc24d9a5a8100290575960be8c0e827191f60667f900e`.
- `pnpm-lock.yaml` SHA-256 remained
  `6b39f60afceceaf8fa6c524e3fdf88449b1c17b500034f31377513f8e0e00651`.
- `oap/active` SHA-256 was
  `16611655138cefa5571ef2535619cb15386457cd8562e45cbaad3c21f0690771`.
- Activated order SHA-256 was
  `ac595f8f624b3d6a77f57adaeaf5b44497317f77f795ca80b8d2cc60c210686c`.
- `AGENTS.md` SHA-256 remained
  `9b5995c3c661505bab700d077aa46f5feea34357ea4481a9fe5bd07d4a4e4e38`.
- `ARCHITECTURE.md` SHA-256 remained
  `813f57d5705444de6664ce9f065c1f559485473433569076500551904d6d02fa`.
- `OAP-COMMUNICATION-coding-agent.md` SHA-256 remained
  `e6150dd29567795719374537b1423bc09cf8341fef72e3287e53be70feaa0604`.
- `SECURITY.md` SHA-256 remained
  `ec327aa12bad19ee7f51a95f996f7e9532f66aa958593c56bb99e61c523e23c`.
- Prior OAP artifact tree checksum remained
  `c26a57bb1ae1f4e2139dc073d30147d24b553473d7da657190e9be2952867886`.
- Staged-scope and generated-evidence secret scans passed. Matches in source
  were limited to configured marker literals and their fake binary test; no
  real credential, capability, cookie, DSN, key, token, or private URL was
  found or printed.

## GitHub CI and code scanning

Implementation-head PR checks all completed successfully:

1. Analyze (actions) — SUCCESS
2. Analyze (javascript-typescript) — SUCCESS
3. Analyze (python) — SUCCESS
4. CodeQL — SUCCESS
5. Compose and edge packaging — SUCCESS
6. Dependency review — SUCCESS
7. Detect supported languages — SUCCESS
8. Foundation PostgreSQL 14 — SUCCESS
9. Foundation PostgreSQL 15 — SUCCESS
10. Foundation PostgreSQL 16 — SUCCESS
11. Foundation PostgreSQL 17 — SUCCESS
12. Foundation PostgreSQL 18 — SUCCESS
13. Markdown — SUCCESS
14. Mermaid — SUCCESS
15. Node contracts — SUCCESS
16. Python 3.12 quality and package — SUCCESS
17. Python 3.13 quality and package — SUCCESS
18. Python 3.14 quality and package — SUCCESS
19. Repository policy — SUCCESS
20. Supply-chain evidence — SUCCESS

The final ordinary workflow run was `32064183488`; the supply-chain evidence
job was `95492177704` and completed in 4 minutes 58 seconds. CodeQL run
`32064183510` completed successfully. GitHub's branch code-scanning API
returned zero open alerts for `oap/008-supply-chain-build-gates`; repository
open-alert count was also zero.

The final CI artifact was downloaded to an isolated temporary directory. All
52 files were present and `sha256sum -c SHA256SUMS` validated every listed
checksum. No skipped, pending, cancelled, neutral, or failed implementation
check is represented as passing.

## Setup and dependencies

- No OS, Python, npm, product, runtime, or repository dependency was installed
  permanently or added to either lockfile.
- Existing local uv, pnpm, Docker, Chromium, and language interpreters were
  used.
- Passwordless `sudo` was used only for disposable Docker/PostgreSQL/Compose
  fixtures and the scanner runner's Docker access.
- Syft and Grype ran from exact digest-pinned public containers; neither tool
  entered a lockfile or product image.
- Public registry and Grype database access required no account, hosted
  service credential, cloud API key, or subscription.

## Documentation impact

Added `docs/SUPPLY_CHAIN.md` and `docs/LICENSE_POLICY.md`; added deterministic
`THIRD_PARTY_NOTICES.md`; updated `NOTICE`, README, CONTRIBUTING, deployment,
and operations documentation. The documents cover trust boundaries, exact
tool/source updates, reproducibility commands, SBOM/evidence structure,
scanner database freshness, exception governance, license classification,
CI retention, and limitations. They preserve the project's pre-alpha status
and do not claim legal certification, complete provenance attestation,
vulnerability absence, release status, or production readiness.

## Safety and scope confirmations

- Allowed path scope respected: YES.
- Product behavior or editorial/runtime authority changed: NO.
- Runtime dependency or service added: NO.
- Compose service/network/volume/port/secret topology changed: NO.
- Database schema, migration, role, or privilege behavior changed: NO.
- Product/architecture/security contract edited: NO.
- `uv.lock` or `pnpm-lock.yaml` edited: NO.
- Hosted/account-bound runtime service or credential added: NO.
- Telemetry enabled: NO.
- License or vulnerability exception added: NO.
- Scanner or vulnerability gate skipped/weakened: NO.
- Required local regression gate skipped: NO.
- Required GitHub implementation-head check missing/pending/failed: NO.
- Real secret, production data, or production credential accessed: NO.
- Production system or Docker socket outside the disposable test boundary
  accessed: NO.
- Broad Docker prune or unrelated resource deletion performed: NO.
- Activated order or pointer edited by the coding agent: NO; exact strategic
  input bytes were committed.
- Prior OAP artifact edited: NO.
- Extra branch or objective PR created: NO.
- Force push performed: NO.
- Merge, auto-merge, release, publication, signing, tag, deployment, or GitHub
  setting change performed: NO.
- Report publication commit changes only this report: YES, to be verified
  locally and against the remote before FIFO response.
- Report first parent is the literal implementation head: YES, to be verified
  locally and against the remote before FIFO response.

## Limitations and blockers

- Blockers: none.
- Grype reports 35 High and 124 lower/unknown-severity findings. They remain
  review evidence and do not disappear merely because the Critical gate is
  green.
- Twenty-four OS/runtime package records have unknown license metadata across
  the six images. They remain highlighted for human/legal review; the strict
  direct-application gate does not misclassify them as permissive.
- Scanner results are time-bounded to the recorded database and can change as
  advisories or package metadata change. Green CI is not proof of vulnerability
  absence.
- Same-environment application artifacts/manifests are reproducible under the
  documented contract. Whole OCI image IDs are not byte-identical because of
  BuildKit layer/image creation metadata, and local versus CI optional-package
  counts may vary by platform. Neither difference is hidden or overclaimed.
- Browser binary inventory is correctly empty because Playwright/browser
  binaries are explicit non-goals for this objective.
- SPDX/Syft/license inventories and policy automation are evidence, not legal
  advice, legal approval, a complete license opinion, a provenance attestation,
  SLSA certification, release approval, or production-readiness evidence.
- The evidence artifact is retained for 14 days and is not a permanent release
  asset.

## Strategic follow-up

- Independently review PR #11, the implementation head, report-only remote
  head/parent, final fresh-head checks, zero-alert state, downloaded evidence
  artifact, remaining High/OS-metadata review evidence, and the deliberately
  bounded reproducibility contract.
- Decide acceptance and merge separately. The coding agent did not merge,
  enable auto-merge, publish, release, sign, deploy, or select another work
  order.
