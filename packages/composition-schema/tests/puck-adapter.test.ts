import { describe, expect, it } from "vitest";
import {
  compositionToPuck,
  generatePuckConfig,
  puckToComposition,
  type NormalizedCompositionNode,
} from "../src/puck-adapter";

const nodes: readonly NormalizedCompositionNode[] = [
  {
    id: "root",
    componentType: "Section",
    schemaVersion: "1",
    parentId: null,
    slotKey: "default",
    orderKey: 10,
    props: { variant: "narrow" },
  },
  {
    id: "child-a",
    componentType: "Heading",
    schemaVersion: "1",
    parentId: "root",
    slotKey: "default",
    orderKey: 20,
    props: { text: "Hello", level: 2 },
  },
  {
    id: "child-b",
    componentType: "Button",
    schemaVersion: "1",
    parentId: "root",
    slotKey: "default",
    orderKey: 30,
    props: { label: "Open", href: "/open" },
  },
];

describe("puck adapter", () => {
  it("generates config for all trusted catalog components", () => {
    const config = generatePuckConfig();
    expect(Object.keys(config)).toHaveLength(22);
    expect(Object.keys(config)).toContain("Heading");
    expect(Object.keys(config)).toContain("Section");
  });

  it("preserves IDs, metadata, hierarchy, slots, order, and props exactly", () => {
    const puck = compositionToPuck(nodes);
    expect(puck.content).toHaveLength(1);
    expect(puck.content[0]?.props.id).toBe("root");
    expect(puck.zones?.["root:default"]).toHaveLength(2);
    expect(puck.content[0]?.props.variant).toBe("narrow");
    expect(puck.content[0]?.props.schemaVersion).toBeUndefined();
    expect(puck.metadata?.root?.orderKey).toBe(10);
    expect(puckToComposition(puck)).toEqual(nodes);
  });

  it("preserves nested parent and slot metadata through a Puck edit", () => {
    const puck = compositionToPuck([
      ...nodes,
      {
        id: "column",
        componentType: "Columns",
        schemaVersion: "2",
        parentId: "root",
        slotKey: "col-1",
        orderKey: 1,
        props: { count: 2 },
      },
    ]);
    const roundTrip = puckToComposition(puck);
    expect(roundTrip.find((node) => node.id === "column")).toMatchObject({
      schemaVersion: "2",
      parentId: "root",
      slotKey: "col-1",
      orderKey: 1,
    });
  });

  it("assigns deterministic index order after a same-zone reorder", () => {
    const puck = compositionToPuck(nodes);
    const reordered = {
      ...puck,
      zones: {
        ...puck.zones,
        "root:default": [
          puck.zones?.["root:default"]?.[1],
          puck.zones?.["root:default"]?.[0],
        ].filter((node): node is NonNullable<typeof node> => Boolean(node)),
      },
    };
    const result = puckToComposition(reordered);
    expect(
      result.filter((node) => node.parentId === "root").map((node) => node.orderKey),
    ).toEqual([0, 1]);
  });

  it("rejects unknown component types and executable/bookkeeping props", () => {
    expect(() =>
      puckToComposition({
        content: [{ type: "Unknown", props: { id: "x" } }],
        root: {},
      }),
    ).toThrow("unknown-component-type");
    expect(() =>
      compositionToPuck([
        {
          ...nodes[0]!,
          props: { innerHTML: "<script>bad</script>" },
        },
      ]),
    ).toThrow("forbidden-component-prop");
  });
});
