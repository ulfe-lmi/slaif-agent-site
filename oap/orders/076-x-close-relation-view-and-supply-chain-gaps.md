# OAP Work Order — 076-x

## Objective and authoritative starting state

Amend only Objective 076 PR
[#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72), branch
`oap/076-agent-model-content-semantics`, base `main`; no new PR and no merge.
Required starting report head:
`25e27a0b368881f57c39b7ac043c25761da71fb1`, sole parent
`2332b0026203fbb99fe385106c0c0fa398042347`; remote `main` remains
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`.

076-w produced substantive relation/view/stale-cleanup code and truthfully
reported `BLOCKED`. Its report-head CI is terminal: 19 required checks pass;
only Supply-chain evidence fails, on
`postgres:18.6-alpine3.23@sha256:697c180dbf244d3ce4a8f4cbc0156cde840af055c1bf8b76aebe422a4822086f`
with unexcepted Critical `CVE-2026-63073`. Preserve the useful production
implementation but do not accept its broader proof claims yet.

## Verified defects and security state

1. The CVE is in the image’s OpenSSL CMP client path, not PostgreSQL core. It
   is an attacker-controlled format-string denial of service reached by a CMP
   client validating a malicious/intercepted endpoint. Fixed OpenSSL 3.5-line
   packages are available; a new vulnerability exception is neither necessary
   nor authorized. The existing human exception file is exact to Chrome
   `152.0.7977.64`, issue #67, and expiry `2026-09-04`; it does not cover this
   PostgreSQL image/CVE.
2. At strategic inspection, official `postgres:18.6-trixie` resolves to OCI
   index `sha256:4ef4dbc939d61acea57712655ddb4b4ab27419c913f94cca0cd57cb3ea3c2280`,
   with amd64 manifest created 2026-08-25. Treat this only as the verified
   candidate: independently re-resolve, inspect packages/SBOM, and scan before
   pinning. Prefer the current official Debian 13 Trixie/glibc image with
   OpenSSL `3.5.7-1~deb13u2` or later and zero unexcepted Critical findings.
   The human has explicitly confirmed this project has no existing deployment
   or persistent installation to migrate; all installations are fresh, and
   PostgreSQL should not rely on musl where a maintained glibc variant exists.
3. `048_001_agent_relations_and_collection_views.py::downgrade` replays the 047
   upgrade after installing a placeholder check. It cannot restore revision
   047 when `audit.agent_mutation` contains 048-only relation/view semantic
   rows, because the canonical 047 constraint rejects those non-null action
   shapes. Existing tests never create 048 relation/view audit rows before the
   downgrade, so the report’s data-bearing round-trip claim is false.
4. The added tests contain no direct Agent-runtime wrong-scope/resource/grant
   attacks for relation/view wrappers, no concurrent relation create/update
   proof, and no hostile collection-query matrix. The happy CRUD and view/
   translation races are useful but do not satisfy the activated 076-w
   negative/concurrency contract.

## 1. Remediate PostgreSQL image without an exception

- Resolve the current official `postgres:18.6-trixie` multi-platform index and
  verify source provenance, supported architectures, PostgreSQL version,
  Debian/glibc base, OpenSSL fixed package version, license/SBOM, and current
  Grype results. Pin the exact verified OCI index digest everywhere the current
  Alpine PostgreSQL image is authoritative: Compose, supply-chain policy/image
  inventory, packaging/verification fixtures, documentation/attribution if
  affected. Never leave a mutable tag-only reference or mismatched digest.
- Do not add/extend/repurpose a vulnerability exception; do not suppress this
  CVE, downgrade severity, freeze an old vulnerability DB, weaken thresholds,
  omit PostgreSQL from scans, or accept a hosted/proprietary/account-bound
  replacement. Preserve the exact Chrome exception and expiry unchanged.
- Verify the official PostgreSQL 18 data-directory/entrypoint/health/init-user
  contract used by this repository, non-root/runtime permissions, COW
  extensions/functions, clean initialization, restart persistence, backup-tool
  assumptions, and only-NGINX-host-port rule. This is a fresh-install baseline;
  do not invent an in-place Alpine-volume compatibility claim.
- Run the full supply-chain evidence locally with a freshly updated scanner DB
  and require PostgreSQL zero unexcepted Critical. Preserve visible evidence
  for the CVE’s absence/fixed package and all other images’ exact exception
  status. Current-head remote Supply-chain evidence must pass.

## 2. Make the 047/048 migration transition honest and data-safe

Repair the unreleased 047/048 migration pair so clean upgrade-to-047 and
downgrade-from-048-to-047 produce one equivalent, safe revision-047 contract
while preserving immutable historic 048 relation/view audit rows.

- Do not delete, rewrite to legacy, null, or otherwise falsify 048 audit rows.
  A safe forward-compatible revision-047 audit check may allow the exact later
  relation/view historical shapes while its 047 completion function still
  cannot create them; document and test that distinction. Alternatively use an
  equally truth-preserving design, but no audit loss or permissive `CHECK(true)`
  may remain in the final 047 state.
- Revision 047 after downgrade must have exactly its intended functions,
  owners, grants, completion action set, content/COW state and hardened
  readiness; 048-only Agent wrappers are absent. Existing relation/view rows
  in the already-existing COW tables and their exact audit/idempotency records
  survive unchanged. New 048 actions cannot be completed at 047.
- Upgrade back to 048 restores wrappers and completion while retaining exact
  rows/digests/actions/method/status/quota identity. Remove brittle placeholder
  or dynamic replay behavior if a direct explicit downgrade is safer; no
  network, mutable input, hidden DDL, audit mutation or private foundation API.
- Add a real 048 production setup through Agent REST, then stop application
  use, execute 048→047→048, and assert relation/view content, COW operations,
  audit/idempotency rows, check definitions, function identities, owners,
  grants, head/readiness and post-upgrade replay/read behavior.

## 3. Supply the missing relation/view acceptance proof

Use real human-issued capabilities and actual Agent HTTP against real
PostgreSQL for product claims; direct SQL only for neutral setup, adversarial
least-privilege calls and owner/reviewer assertions.

- **Direct authority:** as `slaif_agent_runtime`, attack every relation/view
  list/get/create/update/delete wrapper and callable helper with missing/wrong/
  malformed-scope capability context, wrong workspace/site/source/path/type,
  disallowed source and target type ID/key, exhausted mutation/delete/
  `max_deletes`, delete-disabled and irrelevant roles/PUBLIC. Require denial
  before disclosure, charge or COW/audit/idempotency residue. Correct-scope
  representative direct calls remain confined and charge exactly once.
- **Relation concurrency:** two connections race valid creates at a single-
  reference or exact maximum cardinality; exactly one commits. Two connections
  PATCH one relation at the same row version; exactly one returns `200` and one
  stable `409`, with one version/charge/audit/idempotency/COW increment. Cover
  cancellation rollback.
- **Relation hostile matrix:** wrong source/relation path, cross-site/
  cross-workspace target, field belonging to another type, non-reference field,
  target-type mismatch, stale source/target/field, cardinality, position,
  oversized/nonobject/executable metadata, replay/mismatch and delete limits.
  Every rejection has zero unintended residue.
- **View hostile matrix:** wrong scope/site/path/type/resource, stale row and
  definition, duplicate key, unknown/localized/nonindexable fields, unsupported
  operators/value shape, raw SQL/comment/semicolon/script/prototype input,
  excessive nodes/depth/size/projection/pagination, malformed JSON shapes,
  replay/mismatch, delete limits, cancellation and direct wrapper abuse. Prove
  the Python and trusted database validators reject equivalent attacks and
  that one valid nonlocalized bounded query still works.
- Retain the already passing translation and view two-connection races, CRUD,
  strict audit, stale dependency cleanup, canonical/other-workspace/site
  isolation, and item/type delete chain. Correct 076-w’s unsupported proof and
  data-round-trip claims append-only in the 076-x report.

## Verification and termination

Run focused security/migration/concurrency tests, complete Agent mutation and
075 query/domain regressions, then full Python quality/unit/integration/
PG14–18, Editor/Render, migration/bootstrap/privilege/package, Node,
repository/Markdown/Mermaid, clean Compose/edge restart, and full supply-chain
with current scanner DB. Push and wait for every required current report-head
check; none may be pending/failed/cancelled/missing. A scanner rerun without a
code/image change is not remediation.

Do not return `COMPLETE` until the PostgreSQL image is fixed and scanned,
data-bearing 048→047→048 is proven, and all missing negative/concurrency tests
exist and pass. `PARTIAL`/`BLOCKED` requires a precise remaining external or
technical blocker with attempts; do not call the known fixed-image option an
external outage.

## Scope and report

No new Agent entity/API beyond repair, no final public OpenAPI/NGINX semantic
acceptance (076-y owns it), no page/navigation/redirect/composition/design/
media/MCP/browser/review/promotion, hosted service, dependency beyond the
official PostgreSQL image variant, architecture/governance, prior artifact
edit, production or release claim. No production secrets/systems/data. Routine
image/scanner/Compose work belongs to executor sudo.

Commit the exact order and `oap/active` unchanged on the same branch, push,
never create/close/merge another PR, then publish exactly
`oap/reports/076-x-close-relation-view-and-supply-chain-gaps.md` as a
report-only child of the literal implementation SHA with
`Report publication commit: SELF`. Include exact image/tag/index/platform
digests/package/CVE/scan evidence, migration state/rows/functions/checks,
negative/concurrency evidence, commands/checks/skips/risks, append-only 076-w
corrections, no exception/no extra PR/no merge, and state only consolidated
public OpenAPI/NGINX/restart acceptance plus final hostile audit remain. No
post-report push; signal exact FIFO `OK` and wait.
