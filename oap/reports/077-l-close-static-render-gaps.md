# OAP implementation report — 077-l

## Publication and identity

- Order: `077-l`, `oap/orders/077-l-close-static-render-gaps.md`
- Order SHA-256: `1f7c5d51c1dfa46192da6716d6903c063ab681cd485b57031d15cf37eb75a2ac`
- Active bytes: `077-l` followed by LF; active SHA-256:
  `79711c767719bc0d6917ed8ab3840bd96b7d041b6b6f09ecea8f16819e2501c0`
- Delivery: `AMENDED_EXISTING_PR`
- Result: `BLOCKED`
- Repository: `/home/ubuntu/codex-work/slaif-agent-site`
- PR: [#74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74), open,
  non-draft, base `main`, branch `oap/077-agent-site-structure-semantics`
- Required starting remote report head:
  `a24d9367b7668734605dab01c7310a4307d00e98`
- Literal final implementation SHA:
  `92706355de37b38d6eda10ed8c0447415ca234b8`
Report publication commit: SELF

The strategy-owned `oap/active` and `077-l` order were read in full and were
committed unchanged. No second PR was created and no merge or auto-merge was
performed.

## Ordered changes delivered

The Render navigation projection now validates the complete stored tree and
target graph before applying selected-locale visibility, while resolving item
labels only for items actually projected. Hidden parents suppress their visible
children as a subtree; locale-hidden items cannot break another locale or float
into its output. A real PostgreSQL regression covers English-only and
Slovenian-only labels plus a selected-locale child under a hidden parent.

The public Web proxy now preserves all five allowed human canonical/preview
redirect statuses (301, 302, 303, 307, 308) with exact validated Location
values. Preview safety headers are supplied by the existing public NGINX edge
policy without duplicate Web headers. Internal preview targets retain
`/preview/<workspace-id>` and the trusted site prefix; external HTTPS targets
remain external. Browser-preview requests continue to bypass proxy preflight so
the one-time browser credential is consumed exactly once.

The Compose public preview fixture and Playwright boundary test now table-drive
all five internal statuses plus an external target for both canonical and
authorized human preview requests, with redirect following disabled and exact
preview safety-header assertions. A pin-scoped Web contract test covers the
Next browser fallback statuses still used by the browser path.

The production-boundary evidence was extended through existing Agent HTTP
operations to cover page move, canonical isolation, explicit-locale moved-route
projection, foreign-workspace denial, and fail-closed navigation corruption.
Existing current tests cover browser one-time authorization, repeatable-read
barriers/cancellation, restart/authorization isolation, and PostgreSQL role
privileges. No migration, resolver grant, Agent route, or architecture policy
was broadened.

## Verification evidence

Local verification passed:

- Full integration suite: 166 passed in 1289.96 seconds.
- Focused structure-router suite: 3 passed; browser-preview suite: 1 passed;
  Render projection barrier suite: 2 passed; cross-interface structural race:
  1 passed.
- Python unit/repository/packaging/supply-chain suites: 603 passed, 1 warning,
  80 subtests; mypy passed; Ruff check/format passed.
- Repository policy passed; Mermaid passed for 16 diagrams; Markdownlint passed
  with zero issues.
- Frozen Node gates passed with Node 24.14.1 and pnpm 11.22.0: install, lint,
  format check, typecheck, contract tests, build, and approved license
  inventory. The Web surface suite passed 10 tests.
- Compose browser evidence reached compose-e2e: OK; the preview contract
  recorded all five statuses and the external target successfully before the
  later public-Agent acceptance failure.

Current public boundary logs prove:

~~~text
browser-e2e: ... stage=preview-redirect-external-301-other
compose-e2e: OK projects=11 setup=1 governance=1 preview=1 stable-devices=6 agent-sessions=2 artifacts=disabled
~~~

## Concrete blocker

The remaining current-head failure is outside the ordered Render/Web scope and
is repeated on the current branch after the ordered diagnostics:

~~~text
public-agent-acceptance: FAILED
reason=oap-navigation-internal-page-delete-<random>-status-404-code-RESOURCE_NOT_FOUND
~~~

Immediately before the production Agent DELETE, the same capability reads the
internal page successfully with status=200 and row_version=1. Owner-side
diagnostics show zero redirect rows targeting that page route and zero
navigation rows with that page as page_id. The existing Agent DELETE still
returns 404/RESOURCE_NOT_FOUND. The order forbids broadening or reimplementing
Agent mutation semantics; changing the acceptance assertion to ignore this
failure would weaken the required production evidence. The same failure has
recurred across current-head Compose runs 34002954783,
34003204105, and 34002595211/successor retries.

The current CI workflow-dispatch run is
[34003204105](https://github.com/ulfe-lmi/slaif-agent-site/actions/runs/34003204105);
its Compose job is failed while the PostgreSQL and supply-chain jobs were still
pending at report preparation. Earlier current-head runs also passed the
redirect/browser portion and failed at this same public-Agent cleanup boundary.
Therefore COMPLETE is not claimed.

## Scope and handoff

No dynamic {slug} matching, collection-detail selection, new Agent route,
dependency, image, migration, privilege broadening, media/MCP, freeze/review/
promotion, production access, release, extra PR, merge, or secret exposure
occurred. Chrome 152.0.7977.82 and the existing exception/Critical findings
boundaries were preserved. GitHub issue #67 remains open.

The strongest reason not to accept this round is the unresolved production
Agent page-delete 404 described above. Strategy must either issue a narrowly
scoped continuation authorizing the Agent-side repair or otherwise resolve that
external repository failure before 077-l can be complete. The coding agent did
not alter Agent mutation semantics or weaken the acceptance proof.
