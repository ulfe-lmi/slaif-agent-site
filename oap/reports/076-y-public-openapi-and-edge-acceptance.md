# OAP Implementation Report — 076-y

## Result

- Order: `076-y-public-openapi-and-edge-acceptance`
- Order SHA-256: `64b40d9e0ec72963e6666885ba43490bde46e8eb91b1245c9e4ca47cf18aa2f4`
- Outcome: `COMPLETE`
- Delivery mode: `AMENDED_EXISTING_PR`
- Repository: `ulfe-lmi/slaif-agent-site`
- Pull request: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72)
- PR state at verification: `OPEN`, `MERGEABLE`, `CLEAN`
- Branch: `oap/076-agent-model-content-semantics`
- Base: `main`
- Starting remote implementation/report head: `24d75e98dcc8c751dbaba3f1b176fd40e98721d9`
- Starting remote `main`: `0e83b26bf9a9f63bff6756d65cbfd527d215ec51`
- Implementation commits pushed: `9ea409490207259c49184fef34c98c1983e6bbc6`, `7ec1cc9691bb9580ee341932184c3051f7b0a06e`, `92fba838f55ca0bbe62397594bbfbd7c11da6681`
- Literal implementation SHA: `92fba838f55ca0bbe62397594bbfbd7c11da6681`
- `oap/active` at implementation commit: exact bytes `076-y\n`
- Report publication commit: `SELF`

The implementation is complete for 076-y. The PR remains unmerged as required;
strategy independently reviews and merges accepted work. Objective 076-z remains
reserved for the final hostile contract audit.

## PostgreSQL security overlay

The project-owned `infra/postgres/Dockerfile` derives only from:

`docker.io/library/postgres:18.6-alpine3.23@sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f`

The exact signed Alpine v3.23 main repository upgrades only
`libcrypto3=3.5.8-r0` and `libssl3=3.5.8-r0`. The Dockerfile verifies both
installed versions and uses `apk add --no-cache`; it does not compile PostgreSQL,
run an unbounded upgrade, add runtime tools, change PostgreSQL configuration, or
use a VCS/local dependency. The qualified Alpine aports OpenSSL source commit is
`2b4b2590f782b95276d31dcaaf41554b1a597a0b`.

Compose now builds and runs `slaif-agent-site-postgres:local`. The supply-chain
policy, Compose verifier, OCI contract tests, deployment documentation, and
evidence runner all identify the exact official base and derived image. The
normalized supply-chain evidence identified the derived image as
`sha256:38e2a78e5b7982972882a5c221e77d478b3783d1d3a80de443b1c163b3622cdc`.

The fresh two-build evidence bundle passed reproducibility, SBOM, rootfs-boundary,
and Grype validation. PostgreSQL evidence was:

- SBOM: `sboms/postgres.spdx.json`
- scan SBOM: `scan-sboms/postgres.syft.json`
- vulnerability report: `scans/postgres.grype.json`
- PostgreSQL result: Critical `0`, High `0`, Medium `4`, Low `1`, Unknown `0`
- unexcepted Critical: `0`

Across all six project-owned images, the fresh Grype gate reported 41 Critical
findings, all matched to the existing approved Chrome exceptions; no new exception,
severity change, scanner change, or threshold weakening was made. The final remote
Supply-chain evidence check passed. Existing PostgreSQL 14–18 foundation jobs all
passed. The Compose smoke also passed fresh initialization, migrations/COW
hardening, role/privilege, restart, outage/recovery, health, collation/fresh-volume,
and only-NGINX host-port checks. No in-place migration claim is made for external
old volumes.

## Deterministic Agent OpenAPI contract

The canonical artifact is [contracts/openapi/agent-v1.json](../../contracts/openapi/agent-v1.json)
with SHA-256
`b828fd79092847071dc267fb322692f61463e60e86694b61f1eabb029e9c264e`.

It is generated from the production FastAPI handlers by
`tools/contracts/generate_agent_openapi.py`; `--check` compares bytes and the
unit contract test compares both generator and public endpoint output. The
artifact has OpenAPI `3.1.0`, 23 public Agent paths, 45 reachable typed schemas,
UUID/row/definition-version fields, discovery/browser/content-model/content/page
routes, and no internal health schemas. The public NGINX acceptance fetched the
endpoint and matched the committed bytes exactly.

The contract publishes an `AgentCapability` HTTP bearer scheme with empty bearer
security values and stable `x-slaif-required-scopes` route metadata. Every
mutation has a required `Idempotency-Key`; DELETE optimistic-version bodies and
the stable 400/401/403/404/409/413/422/429/503 error envelope are represented.
Swagger/ReDoc and generic FastAPI documentation remain disabled. Supply-chain
generated-contract policy permits only this exact canonical path; arbitrary
generated/OpenAPI outputs remain rejected.

## Public NGINX acceptance

`tools/compose/public_agent_acceptance.py` is wired into the clean
`tools/compose/smoke.sh` flow. Its successful final output was:

`public-agent-acceptance: OK workspace=c1d945b4-4ea8-45f9-96eb-650734f16fe1 types=2 fields=3 items=2 translations=1 relations=1 views=1 pages=1 components=1 openapi=exact restart=verified nginx-outage=verified crud=public quotas=mutation-429,max-delete-429 dependency-delete=422 tombstones=verified`

The proof used the public Control product to log in, resolve the demo and other
site, create a human L4 workspace, issue a capability, and verify one-time token
display. Through public NGINX and Agent HTTP only, it then:

- discovered all 17 inert field primitives;
- created, read, updated, and dependency-deleted two content types, three fields,
  two items, one translation, one relation, and one collection view;
- created/read a page and trusted Heading component;
- verified exact mutation envelopes, operation UUIDs, idempotent replay and
  mismatch, row versions, definition versions, and type-definition invalidation;
- verified stale `409`, dependency-domain `422`, missing-auth `401`, lower-scope
  and resource-constraint `403`, malformed UUID `422`, invisible/wrong-site `404`,
  publication-route `404`, and mutation/max-delete quota `429` behavior;
- restarted Agent and reread the same overlay with the same capability;
- stopped NGINX, observed public fail-closed connection/readiness behavior, restored
  NGINX, and reread successfully;
- compared canonical content against a separate observer workspace, compared the
  other site/workspace and site list before/after, then verified COW tombstones and
  dependency-safe deletion;
- used direct SQL only for neutral post-journey canonical/audit assertions.

The existing public restart proof also passed with durable audit rows and a revoked
capability. Existing media, browser-worker, editor, governance, edge, secret,
render, and outage checks remained green in the same clean Compose run.

## Verification evidence

Local gates passed:

- `uv lock --check`; `uv sync --frozen --all-groups`
- Ruff check and format check; mypy: no issues in 246 files
- Python unit/repository tests: 517 passed
- Python integration tests: 137 passed in 16:32
- `uv build --out-dir /tmp/slaif-agent-site-distributions-076y-final`
- `node --version`: `v24.14.1`; `pnpm --version`: `11.22.0`
- frozen pnpm install, lint, format check, typecheck, test, build, and license inventory
- compileall, repository policy, 58 repository unittest cases, OpenAPI drift, and
  Mermaid: 16 diagrams / 364 Markdown files scanned
- Markdownlint: 358 Markdown files, 0 issues
- all ten process `--check` smoke commands passed through `uv run --frozen`
- clean Compose smoke: passed, including the public acceptance above
- full fresh local supply-chain gate: passed, six images, zero unexcepted Critical

Final remote checks for implementation SHA `92fba838f55ca0bbe62397594bbfbd7c11da6681`
were all terminal `pass`:

`Analyze (actions)`, `Analyze (javascript-typescript)`, `Analyze (python)`,
`CodeQL`, `Compose and edge packaging`, `Dependency review`,
`Detect supported languages`, `Foundation PostgreSQL 14`, `Foundation PostgreSQL 15`,
`Foundation PostgreSQL 16`, `Foundation PostgreSQL 17`, `Foundation PostgreSQL 18`,
`Markdown`, `Mermaid`, `Node contracts`, `Python 3.12 quality and package`,
`Python 3.13 quality and package`, `Python 3.14 quality and package`,
`Repository policy`, and `Supply-chain evidence`.

During execution, one local supply-chain attempt stopped because the new Postgres
image lacked the validator's required application-file boundary; the legitimate
single `usr/local/bin/docker-entrypoint.sh` boundary was added and the fresh rerun
passed. Two early local proof attempts exposed parser assumptions, and the remote
Compose job once encountered a transient pre-existing browser-worker evidence
failure after the new acceptance had already passed; the targeted unchanged-head
job rerun passed. No failure was ignored, excepted, or hidden.

## Scope and governance confirmations

- No historical strategic order or prior report was rewritten.
- The exact active order and `oap/active` bytes were committed unchanged.
- No second PR was created; PR #72 alone was amended.
- No merge, auto-merge, release, or external production operation was performed.
- No real secret, capability, cookie, private URL, database credential, or
  production data was printed or committed.
- No new Agent entity family, publication, review/promotion, MCP, hosted service,
  architecture boundary, or unrelated cleanup was added.
- The only product-contract additions are the exact canonical Agent OpenAPI
  artifact and the public acceptance evidence required by 076-y.
- The PostgreSQL change is a fresh-install security overlay only; no external-volume
  migration compatibility is asserted.
- No verification item was skipped, weakened, or replaced.

Objective 076-y / PR #72 may be declared complete when the strategy authority has
independently reviewed this report and the already-green remote state. Acceptance
or merge remains strategy-owned; the next reserved work is only 076-z's hostile
contract audit.
