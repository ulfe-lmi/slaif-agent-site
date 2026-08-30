# OAP Report — 076-p strategic restart repair

ID: 076-p  
Order: `oap/orders/076-p-fix-nginx-restart-routing.md`  
Result: COMPLETE  
Delivery: HUMAN-AUTHORIZED_STRATEGIC_AMENDMENT_OF_EXISTING_PR

Repository: `ulfe-lmi/slaif-agent-site`  
PR: [#72](https://github.com/ulfe-lmi/slaif-agent-site/pull/72) (OPEN)  
Base: `main` (`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`)  
Branch: `oap/076-agent-model-content-semantics`  
Starting report head: `43f1b50b31f8fd019d4d46193256d748181a3396`  
Implementation head SHA: `1a74ae193ef9ca835b5420b6d671491dde0a755d`  
Report publication commit: SELF

## Root cause

CI Compose job `99334415830` and two local clean reproductions passed all 11
Playwright projects and then returned 404 from the Agent session after restarting
Control and Agent together. A preserved diagnostic stack proved Docker swapped
the services' edge-network IPs: NGINX retained its startup mapping of Agent to
`172.20.0.2` and Control to `172.20.0.6`, while those addresses belonged to
Control and Agent after restart. Static upstream DNS caching therefore sent
Agent requests to Control. Both generic readiness endpoints returned 200 through
the cross-wire, falsely declaring the edge ready. The bounded 404 body contained
no bearer token.

## Implementation

- NGINX OSS now uses Docker DNS `127.0.0.11`, a five-second validity/timeout,
  and six named shared-zone upstreams with `resolve` for Control, Editor, Agent,
  MCP, Media and Web.
- All existing health rewrites, versioned prefix preservation, MCP/Media prefix
  stripping, body limits, headers, buffering and deny rules are unchanged.
- Restart readiness now parses each response and requires exact service identity
  (`control-api` and `agent-api`) in addition to HTTP 200, so cross-wiring cannot
  masquerade as ready.
- Packaging tests verify the resolver, every zone/server/resolve tuple, route
  preservation, Apache equivalence and wrong-service readiness rejection.

## Verification

- Ruff check and format check on changed Python — passed.
- Targeted restart/edge tests — `13 passed in 0.08s`.
- Full repository/packaging suite — `104 passed, 61 subtests passed in 2.72s`.
- `python tools/compose/verify.py --root .` — `compose-policy: OK`.
- Rebuilt NGINX 1.29.7 image `nginx -t` — syntax and configuration successful.
- First clean local smoke after the repair proved the target behavior:
  `agent-before=200`, `agent-after-restart=200`, `agent-after-revoke=401`, and
  three exact audit rows. That run later encountered a separate browser-attempt
  failure and was not called a full pass.
- Exact current implementation-head CI run `33341551846` — every job passed,
  including Compose and edge packaging in 8m16s, PostgreSQL 14–18, Python
  3.12–3.14, Node, supply-chain, repository policy, Markdown, Mermaid and
  dependency review.
- CodeQL run `33341551861` — all Python, Actions and JavaScript/TypeScript
  analyses passed.
- `git diff --check` — passed.

## Scope and authority

The human explicitly authorized direct strategic repair after the executor-
control failure. No agent was launched, queued, resumed, or signaled; there
were zero FIFO readers. No application authority, migration, dependency,
architecture, prior transcript, second PR, merge, production system, secret,
capability, cookie, or credential changed. Objective 076 remains open beyond
this recovery.

Report publication commit: SELF
