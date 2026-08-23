# OAP Work Order — 024-a

## Objective

Replace the capability authentication placeholder in `agent_http.py` with
real token validation against the `control.capability` table.

## GitHub objective state

- Numeric objective: `024`; round: `024-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR
- Base: current main (after 023-a merge)

## Verified current state

- `agent_http.py` has `_authenticate()` that checks `Bearer sas2_` prefix
  but calls `database.authenticate_agent_capability()` which doesn't exist.
- `control.capability` table exists (migration 024) with `public_id`,
  `secret_digest`, `workspace_id`, `scopes`, `expires_at`, `revoked_at`.
- `agent_state/capability.py` has `compute_digest()` and
  `constant_time_digest_compare()`.

## Required changes

1. Add `authenticate_agent_capability(auth_header)` method to ControlDatabase
   that:
   - Parses the `sas2_<public_id>_<secret>` format
   - Looks up the capability by public_id
   - Computes SHA-256 digest of the full presented token
   - Uses constant-time comparison against stored secret_digest
   - Checks that revoked_at IS NULL
   - Checks that expires_at > now()
   - Returns an AgentCapabilityContext with site_id, workspace_id, scopes
2. Wire `_authenticate()` in `agent_http.py` to use this method.
3. Add negative tests:
   - Invalid format → 401
   - Unknown public_id → 401
   - Wrong secret → 401
   - Revoked → 401
   - Expired → 401
4. Add positive test: valid capability returns correct context.

## Anti-false-positive clause

A prefix check alone does NOT satisfy this objective. The implementation
must perform a real database lookup, real digest comparison, and real
revocation/expiry checks.

## Acceptance criteria

- Valid capability authenticates and returns correct site/workspace/scopes.
- All 5 negative tests pass.
- No capability token or digest appears in any log or response body.
