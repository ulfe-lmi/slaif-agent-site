# OAP Work Order — 073-c

## Objective and verified state

Amend only PR #69 on `oap/073-repair-mvp-control-state`; no new PR/merge.
Required starting report head is
`13cb82ece75b8a10b9f95ef97306d7d118c997a6`, sole parent
`1ab19a3b3824461145fb7f9e55584c15f347ea84`; `main` is
`bcaddc41f9ef4e779dd1a8c9a41eb08462250d53`; all 20 checks are green.
Strategic review accepts 073-b's requested phrase fixes but found remaining
false inventory prose in README. Correct it once, exactly and comprehensively.

## Required README corrections

Update only `README.md` so these sections match current merged code:

1. Delivery sequence:
   - correct the HTTP process count/inventory (Control, Editor, Agent, Render,
     MCP and Media; distinguish internal Render exposure and scaffolded MCP);
   - replace “three empty product schemas” with the real Control/content/audit
     and COW-enabled populated boundary, without claiming complete domain data;
   - keep review/scheduler/GC/reconstruction gaps explicit.
2. Repository map:
   - `apps/web` is a real pre-alpha public/admin/Puck/preview surface, not only
     a minimal status surface;
   - `packages` contain real normalized composition/catalog/scope/browser
     contracts where implemented, not seven empty scaffold-only boundaries;
   - preserve accurate services/browser-worker and bounded-exception comments.
3. Following inventory prose:
   - remove the false sentence that TypeScript packages contain no schemas,
     components, scopes or browser tools;
   - remove the false statement that all other public Python processes are
     health-only; name the real bounded Agent/Editor/Render/Media behavior and
     the MCP/lifecycle gaps conservatively;
   - remove obsolete single-injected-Control-component wording if it no longer
     describes the current deployment;
   - rephrase “as product code/tests arrive” so existing product tests are not
     described as absent while future gates may still expand.

Do not change the logo, mission, normative planned architecture/capability
sections, incomplete-MVP verdict, 074–091 queue, or the accurate 073-b facts.
Do not claim complete Agent semantics, MCP, review/promotion, source/sweep,
public media, scheduler/GC, restore or release readiness.

## Scope, verification and report

Change only `README.md`, exact unchanged 073-c order/active, and new report.
No other docs/audit/progress/queue/policy/product/migration/dependency/workflow/
architecture/issue or prior artifact. Run Markdownlint, repository policy,
`git diff --check`, and searches proving the exact stale inventory phrases are
gone. Require all current PR-head checks successful. No broad product run.

Publish `oap/reports/073-c-final-readme-inventory-truth.md` as immutable
report-only child of literal implementation SHA; include exact claims/files/
checks/skips/no extra PR/no merge and SELF.
