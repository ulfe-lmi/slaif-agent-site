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

Tailwind CSS 4.3.3 is compiled locally through the exact PostCSS integration.
The small shadcn-style component layer is repository-owned source. Radix
Dropdown Menu 2.1.24 is the only direct Radix primitive. These MIT dependencies
are registry-locked for Node 24, React 19, and Next 16. The UI uses the local
logo, system fonts, no remote origin or telemetry, and no browser-persisted
token, permission, or selected-site state.

Site and membership mutations remain API-only until 013-b/c. User creation,
invitations, custom roles, content/models/pages, Puck, workspaces/capabilities,
review, audit workflows, and publication execution are not implemented.
