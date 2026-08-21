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

Objective 013-a deliberately does not run local Compose or Playwright. Those browser and
public-edge checks are reserved for objective 013-d; GitHub's existing packaging check
remains the clean-stack evidence for this round.
