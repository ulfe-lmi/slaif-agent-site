import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  compositionToPuck,
  puckToComposition,
  type NormalizedCompositionNode,
} from "../../../packages/composition-schema/src/puck-adapter";
import { renderComponent, renderProjection } from "../src/renderer/components";

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

  it("renders only bounded responsive design classes", () => {
    const section = renderToStaticMarkup(
      renderComponent(
        {
          componentType: "Section",
          props: {
            variant: { desktop: "default", tablet: "narrow", mobile: "full" },
            alignment: { desktop: "start", tablet: "center", mobile: "stretch" },
          },
        },
        "en",
      ),
    );
    const grid = renderToStaticMarkup(
      renderComponent(
        {
          componentType: "Grid",
          props: {
            columns: { desktop: 4, tablet: 2, mobile: 1 },
            gap: { desktop: "lg", tablet: "md", mobile: "sm" },
            alignment: "center",
          },
        },
        "en",
      ),
    );
    const heading = renderToStaticMarkup(
      renderComponent(
        {
          componentType: "Heading",
          props: { text: "Safe heading", level: 2, alignment: "center" },
        },
        "en",
      ),
    );
    expect(section).toContain("renderer-section--default");
    expect(section).toContain("renderer-section--tablet-narrow");
    expect(section).toContain("renderer-section--mobile-full");
    expect(section).toContain("renderer-align--tablet-center");
    expect(grid).toContain("renderer-grid--4");
    expect(grid).toContain("renderer-grid--tablet-2");
    expect(grid).toContain("renderer-grid--mobile-1");
    expect(grid).toContain("renderer-gap--tablet-md");
    expect(heading).toContain("renderer-align--center");
    expect(section + grid + heading).not.toMatch(/style=|class="[^"]*javascript/i);
  });

  it("renders classified visual properties with responsive semantics", () => {
    const button = renderToStaticMarkup(
      renderComponent(
        {
          componentType: "Button",
          props: {
            label: "Open",
            href: "/open",
            variant: { desktop: "primary", tablet: "secondary", mobile: "ghost" },
          },
        },
        "en",
      ),
    );
    const image = renderToStaticMarkup(
      renderComponent(
        {
          componentType: "Image",
          props: {
            mediaId: "11111111-1111-4111-8111-111111111111",
            alt: "Preview",
            aspectRatio: { desktop: "16:9", mobile: "1:1" },
          },
        },
        "en",
      ),
    );
    const collection = renderToStaticMarkup(
      renderComponent(
        {
          componentType: "CollectionGrid",
          props: {
            viewId: "22222222-2222-4222-8222-222222222222",
            columns: { desktop: 4, tablet: 2, mobile: 1 },
          },
        },
        "en",
      ),
    );
    expect(button).toContain("renderer-button--primary");
    expect(button).toContain("renderer-button--tablet-secondary");
    expect(button).toContain("renderer-button--mobile-ghost");
    expect(image).toContain("renderer-image-placeholder--16-9");
    expect(image).toContain("renderer-image-placeholder--mobile-1-1");
    expect(collection).toContain("renderer-collection-grid--4");
    expect(collection).toContain("renderer-collection-grid--tablet-2");
    expect(collection).toContain("renderer-collection-grid--mobile-1");
  });

  it("applies only schema-owned theme classes to the shared projection root", () => {
    const rendered = renderToStaticMarkup(
      renderProjection({
        route_kind: "page",
        render_mode: "preview",
        site: {
          id: "11111111-1111-4111-8111-111111111111",
          key: "theme-site",
          canonical_revision: 1,
        },
        requested_path: "/",
        matched_path: "/",
        locale: "en-US",
        route_parameters: {},
        page: {
          id: "22222222-2222-4222-8222-222222222222",
          site_id: "11111111-1111-4111-8111-111111111111",
          slug: "home",
          title: "Theme home",
          status: "DRAFT",
          locale: "en-US",
          parent_id: null,
          route_template: null,
          effective_route: "/",
          row_version: 1,
        },
        composition: {
          schema_version: "site-composition/v1",
          catalog_version: "catalog-v1",
          nodes: [],
        },
        theme: {
          id: "11111111-1111-4111-8111-111111111111",
          site_id: "11111111-1111-4111-8111-111111111111",
          schema_version: "theme-schema/v1",
          renderer_version: "renderer-v1",
          row_version: 2,
          palette: { preset: "meadow" },
          typography: { family: "serif", scale: "spacious", weight: "bold" },
          layout: { content_width: "lg", spacing: "lg", grid_gap: "sm" },
          shape: { radius: "lg", shadow: "md" },
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:01Z",
        },
        page_style: {
          id: "11111111-1111-4111-8111-111111111111",
          site_id: "11111111-1111-4111-8111-111111111111",
          schema_version: "theme-schema/v1",
          renderer_version: "renderer-v1",
          row_version: 2,
          palette: { preset: "ember" },
          typography: { family: "mono", scale: "compact", weight: "medium" },
          layout: { content_width: "xl", spacing: "sm", grid_gap: "lg" },
          shape: { radius: "full", shadow: "none" },
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-01T00:00:01Z",
        },
        locales: [],
        navigation: [],
        bindings: {},
      }),
    );
    expect(rendered).toContain("renderer-theme-palette--ember");
    expect(rendered).toContain("renderer-theme-family--mono");
    expect(rendered).toContain("renderer-theme-width--xl");
    expect(rendered).toContain("renderer-theme-radius--full");
    expect(rendered).not.toMatch(/style=|javascript:|data:text/i);
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
