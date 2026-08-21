/**
 * Agent delegation scope catalog.
 *
 * Architecture reference: ARCHITECTURE-for-agents.md §5 (Human RBAC and
 * agent delegation). Scope strings are exact identifiers used by the
 * server-side authorization layer; clients must never construct or mutate
 * these values at runtime.
 */

export const AGENT_READ_SCOPES = [
  "site:read",
  "content-model:read",
  "content-item:read",
  "collection-view:read",
  "page:read",
  "composition:read",
  "navigation:read",
  "translation:read",
  "media:read",
  "theme:read",
  "redirect:read",
  "component-catalog:read",
  "preview:inspect",
  "validation:read",
] as const;

export const AGENT_L1_WRITE_SCOPES = [
  "content-item:create",
  "content-item:write",
  "content-item:delete",
  "translation:write",
  "media:upload",
  "media-metadata:write",
  "media-reference:delete",
  "component-content-props:write",
  "seo:write",
  "preview:inspect",
] as const;

export const AGENT_L2_WRITE_SCOPES = [
  "page:create",
  "page:write",
  "page:delete",
  "page:restore",
  "page:move",
  "route:write",
  "redirect:create",
  "redirect:write",
  "redirect:delete",
  "navigation:create",
  "navigation:write",
  "navigation:delete",
  "collection-view:create",
  "collection-view:write",
  "collection-view:delete",
  "component-structure:create",
  "component-structure:delete",
  "component-structure:move",
  "relationship:write",
] as const;

export const AGENT_L3_WRITE_SCOPES = [
  "composition:write",
  "component-props:write",
  "component-variant:write",
  "layout:write",
  "responsive-design:write",
  "page-style:write",
  "theme-tokens:write",
  "preview:responsive-sweep",
] as const;

export const AGENT_L4_WRITE_SCOPES = [
  "content-model:create",
  "content-model:write",
  "content-model:delete",
  "field-definition:create",
  "field-definition:write",
  "field-definition:delete",
  "content-model:mapping",
  "site-structure:write",
  "global-region:create",
  "global-region:write",
  "global-region:delete",
  "header-footer:write",
  "theme-global:write",
  "locale:configure",
  "site-import:validate",
  "site-import:apply",
  "source:inspect",
  "site-reset:workspace",
] as const;

export type AgentScope = (typeof AGENT_READ_SCOPES)[number];

export const DELEGATION_LEVELS = {
  1: [...AGENT_READ_SCOPES, ...AGENT_L1_WRITE_SCOPES],
  2: [...AGENT_READ_SCOPES, ...AGENT_L1_WRITE_SCOPES, ...AGENT_L2_WRITE_SCOPES],
  3: [
    ...AGENT_READ_SCOPES,
    ...AGENT_L1_WRITE_SCOPES,
    ...AGENT_L2_WRITE_SCOPES,
    ...AGENT_L3_WRITE_SCOPES,
  ],
  4: [
    ...AGENT_READ_SCOPES,
    ...AGENT_L1_WRITE_SCOPES,
    ...AGENT_L2_WRITE_SCOPES,
    ...AGENT_L3_WRITE_SCOPES,
    ...AGENT_L4_WRITE_SCOPES,
  ],
} as const;
