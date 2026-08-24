# Testing

## Administration read model and shell

Backend tests cover the current-human site and authority read functions against a
disposable PostgreSQL database, including Platform Administrator behavior, ordinary
memberships, archived and disabled records, deterministic ordering, cross-site denial,
and exact grants. Unit and repository tests keep the HTTP route-policy inventory and
migration/privilege manifests exact.

The web source-contract tests exercise the same-origin, no-store read requests, response
validation, session redirect, canonical URL selection, loading/empty/ error/archived
copy, keyboard-managed Radix site switcher, responsive 320 px layout rules, and the
absence of browser storage, remote origins, or telemetry. The normal Node gate also runs
lint, formatting, type checking, package tests, the production build, and license
inventory.

Repository and supply-chain gates pin the administration build to Tailwind CSS 3.4.19,
PostCSS 8.5.26, and Autoprefixer 10.5.4. They reject Tailwind 4, `@tailwindcss/postcss`,
Lightning CSS, remote CSS origins, and unfrozen UI packages. The Node license inventory
must contain no MPL license family.

The clean Compose browser sequence is deliberately ordered: `setup` initializes
once, Chromium `governance` performs the only UI mutations, and the six stable
desktop/tablet/mobile projects depend on governance and remain read-only. The
governance project creates and archives a site, changes profile/domains, manages
an existing-user membership, exercises optimistic conflict recovery and crafted
server denials, and checks CSP/privacy through NGINX. Each stable project proves
dashboard, switcher, site overview/settings/membership reads, keyboard dialog
behavior, 44 px critical targets, 320 px overflow safety where applicable,
reduced motion, and logout. Stop/start fingerprints then verify site, domain,
membership, fixture, setup, and secret persistence. These automated checks are
bounded executable evidence, not an accessibility or security certification.

The governance Puck scenario creates an empty page through the Editor API only,
then adds two trusted Sections and performs a visible drag/reorder in the Puck
canvas. It saves through the visible button, reloads the composition, and
verifies the normalized server records, workspace overlay, HUMAN audit, and
idempotency evidence. The final editor response must carry only the documented
style-only CSP exception; scripts remain nonce-bound and the observer fails on
any CSP console violation, unexpected console/page/network failure, or server
error. Public and unrelated admin policies remain strict.
