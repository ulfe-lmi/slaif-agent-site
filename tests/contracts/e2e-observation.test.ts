import { describe, expect, it } from "vitest";
import {
  classifyConsoleMessage,
  classifyConsoleMessageFamily,
  classifyConsoleOriginFamily,
  classifyConsoleSource,
  classifyResponseFailure,
  classifyResponseRoute,
  type ConsoleMessageClass,
  type ConsoleMessageFamily,
  type ConsoleOriginFamily,
  type ConsoleSourceClass,
  type ResponseRouteClass,
} from "../e2e/observation";

const sourceVocabulary = new Set<ConsoleSourceClass>([
  "empty",
  "same-origin-control",
  "same-origin-admin-site",
  "same-origin-static",
  "same-origin-page-other",
  "other",
]);
const messageVocabulary = new Set<ConsoleMessageClass>([
  "failed-resource-404",
  "failed-resource-other",
  "uncaught",
  "other-browser-error",
]);
const originFamilyVocabulary = new Set<ConsoleOriginFamily>([
  "same-origin",
  "empty",
  "unparseable",
  "embed-youtube-nocookie",
  "embed-vimeo",
  "embed-openstreetmap",
  "other",
]);
const messageFamilyVocabulary = new Set<ConsoleMessageFamily>([
  "policy-refused",
  "policy-csp",
  "policy-permissions",
  "cors-mixed-content",
  "network-tls",
  "api-decode-runtime",
  "other",
]);
const responseVocabulary = new Set<ResponseRouteClass>([
  "same-origin-control",
  "same-origin-editor",
  "same-origin-agent",
  "same-origin-preview",
  "same-origin-admin-site",
  "same-origin-static",
  "same-origin-canonical-site",
  "same-origin-auth",
  "other",
]);

describe("safe E2E console diagnostics", () => {
  it("emits only fixed source classes without preserving URL data", () => {
    const page = "http://localhost:8080/admin/sites/fixed";
    const cases = [
      ["", "empty"],
      [
        "http://localhost:8080/api/control/v1/sites/secret?token=secret",
        "same-origin-control",
      ],
      ["http://localhost:8080/admin/sites/secret", "same-origin-admin-site"],
      ["http://localhost:8080/_next/static/secret.js", "same-origin-static"],
      ["http://localhost:8080/login?token=secret", "same-origin-page-other"],
      ["https://private.invalid/path?credential=secret", "other"],
      ["not a URL with secret data", "other"],
    ] as const;

    for (const [source, expected] of cases) {
      const result = classifyConsoleSource(source, page);
      expect(result).toBe(expected);
      expect(sourceVocabulary.has(result)).toBe(true);
      expect(result).not.toContain("secret");
    }
  });

  it("emits only fixed message classes without preserving message data", () => {
    const cases = [
      [
        "Failed to load resource: the server responded with a status of 404 (Not Found)",
        "failed-resource-404",
      ],
      [
        "Failed to load resource: status 404 with private detail omitted",
        "failed-resource-404",
      ],
      ["Failed to load resource: classified without status", "failed-resource-other"],
      ["Uncaught private detail", "uncaught"],
      ["credential=secret and arbitrary browser text", "other-browser-error"],
    ] as const;

    for (const [text, expected] of cases) {
      const result = classifyConsoleMessage(text);
      expect(result).toBe(expected);
      expect(messageVocabulary.has(result)).toBe(true);
      expect(result).not.toContain("secret");
    }
  });

  it("classifies response failures by safe method, status, and closed route family", () => {
    const page = "http://localhost:8080/admin/sites/fixed";
    const cases = [
      [
        "GET",
        404,
        "http://localhost:8080/api/control/v1/sites/secret?token=secret",
        "same-origin-control",
        "response-GET-404-same-origin-control",
      ],
      [
        "PATCH",
        422,
        "http://localhost:8080/api/agent/v1/theme?workspace=secret",
        "same-origin-agent",
        "response-PATCH-422-same-origin-agent",
      ],
      [
        "GET",
        503,
        "https://private.invalid/secret?credential=secret",
        "other",
        "response-GET-503-other",
      ],
      [
        "invented",
        700,
        "not a URL with secret data",
        "other",
        "response-OTHER-UNKNOWN-other",
      ],
    ] as const;

    for (const [method, status, source, expectedRoute, expectedFailure] of cases) {
      expect(classifyResponseRoute(source, page)).toBe(expectedRoute);
      expect(responseVocabulary.has(classifyResponseRoute(source, page))).toBe(true);
      const result = classifyResponseFailure(method, status, source, page);
      expect(result).toBe(expectedFailure);
      expect(result).not.toContain("secret");
      expect(result).not.toContain("workspace");
      expect(result).not.toContain("token");
    }
  });

  it("classifies console origin families with exact-origin boundaries", () => {
    const page = "http://localhost:8080/preview/workspace";
    const opaquePage = "data:text/html,secret";
    const cases = [
      ["", page, "empty"],
      ["not a URL with secret data", page, "unparseable"],
      ["http://localhost:8080/api/control/v1/secret", page, "same-origin"],
      ["http://localhost:8080/other/path?token=secret", page, "same-origin"],
      // Equal opaque "null" origins are never same-origin.
      ["data:text/plain,secret", opaquePage, "other"],
      // An invalid page URL never grants same-origin.
      ["http://localhost:8080/api/control/v1/secret", "not a page URL", "other"],
      // Exact HTTPS provider origins (default port normalized away).
      [
        "https://www.youtube-nocookie.com/embed/secret?token=secret",
        page,
        "embed-youtube-nocookie",
      ],
      [
        "https://www.youtube-nocookie.com:443/embed/secret",
        page,
        "embed-youtube-nocookie",
      ],
      ["https://player.vimeo.com/video/secret", page, "embed-vimeo"],
      [
        "https://www.openstreetmap.org/export/embed.html?bbox=secret",
        page,
        "embed-openstreetmap",
      ],
      // Hostile scheme/port/userinfo/suffix values stay other.
      ["http://www.youtube-nocookie.com/embed/secret", page, "other"],
      ["http://player.vimeo.com/video/secret", page, "other"],
      ["http://www.openstreetmap.org/export/embed.html?bbox=secret", page, "other"],
      ["https://www.youtube-nocookie.com.evil.example/x", page, "other"],
      ["https://evilyoutube-nocookie.com/x", page, "other"],
      ["https://sub.www.youtube-nocookie.com/x", page, "other"],
      ["https://www.openstreetmap.org.attacker.example/x", page, "other"],
      ["https://www.youtube-nocookie.com:8443/x", page, "other"],
      ["https://user@player.vimeo.com/video/secret", page, "other"],
      ["https://user:pass@www.openstreetmap.org/export/embed.html", page, "other"],
      ["https://player.vimeo.com@evil.example/x", page, "other"],
      ["https://private.invalid/path?credential=secret", page, "other"],
      // blob: URLs never grant provider attribution (protocol guard);
      // a blob whose embedded origin equals the page stays same-origin.
      ["blob:https://player.vimeo.com/secret-uuid", page, "other"],
      ["blob:https://www.youtube-nocookie.com/secret-uuid", page, "other"],
      ["blob:http://localhost:8080/secret-uuid", page, "same-origin"],
    ] as const;

    for (const [source, pageUrl, expected] of cases) {
      const result = classifyConsoleOriginFamily(source, pageUrl);
      expect(result).toBe(expected);
      expect(originFamilyVocabulary.has(result)).toBe(true);
      expect(result).not.toContain("secret");
      expect(result).not.toContain("token");
      expect(result).not.toContain("credential");
    }
  });

  it("classifies console message families with fixed standard prefixes", () => {
    const cases = [
      [
        "Refused to apply content from https://evil.example/x because of CSP secret",
        "policy-refused",
      ],
      [
        "Content Security Policy: Blocked 'script' loaded from secret origin",
        "policy-csp",
      ],
      [
        "Permissions policy violation: secret-feature is not allowed in this context",
        "policy-permissions",
      ],
      [
        "Refused to connect to https://private.invalid/x?credential=secret",
        "policy-refused",
      ],
      [
        "Content Security Policy: report blocked for secret origin and token",
        "policy-csp",
      ],
      [
        "Permissions policy violation: camera denied in secret context",
        "policy-permissions",
      ],
      [
        "Access to script at 'https://private.invalid/x' from origin 'secret' has been blocked by CORS policy: no token",
        "cors-mixed-content",
      ],
      [
        "Mixed Content: The page at 'https://secret.example' was loaded over a more secure connection",
        "cors-mixed-content",
      ],
      [
        "Failed to load resource: net::ERR_NAME_NOT_RESOLVED for secret host",
        "network-tls",
      ],
      ["Uncaught TypeError: cannot read secret property", "api-decode-runtime"],
      ["Uncaught (in promise) TypeError: secret reject", "api-decode-runtime"],
      // Non-standard lookalike prefixes stay other (exact predicates).
      ["Permissions-Policy: feature is not allowed in secret context", "other"],
      ["content security policy blocked secret origin", "other"],
      ["Refused  to load resource from secret host", "other"],
      ["Permissions policy violation secret-feature denied", "other"],
      ["Content Security Polices blocked secret origin", "other"],
      ["net::ERR_NAME_NOT_RESOLVED for secret host", "other"],
      ["TLS error 100 while connecting to secret.example", "other"],
      ["JSON.parse failed: unexpected token in secret payload", "other"],
      ["TypeError: cannot read secret property", "other"],
      ["credential=secret and arbitrary browser text", "other"],
      ["%3Cscript%3E encoded secret value", "other"],
    ] as const;

    for (const [text, expected] of cases) {
      const result = classifyConsoleMessageFamily(text);
      expect(result).toBe(expected);
      expect(messageFamilyVocabulary.has(result)).toBe(true);
      expect(result).not.toContain("secret");
      expect(result).not.toContain("token");
      expect(result).not.toContain("credential");
    }
  });

  it("keeps the original message verdicts for the standard forms", () => {
    const cases: [string, ConsoleMessageClass][] = [
      [
        "Failed to load resource: the server responded with a status of 404 (Not Found)",
        "failed-resource-404",
      ],
      [
        "Failed to load resource: net::ERR_NAME_NOT_RESOLVED for secret host",
        "failed-resource-other",
      ],
      ["Uncaught (in promise) TypeError: secret reject", "uncaught"],
      ["other browser error text with secret and len 79", "other-browser-error"],
      [
        "Refused to apply content from https://evil.example/x because of CSP secret",
        "other-browser-error",
      ],
      [
        "Content Security Policy: Blocked 'script' loaded from secret origin",
        "other-browser-error",
      ],
      [
        "Permissions policy violation: secret-feature is not allowed in this context",
        "other-browser-error",
      ],
    ];
    for (const [text, expected] of cases) {
      expect(classifyConsoleMessage(text)).toBe(expected);
      expect(messageVocabulary.has(expected)).toBe(true);
    }
  });
});
