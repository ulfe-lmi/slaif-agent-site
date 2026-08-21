import { describe, expect, it } from "vitest";
import {
  classifyConsoleMessage,
  classifyConsoleSource,
  type ConsoleMessageClass,
  type ConsoleSourceClass,
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
});
