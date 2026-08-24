import { describe, expect, it } from "vitest";
import {
  compositionToPuck,
  generatePuckConfig,
  puckToComposition,
  type NormalizedCompositionNode,
} from "../src/puck-adapter";
import {
  derivePuckSiblingReorderActions,
  shouldReleasePuckMovedSelection,
  type PuckReorderPlan,
} from "../src/puck-reorder";

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

function plan(
  sourceIndex: number,
  destinationIndex: number,
  destinationZone: string,
): PuckReorderPlan {
  const reorder = {
    type: "reorder" as const,
    sourceIndex,
    destinationIndex,
    destinationZone,
    recordHistory: true as const,
  };
  const selection = {
    type: "setUi" as const,
    ui: { itemSelector: { index: destinationIndex, zone: destinationZone } },
    recordHistory: false as const,
  };
  return { reorder, selection, actions: [reorder, selection] };
}

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

  it("derives fail-closed root boundary actions with history", () => {
    const puck = compositionToPuck([
      nodes[0]!,
      { ...nodes[0]!, id: "root-2", orderKey: 20 },
      { ...nodes[0]!, id: "root-3", orderKey: 30 },
    ]);
    expect(derivePuckSiblingReorderActions(puck, null)).toEqual({
      zone: null,
      sourceIndex: null,
      siblingCount: 0,
      moveUp: null,
      moveDown: null,
    });
    expect(derivePuckSiblingReorderActions(puck, { index: 0 })).toMatchObject({
      zone: "root:default-zone",
      sourceIndex: 0,
      siblingCount: 3,
      moveUp: null,
      moveDown: plan(0, 1, "root:default-zone"),
    });
    expect(derivePuckSiblingReorderActions(puck, { index: 1 })).toMatchObject({
      moveUp: plan(1, 0, "root:default-zone"),
      moveDown: plan(1, 2, "root:default-zone"),
    });
    expect(derivePuckSiblingReorderActions(puck, { index: 2 })).toMatchObject({
      moveUp: plan(2, 1, "root:default-zone"),
      moveDown: null,
    });
    expect(derivePuckSiblingReorderActions(puck, { index: 3 })).toMatchObject({
      zone: null,
      sourceIndex: null,
      siblingCount: 0,
      moveUp: null,
      moveDown: null,
    });
  });

  it("derives the exact same-zone action for a nested sibling zone", () => {
    const puck = compositionToPuck(nodes);
    const result = derivePuckSiblingReorderActions(puck, {
      index: 1,
      zone: "root:default",
    });
    expect(result).toEqual({
      zone: "root:default",
      sourceIndex: 1,
      siblingCount: 2,
      moveUp: plan(1, 0, "root:default"),
      moveDown: null,
    });
  });

  it("releases continuity only for deliberate selection without a data transition", () => {
    expect(
      shouldReleasePuckMovedSelection({
        movedComponentId: "moved",
        selectedComponentId: "other",
        dataChanged: false,
      }),
    ).toBe(true);
    expect(
      shouldReleasePuckMovedSelection({
        movedComponentId: "moved",
        selectedComponentId: "moved",
        dataChanged: false,
      }),
    ).toBe(false);
    expect(
      shouldReleasePuckMovedSelection({
        movedComponentId: "moved",
        selectedComponentId: "other",
        dataChanged: true,
      }),
    ).toBe(false);
    expect(
      shouldReleasePuckMovedSelection({
        movedComponentId: null,
        selectedComponentId: "other",
        dataChanged: false,
      }),
    ).toBe(false);
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
