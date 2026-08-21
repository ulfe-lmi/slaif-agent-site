# Read-only administration foundation

The authenticated `/admin` dashboard is a responsive, read-only administration
shell. It loads the current session and server-filtered current-human site list.
`/admin/sites/{site_id}` uses the URL UUID only as a lookup key and renders facts
returned by the authority endpoint; it never derives authority from the URL,
browser storage, a client role, or a hidden control.

Platform Administrators see every site, including archived sites, with an
explicit global fact and no fabricated membership. Ordinary users see only
active sites with an active membership. Direct unknown, archived-for-member,
inactive, disabled, or cross-site access returns the same bounded state.

The shell has a skip link, landmarks, one page heading, visible focus, touch
targets, reduced-motion behavior, a keyboard/Escape/focus-return Radix menu,
and a single-column layout below 760 px without 320 px overflow. Loading,
no-sites, denied/not-found, expired session, service, and network failure have
stable non-leaking states. Missing sessions redirect to `/login`.

Tailwind CSS 3.4.19 is compiled locally through PostCSS 8.5.26 and Autoprefixer
10.5.4. The small shadcn-style component layer is repository-owned source.
Radix Dialog 1.1.23 is the only direct Radix primitive. This build and runtime
chain is exact, registry-locked, MIT-licensed, and compatible with Node 24,
React 19, and Next 16. It contains no Lightning CSS or MPL-licensed npm package.
The UI uses the local logo, system fonts, no remote origin or telemetry, and no
browser-persisted token, permission, or selected-site state.

Site and membership mutations remain API-only until 013-b/c. User creation,
invitations, custom roles, content/models/pages, Puck, workspaces/capabilities,
review, audit workflows, and publication execution are not implemented.
