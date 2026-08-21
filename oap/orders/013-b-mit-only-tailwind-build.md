# OAP Work Order — 013-b

## Objective and existing-PR state

Amend objective-013 PR #25 to retain the responsive admin shell while replacing
the Tailwind 4 build chain that installed MPL-2.0 `lightningcss` with an exact
architecture-allowed permissive Tailwind/PostCSS build path. Remove the
executor-added MPL policy exception and generated notice entries. This is a
license-boundary repair only; site workflows move to 013-c.

- Numeric objective: `013`; round: `013-b`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#25](https://github.com/ulfe-lmi/slaif-agent-site/pull/25)
- Base/head: `main` / `oap/013-responsive-admin`
- Required starting remote head:
  `8032489382a461903840d2e0cb3ce7ca2af0f7e5`
- 013-a implementation parent:
  `603aafb0aab0bd5e53eaf699757a6040ff0ee934`
- Verified state: open, ready/non-draft, mergeable, no reviews/threads; correct
  report-only topology; current-head CI 20/20 successful.

Fetch and verify the exact PR/head. Amend only PR #25; keep it ready and never
create a PR, merge, close, auto-merge, or workflow-rerun.

## Finding and authority boundary

013-a added `tailwindcss@4.3.3` plus `@tailwindcss/postcss@4.3.3`, which installs
`lightningcss@1.32.0` and its native artifact under MPL-2.0. The architecture's
normally allowed families are Apache-2.0, MIT, BSD-2/3-Clause, ISC, PostgreSQL,
and PSF. The coding agent cannot approve a new license family by editing
`supply-chain/policy.json`; no human architecture exception was granted.

Tailwind itself remains architecture-mandated. Use an official exact Tailwind
3.x release from npm with the standard PostCSS integration and only minimum
actually required MIT/allowed build dependencies (for example exact PostCSS and
Autoprefixer if needed). Verify the selected version is real, non-deprecated for
this bounded use, compatible with Node 24/Next 16/React 19, and self-hosted.

## Allowed scope

```text
apps/web/package.json
apps/web/postcss.config.mjs
apps/web/tailwind.config.*
apps/web/app/styles.css and admin class compatibility only
package.json only if an exact build/test command needs no semantic change
pnpm-lock.yaml
supply-chain/policy.json
THIRD_PARTY_NOTICES.md
docs/{ADMIN,TESTING}.md and README.md only for version/license correction
apps/web/tests/** and supply-chain/repository tests only for exact inventory
oap/active
oap/orders/013-b-mit-only-tailwind-build.md
oap/reports/013-b-mit-only-tailwind-build.md
```

No backend/API/migration/database/route, admin behavior/layout/content, Radix
Dialog removal, Web route, Compose/edge, Playwright, feature workflow,
unrelated dependency/version, or prior OAP artifact may change.

## Requirements

1. Remove Tailwind 4 and `@tailwindcss/postcss` completely. Install an exact
   official Tailwind 3.x package and minimum allowed-license PostCSS plugins.
   Regenerate the frozen lock from registry packages only; no VCS/path/editable/
   mutable source.
2. Convert the Tailwind CSS/config syntax deterministically (`content` globs,
   base/components/utilities or equivalent supported v3 directives) while
   preserving every admin/public/auth/routing visual class and strict CSP. No
   CDN, remote font/asset, inline style, unsafe-inline/eval, telemetry, or
   runtime compiler.
3. Keep `@radix-ui/react-dialog@1.1.23` and its MIT chain unchanged unless the
   lock resolver requires only metadata normalization. Do not add a component,
   icon, animation, form, state, or styling library.
4. Remove `lightningcss` and every native `lightningcss-*` artifact from the
   installed graph and lock. Prove `pnpm why lightningcss --recursive` finds no
   installed package and `pnpm licenses list --json` contains no MPL entry.
5. Remove only the 013-a MPL-2.0 allowance/package-specific review and
   Lightning CSS notice rows. Restore central policy to architecture-allowed
   families; preserve all unrelated historic policy/notice decisions.
6. Add repository/supply tests that fail if Tailwind 4,
   `@tailwindcss/postcss`, Lightning CSS, MPL allowance, remote CSS origin, or
   unfrozen UI package returns. Preserve exact admin shell behavior, accessible
   Dialog focus semantics, 320 px contract, storage/token absence, and source
   tests.

## Acceptance and verification

Acceptance requires an exact allowed-license installed graph, clean lock,
unchanged admin behavior/build output, strict CSP, and no product scope change.
Run:

```text
pnpm install --frozen-lockfile
pnpm lint
pnpm format:check
pnpm typecheck
pnpm test
pnpm build
pnpm licenses list --json
pnpm why lightningcss --recursive
python tools/check_repository.py
uv run --frozen python -m tools.supply_chain.policy validate
git diff --check
```

Also run focused repository/supply-chain tests, changed Markdown/order/report
lint, exact lock/integrity/license/remote-origin/telemetry/CSP scans. Do not run
local PostgreSQL, Compose, Playwright/browser, images, or broad SBOM; GitHub
runs established gates.

Target 25 minutes; hard stop 45 minutes. Fix diagnosed local build/config/lock
issues within scope. Push one coherent generation after local green; one
corrective generation only for a concrete clean-runner/build defect, never a
workflow rerun. Report `PARTIAL` at the hard stop. Access no production system,
credential, or data.

Preserve prior transcript bytes, commit this order and `oap/active`
byte-identically, and never merge. Atomically publish:

```text
oap/reports/013-b-mit-only-tailwind-build.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
selected exact packages/versions/integrities/licenses; removed MPL graph/policy/
notices; CSS/config equivalence; exact commands/results; current 20 checks;
diff/scope/hashes/skips; and explicit no-new-PR/no-rerun/no-merge. Signal FIFO
`OK` only after report and claimed remote state exist.
