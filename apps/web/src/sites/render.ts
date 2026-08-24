import "server-only";

import { renderServiceHeaders } from "./service-auth";

const RENDER_CONTEXT_URL = "http://render-api:8000/internal/render/v1/site-context";
const RENDER_PAGE_URL = "http://render-api:8000/internal/render/v1/page";
const RENDER_PREVIEW_URL = "http://render-api:8000/internal/render/v1/preview";

export type SiteContext = Readonly<{
  site_id: string;
  site_key: string;
  canonical_revision: number;
  default_locale: string;
  matched_hostname: string;
  matched_path_prefix: string;
}>;

export type ProjectionNode = Readonly<{
  id: string;
  component_type: string;
  schema_version: string;
  parent_id: string | null;
  slot_key: string;
  order_key: number;
  props: Record<string, unknown>;
  children: readonly ProjectionNode[];
}>;

export type PageProjection = Readonly<{
  render_mode: "canonical" | "preview";
  site: { id: string; key: string; canonical_revision: number };
  requested_path: string;
  matched_path: string;
  locale: string;
  page: {
    id: string;
    site_id: string;
    slug: string;
    title: string;
    status: string;
    locale: string;
    row_version: number;
  };
  composition: {
    schema_version: string;
    catalog_version: string;
    nodes: readonly ProjectionNode[];
  };
  theme: Record<string, unknown>;
  navigation: readonly Record<string, unknown>[];
  bindings: Record<string, readonly Record<string, unknown>[]>;
}>;

export async function resolveSiteContext(
  authority: string,
  path: string,
): Promise<SiteContext | null> {
  const signal = AbortSignal.timeout(1500);
  try {
    const response = await fetch(RENDER_CONTEXT_URL, {
      method: "POST",
      cache: "no-store",
      credentials: "omit",
      headers: {
        "content-type": "application/json",
        ...(await renderServiceHeaders()),
      },
      body: JSON.stringify({ authority, path }),
      signal,
    });
    if (!response.ok) return null;
    return (await response.json()) as SiteContext;
  } catch {
    return null;
  }
}

export async function renderReady(): Promise<boolean> {
  try {
    const response = await fetch(RENDER_CONTEXT_URL, {
      method: "POST",
      cache: "no-store",
      credentials: "omit",
      headers: {
        "content-type": "application/json",
        ...(await renderServiceHeaders()),
      },
      body: JSON.stringify({ authority: "readiness.invalid", path: "/health" }),
      signal: AbortSignal.timeout(1500),
    });
    return response.status === 404;
  } catch {
    return false;
  }
}

async function resolveProjection(
  url: string,
  body: Record<string, unknown>,
  sessionToken?: string,
): Promise<PageProjection | null> {
  try {
    const headers: Record<string, string> = {
      "content-type": "application/json",
      ...(await renderServiceHeaders()),
    };
    if (sessionToken) headers["x-slaif-human-session"] = sessionToken;
    const response = await fetch(url, {
      method: "POST",
      cache: "no-store",
      credentials: "omit",
      headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(2500),
    });
    if (!response.ok) return null;
    return (await response.json()) as PageProjection;
  } catch {
    return null;
  }
}

export function resolveCanonicalPage(
  authority: string,
  path: string,
  locale?: string,
): Promise<PageProjection | null> {
  return resolveProjection(RENDER_PAGE_URL, { authority, path, locale });
}

export function resolvePreviewPage(
  authority: string,
  path: string,
  workspaceId: string,
  sessionToken: string,
  locale?: string,
): Promise<PageProjection | null> {
  return resolveProjection(
    RENDER_PREVIEW_URL,
    { authority, path, workspace_id: workspaceId, locale },
    sessionToken,
  );
}
