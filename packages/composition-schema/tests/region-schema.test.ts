import { describe, expect, it } from "vitest";
import {
  GLOBAL_REGION_SCHEMA_VERSION,
  MAX_HEADER_NAV_ENTRIES,
  REGION_VARIANTS,
  globalRegionDefaults,
  isGlobalRegionRecord,
  isRegionTarget,
  isRegionVariant,
  regionContentBytes,
  validateRegionTarget,
} from "../src/region-schema";

describe("region schema", () => {
  it("pins the schema version and closed variant enums", () => {
    expect(GLOBAL_REGION_SCHEMA_VERSION).toBe("global-region/v1");
    expect(REGION_VARIANTS.header).toEqual(["institutional", "minimal"]);
    expect(REGION_VARIANTS.footer).toEqual([
      "multi-column",
      "single-column",
    ]);
    expect(isRegionVariant("header", "institutional")).toBe(true);
    expect(isRegionVariant("header", "multi-column")).toBe(false);
    expect(isRegionVariant("footer", "single-column")).toBe(true);
  });

  it("derives the lazy bootstrap defaults", () => {
    const defaults = globalRegionDefaults("demo");
    expect(defaults.header.variant).toBe("institutional");
    expect(defaults.header.content.nav).toEqual([
      { label: "demo", target: { kind: "internal", value: "/" } },
    ]);
    expect(defaults.footer.variant).toBe("single-column");
    expect(defaults.footer.content).toEqual({ links: [], note: "" });
  });

  it("validates the closed target bounds", () => {
    expect(
      validateRegionTarget(
        "page",
        "0f8fad5b-d9cb-469f-a165-70867728950e",
      ),
    ).toBe(true);
    expect(validateRegionTarget("page", "not-a-uuid")).toBe(false);
    expect(validateRegionTarget("internal", "/")).toBe(true);
    expect(validateRegionTarget("internal", "/about/team")).toBe(true);
    expect(validateRegionTarget("internal", "/API/x")).toBe(false);
    expect(validateRegionTarget("internal", "//x")).toBe(false);
    expect(validateRegionTarget("internal", "/a/../b")).toBe(false);
    expect(validateRegionTarget("external", "https://example.org/x")).toBe(
      true,
    );
    expect(validateRegionTarget("external", "http://example.org")).toBe(true);
    expect(validateRegionTarget("external", "javascript:alert(1)")).toBe(false);
    expect(validateRegionTarget("external", "ftp://example.org/x")).toBe(false);
    expect(
      validateRegionTarget("external", "https://user:pass@example.org/x"),
    ).toBe(false);
    expect(
      isRegionTarget({ kind: "internal", value: "/" }),
    ).toBe(true);
    expect(isRegionTarget({ kind: "external", value: "https://x.io" })).toBe(
      true,
    );
    expect(validateRegionTarget("external", "http:/x")).toBe(false);
  });

  it("bounds the header nav entry count", () => {
    const defaults = globalRegionDefaults("demo");
    expect(defaults.header.content.nav.length).toBeLessThanOrEqual(
      MAX_HEADER_NAV_ENTRIES,
    );
  });

  it("serializes bounded content sizes", () => {
    const footer = globalRegionDefaults("demo");
    expect(regionContentBytes(footer.footer.content)).toBeGreaterThan(0);
  });

  it("recognizes well-formed region records", () => {
    expect(
      isGlobalRegionRecord({
        id: "0f8fad5b-d9cb-469f-a165-70867728950e",
        site_id: "11111111-1111-4111-8111-111111111111",
        region_key: "header",
        variant: "institutional",
        content: globalRegionDefaults("demo").header.content,
        schema_version: GLOBAL_REGION_SCHEMA_VERSION,
        row_version: 1,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      }),
    ).toBe(true);
    expect(
      isGlobalRegionRecord({
        id: "x",
        site_id: "y",
        region_key: "header",
        variant: "single-column",
        content: globalRegionDefaults("demo").header.content,
        schema_version: GLOBAL_REGION_SCHEMA_VERSION,
        row_version: 1,
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:00Z",
      }),
    ).toBe(false);
  });
});
