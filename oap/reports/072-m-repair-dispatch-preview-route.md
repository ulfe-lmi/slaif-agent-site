# OAP Report — 072-m

- Order: `072-m-repair-dispatch-preview-route`
- Result: `PARTIAL`
- Delivery: `AMENDED_EXISTING_PR`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66) (OPEN)
- Base: `main` at `082f2359b0c4d59b692580d17992c35d46183b12`
- Branch: `oap/072-browser-worker-real-playwright`
- Starting remote SHA: `8ad0d59f22976fe088e311349839757b6b754d63`
- Implementation SHA: `e40fbbb379e8819feb81c3feb9a57102cf0de3e8`
- Report publication parent: `e40fbbb379e8819feb81c3feb9a57102cf0de3e8`

## Changes

The Compose durable-dispatch fixture now binds the Agent and direct-worker
requests to the authoritative seeded `/s/demo/` route and matching digest,
removing the guessed `/s/demo/home` suffix. Durable worker polling now stops
immediately on `FAILED`, `TIMED_OUT`, or `CANCELLED` and prints only the bounded
run ID, state, error code, and truncated safe message. A packaging regression
asserts the route and terminal-diagnostic contract (including the full Python
format gate). No product, migration,
grant, token, Render, worker-runtime, public-artifact, or exception changes
were made.

## Evidence

- `sh -n tools/compose/smoke.sh` — passed.
- `python -m unittest tests/packaging/test_compose_smoke_contract.py` — 7 passed.
- Focused `ruff`, `mypy`, dispatcher unit, and prior full backend/Node gates — passed.
- Clean Compose run `sudo sh tools/compose/smoke.sh slaif071m` completed its
  setup, governance, preview, and restart checks, then failed fast with:
  `agent-browser-dispatch: terminal run=af24c2f4-8bd3-47d9-8320-5d62fe45a297 state=FAILED code=BROWSER_NAVIGATION_HTTP_404 message=browser attempt failed`.
  It therefore did not prove real Chromium `COMPLETED`, artifacts, or the
  two-run isolation assertions. The remaining 404 is an executable product/
  projection defect outside this test-only repair; no route-policy weakening
  was applied.

The 31-entry temporary browser exception and issue #67 remain unchanged and
valid through `2026-09-04`. Objective 072 remains `PARTIAL` pending the actual
preview route/projection repair and public artifact retrieval.

## CI and safety

Fresh checks for the implementation/report head are recorded by GitHub; all
standard analysis, Python, Node, Foundation PostgreSQL, Markdown, Mermaid,
repository policy, dependency, supply-chain, and CodeQL checks pass except
`Compose and edge packaging`, which fails on the same dispatcher HTTP 404.
No check was treated as pass. No extra PR, merge, auto-merge, release,
production access, credential/capability/cookie exposure, or artifact-byte
publication occurred.

Report publication commit: SELF
