import type { BrowserWorkerSubmitRequest } from "@slaif-agent-site/browser-tool-contracts";
import type { BrowserContext, Request, Route } from "playwright-core";

const forbiddenHost =
  /^(?:localhost|localhost\.|0\.0\.0\.0|127(?:\.[0-9]{1,3}){3}|169\.254(?:\.[0-9]{1,3}){2}|::1|\[::1\])$/iu;
const allowedStaticPrefixes = ["/_next/static/"] as const;
const allowedStaticPaths = new Set(["/_next/image", "/slaif-logo.svg"]);

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
  const value = new URL(`/preview/${request.workspaceId}${request.route}`, origin);
  if (value.origin !== origin.origin) throw new BrowserUrlPolicyError();
  return value;
}

function allowedAsset(url: URL): boolean {
  return (
    allowedStaticPaths.has(url.pathname) ||
    allowedStaticPrefixes.some((prefix) => url.pathname.startsWith(prefix))
  );
}

export function requestIsAllowed(
  urlValue: string,
  method: string,
  resourceType: string,
  document: URL,
): "DOCUMENT" | "ASSET" | null {
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
