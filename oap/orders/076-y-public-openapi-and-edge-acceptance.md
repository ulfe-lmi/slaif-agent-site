# OAP Work Order — 076-y

## Objective and authoritative starting state

Amend only Objective 076 PR
[#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72), branch
`oap/076-agent-model-content-semantics`, base `main`; no new PR and no merge.
Required starting report head:
`24d75e98dcc8c751dbaba3f1b176fd40e98721d9`, sole parent
`0ba6ef3a863804a16708001cdf6396c3ec463bbc`; remote `main` remains
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. Current report-head CI is
terminal: 19 checks pass; only Supply-chain evidence fails.

076-x closes the migration and relation/view proof defects. Preserve that
work. Its PostgreSQL Trixie candidate is rejected: the immutable image contains
unfixed OpenSSL 3.5.6 and expands the scanner-Critical set to eight. The next
round must close the image blocker without an exception and deliver the final
consolidated public Agent REST/OpenAPI/NGINX/restart acceptance for Objective
076. Objective 076 remains unmerged; 076-z is reserved solely for final hostile
contract audit/closure and any last bounded correction.

## Verified zero-exception PostgreSQL packaging path

- Previously qualified official base:
  `docker.io/library/postgres:18.6-alpine3.23@sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f`.
  Its installed `libcrypto3/libssl3` are 3.5.7-r0, producing the single
  unexcepted `CVE-2026-63073` finding.
- Alpine v3.23 main now publishes signed exact `libcrypto3=3.5.8-r0` and
  `libssl3=3.5.8-r0`, OpenSSL source commit
  `2b4b2590f782b95276d31dcaaf41554b1a597a0b`, built 2026-08-25. OpenSSL 3.5.8
  contains the CMP format-string fix. Verify this live before use.
- Official PostgreSQL 18.6 Bookworm/Trixie glibc variants currently retain
  several unpatched scanner-Critical Perl/glibc findings; switching among them
  is not remediation. No hosted/account-bound/hardened commercial image and no
  new exception is authorized.
- The human explicitly confirms there is no existing installation or volume to
  migrate: this project is fresh-install only. The repository has already
  qualified the Alpine/musl PostgreSQL 18.6 base for fresh volumes; retain and
  strengthen its collation/fresh-init/restart tests. Do not claim in-place
  compatibility for external old volumes.

## 1. Build a reproducible patched PostgreSQL runtime image

- Add a minimal project-owned PostgreSQL Dockerfile/build context derived only
  from the exact official Alpine OCI base above. Upgrade only the exact signed
  vulnerable runtime packages to `libcrypto3=3.5.8-r0` and
  `libssl3=3.5.8-r0` (plus `openssl=3.5.8-r0` only if actually installed/
  required). Verify package versions in the build and remove caches. Do not
  compile PostgreSQL, change its version/configuration, add shells/tools, or
  broaden runtime packages.
- Pin base digest, package versions, Alpine branch/repository and provenance in
  inspectable policy/tests/docs. Package signature verification must remain
  enabled. Builds must be deterministic under the repository’s two-build
  evidence; no mutable tag-only fallback, `apk upgrade` without exact versions,
  unverified download, local binary blob, or VCS dependency.
- Replace the rejected Trixie references in Compose, supply-chain policy,
  verification fixtures and deployment attribution with the derived image
  contract. Supply-chain evidence must build/SBOM/scan the actual derived
  PostgreSQL image and prove the exact immutable base plus patched packages.
  It must not merely scan the old upstream base or ignore the derived layer.
- Require a fresh current Grype DB and zero unexcepted Critical for PostgreSQL;
  preserve exact Chrome exceptions/expiry unchanged. No CVE exception, severity
  change, scanner pin-back, omitted image, threshold weakening or false
  `zero Critical` wording.
- Run clean init, bootstrap/migrations/COW hardening, service-role checks,
  restart persistence, DB outage/recovery, backup-tool assumptions,
  collation/fresh-volume guard, resource/health checks and only-NGINX host-port
  proof. Preserve PostgreSQL 14–18 foundation matrix. Document that this is a
  fresh-install security overlay and that existing external volumes are not an
  asserted migration path.

## 2. Publish deterministic Agent OpenAPI as a real product contract

Current runtime exposes `/api/agent/v1/openapi.json` but no committed artifact;
docs/supply-chain rules still say generated product contracts are absent. Close
that contradiction.

- Commit canonical deterministic `contracts/openapi/agent-v1.json` generated
  from the same production FastAPI handlers. Add a repository command and drift
  test that regenerates it byte-for-byte with stable sorting/newline and fails
  on route/model/security/error/header drift. No timestamp, host, environment,
  DB/COW/internal credential/function/schema or nondeterministic operation ID.
- Update the supply-chain generated-contract policy narrowly to permit and
  inventory only this exact approved canonical path; arbitrary `.next`, build,
  `generated/`, duplicate or untracked OpenAPI artifacts still fail. Include the
  contract in source/wheel inventory only if intentionally designed and tested.
- OpenAPI 3.1 document must include every current public Agent `/v1` route,
  typed request/response schemas, UUID/row/definition versions, all discovery/
  browser and model/content routes, and exact HTTP methods/statuses. The schema
  path itself is included deliberately; Swagger/ReDoc UI and generic FastAPI
  `/openapi.json` remain disabled.
- Define `AgentCapability` HTTP bearer security correctly. OpenAPI security
  requirement values for a bearer scheme are empty arrays; publish exact route
  scopes separately as a stable `x-slaif-required-scopes` extension. Public
  schema retrieval may be unauthenticated if that is the current deliberate
  contract, but it grants no operation authority.
- Every mutation declares required `Idempotency-Key`; DELETE request bodies and
  optimistic-version fields are required where production enforces them.
  Document stable error envelopes/codes/statuses for malformed 400,
  authentication 401, scope/resource 403, invisible 404, stale/dependency/
  idempotency 409, oversized 413, domain 422, quota 429 and infrastructure 503
  as applicable. Do not advertise unsupported paths, scopes, batches, UI, MCP,
  media or publication behavior.
- Update `contracts/README.md`, `docs/API.md`, `docs/CONFIGURATION.md`, and
  `docs/SUPPLY_CHAIN.md` only to current implemented truth and regeneration/
  drift instructions. No docs UI or production/readiness overclaim.

## 3. Consolidated public NGINX/restart acceptance

Add one decisive clean-Compose E2E that uses only intended product interfaces
for actor behavior. Neutral owner fixture setup/assertion reads are allowed;
no service/ORM/direct SQL/internal API/test helper may perform the Agent actions
being claimed.

1. Start a clean patched PostgreSQL/complete stack through the normal Compose
   entrypoint with only NGINX on the host. Complete real setup/login/site and
   human Agent-workspace + L4 capability issuance through the public Control
   product surface.
2. Fetch canonical OpenAPI through public NGINX; verify exact committed bytes
   or canonical semantic equality and derive/use real paths/schemas from it.
3. Through public NGINX and the issued capability, discover field primitives;
   create/read/update/delete content type, field, item, translation, relation
   and collection view using valid dependency order. Assert exact status/body,
   row/definition versions, type-definition invalidation, COW visibility,
   idempotent replay/mismatch, scopes/resources, mutation/delete/max-delete
   quotas, operation IDs and durable semantic audit identities.
4. Restart the Agent container/process while retaining DB/media volumes; the
   same capability reads the exact workspace overlay and idempotent results.
   NGINX continues routing to the correct Agent/Control services and readiness
   fails closed during actual outage then recovers.
5. Prove canonical and another workspace/site remain unchanged; lower preset,
   wrong/missing scope, wrong site/type/path/resource, stale version,
   dependency, revoked/expired/frozen/delegator-loss, direct reviewer/control
   endpoint and Agent publish attempts are denied with no unintended residue.
   Request-time auth is real, not fixture bypass.
6. Delete in dependency order and prove real COW tombstones; no physical DDL,
   Alembic, executable primitive/query/code, canonical write, publish or user
   management occurs. The test must fail if any production route/wrapper/
   NGINX mapping/restart persistence/OpenAPI artifact is removed.

Keep the test deterministic and bounded; reuse proven fixtures/helpers only for
neutral setup and assertions. Preserve existing public Agent restart probe and
all earlier Compose/browser/media/editor/security/outage/Apache evidence.

## Verification and termination

Run focused image/OpenAPI/public E2E, complete Agent mutation and 075 domain/
query regressions, then full Python quality/unit/integration/PG14–18, Node,
contract drift, repository/Markdown/Mermaid, clean Compose/edge/Apache/restart,
and fresh full supply-chain. Repair in-scope failures on this branch. Wait for
every required report-head check: none pending/failed/cancelled/missing.

Do not return `COMPLETE` until the derived PostgreSQL image scans with zero
unexcepted Critical, deterministic committed OpenAPI passes drift, and the full
public NGINX/restart semantic journey passes. `PARTIAL`/`BLOCKED` requires a
precise external/technical blocker plus attempted evidence; do not add an
exception or substitute an internal test.

## Scope and report

No new Agent entity family, page/navigation/redirect/composition/design/media/
MCP/source/browser/review/promotion behavior, hosted service, architecture/
governance, prior artifact edit, production or release claim. The PostgreSQL
Dockerfile is a narrow packaging security repair. No production secret/system/
data access; routine image/scanner/Compose work belongs to executor sudo.

Commit the exact order and `oap/active` unchanged on the same branch, push,
never create/close/merge another PR, then publish exactly
`oap/reports/076-y-public-openapi-and-edge-acceptance.md` as a report-only
child of the literal implementation SHA with `Report publication commit:
SELF`. Include exact base/package/image/platform digests, SBOM/CVE/scan and no-
exception evidence, OpenAPI path/hash/drift/inventory, full public journey,
migration/security regressions, commands/checks/skips/risks, append-only 076-x
blocker resolution, no extra PR/no merge, and state only 076-z final hostile
audit remains. No post-report push; signal exact FIFO `OK` and wait.
