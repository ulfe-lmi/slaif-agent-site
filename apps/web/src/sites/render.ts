import "server-only";

import { getRedirectError } from "next/dist/client/components/redirect";
import { RedirectStatusCode } from "next/dist/client/components/redirect-status-code";

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

export type ProjectionLocale = Readonly<{
  id: string;
  site_id: string;
  tag: string;
  enabled: true;
  is_default: boolean;
  position: number;
  metadata: Record<string, unknown>;
}>;

export type ProjectionNavigationItem = Readonly<{
  id: string;
  site_id: string;
  navigation_id: string;
  parent_id: string | null;
  page_id: string | null;
  locale: string | null;
  position: number;
  label: string;
  labels: Record<string, unknown>;
  target: Readonly<{
    kind: "PAGE" | "INTERNAL" | "EXTERNAL";
    value: string;
  }>;
  children: readonly ProjectionNavigationItem[];
}>;

export type ProjectionNavigation = Readonly<{
  id: string;
  site_id: string;
  key: string;
  label: string;
  labels: Record<string, unknown>;
  settings: Record<string, unknown>;
  items: readonly ProjectionNavigationItem[];
}>;

export type PageProjection = Readonly<{
  route_kind: "page";
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
    parent_id: string | null;
    route_template: string | null;
    effective_route: string;
    row_version: number;
  };
  composition: {
    schema_version: string;
    catalog_version: string;
    nodes: readonly ProjectionNode[];
  };
  theme: Record<string, unknown>;
  locales: readonly ProjectionLocale[];
  navigation: readonly ProjectionNavigation[];
  bindings: Record<string, readonly Record<string, unknown>[]>;
}>;

export type RedirectProjection = Readonly<{
  route_kind: "redirect";
  render_mode: "canonical" | "preview";
  site: { id: string; key: string; canonical_revision: number };
  requested_path: string;
  matched_path: string;
  locale: string;
  locales: readonly ProjectionLocale[];
  redirect: Readonly<{
    source: string;
    target: string;
    status_code: 301 | 302 | 303 | 307 | 308;
    locale: string | null;
  }>;
}>;

export type RenderProjection = PageProjection | RedirectProjection;

export class RenderResolutionError extends Error {
  readonly status: number;

  constructor(status: number) {
    super(`Render resolution failed with status ${status}.`);
    this.name = "RenderResolutionError";
    this.status = status;
  }
}

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
    if (response.status === 404) return null;
    if (!response.ok) throw new RenderResolutionError(response.status);
    return (await response.json()) as SiteContext;
  } catch (error) {
    if (error instanceof RenderResolutionError) throw error;
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
  credentials?: Readonly<{
    humanSessionToken?: string;
    browserToken?: string;
  }>,
): Promise<RenderProjection | null> {
  try {
    const headers: Record<string, string> = {
      "content-type": "application/json",
      ...(await renderServiceHeaders()),
    };
    if (credentials?.humanSessionToken)
      headers["x-slaif-human-session"] = credentials.humanSessionToken;
    if (credentials?.browserToken)
      headers["x-slaif-browser-run-token"] = credentials.browserToken;
    const response = await fetch(url, {
      method: "POST",
      cache: "no-store",
      credentials: "omit",
      headers,
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(2500),
    });
    if (response.status === 404) return null;
    if (!response.ok) throw new RenderResolutionError(response.status);
    return (await response.json()) as RenderProjection;
  } catch (error) {
    if (error instanceof RenderResolutionError) throw error;
    return null;
  }
}

export function resolveCanonicalPage(
  authority: string,
  path: string,
  locale?: string,
): Promise<RenderProjection | null> {
  return resolveProjection(RENDER_PAGE_URL, { authority, path, locale });
}

export function resolvePreviewPage(
  authority: string,
  path: string,
  workspaceId: string,
  credentials: Readonly<{
    humanSessionToken?: string;
    browserToken?: string;
    browserRoute?: string;
  }>,
  locale?: string,
): Promise<RenderProjection | null> {
  return resolveProjection(
    RENDER_PREVIEW_URL,
    {
      authority,
      path,
      workspace_id: workspaceId,
      locale,
      ...(credentials.browserRoute ? { browser_route: credentials.browserRoute } : {}),
    },
    credentials,
  );
}

export function isRedirectProjection(
  projection: RenderProjection,
): projection is RedirectProjection {
  return projection.route_kind === "redirect";
}

export function redirectProjection(projection: RedirectProjection): never {
  throw getRedirectError(
    projection.redirect.target,
    "replace",
    projection.redirect.status_code as RedirectStatusCode,
  );
}
