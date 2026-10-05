import "server-only";

import {
  isReviewDocument,
  projectionFromReviewDocument,
  reviewBannerFacts,
  type ReviewDocument,
  type ReviewProjectionResult,
} from "./review-projection";

/**
 * 082/2 review render resolution. The resolver fetches the trusted
 * read-model document from the Control read route (the R1 read path) and
 * builds the frozen projection from the document alone: it never reads
 * live COW or canonical state (the pure mapping is the unit-level proof
 * target, see ``review-projection.ts``).
 */

const CONTROL_INTERNAL_BASE = "http://control-api:8000/api/control/v1";
const FETCH_TIMEOUT_MS = 2500;

export type ReviewRequestContext = {
  requestHeaders: { get(name: string): string | null };
  /** Exact session cookie name + value (the trusted deployment name). */
  sessionCookie: { name: string; value: string } | null;
};

export type WorkspaceReviewResolution =
  | { kind: "login" }
  | { kind: "not_found" }
  | { kind: "redirect"; target: string; status_code: 301 | 302 | 303 | 307 | 308 }
  | {
      kind: "page";
      projection: import("./render").PageProjection;
      document: ReviewDocument;
      banner: ReturnType<typeof reviewBannerFacts>;
    };

const WORKSPACE_UUID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

function controlFetch(path: string, sessionCookie: { name: string; value: string }) {
  return fetch(`${CONTROL_INTERNAL_BASE}${path}`, {
    method: "GET",
    cache: "no-store",
    credentials: "omit",
    headers: { cookie: `${sessionCookie.name}=${sessionCookie.value}` },
    signal: AbortSignal.timeout(FETCH_TIMEOUT_MS),
  });
}

/**
 * Fetch the trusted read-model document for one workspace. The review
 * route is site-scoped while the review URL is workspace-scoped, so the
 * resolver discovers the site through the caller's own trusted site list
 * (``/me/sites``) and tries each site in its deterministic order: the
 * first uniform 404-free review read wins. Every other outcome (no
 * session, no matching site, uniform 404 on all, unavailable) is the
 * same ``null``: uniform, no oracle.
 */
export async function fetchReviewDocument(
  workspaceId: string,
  sessionCookie: { name: string; value: string } | null,
): Promise<ReviewDocument | null> {
  if (!sessionCookie || !WORKSPACE_UUID.test(workspaceId)) return null;
  let sitesResponse: Response;
  try {
    sitesResponse = await controlFetch("/me/sites", sessionCookie);
  } catch {
    return null;
  }
  if (sitesResponse.status !== 200) return null;
  let sites: unknown;
  try {
    sites = await sitesResponse.json();
  } catch {
    return null;
  }
  if (!Array.isArray(sites)) return null;
  for (const rawSite of sites) {
    if (typeof rawSite !== "object" || rawSite === null) return null;
    const siteId = (rawSite as Record<string, unknown>)["site_id"];
    if (typeof siteId !== "string") return null;
    let docResponse: Response;
    try {
      docResponse = await controlFetch(
        `/sites/${encodeURIComponent(siteId)}/workspaces/${encodeURIComponent(
          workspaceId,
        )}/review/`,
        sessionCookie,
      );
    } catch {
      return null;
    }
    if (docResponse.status === 200) {
      let document: unknown;
      try {
        document = await docResponse.json();
      } catch {
        return null;
      }
      if (!isReviewDocument(document)) return null;
      return document;
    }
    if (docResponse.status !== 404) return null; // non-uniform: fail closed
  }
  return null;
}

/**
 * Resolve one review request. ``login`` (307 target), ``not_found``
 * (uniform), ``redirect`` (the snapshot's frozen redirect set), or
 * ``page`` (the frozen projection built from the read-model document).
 */
export async function resolveWorkspaceReview(
  workspaceId: string,
  sitePath: string[] | undefined,
  requestContext: ReviewRequestContext,
): Promise<WorkspaceReviewResolution> {
  if (!requestContext.sessionCookie) return { kind: "login" };
  const document = await fetchReviewDocument(workspaceId, requestContext.sessionCookie);
  if (!document) return { kind: "not_found" };
  const path = `/${(sitePath ?? []).join("/")}`;
  const result: ReviewProjectionResult = projectionFromReviewDocument(document, path);
  if (result.kind === "not_found") return { kind: "not_found" };
  if (result.kind === "redirect") {
    // Internal frozen targets are re-rooted under the review base, the
    // exact preview contract.
    const target = result.target.startsWith("/")
      ? result.target === "/"
        ? `/review/${workspaceId}`
        : `/review/${workspaceId}${result.target}`
      : result.target;
    return { kind: "redirect", target, status_code: result.status_code };
  }
  return {
    kind: "page",
    projection: result.projection,
    document,
    banner: reviewBannerFacts(document),
  };
}
