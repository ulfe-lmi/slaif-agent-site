import type { BrowserWorkerSubmitRequest } from "@slaif-agent-site/browser-tool-contracts";
import type { BrowserContext, Request, Route } from "playwright-core";

const forbiddenHost =
  /^(?:localhost|localhost\.|0\.0\.0\.0|127(?:\.[0-9]{1,3}){3}|169\.254(?:\.[0-9]{1,3}){2}|::1|\[::1\])$/iu;
const allowedStaticPrefixes = ["/_next/static/"] as const;
const allowedStaticPaths = new Set([
  "/_next/image",
  "/renderer-v1.css",
  "/slaif-logo.svg",
]);

/**
 * 083/5 run-bound private media subresource: the exact bound preview
 * asset path only.  The bound-run token (existing run credential) is
 * re-verified server-side against the run row, so this exact shape is
 * the only authorized private byte subresource of a bound preview.
 */
const boundMediaAssetPath =
  /^\/media\/v1\/browser-preview\/assets\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\/content$/u;

const boundMediaUuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/u;

/**
 * The exact bound media URL for a validated media id, or null when the id
 * cannot produce the exact authorized path.  Used only by the worker's
 * bounded document-media resource read; no client or page input can select
 * another path, origin or upstream.
 */
export function boundMediaUrl(document: URL, mediaId: string): URL | null {
  if (!boundMediaUuidPattern.test(mediaId)) return null;
  const url = new URL(
    `/media/v1/browser-preview/assets/${mediaId}/content`,
    document.origin,
  );
  if (url.origin !== document.origin || !boundMediaAssetPath.test(url.pathname))
    return null;
  return url;
}

export class BrowserUrlPolicyError extends Error {
  public constructor() {
    super("browser navigation is unavailable");
    this.name = "BrowserUrlPolicyError";
  }
}

export function validatePreviewOrigin(value: string): URL {
  let origin: URL;
  try {
    origin = new URL(value);
  } catch {
    throw new BrowserUrlPolicyError();
  }
  if (
    !["http:", "https:"].includes(origin.protocol) ||
    origin.username !== "" ||
    origin.password !== "" ||
    origin.pathname !== "/" ||
    origin.search !== "" ||
    origin.hash !== "" ||
    forbiddenHost.test(origin.hostname) ||
    origin.hostname.includes("%")
  )
    throw new BrowserUrlPolicyError();
  return new URL(origin.origin);
}

export function previewDocumentUrl(
  origin: URL,
  request: BrowserWorkerSubmitRequest,
): URL {
  // Canonical (slashless) document form.  The framework normalizes a
  // trailing slash with a 308 before app routing, and the confinement
  // handler admits exactly ONE non-redirected document request, so the
  // route must be requested in its canonical form or the normalization
  // hop would be aborted and the run would fail closed.  The server
  // already normalized the route (trailing slash stripped except for the
  // root "/", query pairs sorted) and bound its digest, so only the path
  // is reshaped here - the root requests no segment after the workspace
  // prefix, also when a query follows - and the query is preserved
  // verbatim.
  const questionMark = request.route.indexOf("?");
  let path = questionMark === -1 ? request.route : request.route.slice(0, questionMark);
  const query = questionMark === -1 ? "" : request.route.slice(questionMark);
  if (path.length > 1 && path.endsWith("/")) path = path.slice(0, -1);
  const documentPath = path === "/" ? "" : path;
  const value = new URL(
    `/preview/${request.workspaceId}${documentPath}${query}`,
    origin,
  );
  if (value.origin !== origin.origin) throw new BrowserUrlPolicyError();
  return value;
}

function allowedAsset(url: URL): boolean {
  return (
    allowedStaticPaths.has(url.pathname) ||
    allowedStaticPrefixes.some((prefix) => url.pathname.startsWith(prefix))
  );
}

function isBoundMediaSubresource(url: URL, resourceType: string): boolean {
  return (
    boundMediaAssetPath.test(url.pathname) &&
    url.search === "" &&
    url.hash === "" &&
    resourceType === "image"
  );
}

// Strictly bounded authorized resource read for DOCUMENT media that the
// rendered preview references (DocumentList anchors).  The worker issues
// these as same-origin fetches from the page; they are never top-level
// navigations, and the same confinement handler injects the run credential
// and strips every other credential.
function isBoundMediaDocumentFetch(url: URL, resourceType: string): boolean {
  return (
    boundMediaAssetPath.test(url.pathname) &&
    url.search === "" &&
    url.hash === "" &&
    resourceType === "fetch"
  );
}

export function requestIsAllowed(
  urlValue: string,
  method: string,
  resourceType: string,
  document: URL,
): "DOCUMENT" | "ASSET" | "MEDIA" | null {
  let url: URL;
  try {
    url = new URL(urlValue);
  } catch {
    return null;
  }
  if (
    url.origin !== document.origin ||
    url.username !== "" ||
    url.password !== "" ||
    !["GET", "HEAD"].includes(method)
  )
    return null;
  if (url.href === document.href && resourceType === "document" && method === "GET") {
    return "DOCUMENT";
  }
  if (
    url.origin === document.origin &&
    method === "GET" &&
    (isBoundMediaSubresource(url, resourceType) ||
      isBoundMediaDocumentFetch(url, resourceType))
  ) {
    return "MEDIA";
  }
  if (allowedAsset(url) && resourceType !== "document") return "ASSET";
  return null;
}

function confinedHeaders(
  request: Request,
  previewCredential: string,
): Record<string, string> {
  const retained: Record<string, string> = {};
  for (const [name, value] of Object.entries(request.headers())) {
    const lowered = name.toLowerCase();
    if (
      ![
        "authorization",
        "cookie",
        "proxy-authorization",
        "x-slaif-browser-preview",
        "x-slaif-browser-worker-token",
      ].includes(lowered)
    )
      retained[lowered] = value;
  }
  retained["x-slaif-browser-preview"] = previewCredential;
  return retained;
}

export async function installRequestConfinement(
  context: BrowserContext,
  document: URL,
  previewCredential: string,
  onBlocked: (request: Request) => void,
): Promise<void> {
  let initialDocumentAuthorized = false;
  await context.route("**/*", async (route: Route, request: Request) => {
    const policy = requestIsAllowed(
      request.url(),
      request.method(),
      request.resourceType(),
      document,
    );
    if (policy === null) {
      onBlocked(request);
      await route.abort("blockedbyclient");
      return;
    }
    if (
      policy === "DOCUMENT" &&
      !initialDocumentAuthorized &&
      request.redirectedFrom() === null
    ) {
      initialDocumentAuthorized = true;
      await route.continue({
        headers: confinedHeaders(request, previewCredential),
      });
      return;
    }
    if (policy === "DOCUMENT") {
      onBlocked(request);
      await route.abort("blockedbyclient");
      return;
    }
    if (policy === "MEDIA") {
      // Exact bound media subresource only: a direct fetch of the
      // bound asset path, never a redirect hop.  The worker injects
      // the existing run credential and strips every other
      // credential (cookie, authorization, proxy, worker token) -
      // the browser itself never holds the credential.
      if (request.redirectedFrom() !== null) {
        onBlocked(request);
        await route.abort("blockedbyclient");
        return;
      }
      await route.continue({
        headers: confinedHeaders(request, previewCredential),
      });
      return;
    }
    await route.continue({
      headers: Object.fromEntries(
        Object.entries(request.headers()).filter(
          ([name]) =>
            ![
              "authorization",
              "cookie",
              "proxy-authorization",
              "x-slaif-browser-preview",
              "x-slaif-browser-worker-token",
            ].includes(name.toLowerCase()),
        ),
      ),
    });
  });
}

export const CONFINEMENT_SELF_CHECK_URLS = Object.freeze([
  "http://agent-api:8000/health/live",
  "http://browser-worker:3100/health/live",
  "http://control-api:8000/health/live",
  "http://editor-api:8000/health/live",
  "http://render-api:8000/health/live",
  "http://media-service:8000/health/live",
  "http://postgres:5432/",
  "http://host.docker.internal/",
  "http://127.0.0.1/",
  "http://169.254.169.254/latest/meta-data/",
  "http://example.com/",
] as const);
