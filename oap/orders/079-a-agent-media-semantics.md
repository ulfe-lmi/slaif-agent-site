# OAP Work Order — 079-a (inert until activated)

## Contract and objective

Expose capability-authenticated Agent media upload, metadata and reference
semantics over Objective 070's immutable store. Links: §§15.7, 24.7, 30,
52.7–52.8; requires 074–078.

## Production requirements

- Add Agent capability authentication to the public Media boundary or an
  equivalent semantic Agent route; never use human cookie/CSRF as fake agent
  behavior. Site/workspace/delegator/scopes/resource/upload quotas derive only
  from trusted capability context, not path/body.
- Stream bounded bytes, hash/sniff/validate into private workspace CAS staging;
  create/update/list/read/delete-reference COW metadata with durable semantic
  audit/idempotency. Existing digest bytes are immutable and delete never
  removes canonical/public bytes.
- Integrate media-reference validation with items/components and authorized
  private preview reads. Browser artifacts remain a separate namespace.
- Persist deterministic promotion-ready metadata without making workspace media
  public in this objective.

## Acceptance and anti-bypass

Real public capability uploads/binds/updates/unbinds media, replays safely,
survives restart and renders only in its private preview; canonical/public
remain unchanged. Deny foreign site/workspace/media, wrong scope/MIME/size/
digest/quota, overwrite/symlink/corruption/race, revoked/expired/frozen token,
direct staging path and conversion of browser artifacts. Human Media/Puck paths
remain intact.

No direct store/service/SQL/helper may perform claimed Agent behavior. Run real
bytes/store/PostgreSQL/NGINX/preview, concurrency/restart, supply-chain and full
Compose/CI. No promotion/GC/source/MCP. Binary done is complete Agent media
semantics ready for review. Report `079-a-agent-media-semantics.md` with SELF;
no merge/extra PR.
