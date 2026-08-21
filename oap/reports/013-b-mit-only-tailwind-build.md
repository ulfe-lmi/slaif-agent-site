# OAP Coding-Agent Report — 013-b

## Work order

- Identifier: `013-b`
- Work-order file: `oap/orders/013-b-mit-only-tailwind-build.md`
- Numeric objective: `013`
- PR mode: `AMEND_EXISTING_PR`
- Delivery mode: `AMENDED_EXISTING_PR`

## Status

`COMPLETE`

## Executive summary

Amended only objective-013 PR #25. Replaced Tailwind 4 and its MPL-2.0
Lightning CSS build chain with exact MIT-licensed Tailwind CSS 3.4.19,
PostCSS 8.5.26, and Autoprefixer 10.5.4. Converted the stylesheet to supported
Tailwind 3 directives and added deterministic content globs while preserving
the responsive administration shell and Radix Dialog behavior.

The installed and locked package artifact graph contains no Lightning CSS or
native Lightning CSS package. `pnpm why lightningcss --recursive` returned no
package, the complete installed Node license inventory contains no MPL family,
and generated notices contain no Lightning CSS row. The 013-a package-specific
Lightning reviews and inline Node MPL allowance were removed; the central
policy is byte-equivalent to its pre-013 value.

All local gates passed. The literal implementation head passed all 20 GitHub
CI/CodeQL checks, including Node, PostgreSQL 14–18, clean Compose/browser, and
supply-chain evidence. No corrective generation or workflow rerun was needed.

## Authoritative GitHub state

- Repository: `ulfe-lmi/slaif-agent-site`
- PR: `#25` — `https://github.com/ulfe-lmi/slaif-agent-site/pull/25`
- State: `OPEN`, non-draft, `MERGEABLE`, merge-state `CLEAN`
- Base/head: `main` / `oap/013-responsive-admin`
- Starting remote head:
  `8032489382a461903840d2e0cb3ce7ca2af0f7e5`
- Implementation head SHA:
  `1ecf4d402b232bba64709ba63bd95c8300b93eb5`
- Report publication commit: `SELF`
- Implementation commit pushed:
  - `1ecf4d402b232bba64709ba63bd95c8300b93eb5` — `Replace Tailwind build
    with MIT-only chain`
- Report commit first parent: same as Implementation head SHA
- New PR created: `NO`
- Additional objective PR: none
- Auto-merge request: none
- Merge/close/acceptance performed: `NO`

## Exact package and build inventory

| Package | Version | License | Registry integrity |
| --- | --- | --- | --- |
| `tailwindcss` | `3.4.19` | MIT | `sha512-3ofp+LL8E+pK/JuPLPggVAIaEuhvIz4qNcf3nA1Xn2o/7fb7s/TYpHhwGDv1ZU3PkBluUVaF8PyCHcm48cKLWQ==` |
| `postcss` | `8.5.26` | MIT | `sha512-u82N74LFzG8ca+dD8puPnplTXoGH4fTPpVGuIbt36G3qvNlkvfD0lEAZSxaly3KX8TS/L1A1gsCEmvKmBcVbkQ==` |
| `autoprefixer` | `10.5.4` | MIT | `sha512-MaU0U/za7N3r6brxD4YB/l4NSrFzLPlANv6wEuQVaIPlD3L4W9rFcQPbL/EilY9BHhHvhfcz3gInDLrEtWT4EA==` |
| `@radix-ui/react-dialog` | `1.1.23` | MIT | unchanged exact runtime dependency |

Registry metadata reported no deprecation. Tailwind requires Node 14 or later;
PostCSS and Autoprefixer accept Node 14 or later, so Node 24 is supported.
Autoprefixer's peer range accepts PostCSS 8.5.26.

- `pnpm-lock.yaml` SHA-256:
  `9bef21513c7ae42890c39b4adf2d1a3b7c6d8ef83730d1053b0117b5e1f2edd5`
- `apps/web/package.json` SHA-256:
  `1490e92aedddc5f2a050ca440668f7950e39b695a5b58aaa0fcbb002be2084de`
- PostCSS config SHA-256:
  `e32657baf631d7c5f4dc67b4b2ee0ec8e7d5b3c41860e09cddce7c0377cd80bc`
- Tailwind config SHA-256:
  `85eea616baafcf77bbccba9e3a4f4c49bd588fddbc622bcfd8448254651ee917`
- Restored central policy SHA-256:
  `41ccc91482ba8dff4a7fbb4a2d06c5917796878cee646bcc4cbd15e2fd347c97`

The lock still records Vite's upstream optional peer name `lightningcss`, as it
did before objective 013. It contains no `lightningcss@...` package artifact,
integrity, native package, installed dependency, or resolved package. This is
metadata only and is not an installed or licensed graph member.

## Changes and equivalence evidence

- Removed `tailwindcss@4.3.3` and `@tailwindcss/postcss@4.3.3`.
- Added exact Tailwind 3.4.19 and Autoprefixer 10.5.4; retained exact PostCSS
  8.5.26.
- Replaced `@import "tailwindcss"` with Tailwind 3 base, components, and
  utilities directives.
- Added `tailwind.config.mjs` with only bounded `app` and `src` JS/TS/JSX/TSX/
  MDX content globs, empty plugins, and no runtime compiler.
- Configured PostCSS with only `tailwindcss` and `autoprefixer`.
- Preserved all authored admin/public/auth CSS rules, responsive breakpoints,
  320 px behavior, focus rules, reduced motion, CSP constraints, and Radix
  Dialog source.
- Added web and repository regression assertions rejecting Tailwind 4,
  `@tailwindcss/postcss`, Lightning artifacts, remote CSS origins, and manifest
  drift.
- Regenerated third-party notices from the exact graph. Only the obsolete
  Tailwind 4/Lightning closure was removed and the Tailwind 3 MIT closure was
  added; unrelated Python MPL review rows remain unchanged.
- Restored the executor-added inline CI MPL allowance. The remaining workflow
  diff against main is only the 013-a PostgreSQL integration test addition.
- Updated only admin/testing documentation for exact versions and license
  correction. No behavior or layout content changed.
- Committed `oap/active` and the activated order byte-identically.

## Local verification

Passed:

```text
pnpm install --frozen-lockfile
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
  web 7/7; browser worker 1/1; contracts 2/2
pnpm build
  two successful Web/Next production builds plus all packages
pnpm licenses list --json
  0BSD, Apache-2.0, BSD-2-Clause, BSD-3-Clause, BlueOak-1.0.0,
  CC-BY-4.0, ISC, MIT; no MPL
pnpm why lightningcss --recursive
  no output; no installed package
python -m unittest discover -s tests/repository -p 'test_*.py'
  53 passed
python tools/check_repository.py
  PASS repository policy
uv run --frozen python -m tools.supply_chain.policy validate
  supply-chain-policy: OK
npx --yes markdownlint-cli2@0.23.2 --no-globs <changed docs/order>
  0 issues
git diff --check
exact package/artifact/integrity/license/remote-origin/telemetry/CSP scans
```

Local PostgreSQL, Compose, Playwright/browser, images, and broad SBOM were not
run, exactly as prohibited/deferred by the order. GitHub supplied the
authoritative Compose/browser and supply-chain evidence. No skipped or pending
test is claimed as passing.

## GitHub current-head checks

All 20 checks on `1ecf4d402b232bba64709ba63bd95c8300b93eb5`
completed successfully:

1. Repository policy
2. Detect supported languages
3. Node contracts
4. Analyze (actions)
5. Analyze (python)
6. Analyze (javascript-typescript)
7. Python 3.12 quality and package
8. Python 3.13 quality and package
9. Python 3.14 quality and package
10. Foundation PostgreSQL 14
11. Foundation PostgreSQL 15
12. Foundation PostgreSQL 16
13. Foundation PostgreSQL 17
14. Foundation PostgreSQL 18
15. Compose and edge packaging
16. Supply-chain evidence
17. Markdown
18. Mermaid
19. Dependency review
20. CodeQL

Compose/edge passed in 6m42s and supply-chain evidence in 6m31s. No workflow
was manually rerun.

## Scope, transcript, and safety confirmations

- No backend, API, migration, database, route, admin behavior/layout/content,
  Radix removal, web route, Compose topology, browser test, product workflow,
  or unrelated dependency/version changed.
- Final 013-b implementation paths are the exact Tailwind/config/lock/notices,
  tests/policy, docs, and strategic artifacts required for this repair. The CI
  change only removes the 013-a MPL allowance and restores the prior boundary.
- No production system/data/credential, Docker socket, or protected secret was
  accessed. No secret was printed or committed.
- `oap/active` SHA-256:
  `c87195dd502e7f9b2ef61845cc532fa7e4e989a05007f714e2a43ed647f889df`
- Activated-order SHA-256:
  `08756c1837f91a19be234b960a35306891ae3a4d33aca9aae5878b3134de35d3`
- Prior orders/reports and governing files were not edited.
- No new PR, workflow rerun, corrective generation, merge, auto-merge, close,
  acceptance, issue, release, or tag was performed.

## Limitations and blockers

None for 013-b. `COMPLETE` means delivered for strategic review, not accepted
or merged.
