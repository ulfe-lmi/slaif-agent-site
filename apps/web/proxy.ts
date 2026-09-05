import type { NextRequest } from "next/server";
import { normalizeBrowserPreviewRoute } from "@slaif-agent-site/browser-tool-contracts";

import {
  isRedirectProjection,
  resolveCanonicalPage,
  resolvePreviewPage,
} from "./src/sites/render";

const WORKSPACE_ID = /^[0-9a-f-]{36}$/iu;
const AUTHORITY = /^[a-z0-9.-]+(?::[1-9][0-9]{0,4})?$/u;
const RESERVED =
  /^\/(?:admin|api|agent|control|editor|health|internal|login|logout|mcp|media|setup|_next|static)(?:\/|$)/u;

function isLoopbackAuthority(authority: string): boolean {
  const hostname = authority.split(":", 1)[0]?.replace(/^\[|\]$/gu, "");
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1";
}

function previewRoute(request: NextRequest): {
  workspaceId: string;
  path: string;
} | null {
  const match = request.nextUrl.pathname.match(/^\/preview\/([^/]+)(\/.*)?$/u);
  if (!match || !WORKSPACE_ID.test(match[1] ?? "")) return null;
  return { workspaceId: match[1]!, path: match[2] || "/" };
}

export async function proxy(request: NextRequest): Promise<Response | undefined> {
  if (request.method !== "GET" && request.method !== "HEAD") return;

  const preview = previewRoute(request);
  if (preview) {
    const session =
      request.cookies.get("__Host-slaif_session")?.value ??
      request.cookies.get("slaif_session")?.value;
    const browserToken = request.headers.get("x-slaif-browser-preview");
    if ((session && browserToken) || (!session && !browserToken)) return;

    const browserAuthority = process.env.SLAIF_BROWSER_PREVIEW_AUTHORITY;
    if (browserToken && (!browserAuthority || !AUTHORITY.test(browserAuthority)))
      return;

    const browserRoute = normalizeBrowserPreviewRoute(
      request.nextUrl.search
        ? `${preview.path}?${request.nextUrl.search.slice(1)}`
        : preview.path,
    );
    try {
      const projection = await resolvePreviewPage(
        browserToken ? browserAuthority! : (request.headers.get("host") ?? ""),
        browserRoute.split("?", 1)[0] ?? browserRoute,
        preview.workspaceId,
        browserToken ? { browserToken, browserRoute } : { humanSessionToken: session! },
      );
      if (
        projection &&
        isRedirectProjection(projection) &&
        (projection.redirect.status_code === 301 ||
          projection.redirect.status_code === 302)
      ) {
        return Response.redirect(
          new URL(projection.redirect.target, request.url),
          projection.redirect.status_code,
        );
      }
    } catch {
      // The page route remains authoritative for normal rendering and errors.
    }
    return;
  }

  if (request.nextUrl.pathname !== "/" && RESERVED.test(request.nextUrl.pathname))
    return;
  if (
    request.nextUrl.pathname === "/" &&
    isLoopbackAuthority(request.headers.get("host") ?? "")
  )
    return;

  try {
    const projection = await resolveCanonicalPage(
      request.headers.get("host") ?? "",
      request.nextUrl.pathname,
    );
    if (
      projection &&
      isRedirectProjection(projection) &&
      (projection.redirect.status_code === 301 ||
        projection.redirect.status_code === 302)
    ) {
      return Response.redirect(
        new URL(projection.redirect.target, request.url),
        projection.redirect.status_code,
      );
    }
  } catch {
    // The page route remains authoritative for normal rendering and errors.
  }
}
