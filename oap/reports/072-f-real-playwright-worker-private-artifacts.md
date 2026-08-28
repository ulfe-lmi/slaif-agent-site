# OAP implementation report — 072-f

ID: `072-f`

Order: `oap/orders/072-f-real-playwright-worker-private-artifacts.md`

Result: `PARTIAL`

PR: [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66)

PR mode: `AMENDED_EXISTING_PR`

Repository: `ulfe-lmi/slaif-agent-site`

Base: `main` (`082f2359b0c4d59b692580d17992c35d46183b12`)

Head branch: `oap/072-browser-worker-real-playwright`

Starting remote report head: `76e0f0a45dc8120ace8b7b7c4c5a29b29398ab4a`

Implementation commit: `b946d266bf59c9c74893d2a8a17e7893950eccc1`

Report publication commit: SELF

## Delivered

- Replaced the browser-worker health stub with a real, bounded Playwright
  worker and typed internal HTTP submit/inspect/retrieve contracts. The public
  Agent routes remain unconnected and public runs remain `QUEUED`.
- Added fixed immutable target descriptors for desktop Chromium, tablet, and
  mobile Chromium; fixed Web preview origin; default-deny URL/redirect/asset
  policy; hostile-URL self-checks; one initial preview credential header only;
  and curated bounded console, request, failure, structure, and PNG evidence.
- Added descriptor-confined `sbws1` worker credentials, constant-time
  authentication before body framing, exact request binding, signed typed
  results, overload and disconnect cancellation, and readiness failure states.
- Added immutable content-addressed private artifacts with staged exclusive
  creation, fsync, deterministic metadata, mode/owner/link/digest/size/expiry
  checks, restart-safe retrieval, and rollback on failed publication.
- Added one-shot worker-secret and artifact-root initialization, Agent
  read-only secret mount, worker-only writable artifact volume, browser
  network isolation, non-root UID 10001, read-only root, dropped capabilities
  plus only `SYS_CHROOT`, no-new-privileges, bounded tmpfs/PID/memory/CPU/shm,
  and no database, Docker, host, or unrelated secret access.
- Baked exact Chrome for Testing `151.0.7922.72` (Chromium slot `1234`,
  SHA-256
  `08254455dc5154fefa0165dc1dea16e496c8298f98c14d89bf38463810d21649`)
  into the worker image. The image uses
  `mcr.microsoft.com/playwright:v1.62.1-noble@sha256:dcc5531e97840b9b5e794f2814476b21571c5124a3fca2267d73041f56e7580e`,
  `playwright-core 1.62.1`, Node 24 policy compatibility, and the exact
  upstream seccomp profile SHA-256
  `294a5523dd03c8dad52215d7970d38711b03f7e6624e09f2ff109ea3628a645c`.
  Firefox and WebKit product binaries are absent; the qualified image is
  Linux/amd64 only.
- Added the dependency-free ZIP extractor, package/lock/importer facts,
  supply-chain inventory and notices, Compose/policy checks, and API,
  configuration, deployment, security, service-authority, operations,
  scaling, testing, and license documentation.

## Evidence

Local focused and full checks passed: worker tests 10; browser-contract tests
23; Web tests 9; Agent client tests 3; backend unit/repository tests 476;
backend integration tests 111; packaging tests 44; repository unittest 54;
supply-chain policy tests 29; archive-extractor tests 2; all Node lint,
format, typecheck, test, build, and license commands; all ten Python process
`--check` commands; repository policy; Mermaid (16 diagrams, 242 Markdown
files); Markdownlint (236 files); and `uv build`.

The clean Compose run passed: all nine existing Playwright projects; real
sandboxed worker execution; two direct runs producing six artifacts; five
negative authorization/policy cases; PNG decoding and bounded evidence;
restart retention of three byte-identical artifacts; public separation with
two durable queued runs and zero database artifacts; twelve artifact files
with mode 0600, one link, and no credential markers; worker image/runtime
policy; worker-secret missing/readiness recovery; signing recovery; existing
media, governance, COW, database-role, edge, and cleanup checks.

Fresh GitHub checks for implementation `b946d266bf59c9c74893d2a8a17e7893950eccc1`:

- PASS: Repository policy, Node contracts, Python 3.12/3.13/3.14 quality and
  package, Foundation PostgreSQL 14/15/16/17/18, Compose and edge packaging,
  Markdown, Mermaid, dependency review, and CodeQL (all language analyses).
- Compose initially failed an existing governance Puck round-trip at line 504;
  the unchanged job-only retry passed the complete clean smoke.
- FAIL: Supply-chain evidence. The latest scanner database reports Critical
  CVEs in the deliberately pinned Playwright/Ubuntu and Chrome
  `151.0.7922.72` runtime, fixed only in later upstream versions. No
  vulnerability exception or scanner weakening was added. This is the sole
  outstanding required check and is why this handoff is `PARTIAL`.

The local supply-chain run independently built both reproducibility passes,
generated inventories/SBOM inputs, and verified the exact image/package
builds before failing the same vulnerability gate. Its earlier Apache package
drift was repaired by exact current Alpine pins (`apr-util 1.6.4-r0`,
`libcrypto3/libssl3 3.5.8-r0`) rather than exceptions.

## Scope and limitations

No migration, database function/grant/role, queued-run behavior, public
artifact retrieval, dispatcher, lease recovery, artifact GC, source crawling,
six-target sweep, review/promotion/publication, human credential, capability,
or Web/Render token semantics were changed. No Firefox/WebKit product
binaries, hosted browser, telemetry, extra PR, merge, auto-merge, or release
was performed. Runtime credentials and artifact bytes were never printed or
committed. The implementation commit is pushed; this report is the sole
report-only child and is intended to be pushed as the PR head after commit.
