# OAP Work Order — 079-2-b (Alpine libcrypto/libssl pin repair; 079/2 continuation)

> **STATUS: ACTIVATED — operative order.** Published atomically by
> strategy 2026-10-03 to
> `oap/orders/079-2-b-alpine-pin-repair.md` with `oap/active` =
> `079-2-b`, as a same-PR continuation of `079-2-a` (PR #93). It
> implements the strategy scope decision of 2026-10-03: repair the
> pre-existing, externally forced Alpine pin failure that blocks every
> Docker-image-build check on this repository (including `main`), as a
> finite packaging defect inside the 079/2 review unit. The coding
> agent executes under the normal OAP execution contract; strategy
> remains reviewer/acceptor/merger.

## 1. Identifier and mode

- ID: `079-2-b` (increment-qualified round ID: second round of semantic
  increment 2 of numeric Objective 079; same PR as `079-2-a`).
- Mode: CONTINUATION (same branch, same PR). CREATE_NEW_PR: no.
- PR: #93 (`079-2-a: Gallery + LogoGrid media-reference list components
  (079/2)`), branch `oap/079-2-a-gallery-logogrid`, base `main`.
- Do not create, amend, close, or touch any other PR.

## 2. Verified current state (strategy-verified 2026-10-03 against
live GitHub and local forensics)

- Remote `main` = `577509e7bc990d85a10af5954bee3c6f7c888a4f` (post-079/1
  merge; unchanged).
- PR #93 is OPEN and MERGEABLE; exact remote head
  `b357f8c6c03078ddc3837a058b93c74b79c6f0b3` (report-only commit; parent
  `0ab21e622e6fc5cac8bb931248332e0272ee1e28` = 079-2-a implementation
  head; chain to base verified). 33 files base->head: 32 implementation
  (+2528/-72) + report.
- `oap/reports/079-2-a-gallery-logogrid.md` status is BLOCKED on exactly
  one gap: Criterion 9 (all 20 required checks green), root cause
  external and pre-existing (documented in the 079-2-a report).
- Required-check states at head `b357f8c` (observed 2026-10-03): 14
  SUCCESS (Repository policy, Detect supported languages, Node
  contracts, Analyze actions/python/javascript-typescript, Python 3.12/
  3.13/3.14 quality and package, Markdown, Mermaid, Dependency review,
  CodeQL); 2 FAILURE (`Compose and edge packaging`, `Supply-chain
  evidence`); 5 PENDING at drafting time (Foundation PostgreSQL
  14-18). Acceptance under this order is based solely on the NEW head
  produced by this round.
- Strategy independently re-proved the external root cause 2026-10-03:
  (1) the live Alpine v3.23 `main/x86_64` index lists exactly one
  `libcrypto3` and one `libssl3` entry, `V:3.5.9-r0` — `3.5.8-r0` was
  rotated out of the index; (2) base `577509e` pins `3.5.8-r0` in
  `apps/web/Dockerfile` (lines 7 and 36), `infra/nginx/Dockerfile`
  (lines 16 and 17), and `infra/postgres/Dockerfile` (lines 20 and 22,
  plus the exact-installed-version assertions at lines 23 and 25) — a
  pin introduced by merged commit `b946d26` and present at base; (3)
  the PR #93 diff touches no Dockerfile; (4) direct reproduction on the
  pinned base image
  `node:24.14.1-alpine3.23@sha256:8510330d3eb72c804231a834b1a8ebb55cb3796c3e4431297a24d246b8add4d5`
  fails with the identical apk resolution error (`breaks:
  world[libcrypto3=3.5.8-r0]` / `world[libssl3=3.5.8-r0]`); (5)
  therefore `main` itself is currently unbuildable for the same reason.
- Strategy scope decision (recorded): this repair is a finite packaging
  defect required to make the already-delivered 079/2 behavior
  mergeable, and is therefore authorized inside the 079/2 PR as a
  continuation round rather than a new semantic family. A separate
  packaging PR from `main` would force a subsequent rebase of PR #93
  (new head SHA, report erratum) plus a second merge cycle with no
  product benefit; the pin bump is forced by the index rotation
  (`3.5.8-r0` no longer exists), is a patch-level OpenSSL update, and
  is bounded to eight line changes in three files.

## 3. Strategic context

- The 079-2-a implementation (R1-R8 of that order) was independently
  verified by strategy on 2026-10-03: catalog 31 with exact Gallery /
  LogoGrid R1 contracts; exact bounded error-key vocabulary
  `{gallery,logogrid}.{item-missing,item-foreign-site,item-not-image,
  items-out-of-range}`; fail-closed trusted renderers with no JS, no
  event handlers, no inline styles, no sandbox/target; OpenAPI delta
  exactly four changed `x-slaif-*` values and exactly five new property-
  scope entries (63 -> 68 / 62 -> 67) with strip-identity sha256
  `921572e78e4af044770cf2faaefa45b64080b5bbb3a9655a6be6d696db819b83`
  verified identical at base and head; in-place `060_001` regeneration
  limited to the two-line baked-catalog pair; lockfiles, workflows,
  supply-chain files, and migrations untouched; full local evidence set
  green (710 unit, 235 integration, pnpm test/build, full Compose
  smoke rc=0, clean debug-stack browser E2E).
- The only unsatisfied acceptance item is Criterion 9, blocked solely by
  the externally forced packaging failure above. No product defect was
  found in review.

## 4. Bounded scope (exactly)

- P1: bump the exact-version pins `libcrypto3=3.5.8-r0` and
  `libssl3=3.5.8-r0` to `libcrypto3=3.5.9-r0` and `libssl3=3.5.9-r0` in
  exactly: `apps/web/Dockerfile` (2 apk sites), `infra/nginx/Dockerfile`
  (2 apk sites), `infra/postgres/Dockerfile` (2 apk sites + the two
  exact-installed-version assertion lines, which must read
  `3.5.9-r0`). Eight line changes across three files. No other pin,
  package, base image, or Dockerfile structure change.
- P2: prove the new pin resolves before relying on builds: run an apk
  resolution probe for `libcrypto3=3.5.9-r0` and `libssl3=3.5.9-r0` on
  the pinned base image (the exact probe command and output belong in
  the report).
- P3: force fresh image builds for the three affected images (no stale
  local-cache reuse of the old pin), then run the FULL Compose smoke
  (`sh tools/compose/smoke.sh <project>`, all 13 projects) to rc=0.
- P4: push the branch; the final head must have ALL 20 required checks
  SUCCESS (in particular `Compose and edge packaging` and `Supply-chain
  evidence` must flip green).
- P5: publish the round report (see Section 9) as a report-only commit
  (`Report publication commit: SELF`) on the same branch.

## 5. Explicit non-goals

- No change to any other pin, base image, or Dockerfile content (base
  images remain digested/pinned exactly as at base).
- No product code, configuration, migration, lockfile, workflow, or
  supply-chain file change of any kind.
- No current-truth documentation changes (the five R5 surfaces remain
  accurate; the pin repair is not an increment-level documentable fact).
- No version other than `3.5.9-r0` (no `3.6.x`, no unversioned pin, no
  index-pinning workaround). If `3.5.9-r0` fails resolution or the
  smoke fails because of the new pin, STOP and report BLOCKED with the
  exact evidence; do not improvise alternatives.
- Do not touch dependabot PRs. Do not merge. Do not edit the committed
  079-2-a order, its report, or any other OAP transcript file; `active`
  is replaced by this order per protocol.

## 6. Requirements

### R1 - Pin bump (P1 + P2)

Exactly the eight line changes of Section 4 P1. First execute and record
the apk resolution probe for `3.5.9-r0` (P2) on the pinned base image
`node:24.14.1-alpine3.23@sha256:8510330d3eb72c804231a834b1a8ebb55cb3796c3e4431297a24d246b8add4d5`.
The probe must show successful resolution (the apk transaction listing
`libcrypto3-3.5.9-r0` and `libssl3-3.5.9-r0`).

### R2 - Fresh builds + full smoke (P3)

Invalidate/avoid reuse of locally cached images built from the old pin
for the web, nginx, and postgres images, rebuild, and run the full
Compose smoke (13 projects) to rc=0. The smoke log must show the
affected images being (re)built (not served from cache) and the exact
key lines: `compose-e2e: OK projects=13 ...`, `media-e2e: OK ...`,
`public-agent-acceptance: OK ...`, `compose-smoke: OK`.

### R3 - Push and CI (P4)

Push the implementation commit(s) of this round to the same branch.
Verify (and report) that ALL 20 required checks reach SUCCESS on the
exact final head. If a required check fails for an in-scope reason,
repair within this round's scope, push, and re-verify; the final head
is the acceptance head. No CI re-run is permitted for an unmodified
head (flake policy); a new pushed head supersedes.

### R4 - Report (P5)

Publish `oap/reports/079-2-b-alpine-pin-repair.md` as a report-only
commit (SELF) whose parent is this round's implementation head.

## 7. Acceptance criteria (observable)

1. `git diff --name-only <079-2-a report commit b357f8c>..<round
   implementation head>` lists exactly: `apps/web/Dockerfile`,
   `infra/nginx/Dockerfile`, `infra/postgres/Dockerfile` — and
   `git diff --stat` on that range shows eight changed lines total.
2. The apk resolution probe output for `3.5.9-r0` is recorded in the
   report (command + exact output).
3. Fresh-build evidence for the three affected images plus the full
   smoke rc=0 key lines are recorded in the report.
4. All 20 required checks SUCCESS on the exact report-only head
   (per-check table with CI/CodeQL run IDs; `Compose and edge
   packaging` and `Supply-chain evidence` included).
5. The report commit changes only the report file; its parent is the
   round implementation head; the remote PR head equals the report
   commit.
6. No other file differs from `b357f8c` (full name-only diff check).
7. Status is COMPLETE only if every criterion above is evidenced;
   otherwise BLOCKED/PARTIAL with the exact gap.

## 8. Verification and workflow

- Local, in order: apk resolution probe (R1); fresh image builds +
  `sh tools/compose/smoke.sh <project>` full smoke (R2);
  `uv run --frozen python tools/check_repository.py` (repository
  policy); `npx --yes markdownlint-cli2@0.23.2` on the report file
  (zero issues).
- Push, then poll required checks on the exact head until all are
  terminal; report the per-check table with run IDs.
- GitHub workflow: push to the existing branch only; one round, one
  implementation commit (or the minimal set of in-scope repair
  commits); then the report-only commit; no merge by the executor.

## 9. Report requirements

`oap/reports/079-2-b-alpine-pin-repair.md` must state: identifier and
mode (CONTINUATION, PR #93); exact round implementation head SHA and
report SELF; the eight-line diff (file:line per site); the apk probe
command and output; the fresh-build evidence and full smoke key lines;
the complete 20-check per-check table at the exact report-only head
with run IDs; the cumulative base->head size table per the 2026-09-14
review-unit governance (base `577509e` -> final head, grouped:
production/config, migrations, tests/evidence, generated artifacts,
docs, OAP transcript; state that the review trigger is not crossed:
cumulative production/config 13 files / ~542 substantive lines);
confirmation that no product code changed this round; and an honest
status (COMPLETE iff all Section 7 criteria are evidenced).

## 10. Predeclared review budget (2026-09-14 review-unit governance)

- Production/config: 3 files (the three Dockerfiles), ~8 substantive
  lines.
- Migrations: 0. Tests/evidence: 0 new (existing full smoke re-run).
  Generated artifacts: 0. Docs: 0.
- OAP transcript: this order + one new round report (~120 lines) +
  `active` replacement.
- Cumulative after this round (base `577509e` -> final head): 35 files,
  ~+2536/-72, production/config 13 files / ~542 substantive lines; the
  ~20-30 implementation-file / several-thousand-line review trigger is
  NOT crossed; CLOSURE_ONLY does not begin.

## 11. Review-unit governance (2026-09-14 amendment, in force)

This round is a finite packaging defect repair inside the 079/2 review
unit per the strategy scope decision recorded in Section 2. No new
semantic family, no adjacent feature, no opportunistic scope. If the
evidence shows the failure is NOT the documented pin (or the new pin
itself fails), stop and report BLOCKED with the exact evidence;
strategy decides the next step.
