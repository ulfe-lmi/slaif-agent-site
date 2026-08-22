import { describe, expect, it } from "vitest";
import { COMPOSITION_SCHEMA_VERSION, isCompositionNode } from "../src/index";

describe("composition schema", () => {
  it("has correct schema version", () => {
    expect(COMPOSITION_SCHEMA_VERSION).toBe("site-composition/v1");
  });

  it("validates composition nodes", () => {
    expect(
      isCompositionNode({
        id: "test-1",
        componentType: "Heading",
        parentId: null,
        slotKey: "default",
        orderKey: 0,
        props: {},
      }),
    ).toBe(true);

    expect(isCompositionNode({ id: "x" })).toBe(false);
    expect(isCompositionNode(null)).toBe(false);
    expect(isCompositionNode("string")).toBe(false);
  });
});
