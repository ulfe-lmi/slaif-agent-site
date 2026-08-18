# Installation setup-token foundation

Revision `008_001` provides only the owner-controlled foundation for a future
first-user setup flow. It creates one constrained
`control.installation_state` row and adds an explicit one-shot bootstrap
command. It does **not** create a user, password, browser session, setup route,
administrator, site, or online authentication behavior. The configured
`/setup` URL is not served by this revision; that operator experience remains
planned work.

## Security boundary

- Only the one-shot `slaif_owner` connection reads or changes installation
  state. Control and every other runtime/reviewer role have no table access.
- A setup token has the public prefix `slaif_setup_v1_` followed by 256 bits of
  cryptographic randomness encoded without padding.
- PostgreSQL stores only a 32-byte SHA-256 digest plus database-clock issuance
  and expiry timestamps. High token entropy makes a plain digest appropriate;
  this is not a password-hashing design.
- Plaintext exists as a masked `SecretStr` inside the one-shot process and is
  printed only when issue or rotation succeeds. It is never put in the setup
  URL, configuration, database, log field, exception, or status output.
- Issuance, rotation, and revoke each lock the singleton row in one database
  transaction. An initialized installation fails closed, although no command
  in this revision can mark it initialized.

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
screenshot, trace, or repository. No current endpoint consumes the token; the
future atomic first-user creation boundary will own verification and
initialization.
