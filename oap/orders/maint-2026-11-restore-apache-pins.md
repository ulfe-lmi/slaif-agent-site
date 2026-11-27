# maint-2026-11 — restore the pinned Apache build

## Authority and remote base

This is the November 2026 scheduled maintenance round. The human
authorized this separate PR on 2026-11-27 under
`oap/governance/2026-11-26-operating-rhythm.md`. Mode `CREATE_NEW_PR`
from current verified `main`
`2ac24ea3ad4047827f4c594185ffa795ccd98853`. Use a fresh isolated checkout
at `/home/janezp/codex-work/slaif-agent-site-maint-2026-11` and branch
`oap/maint-2026-11-apache-pins`. ROOT confirmed no existing scheduled
November maintenance PR or branch. Create exactly one draft PR.

Read the coding constitution, coding communication protocol, compact
architecture and operating-rhythm amendment. The amended monthly identifier
is `maint-2026-11`, without a product number or letter. The existing
083/14 product work is suspended before any remote publication. Its
workspace and order remain preserved. This turn owns only the separate
maintenance checkout and the exact maintenance transcript.

## Required changes and evidence

1. **Restore the exact Apache build.** The former
   `2.4.58-1ubuntu8.19` pins are absent from the configured Noble apt
   archives. ROOT independently read the official amd64 Noble updates
   and security package indexes. Both list `2.4.58-1ubuntu8.20` with
   matching SHA-256 values for `apache2`, `apache2-bin`, `apache2-data`,
   and `apache2-utils`. Reverify from official sources at execution.
   Advance only those four exact pins and the matching install-policy
   and OCI contract expectations. Preserve the official base digest,
   apt/libapt and OpenSSL pins, apt protections, sources, OCI and edge
   settings, and all security, licensing and reproducibility gates.
   Prove clean installation, exact versions, Apache syntax and
   unchanged product routing. If the approved pin is unavailable or
   a required policy gate needs expansion, report the evidence to ROOT
   without widening scope.
2. **Recognize the authorized maintenance identifier.** Current
   `tools/check_repository.py` recognizes only numeric active and
   artifact IDs. Implement the amendment's exact `maint-YYYY-MM` form
   for one active ID and unique order/report mapping, with a real
   calendar month `01` through `12`. Preserve numeric parsing,
   exact full matches, historical required reports, duplicate and
   malformed refusals, temporary-file policy, and all other checks.
   Cover valid maintenance active and historical pairs, malformed
   years/months and extra text, collisions and missing historical
   reports in the repository policy tests. A filename may append a
   descriptive slug under the same existing convention. The resolved
   ID is exactly `maint-2026-11`. This is the targeted tooling
   implementation of the already binding governance, with no change
   to the human policy or product behavior.
3. **Verify the required gates.** Run the focused OCI packaging and
   repository-policy tests plus the required preparation and frozen
   Node gates. Use approved owned local resources for any clean local
   build. Obtain fresh current-head GitHub Compose coverage of NGINX
   and all 19 projects, six browser profiles, real media acceptance,
   isolated worker runs and Apache syntax. Obtain the exact fresh
   six-image supply evidence with reproducible subjects, verified
   checksums, loadable SBOMs and scans under existing policy, with
   zero unexcepted Critical findings and no new exceptions. Require
   CodeQL and all 20 matching-app required checks and ten actual
   PostgreSQL matrix children. ROOT independently verifies those on
   final SELF. State local, GitHub, failed, skipped and pending
   results accurately. No earlier 083/14 diagnostic run qualifies
   this maintenance.

## Scope and durable reporting

Confine changes to Apache pins, associated policy and packaging test,
maintenance-ID validation and its tests, any necessary operations
documentation and this round's transcript. No unrelated dependency
updates, scanner changes or exceptions, database or API code,
product work, release claims, changed required jobs, or use of foreign
resources. Preserve historical orders and reports byte-for-byte.
Do not copy the suspended product order into the maintenance PR.
Leave the existing Dependabot PRs untouched. Routine authorized guest
setup belongs to the executor.

Use test voice and keep fixture credentials only inside the test process
environment. Redact at source and capture time. Durable reports document
exact behavioral evidence and subjects, without process IDs, session
handles, FIFO inodes, or prompt-delivery digests.

Correlate one fresh ASCII `OK` and EOF to canonical `oap/active`
and the unique order. Commit exact order and active bytes with the
maintenance changes, push the branch, publish and verify the sole
draft PR before composing the report. Publish exactly one
`oap/reports/maint-2026-11-restore-apache-pins.md` in canonical and
execution trees using byte-identical atomic publication after exact
Markdownlint on the complete content. Include result by criterion,
commands and exact outcomes, artifact and job identities, limits,
literal `Implementation head SHA: <40-hex>`, and
`Report publication commit: SELF`. Push the report-only child of
that implementation SHA and verify exact remote bytes, path, parent
and PR head. Send exactly the ASCII letters `OK` once, no newline,
and close the verified response FIFO. Use `printf '%s' OK` with
the verified FIFO as the redirection target. No other PR, merge,
auto-merge, force push, extra order or claim of product acceptance.
