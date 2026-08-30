# OAP Work Order — 076-p strategic restart repair

AMEND_EXISTING_PR #72 only, required start report head
`43f1b50b31f8fd019d4d46193256d748181a3396`, parent implementation
`5ccc94ca13527357cb7278ff166a117f330e8c61`, base/main
`0e83b26bf9a9f63bff6756d65cbfd527d215ec51`. Human-authorized direct strategic
repair; launch/signal no agent and do not merge.

## Verified root cause

Current-head CI Compose job `99334415830` and two local clean reproductions pass
all 11 Playwright projects, then fail `public-agent-restart` with 404. A
preserved diagnostic stack proved Docker swapped Control/Agent edge-network IPs
on simultaneous restart: NGINX had cached Agent=`172.20.0.2` and
Control=`172.20.0.6`; afterward those addresses belonged to Control and Agent
respectively. Static `proxy_pass http://service-name` upstream resolution sent
Agent traffic to Control. Generic readiness paths both returned 200 through the
cross-wire, masking it. The 404 body was the bounded application HTTP error; no
token leaked.

## Required repair

- Configure the NGINX OSS Compose edge to use Docker DNS `127.0.0.11` with
  bounded re-resolution and named shared-zone upstreams whose service servers
  use `resolve`. Apply consistently to Control, Editor, Agent, MCP, Media and
  Web; preserve every existing path rewrite/prefix, headers, body limit,
  buffering and denial rule.
- Strengthen the public restart readiness loop to require both HTTP 200 and the
  correct `service` identity (`control-api` and `agent-api`) so swapped/wrong
  upstreams cannot masquerade as ready.
- Update exact NGINX/Apache route-contract tests for named dynamic NGINX
  upstreams while keeping Apache behavior unchanged, and add explicit resolver,
  zone, `resolve`, route-preservation and wrong-service readiness assertions.

Run repository/packaging tests, Python static checks, NGINX image/config test,
then the exact clean Compose smoke once. No dependency, application authority,
migration, API, architecture, prior transcript, or unrelated deployment change.

Publish `oap/reports/076-p-fix-nginx-restart-routing.md` as report-only child
of literal implementation SHA with exact local/CI evidence, human-authorized
strategic exception, SELF, no agent/FIFO/new PR/merge/secrets or post-report
push.
