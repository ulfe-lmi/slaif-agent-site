# OAP Work Order — 078-t: qualify the required browser security update

- Objective078; maintenance increment078/3; round078-t; CREATE_NEW_PR.
- Repository `ulfe-lmi/slaif-agent-site`; base verified current remote `main`:
  `a9d3e6800d5e8b5fd5c9cd9e0be5010184058c6b`.
- New branch `oap/078-3-browser-security-refresh`; exactly one NEW PR.
- PR79 is accepted/merged theme increment; PR77 is also closed. Do not amend,
  reopen or add feature scope to either. Numeric078 remains PARTIAL.
- The prospective bounded-semantic-increment amendment permits this new PR
  with continuing078letters. Page-style draft was never activated and is deferred.

## Concrete executed failure and verified upstream fix

All20required final PR79 head checks passed before merge. The post-merge
CI run34448973084 on maina9d3e68 subsequently FAILED in supply-chain job
102780031003; all other applicable post-merge jobs passed, including CodeQL.
The scanner reports browser-worker unexcepted Critical findings:

```text
CVE-2026-87438 CVE-2026-87448 CVE-2026-87455 CVE-2026-87464
CVE-2026-87470 CVE-2026-87474 CVE-2026-87488 CVE-2026-87492
CVE-2026-87500 CVE-2026-87504 CVE-2026-87520 CVE-2026-87526
CVE-2026-87527 CVE-2026-87529 CVE-2026-87547 CVE-2026-87558
CVE-2026-87581 CVE-2026-87607 CVE-2026-87609 CVE-2026-87613
CVE-2026-87634 CVE-2026-87637 CVE-2026-87638 CVE-2026-87643
CVE-2026-87646 CVE-2026-87650
```

This is a genuinely executed new gate failure, not a date/exception-expiry
investigation. Do not reopen GitHub issue67 or create/extend any exception.
Do not lower severities based on a different vendor rating or platform claim.

Strategy fetched Google's [Chrome153 security release](https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0808145027.html)
and official [CfT Stable metadata](https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json).
Observed metadata timestamp2026-09-09T22:16:52.946Z, Stable153.0.8010.36,
revision1681091, Linux64 artifact:
[official archive](https://storage.googleapis.com/chrome-for-testing-public/153.0.8010.36/linux64/chrome-linux64.zip).
Reverify those exact facts and archive availability before changing pins.

Current `services/browser-worker/Dockerfile` replaces the pinned Playwright
image's payload with CfT152.0.7977.82, archiveSHA256
`0704631fb3e4f741092e08f55272f90abc3e307f991f05f332924364415b02e0`.
`supply-chain/policy.json`, `tools/supply_chain/policy.py`, runtime version/env,
smoke assertions and current deployment docs lock that version/hash. Preserve
exact pin/hash enforcement while replacing the vulnerable payload.

## Bounded implementation and qualification

1. Fetch fresh main and verify the merged baseline, no existing active
   maintenance PR/branch, and same live coding session. Preserve accepted
   component/theme behavior. Create only the named new maintenance PR.
2. Reproduce/identify the affected old browser artifact/package from available
   evidence or a narrow local browser-image scan if needed; do not repeat all
   expensive old-image qualification merely to rediscover the logged finding.
3. Download the exact official153.0.8010.36 archive, compute and freeze its
   actual SHA256, verify real `chrome --version`, and update all directly
   related runtime/policy/inventory/provenance/pin/assertion/docs records.
   Never invent a hash or use a moving channel/download at build/runtime.
   Distinguish CfT revision1681091 from a Playwright bundle-directory revision;
   do not mislabel metadata simply because an existing executable path is reused.
4. Prefer retaining the current exact Playwright1.62.1 package/base image and
   the established verified-browser-replacement mechanism. Prove compatibility
   with the new engine; do not assume it across a major Chrome version. If an
   actual incompatibility requires a minimal matching Playwright/package/base
   upgrade, identify the exact blocker and required version/qualification before
   expanding beyond this browser-payload repair. No unrelated dependency refresh.
5. Preserve sandbox, UID10001, read-only root, exact capabilities/seccomp,
   restricted egress/DNS/redirect policy, no DB/host/Docker mounts, Chromium-only
   product payload, private immutable artifact authentication/quotas, separate
   credentials and no runtime downloader/package manager. If the new binary
   needs weaker confinement, stop for strategic/human decision; never widen it.
6. Run focused worker/preview/target-map/runtime-version/security/network/
   artifact/cancellation/restart tests, the actual same-workspace Agent theme
   and component preview workflows, required six stable E2E targets, clean
   Compose/edge proof and all current-head required CI. Do not equate launching
   Chrome or reading its version with successful qualification.
7. Generate reproducible images, license/notices/dependency inventory, SBOMs
   and fresh scans for all six release-policy images. The built browser-worker
   artifact must actually contain153.0.8010.36 and have zero unexcepted Critical
   findings, including the26above. Retain High/other findings honestly. Existing
   dependency/license/vulnerability gates stay equally strict; no exceptions,
   scanner suppressions, stale database, disabled browser tests or weak hashes.

## Preserve failed-scan evidence

The failed main job skipped its success-only upload step, leaving zero artifacts
available for diagnosis. Make the minimum related correction: retain safe raw
scan/SBOM diagnostics on failure too, clearly marked incomplete/unqualified if
the success manifest was never produced. Never manufacture PASS or suppress the
original gate exit status. Checksum retained diagnostic files where practical;
keep bounded existing retention and exclude credentials/private browser content.
This is preservation of the exact failed security evidence, not a broad CI or
observability redesign. Prove failed validation remains failed with diagnostics
retained, and successful qualification still produces the normal verified bundle.

## Scope, truth and workflow

No page-style/global-region/header-footer/catalog/media/MCP/Puck/lifecycle/
publication feature or unrelated cleanup belongs here. No application SQL or
content-model behavior change. Routine safe downloads/builds/browser/tool/DB
setup belong to the existing coder's passwordless-sudo VM, not the human.

Update current increment/MVP/deployment/security qualification docs: PR79 is
accepted/merged with current post-merge security regression under maintenance;
do not pretend its pre-merge checks failed or that the broader MVP is complete.
Record actual source/artifact hashes, package identities, scan timestamp/digest,
image/SBOM identities and qualification evidence. Preserve historical orders,
reports and the closed exception history. Read back the new PR description
from GitHub before claiming it updated; REST PR API is a fallback for CLI errors.

Commit the supplied strategic `oap/audits/078-2-strategic-acceptance.md` unchanged.
Commit exact order and active078-t, scoped implementation/evidence/current docs;
push and create exactly one new PR. Observe checks and repair concrete in-scope
failures within this turn. Report only genuinely pushed/verified state. Publish
`oap/reports/078-t-qualify-browser-security-update.md` as final report-only SELF
child of a literal implementation SHA, with PR/branch/base/head, exact changes,
artifact/version/hash proof, test/scan/check results, failed-evidence retention,
scope/size, limitations and no exception/no merge confirmation.
Lint Markdown before publication. Never merge/auto-merge or replace the coder.
Send exact responseFIFO OK after publication, then wait using a REAL byte-reading
control listener. Strategy independently reviews and merges only exact-head green.
After this maintenance PR and post-merge verification, page-style work starts
from fresh main in another bounded PR under the next unused078letter.
