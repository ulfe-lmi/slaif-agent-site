# OAP Work Order — 076-f

## Objective and verified state

Amend only PR #72 / `oap/076-agent-model-content-semantics`; no new PR/merge.
Required starting report head
`a2a9f4b1f8711c21cd8501ec00aae195f58d73cd`, sole parent
`6e8a414d9b208a759af1a28aa1e3ff1d1d9f72a1`; base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. 076-e is PARTIAL and
truthfully identifies the only remaining mutation/resource/audit gaps. Current
report-head checks are mostly in progress; do not predict success.

## DB-enforced resource authority

- Add owner-defined fixed-signature helper/wrapper logic that derives the
  immutable workspace resource constraints from trusted current COW
  `app.session_id`, validates exact site/workspace/ACTIVE/delegator state, and
  returns only typed bounded limits. Do not accept caller-selected workspace or
  capability context as authority and do not treat a custom GUC as a credential.
- In Agent type/field create/update/delete wrappers, enforce allowed type IDs/
  keys, max visible content types, max visible fields per type and delete policy
  under deterministic workspace/type advisory or row locking. Counts use the
  current session overlay, including tombstones, and concurrent calls cannot
  overrun limits. HTTP checks remain defense in depth.
- Malformed/unknown constraints should already be rejected at issuance; DB
  helpers also fail closed if legacy/corrupt stored constraints are encountered.
  Direct `slaif_agent_runtime` wrapper calls under a valid COW session cannot
  bypass limits. Preserve server-owned site/operation UUID and no base/change
  table access.

## Durable audit coupling

- Add the next reversible audit migration so every new Agent mutation stores
  exact semantic action, HTTP method, response status and quota kind alongside
  existing operation/capability/site/workspace/resource/digest. Legacy rows are
  explicitly versioned/classified without fabricated facts.
- Owner-defined completion function rejects any mismatch among:
  action↔resource type, action↔method, create/update/delete↔status,
  create/update↔mutation quota, delete↔delete quota, resource ID and current
  reservation/context. Allow only the six type/field actions now.
- Typed executor passes exact fields. Replay returns the original status/body/
  operation and emits no audit/quota/COW duplicate. Mismatch, conflict,
  validation, cancellation and quota denial leave no completed audit.
- Agent/runtime roles retain insert only through the controlled function and
  cannot SELECT sensitive control state beyond returned context or UPDATE/
  DELETE audit. Downgrade restores the exact 043 function/schema/grants and
  preserves documented legacy data safely.

## Required proof and full gate

- Real PostgreSQL concurrency races max-type/max-field creates through public
  Agent and direct wrapper: exactly allowed commits; losers stable and residue-
  free. Test allowlists, malformed stored constraint, visible overlay/tombstone
  counts, delete-disabled/count and other-workspace/site isolation.
- Execute all six type/field actions and assert exact DB audit method/action/
  resource/status/quota/digest/capability/workspace plus HTTP first/replay
  status/body/operation and quota counters. Cover wrong action coupling by
  direct function denial, legacy rows, migration roundtrip and audit immutability.
- Run full post-change Python quality/unit/integration/PG14–18, Node, Agent/
  Editor regressions, clean Compose, repository/Markdown/Mermaid/supply-chain
  and all 20 checks. No reuse of pre-change full suites; exact commands/counts/
  skips and terminal checks only.

## Scope and report

Preserve OpenAPI without claiming final artifact/public proof; 076-g owns it.
No new semantic entity/API family, items/translations/relations/views, pages/
navigation/composition/design/media/MCP/review, dependency, architecture/prior
report edit, production/release. Objective 076 remains open.

Publish exactly
`oap/reports/076-f-enforce-resource-and-audit-in-database.md` once as immutable
report-only child of literal 40-hex implementation SHA. Correct 076-e limits/CI;
include exact PR/base/head/commits/files/migration/functions/locking/concurrency/
audit/tests/checks/skips/risks/no extra PR/no merge and SELF. No post-report push.
