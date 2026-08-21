# OAP Work Order — 013-d

## Objective and PR state

Amend objective-013 PR #25 with responsive membership administration for
existing user UUIDs: role/ceiling assignment, explicit publication separation,
bounded permission overrides, optimistic-version updates, and semantic
deactivation. Full Playwright/accessibility/security closure remains 013-e.

- Numeric objective: `013`; round: `013-d`
- Mode: `AMEND_EXISTING_PR`; **NO NEW PR**
- PR: [#25](https://github.com/ulfe-lmi/slaif-agent-site/pull/25)
- Base/head: `main` / `oap/013-responsive-admin`
- Required starting remote head:
  `d605642d7069309599d35700725ea0de9667d6fe`
- 013-c implementation parent:
  `d6714929fc01bd52f6c69875557f2f5b8ec6ca11`
- Verified state: open, ready/non-draft, mergeable, no reviews/threads; correct
  report-only topology; current-head CI 20/20 successful; installed dependency
  graph remains architecture-allowed and MPL-free.

Fetch and verify the exact PR/head. Amend only PR #25; never create another PR,
merge, close, auto-merge, or workflow-rerun.

## Boundaries

The seven membership/catalog APIs and server RBAC are already implemented.
This UI manages only existing `user_account` UUIDs. There is no user directory,
creation, invitation, email, password reset, OIDC login, custom role designer,
or identity editing. Client controls are UX only; server CSRF, same-site
authority, actor locks, self-escalation, scope/ceiling, and version checks remain
truth.

No backend/API/schema/migration/route-policy, site workflow, dependency/lock,
Compose/edge, content/Puck, workspace/capability, review/publication, or adjacent
product change is expected. If an API change appears necessary, stop and report.

## Allowed scope

```text
apps/web/src/admin/{api,membership-workflows,admin-shell}.tsx|.ts
apps/web/src/components/ui/** only minimum existing-style form/dialog/table primitives
apps/web/app/admin/sites/{siteId}/memberships/**
apps/web/app/styles.css only responsive membership rules/tokens
apps/web/tests/**
tests/contracts/** only shared response validation if needed
docs/{ADMIN,API,AUTHORIZATION,SECURITY,SITES}.md
README.md
oap/active
oap/orders/013-d-membership-management-workflows.md
oap/reports/013-d-membership-management-workflows.md
```

## Requirements

### 1. Strict client contracts and authority

Add runtime validators for role, permission, membership, and stable error
responses. Requests use same-origin credentials and the existing exact CSRF
helper. Never store session/CSRF/user/permission/site data in browser storage,
never derive authority from role names locally, and never accept site/user IDs
outside canonical URL/form fields as trusted context.

The page loads current site authority, roles, permissions, and memberships.
Platform Administrators and members holding both `membership:manage` and
`role:manage` receive controls; others receive a read-only or constant denied
state. Every crafted request remains server-denied. Current human UUID from the
session is used only to prevent presenting self-mutation controls; server policy
still enforces it.

### 2. Responsive membership workflow

Implement canonical `/admin/sites/{site_id}/memberships` integrated into the
admin/site navigation with:

- deterministic membership list showing UUID, role, ACTIVE/INACTIVE, explicit
  and effective ceiling, version, Platform Administrator fact, and concise
  permission/override summary;
- add-existing-user form requiring a valid UUID, built-in role, ceiling bounded
  by that role, and complete explicit overrides; explain that users must already
  be provisioned and no invitation/login is created;
- edit flow prefilled from the exact current record, requiring expected version,
  complete replacement role/ceiling/allow/deny sets, and conflict-safe refresh;
- semantic deactivate confirmation that preserves the row/history and uses the
  current expected version; no hard-delete wording or behavior;
- publication as a clearly separate explicit toggle/override, never implied by
  role ceiling—Architect ceiling 4 remains non-publishing by default;
- advanced permission overrides grouped by READ/L1–L4/human governance while
  installation/system scopes are visible as nonassignable or omitted with an
  explanation, never submit-capable;
- role-change behavior that updates valid ceiling choices/default summary but
  never silently grants overrides; and
- stable loading/empty/401/403/404/409/422/503/invalid-response states,
  duplicate-submit guards, refresh after success, and no stale response overwrite.

Controls must be keyboard accessible, labelled/described, focus visible,
Escape/focus-return safe for dialogs, 44 px targets, reduced-motion aware, and
usable without horizontal overflow at 320 px. Tables must adapt to cards or
scroll accessibly rather than hiding fields. No raw HTML, inline style, remote
origin, telemetry, or new dependency.

### 3. Security and semantic evidence

Web tests must cover Platform Administrator, Owner, bounded manager,
Architect/Viewer/non-member, self target, cross-site UUID, existing/inactive
member, unknown user, duplicate create, stale version, missing/wrong CSRF,
ceiling escape, system permission, publish add/remove, complete override
replacement, and deactivation. Verify exact methods/paths/bodies, no forbidden
fields, and permission-driven controls without client authority claims.

Test response validation, sorting, concurrency/pending guards, refresh/error
focus, responsive structure, dialog keyboard semantics, no storage/token/
remote-origin, strict CSP-compatible source, and unchanged site/admin/public/
auth surfaces. Existing real backend tests and GitHub PostgreSQL 14–18 remain
authoritative; do not duplicate backend policy in JavaScript.

Run full frozen Node lint/format/type/test/build/licenses, repository/supply
policy, changed Markdown/order/report lint, `git diff --check`, CSP/storage/
remote/secret scans. Do not run local PostgreSQL, Compose, Playwright/browser,
images, Mermaid, or broad SBOM; 013-e owns browser closure and GitHub runs
unchanged gates.

### 4. Documentation

Document the existing-user UUID limitation, roles/ceilings/defaults, separate
publish control, overrides, version conflict refresh, semantic deactivation,
server-versus-UX authority, accessibility/error states, and no invitations/
custom roles/user CRUD. Keep content/Puck/workspaces/review/publication execution
explicitly deferred.

## Acceptance and workflow

Acceptance requires a functional responsive membership UI over existing APIs,
exact server-bound request behavior, no overclaim/identity feature/dependency/
backend scope, and all 20 checks green. Target 60 minutes; hard stop 85 minutes.

Front-load API/state/UI design; fix diagnosed local issues within scope. Push
one coherent generation after local green; one corrective generation only for
a concrete clean-runner/build defect, never workflow-rerun or weaken tests.
Publish honest `PARTIAL` at the hard stop. Access no production credential,
system, or data.

Preserve prior transcript bytes and amend only PR #25. Atomically publish:

```text
oap/reports/013-d-membership-management-workflows.md
```

The report-only `SELF` commit must parent the literal implementation SHA. Report
route/body/state/role/ceiling/override/publication matrices, crafted negatives,
responsive/accessibility/CSP evidence, exact commands, current 20 checks,
corrections/skips/scope/hashes, and no-new-PR/no-rerun/no-merge. Signal FIFO
`OK` only after report and claimed remote state exist.
