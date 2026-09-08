# OAP Work Order — 077-w

## Objective and frozen PR state

Amend only [PR #74](https://github.com/ulfe-lmi/slaif-agent-site/pull/74),
branch `oap/077-agent-site-structure-semantics`, base `main`; create no PR and
never merge. Required starting remote report head is
`b336ca9dbf1c39ed7fb17f4845743f3bb5f2f8df`, whose sole parent is 077-v
implementation `217641d6cf546f4ec1175bad7dd93e6b02189a95`. Remote `main`
remains `067676314e0d9664d40cb8514ea549b966a4eb2d`.

PR #74 is feature-frozen. Repair only the remaining renderer CSS/locale defect
identified by strategic review of 077-v. Do not add product behavior or another
feature. After this round strategy will perform the final hostile Objective-077
audit and order truth-document reconciliation.

## Defect

077-v makes canonical and preview reference `/renderer-v1.css`, but it does not
make their effective renderer CSS identical:

- canonical output also inherits `app/styles.css` generic rules for `*`, `h1`,
  `article`, `article h2`, `article p:last-child`, `nav`, `a` and other elements;
- manual preview output does not load that application bundle; and
- current parity evidence compares only one `.renderer-heading` color/line
  height, so it cannot detect the visibly different collection list/detail
  cards, page title and element box model.

The root layout also remains hard-coded to `<html lang="en">`. Preview now has
the selected locale, but canonical non-default-locale site content still lacks
an exact content-language marker.

## Required repair

Make the trusted site-renderer surface self-contained and deterministic so the
same projection/component tree has the same effective CSS in canonical and
active preview contexts.

- Scope the versioned renderer CSS and/or the surrounding renderer markup so
  unrelated generic admin/application rules cannot change renderer page title,
  collection list/grid/detail articles, headings, summaries, box sizing,
  spacing, layout or responsive behavior in canonical only.
- Avoid loading site-renderer styling globally on unrelated admin/auth/setup
  pages if it can be confined to actual site/preview render responses.
- Do not create a second component implementation, second divergent stylesheet,
  new theme/design system, or 078 composition/design behavior. This is parity
  and scoping of the existing trusted renderer only.
- Preserve UUID/credential/Flight-free preview HTML, CSP without unsafe-inline,
  private/no-store/noindex preview headers, stylesheet allowlisting, dynamic
  locale/detail behavior and all 077-v browser evidence.
- Mark canonical rendered content with the exact selected locale using valid
  HTML language semantics. If the Next root document cannot safely vary its
  `<html lang>` without reintroducing private state, put `lang` on the complete
  trusted rendered-content root so assistive technology receives the exact
  locale. Preview must retain its exact document language.

## Executable acceptance

Use actual clean Compose/NGINX/Web browser output with equivalent canonical and
workspace-preview fixtures. Compare more than one cherry-picked property:

- page-title (`h1`) class/box/font/margin/line-height;
- CollectionList/Grid article box model, border, background, padding and its
  `h2`/summary typography/margins;
- CollectionDetail box and text;
- representative layout component behavior; and
- the mobile breakpoint/result.

The canonical and preview values/classes must match for equivalent trusted
renderer nodes. Prove the stylesheet loads through the browser's confined
asset policy, neither response body exposes internal UUID/credential/Flight
state, unrelated admin/auth pages retain their prior application styling, and
canonical plus preview localized content carry the expected `sl-SI` language
semantics. Source regex or merely observing one shared URL is not sufficient.

Run focused Web/Playwright/browser-worker/Compose parity and privacy tests,
then all current Node and repository checks plus the relevant backend/browser
regressions. Run the complete clean Compose acceptance and all six-image zero-
Critical supply-chain gate if any packaged Web/browser artifact changes, then
observe every current-head GitHub check. Pending/skipped/superseded is not pass.

Do not change dynamic data semantics, SQL/migrations/OpenAPI/routes, browser
retention/auth, dependencies/images/exceptions/architecture, historical orders/
reports, MVP truth ledgers, or any 078+ feature area. Preserve Chrome
`152.0.7977.82`, empty vulnerability exceptions and open issue #67.

Commit this exact order and `oap/active` unchanged, amend only PR #74, create no
PR and never merge. Publish exactly
`oap/reports/077-w-repair-render-css-locale-parity.md` as a report-only child
of the literal implementation SHA with `Report publication commit: SELF`.
Report the exact CSS scoping/locale correction, executable canonical-versus-
preview desktop/mobile computed evidence, privacy/CSP/admin non-regression,
commands/counts/skips/current checks, scope/no-secret/no-extra-PR/no-merge, and
the strongest remaining reason not to accept Objective 077.

Do not return early for ordinary implementation/test/CI failure or task size.
`PARTIAL`/`BLOCKED` requires a concrete external outage or unresolved product/
architecture decision. No post-report push; signal exact FIFO `OK`, then wait.
