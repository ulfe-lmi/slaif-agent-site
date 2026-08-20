# Installation setup-token and atomic consumer

Revision `008_001` provides the owner-controlled token foundation. Revision
`009_001` adds a semantic Control adapter operation that can atomically consume
a current token in code/tests to create exactly one local Platform
Administrator. It still does **not** add a setup or login HTTP route, browser
session, cookie, CSRF, recent-auth, UI, site, or other online product behavior.
The configured setup URL is served only by the internal Control boundary;
browser UI and public edge wiring remain out of scope.

## Security boundary

- Only `slaif_owner` has direct table access. Control receives execute on two
  narrow owner-created functions for the atomic consumer; every other runtime
  and reviewer role has neither table nor function authority.
- A setup token has the public prefix `slaif_setup_v1_` followed by 256 bits of
  cryptographic randomness encoded without padding.
- PostgreSQL stores only a 32-byte SHA-256 digest plus database-clock issuance
  and expiry timestamps. High token entropy makes a plain digest appropriate;
  this is not a password-hashing design.
- Plaintext exists as a masked `SecretStr` inside the one-shot process and is
  printed only when issue or rotation succeeds. It is never put in the setup
  URL, configuration, database, log field, exception, or status output.
- Issuance, rotation, and revoke each lock the singleton row in one database
  transaction. The semantic consumer locks and rechecks that row, creates the
  user/assignment, initializes once, and clears all token fields in the same
  transaction. Invalid, expired, revoked, replayed, or conflicting attempts
  fail through one constant result and do not partially consume the token.

## Configuration

Supply the normal production bootstrap owner settings documented in
[configuration](CONFIGURATION.md). Two bounded settings apply here:

| Variable | Default | Contract |
| --- | --- | --- |
| `SLAIF_BOOTSTRAP_SETUP_TOKEN_TTL_MINUTES` | `30` | Integer from 5 through 60; expiry uses the PostgreSQL clock. |
| `SLAIF_BOOTSTRAP_SETUP_URL` | `http://localhost:8080/setup` | Absolute HTTP(S) `/setup` URL without credentials, query, or fragment. |

The token itself has no configuration variable or file input.

## Explicit commands

Default ensure issues a token only when no unexpired token exists:

```bash
python -m slaif_agent_site.bootstrap setup-token
```

Fresh issuance prints bounded status, `setup-url: ...`, and exactly one
`setup-token-secret: ...` line. Capture that stdout only through an
operator-approved secret channel. If an unexpired token already exists, ensure
does not rotate or reveal it; output contains only facts and guidance to use an
explicit rotation if the original plaintext was lost.

```bash
python -m slaif_agent_site.bootstrap setup-token --rotate
python -m slaif_agent_site.bootstrap setup-token --revoke
python -m slaif_agent_site.bootstrap setup-token --status
```

Rotation atomically invalidates the previous digest, advances generation, and
prints the replacement plaintext once. Revoke is idempotent, clears token
material, and does not initialize the installation. Status exposes only
initialized, token-present, token-expired, expiry, and generation facts.
Options are mutually exclusive. Failures emit only
`Database bootstrap failed.` on stderr.

The safe check remains separate and cannot load database settings, generate
randomness, connect, mutate state, or print a secret:

```bash
python -m slaif_agent_site.bootstrap --check
```

Do not place command output in a URL, shell history argument, ticket, log,
screenshot, trace, or repository. No endpoint consumes the token. Only the
typed Control adapter consumes it today, and that behavior is available in
code/tests rather than an operator-facing browser flow. See
[local authentication](LOCAL_AUTHENTICATION.md) for identity, password, and
transaction details.
