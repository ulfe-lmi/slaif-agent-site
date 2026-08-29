# Dependency license policy

SLAIF Agent-Site uses a machine-enforced license and source policy for frozen
Python and npm application dependencies, plus a separate inventory policy for
container operating-system and runtime packages. This is an engineering gate,
not legal advice, legal certification, or a complete license opinion.

The authoritative values are in
[`supply-chain/policy.json`](../supply-chain/policy.json). The generated
[`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md) records every current
Python and npm component, version, scope, license expression or review status,
source, and required attribution note.

## Three distinct review classes

| Class | Gate behavior | Current examples |
| --- | --- | --- |
| Application dependency | Strict automatic SPDX-expression gate; unknown direct or transitive metadata fails. | Python and npm production, development, test, and build closure. |
| Attribution-bearing data or explicit component review | Exact component metadata and attribution must be retained; approval is not generalized to another component. | `caniuse-lite` under CC-BY-4.0; exact MPL-2.0 metadata reviews. |
| Container OS/runtime aggregation | Inventory every package and preserve reported licenses or unknowns for legal review; do not apply the application allowlist as though normal aggregation changed package grants. | Alpine packages, NGINX, Apache, PostgreSQL, Node, and Python runtime contents. |

Fonts will use the attribution-review class when they enter scope. No font
package is currently present. The browser-worker image contains the exact
Apache-2.0 `playwright-core==1.62.1` application dependency and Chromium for
Testing `152.0.7977.64` from Google's exact SHA-256-verified archive over the
reviewed official Playwright dependency image. Firefox
and WebKit product binaries are absent. Browser/Ubuntu runtime metadata and
license facts remain fully inventoried in the container SBOM for human legal
review; passing the application allowlist does not reclassify that aggregation.

## Application allow and review policy

The automatic set is limited to these normalized SPDX expressions:

- `0BSD`;
- `Apache-2.0`;
- `Apache-2.0 OR BSD-2-Clause`;
- `Apache-2.0 OR MIT`;
- `BSD-2-Clause`;
- `BSD-3-Clause`;
- `BlueOak-1.0.0`;
- `ISC`;
- `MIT`;
- `MIT AND PSF-2.0`; and
- `PSF-2.0`.

`CC-BY-4.0` is an attribution-review category, not a generic permissive-code
classification. Its current use is `caniuse-lite` browser compatibility data,
whose source and attribution remain in the generated notice.

`MPL-2.0` requires an exact PURL review entry. Current reviewed instances are
the frozen `certifi` and `pathspec` distributions. The review does not approve
MPL-2.0 for an unrelated component or version.

The gate rejects an unknown license and any unreviewed expression. In
particular, policy prohibits AGPL, SSPL, BUSL/BSL, Elastic License, Commons
Clause, noncommercial, field-of-use, and source-available families. A
prohibited token cannot be placed in an ordinary allow category.

## Sources, scopes, and notices

Python inventory comes from exact `pyproject.toml` requirements, hashed public
PyPI records in `uv.lock`, and frozen installed distribution metadata. The sole
editable record must be the local SLAIF Agent-Site project. npm inventory comes
from exact workspace manifests, the integrity-locked public npm graph, and
`pnpm licenses list`. Production and development scopes remain distinguishable.

Git/VCS, direct URL, unapproved registry, external local/editable path,
workspace escape, package patch, mutable range, and unapproved lifecycle script
inputs fail. Denied hosted/account-bound SDK prefixes and enabled-by-default
telemetry also fail source policy independently of their license.

Generate and check the application notice with the frozen environments:

```bash
uv sync --frozen --all-groups
pnpm install --frozen-lockfile
uv run --frozen python -m tools.supply_chain.policy notices
uv run --frozen python -m tools.supply_chain.policy notices --check
```

CI runs the check form and fails on byte drift. The generated notice does not
copy full license bodies; source links, SPDX expressions, and required notes
support the separate legal review. Project, SLAIF branding, foundation, and
funding notices remain in [`NOTICE`](../NOTICE).

## Container inventory policy

SPDX SBOM evidence inventories OS, runtime, language, and application packages
for every default/reference image. GPL, LGPL, and other OS metadata is not
silently called an approved application library and is not omitted. Missing or
`NOASSERTION` OS metadata is counted in `index.json` as legal-review-required
evidence.

Container aggregation may involve legal obligations different from linking an
application library. This policy records that distinction but does not decide
those obligations. Image publication or production deployment still requires
appropriate human legal and release review.

## Exception governance

[`supply-chain/license-exceptions.json`](../supply-chain/license-exceptions.json)
is empty by default. A human-approved entry must use the common bounded schema
documented in the [supply-chain guide](SUPPLY_CHAIN.md#exceptions-and-updates).
For license matching, `identifier` is the exact reported expression,
`affected` is the exact versioned PURL, and `scope` is the exact dependency
scope. All three must match.

An exception expires within 90 days, cannot contain a wildcard, must link an
exact GitHub review, and never removes inventory or attribution. Automated
agents may validate and report an existing exception but may not create one to
turn a failing build green.

## Review limitations

Metadata can be wrong, incomplete, or legally ambiguous. Passing automation
means only that the frozen inventory matched the source-controlled engineering
policy at that revision. It is not legal advice, a warranty of license
compatibility, a substitute for notices or source-offer obligations, or
authorization to publish an image or deploy this pre-alpha system.
