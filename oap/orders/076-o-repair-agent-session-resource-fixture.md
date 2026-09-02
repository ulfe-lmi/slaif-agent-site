# OAP Work Order — 076-o strategic recovery follow-up

AMEND_EXISTING_PR #72 only, required start report head
`47ab4370dbbaef7dab643dbb4e28cab9e031b7a6`, parent implementation
`fbe2c1eedfa05efcc60390dbc15a4a501b489813`, base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. Human-authorized strategic CI
repair; launch/signal no agent and do not merge.

Current-head Compose job `99333309704` passed setup, governance, preview, six
responsive targets and the first Agent-session contract, then failed both Agent
desktop/mobile L4 cases at `agent-sessions.spec.ts:79` because the fixture and
UI placeholder submit obsolete unknown key `max_items`. The current bounded
Agent resource schema deliberately accepts `max_content_types`,
`max_fields_per_type`, type allowlists, delete controls and max deletes; unknown
keys fail closed during capability authentication.

Replace only the stale E2E input/expectation and matching UI placeholder with
`{"max_content_types":100}`. Do not weaken validation, add `max_items`, change
production authority, migrations, dependencies, workflows, or unrelated UI.
Run changed-file format/lint/type checks and the relevant Node contracts; rely
on fresh current-head Compose CI for the exact clean deployment/browser proof.

Publish `oap/reports/076-o-repair-agent-session-resource-fixture.md` as a
report-only child of literal implementation SHA, with exact evidence/checks,
human-authorized strategic exception, SELF, no agent/FIFO/new PR/merge/secrets
or post-report push.
