# Contract boundaries

The product domain packages under `packages/` own the source definitions for
their respective contracts. This directory does not duplicate those models or
infer compatibility between independently handwritten Python and TypeScript
types.

Architecture Section 12 plans versioned `json-schema/`, `openapi/`, `mcp/`, and
`generated/` directories once real domain contracts and their generators
exist. Generation will be deterministic, and CI will regenerate and reject
tracked drift. Generated artifacts will never be edited manually.

None of those generated directories or artifacts exists yet. Python and
TypeScript schema parity will be introduced with the relevant product-domain
contracts and tested from their shared source of truth; it is not asserted by
the current placeholders.

The seven workspace packages are private package boundaries only. Their sole
export identifies a pre-alpha scaffold. They do not implement product APIs,
schemas, scopes, components, browser tools, HTTP behavior, or fixture data.
