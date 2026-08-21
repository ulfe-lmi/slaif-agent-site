export type ConsoleSourceClass =
  | "empty"
  | "same-origin-control"
  | "same-origin-admin-site"
  | "same-origin-static"
  | "same-origin-page-other"
  | "other";

export type ConsoleMessageClass =
  "failed-resource-404" | "failed-resource-other" | "uncaught" | "other-browser-error";

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
