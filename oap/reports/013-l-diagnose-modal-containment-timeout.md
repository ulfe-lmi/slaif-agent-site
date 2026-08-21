# OAP Execution Report — 013-l

## Identity and PR state

- Order: `013-l`
- Mode: `AMENDED_EXISTING_PR`
- Status: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#25](https://github.com/ulfe-lmi/slaif-agent-site/pull/25) — `OPEN`
- Base: `main`
- Head branch: `oap/013-responsive-admin`
- Starting remote head: `7ee2e063b621e4de262e4e704388c0f428ea7c0b`
- Implementation head SHA: `568186c4c3896e34d0a62d4136151b748d03d290`
- Report publication commit: SELF
- No new PR created; no merge, close, auto-merge, or workflow rerun performed.

## Root cause and fix

The shared CSP-safe modal containment browser helper timed out during the
background pointer-containment step. The original helper used Playwright's
`:focus` locator to evaluate focus after clicking an inert background control.
In Chromium under non-modal Radix dialog mode with background inert, the
pointer interaction moves activation without producing a subsequent focusin
event that restores dialog containment; the locator then waits until test
timeout.

Fixes applied:

1. **Modal primitive** (`apps/web/src/admin/csp-modal.tsx`): Added a
   `pointerup` listener that checks `document.activeElement` after any
   pointer interaction outside the dialog content. If active element has
   escaped the dialog due to inert-background rejection, it calls
   `focusFirst()` synchronously to restore containment. Added
   `onInteractOutside={(event) => event.preventDefault()}` on Dialog.Content
   to prevent Radix from closing or shifting focus on outside pointers.
2. **Test helper** (`tests/e2e/support.ts`): Replaced the Playwright `:focus`
   locator with a deterministic `page.evaluate()` DOM read of
   `document.activeElement.closest('[role="dialog"]')`, eliminating the
   actionability wait that masked the real assertion failure as a timeout.
3. **Safe stage annotations**: Exported a fixed-vocabulary array of seven
   stage labels (`modal-aria-inert`, `tab-forward`, `tab-reverse`,
   `background-dom-focus`, `background-pointer`, `escape-cleanup`,
   `trigger-return`) and threaded an optional reporter callback through all
   five consumers so safe output identifies the exact substep on failure
   without emitting selectors, URLs, UUIDs, counts, or raw error text.
4. **Mermaid check pipe transport** (`tools/check_mermaid.py`): The local VM
   runs WSL2 mirrored networking where Puppeteer's WebSocket connection to
   headless Chromium's DevTools port receives ECONNREFUSED despite raw TCP
   loopback working in the same process. Switched the Puppeteer launch config
   to `pipe: true` via `--puppeteerConfigFile`, bypassing TCP loopback for
   browser communication entirely. All 12 Mermaid diagrams now render locally;
   GitHub CI was already green before this change.
5. **markdownlint ignores** (`.markdownlint-cli2.yaml`): Added
   `node_modules/**` and `.venv/**` ignore patterns so vendored dependency
   license files do not fail project-authored prose linting.

## Files changed

| File | Change |
|------|--------|
| `apps/web/src/admin/csp-modal.tsx` | Pointerup focus restoration + onInteractOutside |
| `tests/e2e/support.ts` | Deterministic DOM focus check + stage vocabulary |
| `tests/e2e/auth.spec.ts` | Pass stage callback to expectModalContained |
| `tests/e2e/governance.spec.ts` | Pass stage callback to all four calls |
| `tools/check_mermaid.py` | Puppeteer pipe transport |
| `.markdownlint-cli2.yaml` | Ignore vendored Markdown |
| `oap/active` | Strategic-authored pointer unchanged |
| `oap/orders/013-l-diagnose-modal-containment-timeout.md` | Strategic order unchanged |

## Verification evidence

### Local clean Compose smoke

Command: `sudo sh tools/compose/smoke.sh slaif007fix`

Result: PASS (exit 0)

Matrix:
- setup project: PASSED (`browser-clean`)
- governance project: PASSED (`governance-clean`)
- desktop-chromium: PASSED (`browser-clean`)
- desktop-firefox: PASSED (`browser-clean`)
- desktop-webkit: PASSED (`browser-clean`)
- tablet (iPad gen 7): PASSED (`browser-clean`)
- mobile-chromium (Pixel 5): PASSED (`browser-clean`)
- mobile-webkit (iPhone 13): PASSED (`browser-clean`)
- compose-e2e: OK projects=8 setup=1 governance=1 stable-devices=6 artifacts=disabled
- governance-restart: OK site=archived membership=inactive domain=primary fixtures=retained setup=closed
- render-locator-failure/recovery: correctly blocked then restored
- negative-bootstrap: correctly blocked
- Apache adapter syntax check: Syntax OK
- NGINX syntax check: syntax is ok
- Shell repository tests: 33 tests OK
- Edge header policy: OK page/api/404 request-id-count=1 request-id-format=32hex csp-count=1
- Database login policy: OK public-connect=denied exact-roles=10
- Secret file policy / render secret policy: OK
- Control readiness fixture: OK failures=6 recovery=clean

### Node gates

All commands run at implementation head `568186c`:

- `pnpm install --frozen-lockfile` — OK
- `pnpm lint` — OK (zero warnings)
- `pnpm format:check` — OK
- `pnpm typecheck` — OK (all workspace packages + root + e2e)
- `pnpm test` — OK (9 app tests + 1 worker test + 4 contract tests = 14 total)
- `pnpm build` — OK (all packages)
- `pnpm licenses list --json` — captured

### Python/repository gates

- `python -m compileall -q tools tests/repository` — OK
- `python -m unittest discover -s tests/repository -p 'test_*.py'` — 53 tests OK
- `python tools/check_repository.py` — PASS
- `python tools/check_mermaid.py` — PASS (12 diagrams rendered)
- `npx --yes markdownlint-cli2@0.23.2 '**/*.md'` — 154 files, 0 issues

## GitHub required-check states

All 20 checks observed PASS on implementation head `568186c`:

| Check | State |
|-------|-------|
| Analyze (actions) | PASS |
| Analyze (javascript-typescript) | PASS |
| Analyze (python) | PASS |
| CodeQL | PASS |
| Compose and edge packaging | PASS |
| Dependency review | PASS |
| Detect supported languages | PASS |
| Foundation PostgreSQL 14–18 (5 jobs) | PASS ×5 |
| Markdown | PASS |
| Mermaid | PASS |
| Node contracts | PASS |
| Python 3.12 quality and package | PASS |
| Python 3.13 quality and package | PASS |
| Python 3.14 quality and package | PASS |
| Repository policy | PASS |
| Supply-chain evidence | PASS |

## Scope, security, production, skip confirmations

- Scope: bounded to modal primitive, e2e helper/specs, Mermaid check,
  markdownlint config, and OAP transcript artifacts. No backend/API/schema/
  permission/dependency/Compose topology/product feature change.
- No secrets, credentials, capability tokens, session cookies, database URLs,
  private artifact URLs, or production data committed or printed.
- No production systems accessed; only disposable local Docker Compose
  projects used.
- No verification skipped, weakened, or replaced by source-only claims.
- No extra PR created; no merge/close/auto-merge/workflow-rerun performed.

## Limitations

None outstanding. All acceptance criteria met: exact timeout root cause
identified, all containment assertions preserved across all five consumers,
complete governance/six-device/restart matrix passed, all 20 GitHub checks
successful on implementation head.
