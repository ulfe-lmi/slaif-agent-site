import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import {
  capSearchInput,
  matchesAllFacets,
  matchesFacet,
  matchesSearch,
  splitInList,
  type CollectionFacet,
  type FilterField,
} from "../src/renderer/bounded-collection-filter";
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
        binding_meta: {},
        regions: [],
        ancestors: [],
        default_locale: "en-US",
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

  it("renders the server-resolved language switcher fail-closed", () => {
    const locale = (tag: string, position: number, href: string | null) => ({
      id: `${position}${"0".repeat(29)}-0000-4000-8000-00000000000${position}`,
      site_id: "33333333-3333-4333-8333-333333333333",
      tag,
      enabled: true as const,
      is_default: position === 0,
      position,
      metadata: {},
      switcher_href: href,
    });
    const base = {
      route_kind: "page" as const,
      render_mode: "canonical" as const,
      site: {
        id: "33333333-3333-4333-8333-333333333333",
        key: "switch-site",
        canonical_revision: 1,
      },
      requested_path: "/",
      matched_path: "/",
      locale: "en-US",
      route_parameters: {},
      page: {
        id: "44444444-4444-4444-8444-444444444444",
        site_id: "33333333-3333-4333-8333-333333333333",
        slug: "home",
        title: "Switch home",
        status: "PUBLISHED" as const,
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
        id: "33333333-3333-4333-8333-333333333333",
        site_id: "33333333-3333-4333-8333-333333333333",
        schema_version: "theme-schema/v1",
        renderer_version: "renderer-v1",
        row_version: 1,
        palette: { preset: "ocean" },
        typography: { family: "system", scale: "balanced", weight: "regular" },
        layout: { content_width: "md", spacing: "md", grid_gap: "md" },
        shape: { radius: "md", shadow: "sm" },
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:01Z",
      },
      page_style: {
        id: "33333333-3333-4333-8333-333333333333",
        site_id: "33333333-3333-4333-8333-333333333333",
        schema_version: "theme-schema/v1",
        renderer_version: "renderer-v1",
        row_version: 1,
        palette: { preset: "ocean" },
        typography: { family: "system", scale: "balanced", weight: "regular" },
        layout: { content_width: "md", spacing: "md", grid_gap: "md" },
        shape: { radius: "md", shadow: "sm" },
        created_at: "2026-01-01T00:00:00Z",
        updated_at: "2026-01-01T00:00:01Z",
      },
      navigation: [],
      bindings: {},
      binding_meta: {},
      ancestors: [],
      default_locale: "en-US",
    } as const;
    const region = (region_key: "header" | "footer") => ({
      id: `${region_key === "header" ? 5 : 6}${"0".repeat(26)}-0000-4000-8000-00000000000${
        region_key === "header" ? 1 : 2
      }`,
      region_key,
      variant:
        region_key === "header"
          ? ("institutional" as const)
          : ("single-column" as const),
      entries: region_key === "header" ? [{ label: "switch-site", href: "/" }] : [],
      note: null,
      row_version: 1,
    });
    const resolvable = renderToStaticMarkup(
      renderProjection({
        ...base,
        locales: [locale("en-US", 0, null), locale("sl-SI", 1, "/sl-SI/home")],
        regions: [region("header"), region("footer")],
      }),
    );
    expect(resolvable).toContain(`<span aria-current="true">en-US</span>`);
    expect(resolvable).toContain(`<a href="/s/switch-site/sl-SI/home">sl-SI</a>`);
    expect(resolvable).not.toContain("renderer-region-language-inert");
    const unresolvable = renderToStaticMarkup(
      renderProjection({
        ...base,
        locales: [locale("en-US", 0, null), locale("sl-SI", 1, null)],
        regions: [region("header"), region("footer")],
      }),
    );
    expect(unresolvable).toContain(`<span aria-current="true">en-US</span>`);
    expect(unresolvable).toContain("renderer-region-language-inert");
    expect(unresolvable).toContain(">sl-SI</span>");
    expect(unresolvable).not.toContain(`/s/switch-site/sl-SI`);
  });

  it("renders the 078/7 static catalog components with bounded markup", () => {
    const cta = renderToStaticMarkup(
      renderComponent(
        {
          componentType: "CallToAction",
          props: {
            heading: "Ship it",
            text: "Bounded copy",
            label: "Read more",
            href: "/news",
            variant: "secondary",
          },
        },
        "en",
      ),
    );
    expect(cta).toContain("renderer-call-to-action--secondary");
    expect(cta).toContain("<h2>Ship it</h2>");
    expect(cta).toContain("<p>Bounded copy</p>");
    expect(cta).toContain('href="/news"');
    expect(cta).toContain("Read more");
    const ctaUnsafeHref = renderToStaticMarkup(
      renderComponent(
        {
          componentType: "CallToAction",
          props: {
            heading: "Ship it",
            label: "Read more",
            href: "https://evil.example",
          },
        },
        "en",
      ),
    );
    expect(ctaUnsafeHref).toContain('href="/"');
    expect(ctaUnsafeHref).not.toContain("evil.example");

    const contact = renderToStaticMarkup(
      renderComponent(
        {
          componentType: "ContactBlock",
          props: {
            organization: "SLAIF Institute",
            address: "Trubarjeva 1",
            phone: "01 000",
            email: "contact@example",
            hours: "Mon-Fri 9-17",
          },
        },
        "en",
      ),
    );
    expect(contact).toContain("renderer-contact");
    expect(contact).toContain("<h2>SLAIF Institute</h2>");
    expect(contact).toContain("renderer-contact-address");
    expect(contact).toContain("renderer-contact-phone");
    expect(contact).toContain("renderer-contact-email");
    expect(contact).toContain("renderer-contact-hours");

    const related = renderToStaticMarkup(
      renderComponent(
        {
          componentType: "RelatedItems",
          props: { heading: "Related" },
        },
        "en",
        [
          {
            id: "99999999-9999-4999-8999-999999999999",
            slug: "second",
            values: { title: "Second story", summary: "Body" },
          },
        ],
      ),
    );
    expect(related).toContain("renderer-related");
    expect(related).toContain("<h2>Related</h2>");
    expect(related).toContain("<h2>Second story</h2>");
    expect(
      renderToStaticMarkup(
        renderComponent(
          { componentType: "RelatedItems", props: { heading: "Related" } },
          "en",
          [],
        ),
      ),
    ).toBe("");
  });

  it("renders the bounded client-filter components statelessly", () => {
    const items = [
      { id: "1", slug: "a", values: { title: "Alpha news", rank: 3 } },
      { id: "2", slug: "b", values: { title: "Beta news", rank: 7 } },
    ];
    const search = renderToStaticMarkup(
      renderComponent(
        {
          componentType: "CollectionSearch",
          props: { placeholder: "Find stories" },
        },
        "en",
        items,
        { filter_fields: [{ key: "title", primitive: "short_text" }] },
      ),
    );
    expect(search).toContain("renderer-collection-search");
    expect(search).toContain('maxLength="256"');
    expect(search).toContain("Find stories");
    expect(search).toContain(">Alpha news<");

    const filterMarkup = renderToStaticMarkup(
      renderComponent(
        {
          componentType: "CollectionFilter",
          props: {
            facets: [{ fieldKey: "rank", operator: "gte", value: "5" }],
          },
        },
        "en",
        items,
        { filter_fields: [{ key: "rank", primitive: "integer" }] },
      ),
    );
    expect(filterMarkup).toContain("renderer-collection-filter");
    expect(filterMarkup).toContain("rank gte");
    expect(filterMarkup).not.toContain(">Alpha news<");
    expect(filterMarkup).toContain(">Beta news<");

    const emptyFilter = renderToStaticMarkup(
      renderComponent(
        {
          componentType: "CollectionFilter",
          props: { facets: [{ fieldKey: "rank", operator: "gte", value: "9" }] },
        },
        "en",
        items,
        { filter_fields: [{ key: "rank", primitive: "integer" }] },
      ),
    );
    expect(emptyFilter).toContain("renderer-collection-filter-empty");
  });

  it("keeps the bounded in-memory filter semantics fixed and fail-closed", () => {
    const fields: readonly FilterField[] = [
      { key: "title", primitive: "short_text" },
      { key: "body", primitive: "long_text" },
      { key: "rank", primitive: "integer" },
      { key: "kind", primitive: "enum" },
      { key: "when", primitive: "date" },
      { key: "active", primitive: "boolean" },
    ];
    const item = {
      id: "1",
      slug: "s",
      values: {
        title: "Weekly Brief",
        body: "the details",
        rank: 7,
        kind: "News",
        when: "2026-09-01",
        active: true,
      },
    };
    expect(matchesSearch(item, fields, "weekly")).toBe(true);
    expect(matchesSearch(item, fields, "details")).toBe(true);
    expect(matchesSearch(item, fields, "absent")).toBe(false);
    expect(capSearchInput("x".repeat(300))).toHaveLength(256);

    const facet = (
      fieldKey: string,
      operator: string,
      value: string,
    ): CollectionFacet => ({ fieldKey, operator, value });
    expect(matchesFacet(item, fields, facet("title", "contains", "week"))).toBe(true);
    expect(matchesFacet(item, fields, facet("title", "prefix", "weekly"))).toBe(true);
    expect(matchesFacet(item, fields, facet("rank", "gte", "7"))).toBe(true);
    expect(matchesFacet(item, fields, facet("rank", "lt", "7"))).toBe(false);
    expect(matchesFacet(item, fields, facet("kind", "in", "blog, news ,press"))).toBe(
      true,
    );
    expect(matchesFacet(item, fields, facet("kind", "in", "blog,press"))).toBe(false);
    expect(matchesFacet(item, fields, facet("when", "gte", "2026-09-01"))).toBe(true);
    expect(matchesFacet(item, fields, facet("when", "lt", "2026-09-01"))).toBe(false);
    expect(matchesFacet(item, fields, facet("active", "eq", "true"))).toBe(true);
    // fail-closed: unknown primitive, missing value, unknown field, bad number
    expect(matchesFacet(item, fields, facet("missing", "eq", "x"))).toBe(false);
    expect(matchesFacet(item, fields, facet("kind", "contains", "news"))).toBe(false);
    expect(
      matchesFacet(
        { id: "2", slug: "t", values: {} },
        fields,
        facet("title", "contains", "weekly"),
      ),
    ).toBe(false);
    expect(matchesFacet(item, fields, facet("rank", "eq", "nope"))).toBe(false);
    expect(
      matchesAllFacets(item, fields, [
        facet("title", "contains", "week"),
        facet("rank", "gte", "5"),
      ]),
    ).toBe(true);
    expect(
      matchesAllFacets(item, fields, [
        facet("title", "contains", "week"),
        facet("rank", "gt", "7"),
      ]),
    ).toBe(false);
    expect(splitInList(",a,,b,")).toEqual(["a", "b"]);
    expect(splitInList("x".repeat(40))).toEqual(["x".repeat(40)]);
  });

  it("renders flight-free static variants with identical initial-state markup", () => {
    const items = [
      { id: "1", slug: "a", values: { title: "Alpha news", rank: 3 } },
      { id: "2", slug: "b", values: { title: "Beta news", rank: 7 } },
    ];
    const interactiveSearch = renderToStaticMarkup(
      renderComponent(
        { componentType: "CollectionSearch", props: { placeholder: "Find" } },
        "en",
        items,
        { filter_fields: [{ key: "title", primitive: "short_text" }] },
      ),
    );
    const staticSearch = renderToStaticMarkup(
      renderComponent(
        { componentType: "CollectionSearch", props: { placeholder: "Find" } },
        "en",
        items,
        { filter_fields: [{ key: "title", primitive: "short_text" }] },
        false,
      ),
    );
    // The only SSR artifact difference is the controlled-input value
    // attribute React emits for the interactive variant; normalize it and
    // the initial-state markup is byte-identical.
    const normalized = (markup: string) =>
      markup.replace(/ value=""/g, "").replace(/\s+/g, " ");
    expect(normalized(staticSearch)).toBe(normalized(interactiveSearch));

    const facets = [{ fieldKey: "rank", operator: "gte", value: "5" }];
    const interactiveFilter = renderToStaticMarkup(
      renderComponent(
        { componentType: "CollectionFilter", props: { facets } },
        "en",
        items,
        { filter_fields: [{ key: "rank", primitive: "integer" }] },
      ),
    );
    const staticFilter = renderToStaticMarkup(
      renderComponent(
        { componentType: "CollectionFilter", props: { facets } },
        "en",
        items,
        { filter_fields: [{ key: "rank", primitive: "integer" }] },
        false,
      ),
    );
    expect(staticFilter).toBe(interactiveFilter);
    // Initial facet state: only rank 7 is visible; the empty state is not
    // rendered because the initial visible set is non-empty.
    expect(staticFilter).toContain(">Beta news<");
    expect(staticFilter).not.toContain(">Alpha news<");
    expect(staticFilter).not.toContain("renderer-collection-filter-empty");
  });
});
