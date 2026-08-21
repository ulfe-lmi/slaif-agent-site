# Responsive site administration

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

Platform Administrators can create sites at `/admin/sites/new`. Returned
`site-policy:manage` and `site-domain:manage` permissions control Site Owner
profile/locale and domain create/replace/remove controls. Domain mappings do
not automate DNS. Archive is Platform-Administrator-only, names the site,
explains that no rows are deleted, requires explicit confirmation and recent
authentication, and remains protected by the server gate.

`/admin/sites/{site_id}/memberships` lists deterministic membership cards and
lets an authorized Platform Administrator or member holding both membership
and role management permissions add an already-provisioned user UUID, replace
its built-in role, bounded delegation ceiling, and complete override set, or
semantically deactivate it. Publication is a separate explicit override:
ceiling 4 never implies publication and Architect does not publish by default.
Version conflicts refresh the server record before another edit. Dialogs retain
Radix keyboard, Escape, and focus-return behavior; stable denied, missing,
conflict, validation, unavailable, loading, and empty states remain usable at
320 px. These controls are only UX; the server remains authoritative for CSRF,
site association, self-change, ceiling, permission, and version policy.

The workflow creates no account, invitation, email, password, or login and has
no user directory, custom roles, or identity editing. Content/models/pages,
Puck, workspaces/capabilities, review, audit workflows, and publication
execution remain deferred.
