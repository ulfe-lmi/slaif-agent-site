import { describe, expect, it } from "vitest";
import {
  COMPONENT_CATALOG,
  COMPONENT_CATALOG_DOCUMENT,
  COMPONENT_CATALOG_VERSION,
  COMPONENT_TYPES,
  validateComponentType,
} from "../src/index";
import {
  DESIGN_SYSTEM_DOCUMENT,
  DESIGN_SYSTEM_VERSION,
  RESPONSIVE_LABELS,
} from "../src/design-system";

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

  it("publishes bounded authority and binding metadata", () => {
    for (const component of COMPONENT_CATALOG) {
      expect(["content", "structure", "global"]).toContain(
        component.authorityClass,
      );
      expect(["none", "collection_view", "media_asset"]).toContain(
        component.bindingKind,
      );
      for (const prop of Object.values(component.propsSchema)) {
        expect(["content", "design"]).toContain(prop.authority);
      }
    }
  });

  it("publishes exact nested schemas for every structured prop", () => {
    expect(COMPONENT_CATALOG_DOCUMENT.components).toHaveLength(22);
    for (const component of COMPONENT_CATALOG) {
      for (const prop of Object.values(component.propsSchema)) {
        if (prop.type === "object" || prop.type === "array") {
          expect(prop.schema).toBeDefined();
        }
      }
    }
    const richText = COMPONENT_CATALOG.find((item) => item.type === "RichText");
    expect(richText?.propsSchema.content?.schema?.properties?.children?.items).toMatchObject({
      type: "object",
      required: ["text"],
      additional_properties: false,
    });
  });

  it("publishes the bounded design-system authority", () => {
    expect(DESIGN_SYSTEM_VERSION).toBe("design-system/v1");
    expect(DESIGN_SYSTEM_DOCUMENT.catalog_version).toBe("catalog-v1");
    expect(DESIGN_SYSTEM_DOCUMENT.responsive_labels).toEqual(RESPONSIVE_LABELS);
    expect(DESIGN_SYSTEM_DOCUMENT.tokens.alignment).toEqual([
      "start",
      "center",
      "end",
      "stretch",
    ]);
    expect(DESIGN_SYSTEM_DOCUMENT.components).toHaveLength(22);
    expect(DESIGN_SYSTEM_DOCUMENT.components.map((item) => item.type)).toEqual(
      Array.from(COMPONENT_TYPES),
    );
    expect(
      DESIGN_SYSTEM_DOCUMENT.components
        .find((item) => item.type === "Image")
        ?.properties.find((item) => item.name === "aspectRatio"),
    ).toMatchObject({
      scope: "component-props:write",
      responsive: true,
    });
    expect(
      DESIGN_SYSTEM_DOCUMENT.components
        .find((item) => item.type === "Button")
        ?.properties.find((item) => item.name === "variant"),
    ).toMatchObject({ scope: "component-variant:write" });
    expect(
      DESIGN_SYSTEM_DOCUMENT.components
        .find((item) => item.type === "CollectionGrid")
        ?.properties.find((item) => item.name === "columns"),
    ).toMatchObject({ scope: "layout:write" });
    expect(JSON.stringify(DESIGN_SYSTEM_DOCUMENT)).not.toMatch(
      /javascript:|<script|style|font|selector|media query/i,
    );
  });
});
