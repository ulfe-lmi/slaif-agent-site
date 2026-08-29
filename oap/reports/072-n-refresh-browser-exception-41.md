# OAP Report — 072-n

- Order: `072-n-refresh-browser-exception-41`
- Result: `COMPLETE`
- Delivery: `AMENDED_EXISTING_PR`
- Repository: `ulfe-lmi/slaif-agent-site`
- PR: [#66](https://github.com/ulfe-lmi/slaif-agent-site/pull/66) (OPEN)
- Base: `main` at `082f2359b0c4d59b692580d17992c35d46183b12`
- Branch: `oap/072-browser-worker-real-playwright`
- Starting remote SHA: `e849ea2380ff2056ae724ec957a59c1187209f0c`
- Implementation SHA: `fcf8cf43c889588e7c6818396a740ef59010b00d`
- Report publication parent: `fcf8cf43c889588e7c6818396a740ef59010b00d`

## Delivered

Expanded the exact human-authorized Chrome exception from 31 to 41 Critical
findings. All 41 entries use PURL `pkg:generic/chrome@152.0.7977.64`, scope
`browser-worker`, approver `human:project-owner`, issue #67, created
`2026-08-28`, and expire `2026-09-04`. The ten additions are:

`CVE-2026-79058`, `CVE-2026-79090`, `CVE-2026-79148`, `CVE-2026-79200`,
`CVE-2026-79232`, `CVE-2026-79235`, `CVE-2026-79257`, `CVE-2026-79275`,
`CVE-2026-79282`, and `CVE-2026-79290`.

Updated the exact-set and synthetic 42nd-finding fail-closed tests and supply-
chain documentation. Added a deterministic issue #67 comment explaining
Grype database drift, the complete 41-ID set, unchanged mitigations, and the
removal trigger. No scanner, severity, threshold, dependency, runtime,
dispatcher, route, public artifact, or exception-scope policy was weakened.

## Evidence

- `uv run --frozen pytest tests/supply_chain/test_policy.py tests/supply_chain/test_evidence.py` — 25 passed.
- `python -m unittest tests/repository/test_repository_policy.py` — 44 passed.
- `uv run --frozen ruff check tests/supply_chain tools` and format check — passed.
- Fresh `tools/supply_chain/run.sh /tmp/slaif-072n-supply` — `supply-chain-evidence: OK images=6 critical=41 high=115`, checksum OK, gate OK.
- Deterministic remote issue verification: latest comment states 41 findings and contains the new IDs; local exception file has 41 unique entries and one exact PURL.

The known Compose browser-preview route failure remains assigned to 072-o and
was not rerun or changed. Objective 072 remains `PARTIAL` pending that route
repair and public artifact retrieval. The existing 31-entry browser exception
and issue #67 were refreshed only as ordered; no additional exception scope
was introduced.

## CI and safety

Fresh implementation/report-head checks are required after this push; Compose
is expected to remain red only for the separately bounded route defect. No
extra PR, merge, auto-merge, release, production access, credential exposure,
or artifact publication occurred.

Report publication commit: SELF
