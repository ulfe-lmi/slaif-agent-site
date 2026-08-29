# OAP Work Order — 074-a (inert until activated)

## Contract and objective

Implement the real human product surface for creating, inspecting and revoking
site-bound AGENT workspaces and one-time capabilities. Links: Architecture
§§15.2, 18–20, 24.2, 46.2, 52.2–52.4; audit row “Human Agent session.”
Prerequisite: merged 073. On activation strategy will refresh exact `main` and
CREATE_NEW_PR state; one numeric objective is one PR.

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
route-policy coverage, full relevant Python/Node/Compose and required CI.

## Non-goals and done

No Agent semantic expansion, freeze/snapshot, promotion/discard, MCP, source
browsing or publication. Binary done means a human can create and revoke the
same capability a real external Agent API request uses, with all positive and
negative evidence green. Report `074-a-human-agent-session-control-plane.md`
with literal implementation SHA and SELF; no merge/extra PR.
