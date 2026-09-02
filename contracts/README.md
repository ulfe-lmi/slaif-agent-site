# Contract boundaries

The product domain packages under `packages/` own the source definitions for
their respective contracts. This directory does not duplicate those models or
infer compatibility between independently handwritten Python and TypeScript
types.

## Canonical Agent OpenAPI

`openapi/agent-v1.json` is the one committed generated product contract for
the capability-bound Agent REST surface. It is generated from the production
FastAPI handlers, request/response models, and route-policy registry; it is
never edited by hand.

Regenerate it from the repository root with:

```bash
uv run --frozen python -m tools.contracts.generate_agent_openapi
```

The deterministic drift check is:

```bash
uv run --frozen python -m tools.contracts.generate_agent_openapi --check
```

The check fixes OpenAPI 3.1 metadata, stable JSON ordering/newline, bearer
security semantics, route scope extensions, required mutation headers, and
stable error envelopes. It exposes only `/api/agent/v1` paths. Interactive
Swagger/ReDoc and generic FastAPI OpenAPI routes remain disabled.

The seven workspace packages are private package boundaries only. Their sole
export identifies a pre-alpha scaffold. They do not implement product APIs,
schemas, scopes, components, browser tools, HTTP behavior, or fixture data.
