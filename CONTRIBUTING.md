# Contributing to SLAIF Agent-Site

SLAIF Agent-Site is currently a pre-alpha foundation-baseline project. The
repository contains architecture, governance, documentation, reproducible
Python packaging, and foundation qualification automation; there is no
application setup or runnable product stack yet.

## Start with the governing documents

Before changing the repository, read:

1. [AGENTS.md](AGENTS.md) for coding/execution rules;
2. [ARCHITECTURE.md](ARCHITECTURE.md) for the normative product architecture;
3. [SECURITY.md](SECURITY.md) for private vulnerability reporting; and
4. any narrower instructions or active OAP work order that applies.

Architecture and security boundaries take precedence over convenient
implementation shortcuts. Do not silently change the normative architecture,
trust model, technology choices, or readiness claims.

## Development workflow

1. Use an issue or explicitly authorized work order to establish scope.
2. Create a focused feature branch from current remote `main`; do not commit
   directly to `main`.
3. Inspect existing remote and local state before editing.
4. Keep the diff bounded to the stated objective and preserve unrelated work.
5. Add proportionate tests and documentation with behavior or contract
   changes.
6. Run the relevant local checks and report exact pass, fail, skipped, pending,
   or not-run outcomes.
7. Open a pull request using the repository template. Never merge your own OAP
   pull request when acting as the coding agent.

Do not claim planned APIs, UI, Compose behavior, isolation guarantees, browser
support, or product tests as implemented until executable evidence exists.

## Current preparation checks

Run from the repository root:

```bash
uv --version
uv lock --check
uv sync --frozen --all-groups
uv run --frozen ruff check services/backend tests/repository tools
uv run --frozen ruff format --check services/backend tests/repository tools
uv run --frozen mypy
uv run --frozen pytest services/backend/tests/unit tests/repository
uv run --frozen pytest services/backend/tests/integration
uv build --out-dir /tmp/slaif-agent-site-distributions
python -m compileall -q tools tests/repository
python -m unittest discover -s tests/repository -p 'test_*.py'
python tools/check_repository.py
python tools/check_mermaid.py
npx --yes markdownlint-cli2@0.23.2 "**/*.md"
```

The Mermaid check transiently obtains the exact approved Mermaid CLI version
and renders every Mermaid fence in a system temporary directory. It adds no
production dependency and commits no rendered output.

GitHub CI and CodeQL on the current PR head are independently authoritative.
The PostgreSQL integration command requires a disposable PostgreSQL 14–18
instance and fake test credentials as described in
[the foundation integration record](docs/FOUNDATION_INTEGRATION.md). GitHub CI
runs every supported PostgreSQL version. Future product work extends these
baseline checks with application,
database-role, concurrency, browser-network, Playwright, Compose, recovery,
license, and SBOM coverage; it does not replace them.

## Security, privacy, and production boundaries

- Never commit or paste real secrets, tokens, cookies, database URLs, private
  keys, personal data, unpublished private artifacts, or environment files.
- Do not access production systems or production data for ordinary development
  or tests.
- Use local fixtures and disposable services at defined boundaries.
- Preserve human-only publication, server-owned site/workspace/operation
  context, least-privilege roles, browser confinement, immutable media, and
  fail-safe promotion semantics.
- Report suspected vulnerabilities through the private process in
  [SECURITY.md](SECURITY.md), not in a public issue.

## Dependencies and licenses

Use `uv 0.12.5` and commit the lock produced for the declared Python
3.12–3.14 range. A clean environment must install with
`uv sync --frozen --all-groups`; normal tests and builds must not resolve from
an unlocked source. New production dependencies require explicit scope,
rationale, lockfile changes, license review, and tests. The project accepts
permissive dependencies under its architecture policy and does not add
required hosted or account-bound services. The integrated
`agent-cow-postgresql` dependency must come from PyPI at the qualified exact
version with hashes in `uv.lock`; Git, direct-URL, local-path, or editable forms
are forbidden for normal builds.

## OAP transcript ownership

The strategic model authors immutable files in `oap/orders/` and the
`oap/active` pointer. The coding agent submits those exact bytes but does not
edit them. The coding agent atomically authors reports in `oap/reports/` and
publishes each round in a final report-only `SELF` commit. Earlier orders and
reports are append-only history.

## Pull-request evidence

Keep evidence concrete: list commands, versions where relevant, exact outcomes,
GitHub check states, documentation impact, dependencies/licenses, and any
limitations. A skipped, missing, pending, cancelled, or failed check is never a
pass. If the application test suite does not yet exist, say `NOT RUN — not
present`; do not turn documentation validation into a product-test claim.
