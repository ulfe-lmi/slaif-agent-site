import { describe, expect, it } from "vitest";
import {
  compositionToPuck,
  generatePuckConfig,
  puckToComposition,
} from "../src/puck-adapter";

describe("puck adapter", () => {
  it("generates config for all catalog components", () => {
    const config = generatePuckConfig();
    expect(Object.keys(config).length).toBeGreaterThanOrEqual(22);
    expect(Object.keys(config)).toContain("Heading");
    expect(Object.keys(config)).toContain("Section");
  });

  it("converts composition to puck format", () => {
    const result = compositionToPuck([
      { id: "n1", componentType: "Heading", props: { text: "Hello", level: 1 } },
    ]);
    expect(result.content).toHaveLength(1);
    expect(result.content[0]?.type).toBe("Heading");
    expect(result.content[0]?.props.id).toBe("n1");
  });

  it("converts puck back to composition", () => {
    const result = puckToComposition({
      content: [
        { type: "Heading", props: { id: "n1", text: "Test", level: 2 } },
      ],
      root: {},
    });
    expect(result).toHaveLength(1);
    expect(result[0]?.componentType).toBe("Heading");
    expect(result[0]?.id).toBe("n1");
  });

  it("no component config accepts arbitrary HTML", () => {
    const config = generatePuckConfig();
    for (const component of Object.values(config)) {
      for (const [key] of Object.entries(component.fields)) {
        expect(key.toLowerCase()).not.toContain("innerhtml");
      }
    }
  });
});
