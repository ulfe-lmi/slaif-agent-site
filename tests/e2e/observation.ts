export type ConsoleSourceClass =
  | "empty"
  | "same-origin-control"
  | "same-origin-admin-site"
  | "same-origin-static"
  | "same-origin-page-other"
  | "other";

export type ConsoleMessageClass =
  "failed-resource-404" | "failed-resource-other" | "uncaught" | "other-browser-error";

export type ResponseRouteClass =
  | "same-origin-control"
  | "same-origin-editor"
  | "same-origin-agent"
  | "same-origin-preview"
  | "same-origin-admin-site"
  | "same-origin-static"
  | "same-origin-canonical-site"
  | "same-origin-auth"
  | "other";

export function classifyConsoleSource(
  source: string,
  pageUrl: string,
): ConsoleSourceClass {
  if (source === "") return "empty";
  try {
    const sourceUrl = new URL(source);
    const currentUrl = new URL(pageUrl);
    if (sourceUrl.origin !== currentUrl.origin) return "other";
    if (sourceUrl.pathname.startsWith("/api/control/")) {
      return "same-origin-control";
    }
    if (/^\/admin\/sites\/[^/]+$/.test(sourceUrl.pathname)) {
      return "same-origin-admin-site";
    }
    return sourceUrl.pathname.startsWith("/_next/")
      ? "same-origin-static"
      : "same-origin-page-other";
  } catch {
    return "other";
  }
}

export function classifyConsoleMessage(text: string): ConsoleMessageClass {
  if (/^Failed to load resource:.*\b404\b/.test(text)) {
    return "failed-resource-404";
  }
  if (text.startsWith("Failed to load resource:")) {
    return "failed-resource-other";
  }
  return text.startsWith("Uncaught ") ? "uncaught" : "other-browser-error";
}

export function classifyResponseRoute(
  source: string,
  pageUrl: string,
): ResponseRouteClass {
  try {
    const sourceUrl = new URL(source);
    const currentUrl = new URL(pageUrl);
    if (sourceUrl.origin !== currentUrl.origin) return "other";
    if (sourceUrl.pathname.startsWith("/api/control/")) return "same-origin-control";
    if (sourceUrl.pathname.startsWith("/api/editor/")) return "same-origin-editor";
    if (sourceUrl.pathname.startsWith("/api/agent/")) return "same-origin-agent";
    if (sourceUrl.pathname.startsWith("/preview/")) return "same-origin-preview";
    if (/^\/admin\/sites\/[^/]+$/u.test(sourceUrl.pathname))
      return "same-origin-admin-site";
    if (sourceUrl.pathname.startsWith("/_next/")) return "same-origin-static";
    if (/^\/(?:login|logout)(?:\/|$)/u.test(sourceUrl.pathname))
      return "same-origin-auth";
    if (/^\/s\//u.test(sourceUrl.pathname)) return "same-origin-canonical-site";
    return "other";
  } catch {
    return "other";
  }
}

export function classifyResponseFailure(
  method: string,
  status: number,
  source: string,
  pageUrl: string,
): string {
  const safeMethod = /^(?:GET|HEAD|OPTIONS|POST|PUT|PATCH|DELETE)$/u.test(method)
    ? method
    : "OTHER";
  const safeStatus =
    Number.isInteger(status) && status >= 100 && status <= 599
      ? String(status)
      : "UNKNOWN";
  return `response-${safeMethod}-${safeStatus}-${classifyResponseRoute(source, pageUrl)}`;
}

// e-round diagnostic-only closed vocabularies: category detail for the
// existing bounded redacted console records. They never replace the original
// classifiers, grant no trust or failure exemption, and unknown input stays
// "other"/"other-browser-error" (unknown stays a failure). Parsed URL
// equality and fixed static predicates only; no raw text/URL/ID/hash output.

export type ConsoleOriginFamily =
  | "same-origin"
  | "empty"
  | "unparseable"
  | "embed-youtube-nocookie"
  | "embed-vimeo"
  | "embed-openstreetmap"
  | "other";

// The edge CSP frame-src allowlists exactly these three origins
// (bounded-embed family); matching is exact HTTPS origin equality with the
// URL parser's default-port normalization (default ports dropped, non-default
// ports retained, userinfo never present in origin). Labels grant no
// authority or exemption.
const APPROVED_EMBED_ORIGINS: ReadonlyArray<readonly [string, ConsoleOriginFamily]> = [
  ["https://www.youtube-nocookie.com", "embed-youtube-nocookie"],
  ["https://player.vimeo.com", "embed-vimeo"],
  ["https://www.openstreetmap.org", "embed-openstreetmap"],
];

export function classifyConsoleOriginFamily(
  source: string,
  pageUrl: string,
): ConsoleOriginFamily {
  if (source === "") return "empty";
  let sourceUrl: URL;
  try {
    sourceUrl = new URL(source);
  } catch {
    return "unparseable";
  }
  let pageOrigin: string;
  try {
    pageOrigin = new URL(pageUrl).origin;
  } catch {
    pageOrigin = "";
  }
  // Opaque origins stringify to "null"; equal "null" strings are never
  // same-origin.
  if (pageOrigin !== "" && pageOrigin !== "null" && sourceUrl.origin === pageOrigin) {
    return "same-origin";
  }
  // Credentials are rejected for provider attribution: a URL carrying a
  // user/password is never attributed to an approved embed origin.
  if (sourceUrl.username !== "" || sourceUrl.password !== "") {
    return "other";
  }
  // Provider attribution requires the actual HTTPS protocol: a matching
  // origin string alone is insufficient (e.g. blob:https://provider).
  if (sourceUrl.protocol === "https:") {
    for (const [approvedOrigin, family] of APPROVED_EMBED_ORIGINS) {
      if (sourceUrl.origin === approvedOrigin) return family;
    }
  }
  return "other";
}

// Bounded static predicates over standard fixed browser-console message
// shapes; unmatched text stays "other". No captured groups or dynamic
// labels. These are additional diagnostic hints only: the original
// classifier verdicts stay unchanged. Its other-browser-error class
// excludes only the "Failed to load resource:" and "Uncaught " forms, so
// CSP/CORS and other new family hints can retain the old other class; the
// len-79/HTTPS cause remains UNKNOWN.
export type ConsoleMessageFamily =
  | "csp-permissions-policy"
  | "cors-mixed-content"
  | "network-tls"
  | "api-decode-runtime"
  | "other";

export function classifyConsoleMessageFamily(text: string): ConsoleMessageFamily {
  if (
    text.startsWith("Refused to ") ||
    text.startsWith("Content Security Policy") ||
    text.startsWith("Permissions policy violation:")
  ) {
    return "csp-permissions-policy";
  }
  if (
    (text.startsWith("Access to") &&
      text.includes("has been blocked by CORS policy")) ||
    text.startsWith("Mixed Content")
  ) {
    return "cors-mixed-content";
  }
  if (text.startsWith("Failed to load resource: net::ERR_")) {
    return "network-tls";
  }
  if (text.startsWith("Uncaught (in promise) ") || text.startsWith("Uncaught ")) {
    return "api-decode-runtime";
  }
  return "other";
}
