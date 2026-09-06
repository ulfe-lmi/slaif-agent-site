import { NextResponse, type NextRequest } from "next/server";

import {
  isRedirectProjection,
  resolveCanonicalPage,
  resolvePreviewPage,
} from "./src/sites/render";

const WORKSPACE_ID = /^[0-9a-f-]{36}$/iu;
const RESERVED =
  /^\/(?:preview-render|admin|api|agent|control|editor|health|internal|login|logout|mcp|media|setup|_next|static)(?:\/|$)/u;
const REDIRECT_STATUSES = new Set([301, 302, 303, 307, 308]);

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

function redirectResponse(
  target: string,
  status: number,
  requestUrl: string,
): Response {
  return new Response(null, {
    status,
    headers: { Location: new URL(target, requestUrl).toString() },
  });
}

function previewRewriteResponse(
  request: NextRequest,
  preview: { workspaceId: string; path: string },
): NextResponse {
  const destination = new URL(`/preview-render${preview.path}`, request.url);
  destination.search = request.nextUrl.search;
  const headers = new Headers(request.headers);
  headers.set("x-slaif-internal-preview", "1");
  headers.set("x-slaif-preview-workspace", preview.workspaceId);
  return NextResponse.rewrite(destination, { request: { headers } });
}

export async function proxy(request: NextRequest): Promise<Response | undefined> {
  if (request.method !== "GET" && request.method !== "HEAD") return;

  const preview = previewRoute(request);
  if (preview) {
    const session =
      request.cookies.get("__Host-slaif_session")?.value ??
      request.cookies.get("slaif_session")?.value;
    const browserToken = request.headers.get("x-slaif-browser-preview");
    // Browser preview credentials are deliberately single-use. The preview
    // page must make the sole render request so its authorization is consumed
    // exactly once by the Render service.
    if (session && browserToken) return;
    if (!browserToken && !session) return;

    if (session) {
      try {
        const projection = await resolvePreviewPage(
          request.headers.get("host") ?? "",
          preview.path,
          preview.workspaceId,
          { humanSessionToken: session },
        );
        if (
          projection &&
          isRedirectProjection(projection) &&
          REDIRECT_STATUSES.has(projection.redirect.status_code)
        ) {
          return redirectResponse(
            projection.redirect.target,
            projection.redirect.status_code,
            request.url,
          );
        }
      } catch {
        // The page route remains authoritative for normal rendering and errors.
      }
    }
    return previewRewriteResponse(request, preview);
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
      REDIRECT_STATUSES.has(projection.redirect.status_code)
    ) {
      return redirectResponse(
        projection.redirect.target,
        projection.redirect.status_code,
        request.url,
      );
    }
  } catch {
    // The page route remains authoritative for normal rendering and errors.
  }
}
