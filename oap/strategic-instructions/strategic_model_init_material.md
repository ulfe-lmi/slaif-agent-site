# Orchestrated Agentic Programming — strategic initialization (compact)

Source: **A Human-Governed Workflow for Strategic AI, High-Autonomy Coding
Agents, and Review-Ready Software Delivery**, Janez Perš
(`janez.pers@fe.uni-lj.si`), v1.0.1, 2026-06-14. This agent-oriented edition
retains the source doctrine, operational facts, examples, templates, and
boundaries while removing generated TOC/layout, repeated exposition, and
reader pedagogy. The verbatim pre-compaction revision is preserved by SLAIF
Agent-Site archival PR #16 / merge `2954a743f3afaaae5d3d26e598007cdbb17e918f`.
Source acknowledgement: EC/EuroHPC JU and Slovenian Ministry of HESI support
through SLAIF grant 101254461.

## 1. Definition, purpose, claims

OAP=human-governed, constitution-driven subtype of agentic software engineering:
a strongest-practical long-context strategic AI is control plane; a high-
autonomy coding agent performs bounded repository work in a hardened,
rebuildable runtime; human retains goal/domain truth/risk/release; remote repo
preserves truth. It composes existing mechanisms (repo instructions, agents,
AI review, branches, human review, multi-agent research), not a claimed new
scientific discipline. It is more disciplined than vibe coding, more autonomous
than ordinary pair programming, more governable than unconstrained swarms.

Central artifacts: `AGENTS.md`/`CLAUDE.md`; architecture/discovery artifacts;
narrow PR-sized work; explicit non-goals; reproducible verification; structured
reports; remote-repository truth; audits/remediation; durable handoffs. Thesis:
AI makes code production cheap, shifting the bottleneck to validation,
governance, continuity, architecture/security judgment, docs, operations, and
release honesty. OAP frees humans from typing/setup, not responsibility.

Nonclaims: coding agents are not safe/reliable without boundaries; high
autonomy is not safe by default; a generated/green PR is not completion; human
need not manually inspect every line; domain-expert software creation is not new
(related to end-user engineering, low-code/citizen development); OAP does not
remove accountability or promise effortless/certified software. Narrow claim:
proper strategy+constitution+rebuildable runtime+PR discipline+verification+
evidence interrogation make agent labor auditable, constrained, test-backed,
and aligned without turning human into operator.

Evolution: completion (human codes, AI suggests; risk=fast bad snippet) → pair
programming (co-edit/explain; plausible but unproved) → chat coding (files/design;
chat/repo drift) → coding agent (repo/tool execution; autonomy without governance)
→ OAP (strategic critique + execution; risk=human rubber-stamp). Copilot bounded-
task study reported 55.8% faster completion; this does not prove whole-delivery
quality. SWE-bench centers real issue resolution; SWE-agent shows agent-computer
interface matters; HULA/MetaGPT/ChatDev illustrate human/multi-agent interest.

Compact control law:

```text
Human pilots strategic AI; strategic AI directs execution agent;
execution agent operates machine; repository preserves truth.
If executor directs human through routine low-level work, control is inverted.
```

## 2. Roles, responsibility, context economics

Human may be product owner, manager, technical director, reviewer, release
authority, or domain expert (physician/teacher/scientist/operator/compliance/
manufacturing/research/library/public-sector). Owns problem/purpose/domain
workflow/user need/ethics/legal limits/risk appetite/priorities/acceptance/
release and responsibility when wrong. Domain proximity can shorten lossy
user→analyst→ticket→engineer handoffs. Human asks strategy: exact requirement?
domain workflow? evidence? regression test? secrets/migrations/deployment?
unrelated scope? skeptical-review proof? refusal-to-merge reason? Human rejects
fluent but wrong strategic/execution results.

Strategic AI=architect+staff engineer+technical-program manager+critic+memory+
prompt compiler, not primarily code generator and never accountable architect of
record. It discovers product category/architecture/tools/trust boundaries;
identifies assumptions/missing requirements; proposes safe ordering/non-goals;
writes constitution/orders; reviews reports/diffs/tests/docs/security; compresses
evidence; tracks risks/state/readiness; creates handoffs; disagrees when needed.
Use strongest practical reasoning/instruction-following/long-context model;
spend expensive context on product story/domain/decisions/PR outcomes/risks/
evidence, not file edits/retries. Strategic continuity should span many PRs.

Executor=disposable implementation labor: inspect/edit; install/configure local
tools; run services/migrations against test DB; test; document; commit/push/open
PR; report exact outcomes. It does not own product, roadmap, scope expansion,
security exceptions, production access, long-term memory, merge/release. One
bounded PR=one consumable executor context, reset/compact afterward.

Durability: VM may die; Git remote/branches/PRs/CI/issues/docs/tests/releases/
handoffs survive. Local state is never project truth. Ideal: strategy does not
lose context, human does not lose goal, executor need not remember beyond PR.

Implementers are not automatically unchanged: routine line labor is compressed.
Healthy transition moves people to acceptance criteria, test/fixture design,
architecture/security/privacy/ops review, runtime/constitution/CI maintenance,
audit→order translation, high-risk diff inspection, release/incident work.
Removing implementers while humans rubber-stamp is not mature OAP.
The new human skill stack is requirements thinking, architectural/security
judgment, test design, evidence interrogation, report-based debugging, release
management, documentation discipline, work-order design, and knowing when not
to delegate; memorizing framework idioms and doing setup manually matter less,
but software understanding remains necessary.

## 3. Strategic discovery before code

Start with operational domain problem, not stack/blank-repo executor prompt.
Ask: real product category? adjacent systems? boring/safe stack? trust boundaries?
components needing separation? first release/non-goals? what executor must never
improvise? Human accepts/rejects using domain truth; only then create architecture,
constitution, schema/contracts, test/deployment plan, first PR sequence.

Discovery sequence:

1. State real workflow/problem and failure cost.
2. Classify system/product.
3. Establish actors, trust/data/credential/side-effect boundaries.
4. Compare architecture/stack alternatives; select boring robust components.
5. Define data model, jobs, admin/ops, tests, recovery.
6. Bound first release and explicit exclusions.
7. Persist architecture, constitution, schema/contracts, test strategy,
   deployment sketch, PR plan before broad execution.

Work order is strategic output/translation artifact. It states current verified
state; exact goal/domain behavior; acceptance; files/areas; constraints/non-goals;
required implementation/tests/docs; safe local packages/services executor may
install; branch/PR workflow; report. It must enable success judgment before work
and avoid human setup chores.

### API Gateway discovery example

Domain need: SLAIF/WP6 workshops need bounded, auditable LLM access without
exposing provider keys. Native provider project/key budgets insufficient for
strict per-user hard quota ⇒ product=local OpenAI-compatible quota gateway,
not “keys/script.” Users retain `OPENAI_API_KEY`+`OPENAI_BASE_URL` and `/v1`;
gateway authenticates, reserves/checks/finalizes quota, routes/substitutes server
provider credential, records usage, fails closed on unknown policy/pricing.

Decisions:

- gateway-issued bearer key plaintext never stored; HMAC-derived digest+pepper;
- reserve-then-finalize accounting for concurrency;
- FastAPI/Starlette streaming + Uvicorn/Gunicorn; `httpx` async proxy;
- PostgreSQL + SQLAlchemy async + asyncpg + Alembic as durable truth;
- Redis/Celery for short coordination/rate/reservation/background mail/reports;
- Jinja2+HTMX+Tailwind admin and Typer CLI;
- pytest/pytest-asyncio, respx/pytest-httpx, testcontainers, Hypothesis,
  Playwright; Docker Compose;
- put human-readable `docs/database-schema.md`, compatibility matrix,
  architecture/tests/deployment/non-goals into repo before models/migrations.

Question→translation: hard per-key limits? native insufficient→gateway; ordinary
clients? OpenAI-compatible env+`/v1`; key storage? high-value bearer→HMAC digest;
concurrent hard quota? reserve/finalize; stack? async API+DB+queue; ops? dashboard+
CLI; executor guidance? constitution/schema/contracts before code.

Managerial prompts were short: “Is hard per-key spend possible? If not, build
own compatible forwarding/accounting server? Can client code remain ordinary?
How should accounting work? Which DB/framework/admin/CLI/email/tests/deployment?
Put schema in repo before execution?” Strategic translates, executor implements.

## 4. Project constitution

Constitution=`AGENTS.md` (Codex layered global/project/nested precedence) or
`CLAUDE.md` (Claude persistent session instructions); keep aligned if both tools
work repo. It is durable machine-readable governance, not README, one prompt, or
style-only text. Write after discovery. It includes:

```text
Discovery summary: domain/product/architecture+stack rationale/rejected options/
  first-release scope
Mission/core promise; domain vocabulary/workflows/failure modes
Architecture/components/versions/ownership/data flows
Non-negotiable security/privacy/data/compatibility invariants
Forbidden files/systems/dependencies/secrets/production actions
Branch/commit/PR/no-direct-main workflow
Unit/integration/E2E/lint requirements; skip/block reporting
Documentation contracts/limitations/release-claim rules
Local setup authority; reporting/evidence/risk/follow-up format; definition done
```

Turn recurring corrections into law (e.g. required README block, skipped≠pass,
new security test). Weak smell: “good code,” no tests/forbidden actions/workflow/
secrets/evidence/continuity. Oversized smell: stale chat, duplicated docs,
contradictions, context overflow, routinely ignored diffusion. Remedy=top-level
universal law+nested specialist rules+separate background docs.

## 5. Work-order engineering and PR unit

Prompting is management artifact, not clever prose. Before each order verify
live remote main/open PR/CI; handoff is snapshot only. Strong non-goals name
features/files/APIs/migrations/dependencies/tests/claims prohibited. Weak:
“improve/finish/fix all/use judgment/run tests/update docs/ask me for deps.”
Strong: exact behavior+risk+proof+boundaries.

Canonical order skeleton:

```markdown
# Coding Agent Work Order
Repo; governing AGENTS/CLAUDE; report live-state differences.
Current verified state; Goal; Domain behavior; Acceptance; Scope; Non-goals;
Files to inspect; Required behavior; Tests; Documentation; Safety.
Local setup: install needed tools only in execution VM, document durable setup,
do not ask human unless explicit safety boundary.
Workflow: fresh main, feature branch, related files only, commit, push, PR, no merge.
Report: branch/commit/PR, summary/domain behavior/files, exact tests/results,
setup/deps, docs, safety, skipped/blockers/risks/follow-up.
```

PR is atomic unit: bounded, coherent, durable diff+CI+history, reviewable,
revertible, separates implementation from acceptance. “One prompt, one PR” is
default; investigation/verification/docs planning may not need PR. Example:
conversation-item delete requires explicit permission and OpenAI-shaped 404 for
unknown/non-owned ID before provider call; non-goals update/Chat Completions/
storage; tests denial+no-forwarding; new branch/PR/no merge.

Open PR with failure/review gap precedes new feature. Repair order: repair named
PR only; no new behavior/refactor; inspect exact CI/comment; minimum fix;
reproduce/run failing test; push same branch; report root cause/fix.

Report is execution→strategy interface/index, not proof:

```markdown
Branch/commit/PR
Summary; Files changed
Tests: command => exact result
Docs impact; local setup/dependencies
Safety: no production secrets/unrelated files; skipped not passed
Known limitations; Follow-up
```

Labels distinguish passed/failed/skipped/not-run/blocked/out-of-scope. Never say
“all passed” unless literally relevant/full suite passed.

Executor discipline: correct branch; inspect before edit; small related commits;
existing patterns; no broad refactor unless ordered; focused then broad tests;
safe self-service setup; stop on real boundary; never fake PR/CI. Most dangerous
executor succeeds loudly while violating scope.

## 6. Runtime/preflight: bounded high autonomy

Autonomy is runtime design. Agent must install/build/test/start services without
host/production blast radius. Preferred: dedicated VM/distro/cloud sandbox (or
narrow trusted container), only repo+disposable fixtures, broad guest authority,
no production secrets/data, deliberate network, version-controlled effects,
PR-only output, cheap snapshot/reset. Question is not “least ability?” but “what
may it destroy in a space we can discard?” High privilege in disposable guest
can be safer/more efficient than weak agent recruiting human.

Codex full access: `codex --yolo` =
`codex --dangerously-bypass-approvals-and-sandbox`; official docs say use only
externally hardened environment. Claude equivalent:
`claude --dangerously-skip-permissions` =
`claude --permission-mode bypassPermissions`. Sandbox capability and approval
policy are separate controls. OAP outer VM/credential/workflow boundary is
safety mechanism; never use full access on normal secret-rich laptop/account.

Guest baseline:

```bash
sudo adduser agent
sudo usermod -aG sudo agent
sudo visudo -f /etc/sudoers.d/90-agent-nopasswd
# add: agent ALL=(ALL) NOPASSWD:ALL
sudo chmod 0440 /etc/sudoers.d/90-agent-nopasswd
sudo visudo -c
su - agent
sudo -n true && echo "passwordless sudo works"
mkdir -p "$HOME/.codex-agent" "$HOME/.claude-agent"
export CODEX_HOME="$HOME/.codex-agent"
export CLAUDE_CONFIG_DIR="$HOME/.claude-agent"
```

Guest-local `~/.ssh/authorized_keys` is expected for inbound SSH; copied host
private/production keys, agent forwarding, cloud/kube/browser/password-store/
Docker-socket/production `.env`, or broad writable host-home mounts are failure.
Install SSH in guest:

```bash
sudo apt update
sudo apt install -y openssh-server
sudo systemctl enable --now ssh || sudo service ssh start
mkdir -p ~/.ssh && chmod 700 ~/.ssh
```

Prefer public-key login and localhost forwarding (`localhost:2222→guest:22`).
SSH is convenience, not boundary. Snapshot/checkpoint/export before run; after
breakage revert/destroy; preserve only Git/PR/logs/documented setup. If rebuild
takes hours, runtime is wrongly precious.

Preflight truth checklist: dedicated disposable guest/user; sudo only guest;
repo guest-local/narrow mount; host home not writable; no host/prod SSH/cloud/
kube/Docker/password/browser/.env secrets; guest-local Codex/Claude state;
network policy known; snapshot+tested recovery; clean/known-dirty tree; logs;
short-lived least-privilege creds; fake/test DB/API; external APIs mocked unless
explicit; install policy understood; agent cannot push protected main/merge;
durable output branch+PR. High-autonomy rule: guest contains nothing human
cannot afford to lose/rotate.

Runtime anti-patterns: secret-rich laptop; production DB/cloud creds; CI-secret
changes; own-PR merge; non-versioned folder; `--privileged`, `/`/home/SSH mounts,
Docker socket, host networking; unverified “tests passed”; human dependency
chasing. Passwordless sudo ≠ no boundary: assess destroy/read/network/persistent
mutation/reversibility/audit/rebuild and whether human is being recruited.

### Platform recipes

Windows/WSL2 default for Linux work:

```powershell
wsl --install -d Ubuntu
wsl -l -v
wsl --set-version Ubuntu 2
```

Inside: `sudo apt update && sudo apt upgrade -y`; install `build-essential git
curl wget unzip zip ca-certificates openssh-server`; keep projects under
`~/work`, not `/mnt/c` (performance). Harden `/etc/wsl.conf`:

```ini
[automount]
enabled=false
[interop]
enabled=false
appendWindowsPath=false
[user]
default=agent
```

Apply with `wsl --shutdown`. SSH via localhost port proxy; Windows 11 mirrored
networking needs firewall attention. Hyper-V Ubuntu VM is clearer isolation +
checkpoint: repo inside, SSH, passwordless sudo, no host profile shares.

Windows Sandbox suits disposable native smoke/one-off work; `.wsb` supports
network, mapped folders, logon command; all installs/host keys/clones/Build Tools
vanish on close. Example: read-only `C:\agent-sandbox\in`→`C:\agent-in`, writable
`...\out`→`C:\agent-out`, `bootstrap.ps1` logon, 8192MB. Bootstrap OpenSSH:

```powershell
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
if (!(Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue)) {
  New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -DisplayName "OpenSSH Server (sshd)" `
    -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
}
ipconfig | Out-File C:\agent-out\sandbox-network.txt
```

Windows 11 24H2+: `wsb list`; `wsb ip --id <sandbox-id>`. VS Build Tools quiet
install uses `--quiet --wait --norestart --nocache --installPath C:\BuildTools
--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended`; technically
works via `Start-Process C:\agent-in\vs_BuildTools.exe -Wait -ArgumentList ...`
but is slow per ephemeral run. Persistent Windows VM is preferred for repeat
MSVC/SDK/COM/PowerShell/service work: dedicated agent, OpenSSH, Build Tools once,
checkpoint, no host share, repo inside; patch/snapshot/rotate/rebuild; verify
separate Windows/VDA virtualization licensing (manual is not legal advice).

Linux: KVM/libvirt clean default:
`sudo apt install -y qemu-kvm libvirt-daemon-system virt-manager openssh-client`;
guest SSH; NAT normally enough, bridge/forward for LAN; libvirt virtual network/
shared-device XML authoritative. Fast Ubuntu VM: `sudo snap install multipass`;
`multipass launch 24.04 --name agent --cpus 6 --memory 12G --disk 80G`;
`multipass shell agent`. LXD works where already operated (containers+VMs).
Trusted narrow CI-like work may use container, but unrestricted agent belongs
in VM; never privileged/root mount/SSH mount/Docker socket/host network.

OverlayFS provides reset, not strong security:

```bash
sudo mkdir -p /srv/agent/{base,upper,work,merged}
sudo mount -t overlay overlay -o lowerdir=/srv/agent/base,upperdir=/srv/agent/upper,workdir=/srv/agent/work /srv/agent/merged
sudo chroot /srv/agent/merged /bin/bash
```

`systemd-nspawn` > bare chroot but still not VM boundary for untrusted full access.

macOS: Lima Ubuntu CLI default; host home read-only by default, but prefer no
host mount/narrow writable `/tmp/lima-agent-share`. `agent.yaml`: Ubuntu 24.04
arm64+amd64 release cloud images from
`https://cloud-images.ubuntu.com/releases/24.04/release/ubuntu-24.04-server-cloudimg-{arm64|amd64}.img`,
`cpus: 6`, `memory: 12GiB`, `disk: 80GiB`, home read-only, narrow temp writable.
`brew install lima`; `limactl start ./agent.yaml --name agent`; `limactl shell
agent`. Mount transports vary (reverse-sshfs/9p/
virtiofs), keep narrow. Alternative: `brew install --cask multipass`, same launch/
shell; UTM/VMware Fusion/Parallels acceptable. Never broad writable macOS home.

Platform sources retained by key: Codex CLI/security/AGENTS docs; Claude CLI/
memory docs; Microsoft WSL install/filesystems/config/networking, Windows Sandbox
overview/config/CLI, Windows OpenSSH, VS installer/workload IDs, Windows licensing;
Ubuntu virt-manager/LXD; Canonical Multipass; libvirt networking/XML; Linux
OverlayFS; systemd-nspawn; Lima usage/mounts.

## 7. Verification, validation debt, security

Generated code velocity increases validation debt: large diffs, shallow tests,
unrelated edits, confident overclaiming, docs ahead of behavior. Constrain unit,
demand evidence, keep human review surface manageable. Tests prove only their
scope: unit=narrow behavior; integration=interaction; E2E=user path; browser
smoke=one rendered path. A skipped/not-run test is unknown, never pass.

Meaningful test fails if dangerous regression occurs. Smells: asserts internals/
non-null, mocks away risk, encodes bug as expected, generated expected output
without independent basis. Reports name exact commands/results/environment:
focused unit pass does not imply blocked integration. Verification-only order:
forbid edit/branch/commit/PR; run named commands; report tested SHA, exact pass/
fail/skip/blocker, final `OK|FAIL|ENVIRONMENT_BLOCKED`.

Fail closed on unknown pricing/route capability/non-owned resource/bad SSH host
key/missing test DB/unsupported provider. Secrets law: no production secret in
runtime/prompt/repo/log/history/screenshots/telemetry; no plaintext gateway key;
no token test output; fake docs placeholders; stop/report exposure. Example
scan: `rg "api_key|Authorization|Bearer|password|secret|token" app tests docs -n`,
`git diff --check`, unit tests, linter.

Human gates: production deploy, protected merge, destructive data, credential
rotation, public release claims, risky dependency, network widening, security
posture. Agents may try disabling tests, weakening validation, broad catch-all,
wrong mocks, skipping hard integration, real services, inflated docs; reject.
“Works” must also obey project rules.

## 8. Documentation, handoffs, review, audit, release

Durable docs may include README/quickstart/architecture/security/compatibility/
deployment/testing/runbooks/release notes/review archive/remediation matrix/
handoff. Docs are contracts: implemented endpoint updates matrix; unsupported
stays explicit; beta is not certification. Runbooks cover key compromise/
rotation, DB backup/restore, Redis outage, email ambiguity, admin lockout,
rollback, metrics; never invent commands/recovery.

Strategic handoff (memory aid, never over live repo): current main/open/recent
PR/CI; goal/milestone/release target; implemented/missing; non-negotiables;
risks/blockers; next and “do not do next.” Verify it on reload.

Every PR produces terse human decision brief:

```text
Recommendation merge|repair|reject|defer
Goal match; evidence(test/CI/files/docs); risks; human decision
```

Human reviews system meaning: scope/behavior/tests/security/docs/migration/
release/operator impact, using brief→questions→targeted files/external audit,
not routine full-line reading. AI review asks for concrete security regressions,
missing tests, docs drift, constitution violations, not praise.

Cross-model audit (build one family, audit another) reduces circularity but is
not objective/certification. Give repo/snapshot, goals, limitations, tests,
specific questions, permission not to praise. Cadence: architecture audit after
constitution/scaffold; boundary audit after auth/secrets/billing/quota/streaming/
deployment; maturity audit before prototype→beta/RC/production language;
follow-up after remediation. Extra audit after broad trust/transaction refactor,
new credentials/boundary, unexplained green tests, doc overclaim, recurrent CI,
unchallenged release assumption, or confidence-induced acceptance temptation.

Audit mechanics: freeze scope/commit; state implemented/excluded; request
findings; classify current defect vs missing test/docs vs future/rejected idea;
record accepted findings in remediation matrix; turn each current item into
bounded PR orders; close only with code/test/docs evidence; archive review;
never call audit certification unless it is. Review comments become narrow
same-PR repair orders.

Release completeness ladder: prototype; narrow implementation; expected-path
tested; negative-path tested; documented; operationally recoverable; reviewed;
RC; production-ready. Assess functional completeness, architecture, security,
tests, docs, ops/recovery, release honesty; score summarizes evidence, never
replaces it. Release brief: recommendation, goal/criteria, CI/tests/security/
docs/rollback evidence, limitations, decision. Gates: explicit goal/criteria;
clean tree; all relevant CI green; no unclassified required skips; docs aligned;
limitations public; scans; migration+rollback; final human decision. Apparent
file/UI/test volume is not coherence; say “not yet” when proof weak.

## 9. Case studies and application patterns

### SLAIF API Gateway

Serious greenfield system: OpenAI-compatible access, issued keys, hard quotas,
routing/accounting/admin/security/deployment. Constitution encoded stack,
key/privacy rules, tests, PR workflow, docs, no real provider keys/plaintext
storage/production overclaim. Many PR slices built schema/key service/reservation/
routing/admin/docs/tests/runbooks/feature families/release verification. Human
asked “fail closed? quota proof? secret leakage? implemented vs documented?
release gaps?”; strategic translated to orders/briefs; executor implemented.

Public review archive/remediation matrix made audit inspectable. Review 6.0/RC1
judged implemented scope credible RC-beta, explicitly not production
certification/compliance/pentest, and found non-message Chat Completions input/
cost pre-reservation underestimation (`tools`, `response_format` schemas), need
quota/accounting/reconciliation/idempotency safe-ledger invariant tests, and
production runbooks. Focused fixes/tests/runbooks closed findings. Lesson:
implementation velocity needs domain management, proofs, runbooks, honest claims.

### SLAIF Connect takeover/rewrite

Browser SSH/HPC prototype/fork contained useful knowledge but wrong long-term
shape. Domain invariant: SLAIF must not receive SSH credentials. Strategic
separated upstream code from owned behavior: non-fork extension; pinned upstream
`libapps` build dependency; WebSocket↔TCP relay; extension-side host policy;
credentials remain browser↔HPC server. Incremental scaffold/vendoring/relay/
browser/signed-policy/pilot PRs replaced “finish divergent Secure Shell fork.”
Rewrite requires reason old architecture cannot carry future, behaviors to
preserve, first-milestone non-goals, testable migration checkpoints, audit trail.

### Managed DHCP/IPAM Edge Appliance

Early-stage infrastructure example, not completed-product claim. Domain hazard
precedes dashboard. Architecture: server-side source of truth; outbound edge
connection; signed desired-state artifacts; tiny auditable local privileged
apply helper; `dnsmasq` validation+rollback+audit; Pi exposes no inbound
management and no root network-facing daemon; public no-login view is sanitized
published snapshot, not hidden-button admin API. Start with scaffold/trust
boundaries/backend foundation, not production DHCP automation.

### General application

Greenfield: discovery→constitution→bounded first PRs; avoid “make app.” Existing
code/fork/research: inventory value/risk; preserve domain logic; distinguish
prototype/upstream; add privacy/tests/CI/packaging before refactor; prefer
dependency over owned copy. Wrong-shaped system: freeze old as reference,
extract invariants, justify rewrite, rebuild incrementally. Existing serious
system: audit-driven hardening and evidence-based release claims. Academic/domain
software: constitution, inventory/privacy/credentials, tests, CI/packaging,
scientific semantics, release/reproducibility. Private examples inform pattern
but never pretend public URL/evidence.

OAP overhead is excessive for throwaway scripts/prototypes/low-risk personal
utilities/direct edits faster than governance. It is especially valuable for
security constraints, multi-component/long-PR systems, documentation/release
stakes, testable behavior, domain-led work, uncertain architecture/toolchain.

Concept mapping across visible examples: human/domain manager defines invariant;
strategic discovers/translates architecture; constitution prevents shortcuts;
executor supplies bounded PR labor; remote repo/audit archive is truth;
cross-model review→remediation; release language stays honest; tests/docs/
runbooks manage validation debt. Public examples: SLAIF API Gateway, SLAIF
Connect, Managed DHCP/IPAM Edge Appliance; never imply repository maturity beyond
visible evidence.

## 10. Failure modes and doctrine

- Hallucinated APIs/packages (supply-chain risk if attackers publish names):
  verify official docs, imports/runtime, pin/lock; add deps deliberately.
- Shallow tests: require negative/regression behavior, scrutinize mocks.
- Context drift: verify remote, current constitution/handoff; reset executor.
- Weak strategic model: strongest practical model, clean context, explicit
  evidence mapping, cross-model audit, early handoff.
- Control inversion: guest privilege/self-service; no human setup/log courier.
- Excess human reading: brief first, targeted drilldown, small PR, structured
  report.
- Scope creep: explicit non-goals; reject/repair broad diff.
- Overclaiming: controlled vocabulary/checklists/docs/audit.
- Credential leakage: secret-free runtime, scans, placeholders, redaction.
- Human complacency: slow gates, demand proof/external review, every merge human
  management decision.

Core doctrine (all source principles): human moves up ladder; domain expert may
lead; discovery precedes code; human owns intent/risk/release; human gets short
evidence-linked material; strategic strongest long-context control plane;
executor disposable one-PR labor; separate planning/mutation roles;
constitution governs; autonomy only in rebuildable boundary; remote repo truth;
PR unit; non-goals=safety; tests=evidence not ritual; skipped≠passed; docs are
artifact; audit normal; release language honest; velocity never outruns judgment;
executor never pilots human.

Minimum viable OAP: discovery/product shape/stack/trust/scope; constitution;
capable strategy; task branch; order with goal/non-goals/tests/report; focused
tests; PR; strategic decision brief; human evidence interrogation; handoff.
Mature: documented rationale; layered constitutions; dedicated VM; high autonomy
inside hard boundary; safe guest sudo; no production secrets/valuable data;
premium strategy; per-PR executor reset; protected branches; CI/security scans;
external audits; runbooks; readiness scoring/briefs; final verification harness;
archived findings. Adopt via low-risk docs/tests/bugs/strong-test refactors/
internal tools, then features after constitution/runtime/review/brief/CI trust.

Conclusion: responsibility relocates from typing/setup to goals, architecture,
criteria, evidence, risk, release. OAP is not “trust agent”; design a control
system in which agent is useful without final authority.

## 11. Reusable compact templates

Constitution fields: Mission; Discovery(product/domain/architecture/tool rationale/
rejected alternatives/scope/non-goals); Domain vocabulary/workflows/failures;
Architecture/components/data flows; invariants; forbidden actions/secrets;
workflow; local setup; tests; docs; final report.

Coding order fields: read AGENTS/CLAUDE; discovery baseline; verified state;
goal/domain behavior/acceptance/non-goals/files/requirements; setup allowed in
VM+documented; tests/docs; fresh branch/related commit/push/PR/no merge; report
branch/commit/PR/summary/domain/tests/files/setup/docs/skips/safety/risks.

Verification-only:

```text
Do not edit/branch/commit/PR. Verify named commands. Report tested SHA, exact
results/blockers and RESULT=OK|FAIL|ENVIRONMENT_BLOCKED.
```

PR checklist: exact scope; no unrelated files; named tests run; skipped honest;
docs addressed; no secrets/production effects; CI/evidence; limitations; setup;
strategic brief; human understands goal/evidence/risk.

Release checklist: explicit goal/criteria; complete scope; negative/integration/
E2E evidence; aligned docs/runbooks/security; known limitations; rollback;
verification; strategic brief; human acceptance.

## 12. Glossary/source evidence

Agentic software engineering=AI plans/tools/edits/runs/iterates. Execution agent=
repo/runtime implementer. Strategic AI=long-context architecture/planning/review/
memory/evidence layer. Strategic control plane=synthesis of intent/context/report/
evidence/next work. Domain-expert orchestrator=domain-authoritative human manager.
Domain truth=real workflow/vocabulary/users/risks/success. Constitution=durable
repo agent law. Validation debt=proof burden from faster generation. High-
autonomy runtime=broad command ability bounded externally. Rebuildable VM=
disposable guest with durable truth elsewhere. PR-sized delegation=coherent
reviewable unit. Decision brief=recommendation+goal+evidence+risk+decision.
Control inversion=executor directs human through routine low-level work.

Evidence families cited by the source manual: GitHub Copilot/productivity;
SWE-bench paper/repo; SWE-agent paper/repo; HULA; MetaGPT; ChatDev; Codex
AGENTS/security/CLI/best-practice/GitHub docs; Claude CLI/memory docs; Cursor/
Copilot agent instructions; package-hallucination research; end-user engineering/
low-code/AI citizen-development research; SLAIF API Gateway repo/review archive/
Review 6.0/remediation matrix; SLAIF Connect; DHCP/IPAM repository; platform
documentation enumerated in §6. These citations support context and examples;
live official docs/repositories must be reverified when facts can change.
