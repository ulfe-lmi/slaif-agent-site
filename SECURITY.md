# Security policy

## Project status and supported versions

SLAIF Agent-Site is pre-alpha and pre-implementation. No released version is
currently production-supported, and the repository does not yet contain the
runnable application described by the architecture.

Security design claims in [ARCHITECTURE.md](ARCHITECTURE.md) are implementation
requirements, not certification, penetration-test results, or evidence that a
runtime already enforces them.

## Report a vulnerability privately

Please use a
[private GitHub Security Advisory](https://github.com/ulfe-lmi/slaif-agent-site/security/advisories/new)
for suspected vulnerabilities. Include a concise description, affected files
or planned boundary, reproduction information where safe, and potential impact.

If the advisory form cannot be used, send a minimal notification to
[`janez.pers@fe.uni-lj.si`](mailto:janez.pers@fe.uni-lj.si) without exploit
details, credentials, personal data, production data, or other sensitive
material. Use that message only to arrange an appropriate channel for further
details; do not send sensitive vulnerability information through ordinary
email or a public issue.

The project does not promise a response or remediation SLA at this stage.
Reports will be evaluated according to available project capacity and the
current implementation state.

## Safe research boundaries

- Do not test against production systems, third-party systems, or data without
  explicit authorization.
- Do not obtain, retain, or disclose real credentials or personal data.
- Use local fixtures and minimal non-destructive demonstrations.
- Do not publish an unresolved vulnerability before maintainers have had a
  reasonable opportunity to assess it.

Repository CI, CodeQL, policy checks, and architecture review are defenses and
evidence sources; none is a security certification or substitute for future
threat modeling, negative tests, privilege tests, and independent review of the
implemented product.
