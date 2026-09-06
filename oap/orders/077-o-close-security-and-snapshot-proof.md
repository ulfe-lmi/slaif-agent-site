# OAP Work Order — 077-o

## Objective and verified state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`f287acc9a176186e0354bc18aff163204e8db347`, whose sole parent is blocked
077-n implementation `4c95dceea50c71276a23dda6f6c3e2321b4cfdb2`. Remote
`main` remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

Preserve the valid 077-m/n product, browser and locale work. Close the remaining
Apache gate through the authorized maintained Ubuntu LTS package path and fix
the exact false-positive snapshot/cancellation evidence. No dynamic `{slug}`
work in this round.

## 1. Qualify an Ubuntu 24.04 LTS Apache edge

The Docker Official Debian Trixie image is blocked by unfixed
`CVE-2026-5450` in glibc. Official Ubuntu security metadata marks that CVE fixed
in Ubuntu 24.04 LTS at `glibc 2.39-0ubuntu8.8`; Ubuntu also maintains its Apache
2.4 package with security backports (including the 2.4.58 Ubuntu package line).
This architecture requires a supported Apache HTTP Server 2.4 adapter, not an
unpatched upstream version number.

Qualify the current immutable Docker Official Image:

```text
docker.io/library/ubuntu:24.04
sha256:33ceb71981b602c1a7443a53469e4dba065f7503eab3078a2d7a57a2ab987517
```

The observed linux/amd64 manifest is
`sha256:1e0a86e57d247923571b75e0aaf48a1449cf8c543d51fb3e07a4a7d7bfa79316`.
Independently reverify the index, manifests, current standard-security package
candidates and Ubuntu CVE status before committing.

- Install only Ubuntu 24.04 standard-repository Apache 2.4 and required runtime
  modules/packages, fully update fixed packages, remove package-manager cache
  and build-only tools, and pin/record exact installed package versions in the
  existing reproducibility evidence.
- Ubuntu Pro, ESM/account-bound repositories, PPAs, arbitrary binaries and
  mutable committed base references are forbidden. If standard LTS packages do
  not provide every fix, do not claim success.
- Adapt the existing reference Apache config/entrypoint/health/parity checks to
  distro paths without changing routing, headers, limits, proxy behavior or
  product semantics. Keep a foreground container process and least privilege
  where the package supports it.
- Replace the failed Trixie facts cleanly and update policy, docs, SBOM/package
  overrides, OCI/repository tests and attribution honestly. Other image pins
  remain untouched.
- Require two reproducible builds, exact base/package facts, Apache config test,
  NGINX/Apache parity, Compose edge behavior, full SBOM/license inventory and
  current Grype scan with zero unexcepted Critical findings. No vulnerability
  exception, scanner suppression, severity override or gate weakening.

If this exact maintained standard-LTS route still cannot reach zero Critical,
report exact package/CVE/fixed-version/Ubuntu status as the genuine blocker.
Do not try unmaintained/interim/rolling/third-party images.

## 2. Make the repeatable-read proof causally valid

Current `test_public_agent_cow_structure_is_visible_only_to_authorized_preview`
does `SELECT 1`, starts Agent mutations, releases Render, and only then awaits
the mutation results. Render can therefore finish before those commits; the
test would pass under `READ COMMITTED` and does not prove a snapshot spanning a
concurrent commit.

Repair the deterministic proof:

- establish the repeatable-read snapshot with a query against the actual
  site/page/locale/navigation/redirect data, not a constant;
- pause Render after that query;
- execute and await the intended public Agent/Editor structural commit(s) while
  Render remains paused;
- only after the commits are durably complete, resume Render;
- prove the paused projection returns the full before-state across page,
  selected/default locale, navigation labels/order/targets, composition/theme/
  bindings and route/redirect decision, while a fresh projection returns the
  full after-state; and
- make the test fail if canonical or preview is downgraded to `READ COMMITTED`.

Provide both preview/COW and canonical read-snapshot proof. Since normal online
Agent/Editor writes cannot alter canonical, owner fixture DML may simulate one
atomic canonical promotion commit solely for the canonical reader test; it must
be clearly identified as test coordination, not claimed product publication.
No timing sleep establishes ordering.

## 3. Assert actual cancellation cleanup and restart state

Current cancellation tests pause before `_query`, cancel, then merely perform a
later render. Extend them to inspect a subsequently checked-out connection and
prove, for canonical and preview pools:

- no open transaction;
- configured default transaction isolation restored (`READ COMMITTED` unless
  the pool contract says otherwise);
- no lingering `app.session_id`, operation or capability context;
- connection remains usable and not aborted;
- no unexpected COW/audit/quota/idempotency change; and
- a subsequent authorized projection returns the expected complete state.

Exercise the Render application lifespan: stop and freshly start the app/
database adapter, then resolve the same durable human-authorized workspace
overlay and unchanged canonical state. A service-object call without lifespan
restart is insufficient.

For browser cancellation, retain the exact before-consume/no-consume and after-
consume/one-event/replay-denied semantics already present; do not weaken the
one-time credential boundary.

## 4. Prove cancellation after tentative locale mutation

077-n adds cancellation while waiting for the structural lock and same-key
retry, not cancellation after the locale row has tentatively changed and graph
validation has completed but before generic mutation completion/audit.

Use a deterministic event around the production service/executor boundary
after `slaif_agent_locale_update` returns but before completion. Cancel there,
then prove locale rows/default/effective routes, redirect/navigation graph,
quota, idempotency, audit and COW operations all rolled back and the identical
idempotency key succeeds on retry. Preserve the shared-lock locale/redirect
race and all migration 053 grants/downgrade evidence.

## Verification and boundaries

Run focused Apache build/SBOM/scan/reproducibility/parity; corrected canonical/
preview snapshot tests; cancellation/pool/lifespan/browser tests; tentative
locale rollback; full Agent/Editor/Render/bootstrap integration; migration and
privilege tests; Python quality/unit/integration; Node contracts; PG14–18;
repository/Markdown/Mermaid; clean Compose/public Agent/browser/Apache edge;
complete supply-chain evidence; then all current-head CI. Push before observing
CI and repair only in-scope failures. No pending/skipped/superseded result is a
pass.

No dynamic `{slug}`/collection detail; no new Agent route or product feature;
no 078 composition/design/Puck; no media/MCP/freeze/review/promotion/source/
sweep/076; no architecture/historical-order/report/general-refactor/production/
release change; no exception or issue closure. Preserve Chrome
`152.0.7977.82`, the empty exception set, every all-status redirect/header case,
the public Agent-created browser workflow and canonical/workspace/site isolation.
GitHub issue #67 remains open until Objective 077 reaches verified `main`.

Commit this exact order and `oap/active` unchanged, push only the existing PR
branch, create no PR, and never merge/auto-merge. Publish exactly
`oap/reports/077-o-close-security-and-snapshot-proof.md` as the final report-
only child of a literal implementation SHA with
`Report publication commit: SELF`. Include exact Ubuntu base/manifests/packages/
CVE status/final digest/reproducibility/SBOM/license/scan/parity; corrected
barrier chronology and proof that `READ COMMITTED` fails; checked connection
state after cancellations; actual lifespan restart; post-tentative locale
rollback/retry/audit/quota/COW evidence; commands/counts/skips/current checks;
no scope/secret/extra PR/merge/exception; remaining dynamic/final 077 scope;
and strongest reason not to accept.

`PARTIAL`/`BLOCKED` requires a concrete external or technical blocker with
exact attempted evidence. Do not return because tests/Compose/CI are long. No
post-report push. Signal exact FIFO `OK`, then wait for strategic review.
