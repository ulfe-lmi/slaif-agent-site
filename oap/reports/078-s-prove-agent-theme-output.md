# OAP Coding-Agent Report — 078-s

## Work order

- Identifier: `078-s`; work-order file: `oap/orders/078-s-prove-agent-theme-output.md`
- Numeric objective: 078; increment: 078/2; round: 078-s
- PR mode: `AMEND_EXISTING_PR`
- Exact order SHA-256: `d37204a5ec98485c96d52543dbaf669fdc2f9d81f236143d6e7575eae24b2b89`
- Active pointer bytes: `078-s\n`; active SHA-256: `3321b053065b56718b8f8af92406d43fb9735366073f781829563337f884c4a7`

## Status

COMPLETE

This is an evidence-only closure of the bounded 078/2 site-theme increment. It
does not reopen the verified 078-r production repairs. Numeric Objective 078
remains `PARTIAL`.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#79](https://github.com/ulfe-lmi/slaif-agent-site/pull/79), `OPEN`
- Base/head: `main` / `oap/078-2-site-theme-tokens`
- Starting remote/report head: `7803a6e4c8a6a7136fd1897210190a859855cbc4`
- Literal implementation head: `4733071685eb11f5c1fc7d6732aeea5d1ab488c9`
- Implementation commits: `f8baae4e011b662d60cee7e9b862ddb8df759a8d`, then
  `4733071685eb11f5c1fc7d6732aeea5d1ab488c9`
- Report publication commit: `SELF`
- Report-only commit parent: the literal implementation head above
- `CREATED_NEW_PR`: NO; `AMENDED_EXISTING_PR`: YES; extra PR: NO
- Merge or auto-merge: NO

The 078-s increment changes 14 paths relative to the starting report head,
with `659` insertions and `37` deletions. They comprise seven current
documentation/ledger paths, one immutable order, five verification paths, and
one public acceptance path. No production dependency, generated contract, or
historical order/report changed. The full PR delta from verified merged main
at this head is 66 paths, `8004` insertions, and `631` deletions; this is the
repository-observed size, not a new scope expansion.

## Exact changes

- Added a real NGINX Playwright proof that creates two human-issued workspaces,
  issues an Agent capability, PATCHes all four theme groups through the public
  Agent API, and reads the same Agent workspace’s authorized preview DOM and
  computed styles without mutating the rendered DOM/classes/styles.
- The proof asserts the returned version/theme and actual palette, typography,
  width, spacing, gap, radius, and shadow classes/styles; it checks private
  `no-store`/`noindex` headers, canonical and other-site isolation, and the
  untouched workspace’s default theme.
- A same-URL response fixture temporarily substitutes canonical/default theme
  classes only to prove the exact assertion rejects wrong output; the route is
  unregistered and the real Agent-workspace response is reloaded and asserted
  again.
- Extended the public Agent browser acceptance helper to inspect same-workspace
  preview HTML theme classes before checking the existing private browser
  artifacts. Existing restart/readback/exact-replay proof is retained.
- Added the final 064-to-065 migration re-upgrade assertion for valid data,
  current version, runtime execute privilege, private legacy schema, and the
  new Agent theme function contract.
- Added redacted E2E response diagnostics that preserve only a finite method,
  numeric status, and route-family classification; added three sanitization
  and vocabulary tests. Raw URL/query/path, payload, headers, cookies, and
  credentials are never emitted.
- Reconciled current README/API/testing/MVP/increment truth and the PR
  description to 078-s, while retaining global Objective-078/MVP boundaries.

## Acceptance evidence

### Same-workspace Agent output

- `agent-theme-patch-renders-in-the-same-authorized-workspace` passed through
  public NGINX. It used a real human-issued capability, public Agent PATCH,
  same-workspace human-authorized preview, actual DOM/computed-style reads,
  all four groups, private headers, canonical/other-site isolation, and an
  exact same-URL wrong-theme sensitivity control followed by restoration.
- The expected Agent output was Meadow/serif/spacious/bold/xl/lg/sm/lg/md,
  with computed root/background/foreground/font/width/padding and existing
  local grid, radius, and shadow values asserted. The untouched same-site
  workspace stayed Ocean/default and the canonical demo/parity pages stayed
  unchanged.
- `public_agent_acceptance.py` also passed its real Agent browser-worker proof,
  same-workspace preview HTML class assertions, private screenshot/summary
  artifact binding, Agent restart/readback, and exact idempotent replay.

### Migration continuity

- `test_agent_065_theme_data_round_trip_preserves_legacy_state` passed the
  genuine fresh-064 baseline, 064-to-065 upgrade, exact five-function and
  semantic-constraint restoration on downgrade, valid data preservation, and
  final 064-to-065 re-upgrade.
- Final re-upgrade assertions proved `065_001`, valid theme schema/data,
  `slaif_agent_runtime` execute privilege for the Agent theme update function,
  the current Agent theme read function, and the private legacy schema.

### Honest response diagnostics and Firefox

- `tests/contracts/e2e-observation.test.ts` passed three cases covering
  same-origin control/Agent and foreign malformed inputs. Labels contain only
  fixed route families, an allowlisted method, and a bounded numeric status;
  secret-shaped URL data is absent.
- Historical run
  [34367041990](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34367041990),
  job `102518331881`, retained only the generic Firefox `browser-response`
  category at `auth.spec.ts:79`; no endpoint, status, trace, or browser artifact
  identifies the original cause. The cause is therefore explicitly unknown and
  not reproduced. Current local and remote desktop-Firefox runs pass, with no
  suppression, weaker assertion, skipped project, or retry-until-green policy.

## Local verification

- `uv run --frozen pytest services/backend/tests/integration/test_agent_mutations.py -k '065_theme_data_round_trip_preserves_legacy_state' -q`: PASSED; 1 test, `7.05s`.
- `pnpm exec vitest run tests/contracts/e2e-observation.test.ts`: PASSED; 3 tests.
- `pnpm lint`: PASSED.
- `pnpm exec prettier --check tests/e2e/preview.spec.ts`: PASSED.
- `pnpm typecheck`: PASSED across all contract, web, worker, and E2E projects.
- `npx --yes markdownlint-cli2 "**/*.md"`: PASSED; 0 issues in 457 files.
- `sh tools/compose/smoke.sh slaif007s1`: PASSED; actual Agent-to-preview
  DOM/computed-style proof and sensitivity control, browser projects including
  desktop Firefox, public acceptance/restart/replay, artifact/secret/edge/
  media/recovery checks, Apache validation, and 48 final smoke tests.
- The unchanged full local suites were not redundantly rerun after this
  evidence-only increment; the current-head remote matrix below ran them.

## GitHub required checks

All required checks are `SUCCESS` on implementation head
`4733071685eb11f5c1fc7d6732aeea5d1ab488c9`:

- CI run [34446574327](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34446574327):
  Compose/edge `102772622632`; Python 3.12 `102772623062`; Python 3.13
  `102772622868`; Python 3.14 `102772622843`; PostgreSQL 14 `102772623016`;
  PostgreSQL 15 `102772622980`; PostgreSQL 16 `102772622907`; PostgreSQL 17
  `102772622883`; PostgreSQL 18 `102772623036`; Node contracts `102772623008`;
  supply-chain `102772623077`; Repository policy `102772623055`; Markdown
  `102772623136`; Mermaid `102772622928`; Dependency review `102772623100`.
- CodeQL run [34446574263](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34446574263):
  Detect languages `102772551609`; Analyze actions `102772585595`; Analyze
  Python `102772585640`; Analyze JavaScript/TypeScript `102772585658`.
- The superseded f8ba CI run was cancelled when the concrete Node lint issue
  was corrected in `4733071`; the fresh current-head CI above passed every job.

## Documentation and scope confirmations

- `docs/API.md` now distinguishes `theme:read` from conditional
  `theme-tokens:write` and no longer calls the bounded theme token data plane
  an unimplemented site-global token feature.
- `README.md`, `docs/TESTING.md`, `oap/INCREMENTS.md`,
  `oap/MVP-PROGRESS.md`, `oap/MVP-CONTRACT-AUDIT.md`, and PR #79 describe
  078-s as bounded evidence closure pending strategic acceptance/merge.
- Historical 078-p/q/r orders, reports, and audits were not edited.
- No global regions, header/footer architecture, site-global expansion, page
  style/catalog, media/MCP, exact-workspace Puck, lifecycle/publication,
  dependency, security-exception, gate-weakening, or unrelated cleanup scope
  was added. No merge or auto-merge was performed.
- No real secret, capability, cookie, DB URL, preview credential, or private
  artifact URL was committed or emitted by the new diagnostics.

## Completion condition

078-s and the bounded 078/2 evidence increment are complete when strategic
authority independently accepts this report and merges PR #79 after verifying
the remote report-only head remains the SELF child of implementation head
`4733071685eb11f5c1fc7d6732aeea5d1ab488c9`. Numeric Objective 078 and the
contractual MVP remain `PARTIAL` until separately ordered global-region,
page-style/catalog, review, publication, and later-objective requirements are
accepted.
