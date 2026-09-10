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
