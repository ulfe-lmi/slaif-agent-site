# OAP Work Order — 074-a

## Contract and objective

Implement the real human product surface for creating, inspecting and revoking
site-bound AGENT workspaces and one-time capabilities. Links: Architecture
§§15.2, 18–20, 24.2, 46.2, 52.2–52.4; audit row “Human Agent session.”
Prerequisite 073 is merged as
`74d9c189fe241356fbe03f2632197ecbb1ce53a3`.

## GitHub objective state and verified current implementation

- Numeric objective `074`, round `074-a`, mode `CREATE_NEW_PR`; create exactly
  one new PR from remote `main` at
  `74d9c189fe241356fbe03f2632197ecbb1ce53a3`, suggested branch
  `oap/074-human-agent-session-control-plane`. No Objective 074 PR exists.
- `control_api/app.py` installs auth/site/membership/current-human only; no
  production caller installs workspace/capability routers or their route policy.
- The dormant handlers use nonexistent `app.state.database`, can fall back to
  UUID zero, create empty effective scopes, omit capability expiry, perform
  direct DML, and do not establish membership/site/CSRF/delegation authority.
- Current Agent authentication validates already-seeded tokens and its five
  create/seven semantic-read slices are real, but the trusted context omits
  general resource/delete/mutation quotas and the latest authentication SQL
  must be rechecked for workspace `ACTIVE` state after browser migrations.
- No AI Sessions Web workflow creates or revokes the capability used by a real
  external Agent request. Review/freeze/promotion remain deliberately absent.

## Production requirements

- Replace the uninstalled/unsafe `workspace_http.py` and `capability_http.py`
  scaffold with installed Control routes using the established human session,
  CSRF, site membership, permission/delegation-ceiling and trusted SiteContext
  machinery; never fall back to UUID zero or caller authority.
- Persist immutable preset intersection, scopes, resource constraints, source
  origins, request/mutation/delete/upload/browser quotas, base site revision,
  expiry and delegator; issue one high-entropy opaque token once and store only
  its digest. Token output is never logged/cached/repeated.
- Add responsive AI Sessions Web UI through NGINX for create, one-time display,
  status/list and revoke. Do not expose freeze/accept/discard until their real
  implementations exist.
- Extend Agent authentication context/request-time checks to carry and enforce
  immutable resource/quota facts without adding reviewer/control authority.
- Use owner-defined fixed-signature Control functions and the final privilege
  allowlist; Control handlers do not gain content DML and Agent never gains
  Control tables/functions. Require workspace `ACTIVE`, account/site/delegator
  validity and expiry at authentication and in later mutation transactions.

## Observable acceptance

Positive public E2E: authenticated Site Owner creates a bounded Level-4 AGENT
workspace, receives the token once, uses it on `/api/agent/v1/session`, lists
safe metadata, revokes it, and receives 401 thereafter across restart. Negative
tests: nonmember, insufficient ceiling/permission, cross-site IDs, CSRF absent,
oversized TTL/quota/source policy, replayed one-time display, expired/revoked
token, forged workspace/site and token leakage. Browser/DOM/storage/log output
must contain no plaintext token after the one-time response.

The test must use public Control/Web and Agent surfaces; direct fixture SQL may
create neutral users/sites only, never the claimed workspace/capability action.
Run real PostgreSQL, public NGINX Playwright desktop+phone, restart, privilege,
route-policy coverage, full Python quality/unit/integration, Node, clean Compose
and every required CI check. Inspect secrets/logs/artifacts for leakage.

## Non-goals and done

No Agent semantic expansion, freeze/snapshot, promotion/discard, MCP, source
browsing or publication. No raw SQL endpoint, new hosted service, dependency,
foundation change, production access, release or architecture edit. Binary done
means a human can create and revoke the
same capability a real external Agent API request uses, with all positive and
negative evidence green.

Fetch/reconcile GitHub, create the fresh branch/one PR, commit this exact order
and `oap/active` unchanged with implementation, push, repair only in-scope
failures, never merge. Publish exactly
`oap/reports/074-a-human-agent-session-control-plane.md` as the final report-
only child with PR/base/head, literal implementation SHA, `Report publication
commit: SELF`, files, migrations/grants, exact tests/E2E/checks, skips/setup,
security/leakage/authority evidence, limitations, no extra PR and no merge.
