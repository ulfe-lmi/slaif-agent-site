# Local identity and password boundary

Revision `009_001` establishes the persistence and semantic service needed to
create the first local Platform Administrator. This boundary is callable in
application code and covered by unit and disposable-PostgreSQL tests. It is
not exposed by an HTTP route, so local authentication is not yet usable from a
browser.

## Local identity contract

A local username uses the ASCII grammar
`[A-Za-z][A-Za-z0-9._-]{2,62}`. Its immutable identity key is the lowercase
form produced identically by Python and PostgreSQL. Display name and optional
email are mutable profile fields, not identity keys. Platform Administrator is
a separate installation-level assignment rather than a site role.

The schema also reserves an `OIDC` identity shape whose immutable key is the
unique `(issuer, subject)` pair. OIDC rows cannot carry a local username or
password hash, and email is never the federated identity key. There is no OIDC
discovery, client, callback, token validation, configuration, or network call
in this implementation.

## Password hashing

The exact runtime dependency is `argon2-cffi==25.1.0`, resolved from PyPI and
locked with artifact hashes. It is MIT licensed; the bindings and new
transitive license inventory are recorded in `THIRD_PARTY_NOTICES.md`.

Production constructs `PasswordHasher` from `RFC_9106_LOW_MEMORY`. The encoded
hash therefore uses Argon2id version 19 with time cost 3, memory cost 65,536
KiB, parallelism 4, a 16-byte random salt, and a 32-byte hash. Each concurrent
hash operation can require roughly 64 MiB for its memory cost; operators must
budget Control-process concurrency accordingly. Tests may inject an explicitly
test-owned cheaper hasher, but configuration and environment variables cannot
lower the production profile.

Passwords arrive at the semantic boundary as masked `SecretStr` values. The
policy requires 12 through 1,024 characters, at most 4,096 UTF-8 bytes, no NUL,
and inequality to the normalized username. It deliberately imposes no
mandatory character classes. Only the self-describing Argon2id hash reaches a
database parameter. Verification returns a stable boolean, and
`check_needs_rehash` provides the later login-time upgrade decision. Errors,
representations, and serialized request/results omit plaintext. Python strings
are immutable, so this implementation makes no claim that plaintext can be
securely wiped from process memory.

## Atomic first-administrator operation

The Control database adapter exposes one typed operation. It validates and
hashes before opening the locked transaction, then:

1. calls an owner-created function that locks the installation singleton and
   returns only initialized/expiry/generation state plus its stored digest;
2. compares the presented token in application code using the setup-token
   helper backed by `secrets.compare_digest`;
3. calls a second narrow function in the same transaction, with generation
   and digest race guards;
4. inserts one active `LOCAL` account and one Platform Administrator
   assignment; and
5. sets the database-clock initialization time and clears all token material.

Both functions are `SECURITY DEFINER`, owned by `slaif_owner`, fixed to
`search_path=pg_catalog`, fully qualify objects, revoke `PUBLIC`, and grant
execution only to `slaif_control`. Control and all other service roles have no
direct access to the identity, assignment, installation, or password-hash
tables. Malformed, invalid, expired, revoked, replayed, initialized, and
constraint-conflicting attempts share one public-safe failure. Cancellation or
any database error rolls the complete transaction back.

## Deliberately deferred

There is no `/setup`, `/login`, `/logout`, user-management, or other product
HTTP route. Server-side sessions, cookies, CSRF protection, expiry, and
recent-auth remain for 010-c. The setup/login UI plus NGINX and default Compose
operator flow remain for 010-d. Setup-token issuance is still explicit and is
never part of default startup.
