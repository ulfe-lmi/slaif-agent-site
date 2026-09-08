# OAP Work Order — 077-p

## Objective and verified state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`be6e40d540ab769edcdfb7d90f1bea7808eb9eb1`, whose sole parent is blocked
077-o implementation `49ad633012d8193406de6ca5c03b769b215198c6`. Remote
`main` remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

Accept the Ubuntu Apache image qualification for progression: its final image
has zero unexcepted Critical findings. Resolve the two concrete remaining
blockers: an architecture-contradicting lifecycle lock mode that prevents
mutation during active preview, and fixable Postgres-image `libcurl` findings.
Then complete the causal snapshot/cancellation proof. Do not implement dynamic
`{slug}` behavior.

## 1. Repair the product lifecycle lock contract

The architecture requires ordinary active-workspace reads and mutations to
take the workspace lifecycle key in shared mode; freeze/review/promotion takes
the same key exclusively after marking `FREEZING`. Structural writes then take
their workspace+site structural key exclusively. Current code contradicts its
own comments:

- migration 050 `control.slaif_agent_require_capability` calls exclusive
  `pg_advisory_xact_lock(hashtextextended(workspace_id,280))` while saying it
  establishes the lifecycle shared lock;
- `control.slaif_agent_structural_lock` repeats that exclusive lifecycle lock
  before the separate structural key; and
- migration 028 `control.slaif_human_editor_workspace_assert(...,p_lock=true)`
  takes the lifecycle key exclusively.

This causes an authorized preview's shared lock to block all Agent/Editor
mutations for the duration of the Render snapshot. Correct the contract:

```text
workspace lifecycle key, namespace 280:
  active preview + Agent/Editor mutation = shared
  freeze/review/promotion transition      = exclusive

workspace+site structure key, namespace 994:
  page/locale/navigation/redirect writes  = exclusive after lifecycle shared
```

- Use `pg_advisory_xact_lock_shared` for the runtime lifecycle acquisition in
  the exact Agent/Editor functions above. Keep the structure key exclusive and
  preserve lock order: lifecycle first, structural/resource locks second.
- Do not change the distinct human-workspace resolution key namespace 281,
  idempotency/resource/quota locks, browser run locks, or future reviewer
  exclusivity.
- Since migrations 028/049–053 exist only on this still-unmerged objective and
  the human has confirmed there are no deployed installations, they may be
  corrected in place if that gives the safest fresh-install and downgrade
  contract. Otherwise add one exact reversible migration. Do not duplicate the
  large capability function merely for convenience or leave fresh and upgraded
  databases with different semantics.
- Preserve capability/workspace/site/state rechecks, freeze fail-closed intent,
  COW isolation, quota/idempotency/audit atomicity, grants/owners/search paths,
  and cancellation behavior.

Add real PostgreSQL multi-connection proof that:

1. a paused authorized preview holds the shared lifecycle key while a public
   Agent and Editor mutation on the same active workspace can acquire shared
   lifecycle authority and commit;
2. structural writers still serialize on the namespace-994 key and cannot
   produce mixed routes/graphs;
3. a test-held exclusive lifecycle lock (standing for freeze) blocks new
   preview and mutation shared locks, then both recheck lifecycle state after
   release; and
4. cancellation at each wait point leaves no lock, transaction, COW, quota,
   idempotency or audit residue.

Never weaken the test by releasing preview before the mutation commits.

## 2. Complete causally valid Render snapshot proof

With the corrected shared lifecycle lock, repair the rejected test chronology:

- establish a `REPEATABLE READ` snapshot with an actual structure-table query;
- pause Render;
- start and fully await the public Agent/Editor structure commit while Render
  remains paused;
- assert that commit is durable before releasing Render;
- resume and require the entire paused projection to be the complete before-
  state; then require a fresh projection to be the complete after-state; and
- add the canonical companion using one atomic owner-fixture update solely to
  simulate a promotion commit for reader isolation.

Cover page, selected/default locale, navigation labels/order/targets,
composition/theme/bindings, and route/redirect decision where present. Include
a negative control that demonstrably produces mixed/after data under
`READ COMMITTED`, so the test proves the isolation level rather than merely
asserting it. Use events/DB lock observation, never timing sleeps.

## 3. Finish exact cancellation and restart assertions

After cancelling in-flight canonical and human-preview projection, acquire the
same pools and directly assert: no open transaction; usable connection;
configured default isolation restored; no `app.session_id`, operation or
capability context; no new audit/idempotency/quota/COW state. Then perform a
successful authorized render.

Stop and freshly start the Render application lifespan/database adapter and
prove the same durable human-authorized workspace overlay plus unchanged
canonical page still resolve. Preserve existing before-consume/no-event and
after-consume/exactly-one-event browser cancellation/replay semantics.

Add the still-missing post-tentative locale cancellation: pause only after the
production locale SQL wrapper returns (therefore its graph validation has run)
but before generic completion/audit, cancel, prove complete rollback, and retry
the identical idempotency key successfully.

## 4. Clear the Postgres image Critical findings

The Ubuntu Apache image is now clean. The full current Grype gate instead finds
these eight Critical IDs on Postgres Alpine `libcurl 8.20.0-r0`, with fixed
version reported as `8.22.0-r0`: `CVE-2026-10536`, `CVE-2026-11564`,
`CVE-2026-11856`, `CVE-2026-8924`, `CVE-2026-8925`, `CVE-2026-8926`,
`CVE-2026-8927`, `CVE-2026-9079`.

- Inspect official Alpine 3.23 and 3.24 stable repositories and exact dependency
  compatibility. Prefer the minimum exact `libcurl` security overlay on the
  current image if available.
- If the fixed package requires the current Docker Official
  `postgres:18.6-alpine3.24`, the independently observed immutable index is
  `sha256:d3e1620b530c944afa6e887d22eb899824da68e19c52024bf98f5220c88a65b2`;
  reverify and qualify it before use. Record the exact manifest and all updated
  crypto/curl package pins.
- Preserve PostgreSQL 18.6 behavior, data-directory/init semantics, extension/
  locale requirements, backup/restart/recovery, COW matrix, multi-platform
  source, reproducible builds, SBOM/license and one-command Compose behavior.
- Update policy/docs/package facts/tests consistently and retain every other
  image pin. Do not use Alpine edge/testing, a mutable tag, mixed-distribution
  packages, a new exception, scanner suppression or severity override.

If no compatible fixed package exists in a maintained stable repository,
report exact solver/repository evidence as a blocker. Do not switch database
engine/version or invent a custom PostgreSQL build in this round.

## Verification and boundaries

Run focused lifecycle-lock/preview-mutation/freeze-wait/cancellation tests;
corrected preview+canonical snapshot negative controls; pool/lifespan/post-
tentative-locale tests; Postgres reproducible build/SBOM/scan/recovery/COW/
PG14–18; full Agent/Editor/Render/bootstrap integration; Python quality/unit/
integration; Node contracts; repository/Markdown/Mermaid; clean Compose/public
journeys/Apache parity; complete supply-chain evidence; then all current-head
CI. Push before observing CI and repair only in-scope failures. No pending,
skipped, superseded or inferred result is a pass.

No dynamic `{slug}`/collection detail; no new public route; no 078 composition/
design/Puck; no media/MCP/freeze implementation/review/promotion/source/sweep/
076; no architecture/historical-order/report/general-refactor/production/
release change; no exception or issue closure. Preserve Chrome
`152.0.7977.82`, clean Ubuntu Apache evidence, all-status redirects, public
Agent browser workflow, migration 053 semantics and canonical/site/workspace
isolation. GitHub issue #67 remains open until verified Objective 077 merge.

Commit this exact order and `oap/active` unchanged, push only the existing PR
branch, create no PR, and never merge/auto-merge. Publish exactly
`oap/reports/077-p-repair-lifecycle-lock-and-postgres-scan.md` as the final
report-only child of a literal implementation SHA with
`Report publication commit: SELF`. Include exact lock functions/modes/order/
wait outcomes; causal snapshot timeline and negative control; post-cancel pool
state; lifespan restart; post-tentative locale rollback/retry; Postgres source/
manifest/packages/CVEs/final digest/reproducibility/SBOM/recovery; commands/
counts/skips/current checks; no scope/secret/extra PR/merge/exception; remaining
dynamic/final 077 scope; and strongest reason not to accept.

`PARTIAL`/`BLOCKED` requires a concrete external or technical blocker with
exact attempted evidence. Do not return because tests/Compose/CI are long. No
post-report push. Signal exact FIFO `OK`, then wait for strategic review.
