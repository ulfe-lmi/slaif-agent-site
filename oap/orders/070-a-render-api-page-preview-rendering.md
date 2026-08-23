# OAP Work Order — 070-a

## Objective

Implement actual page rendering in the Render API using the shared renderer
and trusted component catalog so canonical pages and authorized active-workspace
preview pages return fully rendered HTML.

## GitHub objective state

- Numeric objective: `070`; round: `070-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR

## Verified current state

- `render_api/site_http.py` resolves site context only.
- Shared renderer package exists with component implementations.
- No route composes page data + components into HTML output.
- Preview requires workspace context; none implemented.

## Required changes

1. Add `GET /render/v1/pages/{page_id}` internal endpoint that:
   - resolves site, locale, page, composition tree,
   - resolves content item bindings for data-driven components,
   - invokes shared renderer to produce complete HTML document,
   - returns HTML with correct status.
2. Add `GET /render/v1/preview/{workspace_id}/pages/{page_id}` that reads
   through COW overlay (active workspace) instead of canonical.
3. Preview endpoint requires server-derived session token; rejects anonymous.
4. Preview responses include `X-Robots-Tag: noindex, nofollow`.
5. Wire NGINX routes `/render/internal/` (internal only, not externally bound).
6. Integration tests:
   - canonical page with seeded composition renders expected headings/content;
   - workspace edit visible in preview but not canonical;
   - unauthenticated preview request rejected;
   - unknown page/site returns 404.

## Explicit non-goals

- Do NOT implement review snapshot rendering (separate objective).
- Do NOT implement responsive browser screenshots (separate).
- Do NOT modify component catalog definitions.
- Do NOT expose render API externally without edge restriction.

## Acceptance criteria

- Canonical page returns valid HTML containing seeded content.
- Workspace-only changes appear in preview but not canonical.
- Preview is private/noindex/authenticated.
- Existing tests unaffected; new tests pass.

## Report

Publish `oap/reports/070-a-render-api-page-preview-rendering.md` with SELF
report commit parenting implementation SHA.
