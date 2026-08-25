import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  BROWSER_CONTRACT_BOUNDS,
  BROWSER_CONTRACT_SCHEMAS,
  BROWSER_CONTRACT_VERSION,
  BROWSER_EVIDENCE,
  BROWSER_PREVIEW_CREDENTIAL_FACTS,
  BROWSER_RUN_STATES,
  BROWSER_TARGETS,
  BROWSER_TERMINAL_STATES,
  canonicalSerializePreviewRunRequest,
  packageMetadata,
  parsePreviewRunCreateRequest,
  previewRunRequestDigest,
} from "../src/index";

const validRequest = {
  version: BROWSER_CONTRACT_VERSION,
  route: "/news?locale=en",
  target: "desktop-chromium",
  evidence: ["screenshot", "heading-summary"],
};

describe("browser preview contracts", () => {
  it("matches the language-neutral versioned facts exactly", () => {
    const facts = JSON.parse(
      readFileSync(
        resolve(import.meta.dirname, "../src/browser-preview-v1.json"),
        "utf8",
      ),
    ) as Record<string, unknown>;
    expect(facts).toEqual({
      contractVersion: BROWSER_CONTRACT_VERSION,
      targets: BROWSER_TARGETS,
      evidence: BROWSER_EVIDENCE,
      runStates: BROWSER_RUN_STATES,
      terminalStates: BROWSER_TERMINAL_STATES,
      visibility: "PRIVATE",
      bounds: BROWSER_CONTRACT_BOUNDS,
    });
    expect(packageMetadata).toEqual({
      name: "@slaif-agent-site/browser-tool-contracts",
      status: "typed-preview-contracts",
      version: "browser-preview/v1",
    });
  });

  it("matches the neutral run-token verifier facts exactly", () => {
    const facts = JSON.parse(
      readFileSync(
        resolve(import.meta.dirname, "../src/browser-preview-credential-v1.json"),
        "utf8",
      ),
    ) as Record<string, unknown>;
    expect(facts).toEqual(BROWSER_PREVIEW_CREDENTIAL_FACTS);
  });

  it("normalizes only the fixed request shape and canonicalizes evidence order", async () => {
    const parsed = parsePreviewRunCreateRequest(validRequest);
    expect(Object.isFrozen(parsed)).toBe(true);
    expect(Object.isFrozen(parsed.evidence)).toBe(true);
    expect(
      canonicalSerializePreviewRunRequest({
        ...validRequest,
        evidence: ["heading-summary", "screenshot"],
      }),
    ).toBe(
      '{"evidence":["screenshot","heading-summary"],"route":"/news?locale=en","target":"desktop-chromium","version":"browser-preview/v1"}',
    );
    expect(await previewRunRequestDigest(validRequest)).toBe(
      "6ee9d361a4433878c18c6aa645c6872afae8bd31ac0e628e88f3d0eefa3405f4",
    );
    expect(
      parsePreviewRunCreateRequest({
        ...validRequest,
        route: "/news?z=hello%20world&a=~",
      }).route,
    ).toBe("/news?a=~&z=hello+world");
  });

  it("keeps every exported object schema extra-forbid and state-bounded", () => {
    for (const schema of Object.values(BROWSER_CONTRACT_SCHEMAS)) {
      expect(schema.type).toBe("object");
      expect(schema.additionalProperties).toBe(false);
    }
    expect(BROWSER_CONTRACT_SCHEMAS.previewRunStatus.properties.state.enum).toEqual(
      BROWSER_RUN_STATES,
    );
    expect(BROWSER_CONTRACT_SCHEMAS.runCompletion.properties.state.enum).toEqual(
      BROWSER_TERMINAL_STATES,
    );
    expect(BROWSER_RUN_STATES).not.toContain("UNKNOWN");
  });

  it.each([
    {},
    { ...validRequest, version: "browser-preview/v2" },
    { ...validRequest, target: "desktop-firefox" },
    { ...validRequest, evidence: [] },
    { ...validRequest, evidence: ["screenshot", "screenshot"] },
    { ...validRequest, evidence: ["raw-dom"] },
    { ...validRequest, route: "https://outside.invalid/" },
    { ...validRequest, route: "//outside.invalid/" },
    { ...validRequest, route: "/a/../private" },
    { ...validRequest, route: "/a/%2e%2e/private" },
    { ...validRequest, route: "/news#private" },
    { ...validRequest, route: "/news?access_token=secret" },
    { ...validRequest, route: "/news?next=sas2_0123_secret" },
    { ...validRequest, route: `/${"x".repeat(2049)}` },
    { ...validRequest, viewport: { width: 1200, height: 800 } },
    { ...validRequest, capabilityId: "00000000-0000-4000-8000-000000000001" },
    { ...validRequest, headers: { authorization: "secret" } },
    { ...validRequest, javascript: "document.body" },
  ])("rejects unsafe or authority-bearing create input %#", (candidate) => {
    expect(() => parsePreviewRunCreateRequest(candidate)).toThrow();
  });
});
