import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  compositionToPuck,
  puckToComposition,
  type NormalizedCompositionNode,
} from "../../../packages/composition-schema/src/puck-adapter";
import { renderComponent } from "../src/renderer/components";

const fixtures: readonly NormalizedCompositionNode[] = [
  {
    id: "rich-text",
    componentType: "RichText",
    schemaVersion: "1",
    parentId: null,
    slotKey: "default",
    orderKey: 0,
    props: {
      content: {
        type: "paragraph",
        children: [{ text: "Rich & <b>text</b>", bold: true }],
      },
    },
  },
  {
    id: "statistics",
    componentType: "Statistics",
    schemaVersion: "1",
    parentId: null,
    slotKey: "default",
    orderKey: 1,
    props: { items: [{ label: "Users", value: "42" }] },
  },
  {
    id: "timeline",
    componentType: "Timeline",
    schemaVersion: "1",
    parentId: null,
    slotKey: "default",
    orderKey: 2,
    props: { items: [{ title: "Launch", description: "Released." }] },
  },
  {
    id: "faq",
    componentType: "FAQ",
    schemaVersion: "1",
    parentId: null,
    slotKey: "default",
    orderKey: 3,
    props: { items: [{ question: "Why?", answer: "Because." }] },
  },
];

describe("trusted catalog renderer behavior", () => {
  it("round-trips every structured catalog fixture through production Puck", () => {
    const puck = compositionToPuck(fixtures);
    expect(puckToComposition(puck)).toEqual(fixtures);
    expect(puck.metadata?.["rich-text"]).toMatchObject({
      componentType: "RichText",
      parentId: null,
      slotKey: "default",
      orderKey: 0,
      schemaVersion: "1",
    });
  });

  it("executes the production React renderer with visible safe semantics", () => {
    const rendered = fixtures.map((fixture) =>
      renderToStaticMarkup(
        renderComponent(
          { componentType: fixture.componentType, props: fixture.props },
          "en",
        ),
      ),
    );
    expect(rendered[0]).toContain("Rich &amp; &lt;b&gt;text&lt;/b&gt;");
    expect(rendered[0]).toContain("<strong>");
    expect(rendered[0]).toContain("<p>");
    expect(rendered[1]).toContain("<dt>Users</dt>");
    expect(rendered[1]).toContain("<dd>42</dd>");
    expect(rendered[2]).toContain("<h2>Launch</h2>");
    expect(rendered[2]).toContain("<p>Released.</p>");
    expect(rendered[3]).toContain("<summary>Why?</summary>");
    expect(rendered[3]).toContain("<p>Because.</p>");
    expect(rendered.join(" ")).not.toContain("<script");
    expect(rendered.join(" ")).not.toContain("<style");
    expect(rendered.join(" ")).not.toContain("<b>text</b>");
  });

  it("rejects malformed nested data before rendering", () => {
    expect(() =>
      compositionToPuck([
        {
          ...fixtures[0]!,
          props: {
            content: {
              type: "paragraph",
              children: [{ text: "bad", unknown: true }],
            },
          },
        },
      ]),
    ).toThrow("invalid-component-props");
    expect(() =>
      compositionToPuck([
        {
          ...fixtures[1]!,
          props: { items: [{ label: "missing value" }] },
        },
      ]),
    ).toThrow("invalid-component-props");
    expect(() =>
      compositionToPuck([
        {
          ...fixtures[0]!,
          props: {
            content: {
              type: "paragraph",
              children: [{ text: "vbscript:alert(1)" }],
            },
          },
        },
      ]),
    ).toThrow("invalid-component-props");
  });
});
