# Local identity and password boundary

Revision `009_001` establishes local identity, revision `010_001` adds the
server-side human-session persistence, and revision `011_001` adds the
Control-only local credential lookup/rehash boundary. These boundaries
are callable in application code and covered by unit and disposable-
PostgreSQL tests. They are not exposed by an HTTP route, so local
authentication is not yet usable from a browser.

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

## Local credential authentication

`LocalAuthenticationService` accepts a bounded username and masked `SecretStr`
password. Control calls an owner-defined lookup function returning only the
active local account UUID, normalized username, Argon2id hash, and status.
Active candidates take the real Argon2 verifier; absent, disabled, OIDC, and
malformed candidates take the same fixed production-profile dummy verifier.
Every denial raises the constant `Local login failed.` error and never exposes
account status, hash, or database details.

When a valid hash needs the current profile, the service hashes the already
verified password without reapplying account-creation policy, then uses a
Control-only compare-and-set guarded by user ID, LOCAL identity, ACTIVE status,
and the exact old hash. A failed race is a denial. The memory-hard verifier
runs outside database transactions; cancellation propagates and no session is
issued. Perfect network timing equality is not claimed.

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

## Human sessions and CSRF foundation

Revision `010_001` creates the non-COW `control.user_session` relation. It
stores only a `sas2_` public lookup ID, 32-byte SHA-256 session and CSRF
digests, the active user UUID, database-clock creation/last-seen/absolute-
expiry/recent-auth timestamps, and nullable revocation time. The user foreign
key is `ON DELETE RESTRICT`; expiry and user indexes support bounded cleanup
and lookup. No plaintext session or CSRF value, recoverable token, cookie, or
browser storage value enters PostgreSQL.

The owner-created functions `slaif_create_human_session`,
`slaif_inspect_human_session`, `slaif_finalize_human_session`,
`slaif_finalize_state_changing_human_session`, and
`slaif_revoke_human_session` are fully
qualified `SECURITY DEFINER` functions with fixed `search_path=pg_catalog`.
They revoke `PUBLIC` and grant execution only to `slaif_control`; every other
Control/runtime/reviewer role has no direct relation or function authority.
Creation requires an already-authenticated active user and sets issuance times
from the database clock. Inspection locks only the public-ID row and returns
defense digests to the Control service without authority or mutation. Safe and
state-changing finalizers recheck all database conditions after application
comparison; the latter checks both digests, active-user state, revocation, idle
expiry, and absolute expiry while locking the row. They touch `last_seen_at`
only after the configured interval and never refresh `recent_auth_at`. Revoke
rechecks both digests and is externally idempotent. The typed service keeps
the row lock in one transaction while `secrets.compare_digest` checks stored
fixed-size defense digests before any touch/revoke or authority; PostgreSQL
rechecks the digests in the finalizer.

The typed service uses versioned boundary formats
`sas2_session_<32-hex-id>_<base64url-secret>` and
`sas2_csrf_<base64url-secret>`. Each secret is 256 bits from `secrets`; only
SHA-256 digests cross the database boundary and malformed, unknown, wrong,
expired, disabled, revoked, and cross-session credentials return the same
`HumanSessionError`. Safe reads use `authenticate`; state-changing calls use
`authenticate_state_changing` and require the session-bound CSRF credential;
`revoke` requires it as well.
Issued values are masked `SecretStr` fields and are never part of repr,
serialization, exceptions, logs, URLs, or audit data.

`HumanSessionPolicy` enforces `0 < touch < idle < absolute` and
`0 < recent-auth <= absolute`, with bounded defaults of 300 seconds, 1,800
seconds, 28,800 seconds, and 900 seconds respectively. `SessionCookiePolicy`
defines future handlers' HTTP-only, `SameSite=Lax`, `Path=/`, no-Domain cookie;
production uses `Secure` and `__Host-slaif_session`, while local development
uses a non-Secure `slaif_session` variant. `Max-Age` never exceeds absolute
session lifetime. CSRF is a separately presented credential required for
future state-changing cookie-authenticated Control calls. This round emits no
HTTP response and adds no route or browser storage.

## Deliberately deferred

There is no `/setup`, `/login`, `/logout`, user-management, or other product
HTTP route. The server-side session/CSRF foundation is now present, but HTTP
authentication, cookie emission, setup/login UI, NGINX, default Compose
operator flow, OIDC, MFA, and security-event audit remain future work.
Credential verification is an internal boundary only: no session issuance,
rate limiting, login audit, or UI is implemented. Setup-token issuance is still
explicit and is never part of default startup.
