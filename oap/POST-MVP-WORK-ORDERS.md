# Post-MVP Work Orders — Proposed

These are optional follow-ups after the contractual MVP is honestly complete.
They are not substitutes for the dependency-correct 074–091 MVP sequence in
[`MVP-PROGRESS.md`](MVP-PROGRESS.md). Each requires a separately authorized
work order before activation.

## Production and §51.2 follow-ups

| Follow-up | Scope | Why it remains post-MVP |
|---|---|---|
| Optional OIDC identity mode | Integrate a self-hosted OIDC provider alongside local authentication | §51.2 deployment option; local identity remains the default |
| Optional Prometheus metrics | Expose the architecture metric set without outbound telemetry | §51.2 operations enhancement |
| Shared media backend at scale | Add a self-hosted shared immutable store for multi-node deployments | Local content-addressed storage is the default MVP path |
| Advanced human role designer | Add custom role templates and permission-set editing beyond built-in roles | Built-in roles and bounded delegation are the MVP contract |
| Additional product adapters | Integrate non-website consumers while preserving site/workspace boundaries | The contractual MVP is the website product |
| Extended operational observability | Add self-hosted dashboards, retention policy, and incident runbooks | Baseline health, audit, backup, and restore evidence remain required first |

## Boundary

The MVP queue owns Agent semantics, MCP parity, review and promotion,
conflict-safe publication, source reconstruction, expiry/cleanup workers,
backup/restore proof, and the final hostile truth gate. Those items must not be
reclassified as post-MVP work merely because their implementation is pending.
