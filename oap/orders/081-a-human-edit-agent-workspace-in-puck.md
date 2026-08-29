# OAP Work Order — 081-a (inert until activated)

## Contract and objective

Allow an authorized human to open and edit the exact Agent workspace in Puck,
so the defining workflow does not silently create a separate HUMAN workspace.
Links: §§9.3, 14.3, 15.3, 28.1–28.3, 42.4, 52.6. Requires 074–080.

## Production requirements

- Add explicit human-authorized workspace selection for Editor/Puck: derive
  site/workspace/session server-side from human membership and workspace access;
  never trust a raw workspace ID as COW context. Preserve the convenient HUMAN-
  workspace flow separately.
- Puck loads/saves the Agent workspace's same normalized composition through
  Editor API using human actor audit, shared lock, idempotency, scopes and
  server validation. It never mints/uses the Agent capability or publishes.
- Allow authorized human edit only while `ACTIVE`; FREEZING/REVIEW/terminal
  states deny. Cross-site/nonmember/read-only access is non-leaking.
- Add responsive AI Session/Puck navigation that clearly names the selected
  workspace and cannot confuse canonical, human or Agent state.

## Acceptance and anti-bypass

Public NGINX E2E creates a real Agent workspace/capability, Agent creates a
component, human visibly opens that exact workspace in Puck, changes/reorders
it, saves/reloads, and Agent/preview reads see the same normalized result while
canonical remains unchanged. Assert one workspace/timeline, HUMAN audit actor
and no capability token in browser. Deny forged/foreign/frozen/terminal/
unauthorized workspace, CSRF failure and crafted request.

No direct Editor service/SQL/fixture mutation may substitute for visible Puck.
Run real PostgreSQL, public browser desktop/tablet/phone, Agent/Editor/Render,
full Compose/CI. No freeze/promotion. Binary done is exact same-workspace
convergence. Report `081-a-human-edit-agent-workspace-in-puck.md` with SELF;
no merge/extra PR.
