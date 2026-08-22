import { describe, expect, it } from "vitest";
import {
  COMPONENT_CATALOG,
  COMPONENT_CATALOG_VERSION,
  COMPONENT_TYPES,
  validateComponentType,
} from "../src/index";

describe("component catalog", () => {
  it("has a stable version", () => {
    expect(COMPONENT_CATALOG_VERSION).toBe("catalog-v1");
  });

  it("contains all architecture-required components", () => {
    const required = [
      "Section",
      "Container",
      "Columns",
      "Grid",
      "Stack",
      "Spacer",
      "Heading",
      "RichText",
      "Image",
      "Button",
      "Quote",
      "CollectionList",
      "CollectionGrid",
      "CollectionDetail",
      "Hero",
      "Statistics",
      "Timeline",
      "FAQ",
      "Header",
      "Footer",
      "Breadcrumbs",
      "LanguageSwitcher",
    ];
    for (const type of required) {
      expect(COMPONENT_TYPES.has(type), `missing: ${type}`).toBe(true);
    }
  });

  it("rejects unknown component types", () => {
    expect(validateComponentType("NonExistent")).toBe(false);
    expect(validateComponentType("Script")).toBe(false);
    expect(validateComponentType("iframe")).toBe(false);
  });

  it("every component has bounded maxChildren", () => {
    for (const component of COMPONENT_CATALOG) {
      expect(component.maxChildren).toBeGreaterThanOrEqual(0);
      expect(component.maxChildren).toBeLessThanOrEqual(32);
    }
  });

  it("no component accepts executable props", () => {
    for (const component of COMPONENT_CATALOG) {
      for (const [key, prop] of Object.entries(component.propsSchema)) {
        expect(prop.type).not.toBe("function");
        expect(key.toLowerCase()).not.toContain("script");
        expect(key.toLowerCase()).not.toContain("eval");
      }
    }
  });
});
