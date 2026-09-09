# OAP Work Order — 078-o: qualify the required Next.js security patch

- Objective 078; increment 078/1; round 078-o; AMEND_EXISTING_PR.
- Existing [PR #77](https://github.com/ulfe-lmi/slaif-agent-site/pull/77).
- Branch `oap/078-agent-composition-design-semantics`; base `main`.
- Verified main/base `ae3a4a681bb888260192b7bb1b2a337b4906828d`.
- Starting report head `602086512ddeebdd2c912f9c5f011c8af685cf85`;
  report-only parent `e0928ee8323fe65246022d61a952f7767bf6bf14` verified.
- Accepted product implementation `6e41a5201215015e48d266995242b9c58067b95c`.

## Concrete blocker and strategic authorization

078-n completed the human-approved link-only correction; Markdown now passes.
Its required supply-chain job `102411200291`, run `34334682215`, failed after
refreshing the vulnerability database: Web has unexcepted Critical advisories
`GHSA-2xp9-vwfh-vxw4` and `GHSA-p293-qw3h-jr36`. This is an actually executed
security gate, unrelated to the closed Chrome exception. The docs-only order
correctly did not authorize a dependency repair. This continuation does.

Strategy independently verified `apps/web/package.json` pins Next.js 16.3.1,
`tools/check_repository.py` checks that exact pin, and npm supplies MIT-licensed
16.3.3 with Node engine `>=20.9.0`. Upstream identifies 16.3.3 as patched for
both [AVIF optimization RCE](https://github.com/vercel/next.js/security/advisories/GHSA-2xp9-vwfh-vxw4)
and [Windows-hosted RCE](https://github.com/vercel/next.js/security/advisories/GHSA-p293-qw3h-jr36).
Registry integrity observed for 16.3.3:
`sha512-tuRTx1nQ/yVw83cwJBo9F+njGUgMn3UHQycreWHB8XsStvvAh1AthbI8/4IpKnFaF58F+iSiHejYOlMQ/eq83g==`.
Reverify source/registry when executing; stop on a material contradiction.

Authorize only Next.js 16.3.1 to exact 16.3.3, required matching Next transitive
artifacts/lock entries, exact-pin policy assertions, and directly necessary
qualification/tests/current documentation. Retain unrelated dependency pins.
An upstream disabling of unsafe AVIF optimization must not be overridden.
Do not use Linux deployment as a policy exemption for the Windows advisory.

## Requirements and observable acceptance

1. Fetch and verify this same open PR/branch/base. Preserve all accepted
   component/local-design implementation and previous immutable transcript.
2. Apply the minimal exact patch dependency update and reproducible lockfile.
   Update matching inventory/notices or exact version assertions only where
   necessary; repository pin enforcement remains equally strict. Prove the
   resolved and built Web Next version is 16.3.3, not only package.json text.
3. Run frozen install, Node lint/format/typecheck/tests/production build,
   repository and supply-chain policy tests, and existing Compose/edge browser
   qualification. Reuse existing Web/Puck/local-design/preview/redirect tests;
   preserve SSR, supported responsive values, private no-store/noindex and
   canonical/workspace separation. No new media feature or broad fresh audit.
4. Run the required complete supply-chain evidence workflow: frozen dependency
   inventory/licenses/notices, image reproducibility, six image SBOMs and scans
   against current vulnerability metadata. Both advisories must be absent as
   vulnerable findings in the patched Web artifact, with no new unexcepted
   Critical finding. Retain evidence and exact artifact/image identities.
   CI may provide expensive qualification instead of duplicating it locally;
   clearly distinguish local runs from actual remote job results.
5. Push, observe required implementation-head CI, and repair concrete in-scope
   patch regressions within this turn. All required gates remain authoritative.
   No vulnerability exception, scanner suppression, stale database, test skip,
   lint exclusion or policy relaxation. If another concrete unrelated blocker
   occurs, report the exact failure and required decision, not a generic PARTIAL.

## Scope, documentation and safety

This is a security defect repair necessary to accept the frozen increment,
not expansion of Objective 078. The one whole-PR hostile audit and its technical
closure stand; strategy will review the dependency delta and final gates.
PR currently has 110 changed files, +28,753/-5,362 including generated/tests/OAP:
this inherited large increment is a closure-only size exception, not permission
for growth. No theme/global regions/header-footer/media/MCP/exact-Agent-workspace
Puck/lifecycle/publication/cleanup/new migration or unrelated upgrade.

Update CURRENT increment/status/evidence documents and PR description with the
security repair and observed qualification, preserving historical evidence.
Main still contains accepted Objective 077; Objective 078 overall stays PARTIAL.
Do not claim merge or completion before strategy accepts. Historical orders and
reports are immutable; the two previously approved corrections are already
closed. No additional historical edits. Lint new Markdown before publication.

Use the existing coding session only; no new agent or PR. Routine installation,
Docker/package/browser work belongs to executor, with passwordless sudo in its
disposable environment. No production access, secrets, hosted runtime, authority
expansion or changes to the closed Chrome issue/exception.

## Publication and exact report

Commit unchanged strategic order and `oap/active=078-o` alongside scoped changes,
push the same PR, then publish
`oap/reports/078-o-next-security-patch.md` as a final report-only SELF child of
the literal implementation SHA. Include PR/branch/base/head, changed files,
old/new dependency versions and integrity, upstream evidence, built image/SBOM
identity, exact tests and remote check links/results, vulnerability results,
remaining risks and unchanged policy/scope confirmation. No unpushed claims.
Report-commit checks may be pending; record them honestly for strategic waiting.
Do not merge, enable auto-merge, create another PR, or choose subsequent scope.
Send exact FIFO `OK` after publication and wait for strategy.
