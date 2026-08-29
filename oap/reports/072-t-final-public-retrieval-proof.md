# OAP execution report — 072-t

- Order: `072-t-final-public-retrieval-proof`
- Publication: `AMENDED_EXISTING_PR`
- Result: `COMPLETE`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66)
- PR state: `OPEN`, never merged
- Base: `main`
- Head: `oap/072-browser-worker-real-playwright`
- Starting remote SHA: `8fa508daf5d71ed6edbc4a82d5c04432c4d57a5b`
- Implementation SHA: `8f6928829b0b52ce298dd6a14e66bfd84bbf2d79`
- Report publication commit: `SELF`
- Pushed implementation commit: `8f6928829b0b52ce298dd6a14e66bfd84bbf2d79`

## Changes

- Extended the existing NGINX Compose smoke to prove one deterministic
  `browser-worker` stop/start outage block: public artifact retrieval must be
  503 without binding leakage, canonical output remains 200 and overlay-free,
  recovery serves the same retained bytes, and the formerly authorized Agent
  capability is revoked at fixture end and denied with 401. Foreign capability
  and random IDs remain non-leaking 404s.
- Kept all product code, schema, grants, worker runtime, credentials, and
  artifact files unchanged; only the proof harness and transcript were
  modified for t.

## Evidence

- Final local command: `sudo sh tools/compose/smoke.sh slaif071z`; exit status
  `0`. The captured run proves `browser-artifact-public: OK runs=2
  artifacts=6 bytes=verified`, random and foreign-capability `404`, worker
  restart retention, a worker-only outage with `503` and canonical `200`, no
  partial bytes/internal artifact details, byte-identical recovery, and final
  revocation with valid-token `401` and absent bytes. It ends with `Ran 45
  tests ... OK` and `compose-smoke: OK`.
- Earlier local retries are retained as evidence: one pre-final run exposed an
  unstable structure assertion and several outage probes ended before a `503`.
  The bounded harness was repaired, then the final `slaif071z` replay passed
  every required proof; no product/runtime code was changed.
- Focused checks pass: `sh -n tools/compose/smoke.sh`, Compose contract tests
  (7), public retrieval/service tests (5), repository policy, Mermaid (16
  diagrams), Markdown, and packaging checks.
- Objective 072 predecessor gates remain green: backend unit suite `600 passed`
  plus `26 subtests`, integration `111 passed`, and Node 24.14.1 / pnpm
  11.22.0 lint, format, typecheck, test, build, and license checks.
- The immediately preceding report head had successful CI run `33275472190` and
  CodeQL run `33275472195`; fresh checks for this publication are verified
  after push and recorded in the execution handoff.

## Required confirmations

- Scope: only Compose proof/test harness and transcript; no Agent/worker/Web/
  Render product code, migration/grant, dependency, exception, GC/source/
  review/promotion, second PR, merge, auto-merge, or release changes.
- Secrets, capabilities, cookies, internal IDs, storage paths, and artifact
  bytes were not committed or logged; production systems/data were not
  accessed.
- No required check was intentionally skipped. Strategy retains acceptance and
  merge authority. Objective 072 is `COMPLETE`; this records implementation
  evidence only and does not accept or merge the objective PR.
