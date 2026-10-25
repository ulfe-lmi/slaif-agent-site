// 082/2 R2 web unit proof: the resolver's content source is exclusively the
// trusted read-model document. These tests exercise the pure mapping
// (projectionFromReviewDocument) against in-memory documents: page match,
// locale-prefix contract, frozen redirects, uniform not_found, session-scoped
// private media, navigation projection, determinism, and the structural gate.
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  FACET_INPUT_MAX_LENGTH,
  POST_FORM_MAX_BODY_LENGTH,
  POST_FORM_MAX_FIELDS,
  POST_FORM_MAX_RAW_BYTES,
  controlFieldNames,
  controlInventory,
  defaultControlStates,
  decodePostedForm,
  selectPostedControls,
} from "../src/renderer/bounded-collection-filter.ts";
import {
  isReviewDocument,
  projectionFromReviewDocument,
  reviewRedirectTarget,
  selectReviewView,
  siteLocalPath,
} from "../src/sites/review-projection.ts";

const SITE_ID = "11111111-1111-4111-8111-111111111111";
const WORKSPACE_ID = "22222222-2222-4222-8222-222222222222";

const locale = (tag, { enabled = true, is_default = false, position = 0 } = {}) => ({
  tag,
  enabled,
  is_default,
  position,
});

const page = (extra = {}) => ({
  id: `page-${extra.slug ?? "x"}`,
  site_id: SITE_ID,
  slug: extra.slug ?? "x",
  title: extra.title ?? "Title",
  status: extra.status ?? "PUBLISHED",
  locale: extra.locale ?? "en",
  parent_id: extra.parent_id ?? null,
  route_template: extra.route_template ?? null,
  effective_route: extra.effective_route ?? `/${extra.slug ?? "x"}`,
  row_version: extra.row_version ?? 1,
  nodes: extra.nodes ?? [],
});

const node = (extra = {}) => ({
  id: extra.id ?? "node-1",
  component_type: extra.component_type ?? "Section",
  schema_version: "1",
  parent_id: extra.parent_id ?? null,
  slot_key: extra.slot_key ?? "main",
  order_key: extra.order_key ?? 0,
  props: extra.props ?? {},
  children: extra.children ?? [],
});

const state = (overrides = {}) => ({
  state_version: "review-snapshot/v1",
  workspace_id: WORKSPACE_ID,
  site_id: SITE_ID,
  site: {
    site_key: "demo",
    display_name: "Demo",
    default_locale: "en",
    component_catalog_version: "1",
  },
  base_site_revision: 7,
  operation_watermark: 3,
  locales: [locale("en", { is_default: true })],
  theme: {},
  regions: [],
  navigation: { definitions: [], items: [] },
  redirects: [],
  pages: [],
  media: {},
  ...overrides,
});

const document = (overrides = {}) => ({
  snapshot: {
    id: "snapshot-1",
    digest: "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
    state_version: "review-snapshot/v1",
    revision_watermark: 3,
    base_site_revision: 7,
    status: "COMPLETE",
    created_at: "2026-10-05T00:00:00Z",
    created_by: "human:reviewer",
    versions: {
      catalog: "catalog-v1",
      composition_schema: "site-composition/v1",
      content_model: "content-model/v1",
      design_system: "design-system/v1",
      puck: "0.20.2",
      renderer: "renderer-v1",
    },
  },
  drift: { current_site_revision: 7, base_site_revision: 7, equal: true },
  timeline: [],
  resource_diff: {},
  summaries: {},
  validation: { report: {}, warnings: [] },
  evidence: { runs: [], artifacts: [] },
  metadata: {
    workspace: {
      id: WORKSPACE_ID,
      title: "Demo review",
      actor_type: "HUMAN",
      status: "REVIEW",
    },
    site: { id: SITE_ID, key: "demo" },
    capabilities: [],
    quota_policy: {},
    agent_session_browser: { versions: {}, review_jobs: [] },
  },
  normalized_state: state(),
  ...overrides,
});

test("page match returns the frozen projection with the nested node tree", () => {
  const about = page({
    slug: "about",
    effective_route: "/about",
    nodes: [
      node({
        id: "outer",
        children: [
          node({ id: "inner", component_type: "Heading", parent_id: "outer" }),
        ],
      }),
    ],
  });
  const doc = document({ normalized_state: state({ pages: [about] }) });
  const result = projectionFromReviewDocument(doc, "/about");
  assert.equal(result.kind, "page");
  assert.equal(result.projection.render_mode, "preview");
  assert.equal(result.projection.matched_path, "/about");
  assert.equal(result.projection.locale, "en");
  assert.equal(result.projection.page.effective_route, "/about");
  assert.equal(result.projection.site.canonical_revision, 7);
  const [outer] = result.projection.composition.nodes;
  assert.equal(outer.id, "outer");
  assert.equal(outer.children.length, 1);
  assert.equal(outer.children[0].id, "inner");
  assert.equal(outer.children[0].component_type, "Heading");
  assert.deepEqual(result.projection.theme, {});
  assert.deepEqual(result.projection.page_style, {});
});

test("locale prefix contract: default unprefixed, non-default prefixed, default prefix rejected", () => {
  const doc = document({
    normalized_state: state({
      locales: [locale("en", { is_default: true }), locale("fr", { position: 1 })],
      pages: [
        page({ slug: "root", effective_route: "/", locale: "en" }),
        page({ slug: "root-fr", effective_route: "/fr", locale: "fr" }),
      ],
    }),
  });
  const root = projectionFromReviewDocument(doc, "/");
  assert.equal(root.kind, "page");
  assert.equal(root.projection.locale, "en");
  const frRoot = projectionFromReviewDocument(doc, "/fr");
  assert.equal(frRoot.kind, "page");
  assert.equal(frRoot.projection.locale, "fr");
  // The default locale has no prefix in the effective-route contract.
  assert.equal(projectionFromReviewDocument(doc, "/en").kind, "not_found");
});

test("frozen redirect set: selected by route and locale, re-rooted by the resolver", () => {
  const doc = document({
    normalized_state: state({
      locales: [locale("en", { is_default: true }), locale("fr", { position: 1 })],
      redirects: [
        {
          id: "r-1",
          site_id: SITE_ID,
          source_route: "/old",
          target: "/new",
          status_code: 301,
          locale: null,
        },
        {
          id: "r-2",
          site_id: SITE_ID,
          source_route: "/fr/x",
          target: "/fr/y",
          status_code: 308,
          locale: "fr",
        },
      ],
      pages: [page({ slug: "y-fr", effective_route: "/fr/y", locale: "fr" })],
    }),
  });
  const moved = projectionFromReviewDocument(doc, "/old");
  assert.deepEqual(moved, { kind: "redirect", target: "/new", status_code: 301 });
  const scoped = projectionFromReviewDocument(doc, "/fr/x");
  assert.deepEqual(scoped, { kind: "redirect", target: "/fr/y", status_code: 308 });
  // Locale-scoped binding does not match the default locale's route.
  assert.equal(projectionFromReviewDocument(doc, "/x").kind, "not_found");
  assert.equal(
    reviewRedirectTarget("/fr/y", WORKSPACE_ID),
    `/review/${WORKSPACE_ID}/fr/y`,
  );
  assert.equal(reviewRedirectTarget("/", WORKSPACE_ID), `/review/${WORKSPACE_ID}`);
  assert.equal(
    reviewRedirectTarget("https://example.com", WORKSPACE_ID),
    "https://example.com",
  );
});

test("duplicate frozen redirect binding fails closed", () => {
  const doc = document({
    normalized_state: state({
      redirects: [
        {
          id: "r-1",
          site_id: SITE_ID,
          source_route: "/dup",
          target: "/a",
          status_code: 301,
          locale: null,
        },
        {
          id: "r-2",
          site_id: SITE_ID,
          source_route: "/dup",
          target: "/b",
          status_code: 302,
          locale: null,
        },
      ],
    }),
  });
  assert.equal(projectionFromReviewDocument(doc, "/dup").kind, "not_found");
});

test("uniform not_found: reserved, malformed, percent-encoded, unmatched, ambiguous", () => {
  const doc = document({
    normalized_state: state({
      pages: [
        page({ slug: "dup", effective_route: "/dup", status: "PUBLISHED" }),
        page({ slug: "dup2", effective_route: "/dup", status: "DRAFT" }),
        page({ slug: "draft", effective_route: "/draft" }),
      ],
    }),
  });
  const notFound = [
    "/api/x", // reserved top level
    "/media/x", // reserved top level
    "about", // no leading slash
    "/about/.", // dot segment
    "/a/b//c", // double slash
    "/a/%2f", // percent encoding is rejected by the trusted mirror
    "/missing", // no matching page
    "/dup", // two pages on the same effective route + locale
  ];
  for (const path of notFound) {
    assert.equal(
      projectionFromReviewDocument(doc, path).kind,
      "not_found",
      `expected uniform not_found for ${path}`,
    );
  }
  // DRAFT is a preview-renderable status (the frozen mirror).
  assert.equal(projectionFromReviewDocument(doc, "/draft").kind, "page");
});

test("frozen media always renders through the session-scoped private path", () => {
  const doc = document({
    normalized_state: state({
      pages: [
        page({
          slug: "gallery",
          effective_route: "/gallery",
          nodes: [
            node({ id: "img", component_type: "Image", props: { mediaId: "media-1" } }),
          ],
        }),
      ],
      media: {
        "media-1": {
          id: "media-1",
          mime_type: "image/png",
          size_bytes: 42,
          content_hash: "sha256:media",
          public_status: "PRIVATE",
        },
      },
    }),
  });
  const result = projectionFromReviewDocument(doc, "/gallery");
  assert.equal(result.kind, "page");
  const [image] = result.projection.composition.nodes;
  assert.equal(image.media.url, `/media/v1/sites/${SITE_ID}/assets/media-1/content`);
  assert.equal(JSON.stringify(result.projection).includes("/media/public/"), false);
});

test("navigation projects locale-filtered, position-ordered items with label fallback", () => {
  const doc = document({
    normalized_state: state({
      locales: [locale("en", { is_default: true }), locale("fr", { position: 1 })],
      pages: [
        page({ slug: "about", effective_route: "/about" }),
        page({ slug: "about-fr", effective_route: "/fr/about", locale: "fr" }),
      ],
      navigation: {
        definitions: [
          {
            id: "nav-1",
            key: "primary",
            label: "Nav",
            labels: { en: "Primary", fr: "Primaire" },
            settings: {},
          },
        ],
        items: [
          {
            id: "item-1",
            navigation_id: "nav-1",
            parent_id: null,
            locale: null,
            position: 2,
            labels: { en: "About", fr: "A propos" },
            target_kind: "PAGE",
            resolved_target: "/about",
          },
          {
            id: "item-2",
            navigation_id: "nav-1",
            parent_id: "item-1",
            locale: "fr",
            position: 1,
            labels: { fr: "Detail" },
            target_kind: "PAGE",
            resolved_target: "/fr/about",
          },
        ],
      },
    }),
  });
  const en = projectionFromReviewDocument(doc, "/about");
  assert.equal(en.kind, "page");
  const enNav = en.projection.navigation[0];
  assert.equal(enNav.label, "Primary");
  assert.equal(enNav.items.length, 1);
  assert.equal(enNav.items[0].label, "About");
  assert.equal(enNav.items[0].children.length, 0); // fr-scoped child filtered out
  const fr = projectionFromReviewDocument(doc, "/fr/about");
  assert.equal(fr.kind, "page");
  const frNav = fr.projection.navigation[0];
  assert.equal(frNav.label, "Primaire");
  assert.equal(frNav.items[0].label, "A propos");
  assert.equal(frNav.items[0].children.length, 1);
  assert.equal(frNav.items[0].children[0].label, "Detail");
});

test("the projection is a deterministic function of the document", () => {
  const doc = document({
    normalized_state: state({
      pages: [
        page({
          slug: "about",
          effective_route: "/about",
          nodes: [node({ id: "n1" }), node({ id: "n2", order_key: 1 })],
        }),
      ],
    }),
  });
  const first = projectionFromReviewDocument(doc, "/about");
  const second = projectionFromReviewDocument(doc, "/about");
  assert.deepEqual(first, second);
  assert.equal(JSON.stringify(first), JSON.stringify(second));
});

const faithfulPage = {
  route_kind: "page",
  render_mode: "review",
  site: { id: SITE_ID, key: "demo", canonical_revision: 7 },
  requested_path: "/about",
  matched_path: "/about",
  locale: "en",
  route_parameters: {},
  page: {
    id: "page-about",
    site_id: SITE_ID,
    slug: "about",
    title: "About",
    status: "PUBLISHED",
    locale: "en",
    parent_id: null,
    route_template: null,
    effective_route: "/about",
    row_version: 1,
  },
  composition: {
    schema_version: "1",
    catalog_version: "catalog-v1",
    nodes: [node({ id: "v2-node", component_type: "Section" })],
  },
  theme: {},
  page_style: {},
  locales: [],
  navigation: [],
  bindings: {},
  binding_meta: {},
  regions: [],
  ancestors: [],
  default_locale: "en",
};

const faithfulRedirect = {
  route_kind: "redirect",
  render_mode: "review",
  site: { id: SITE_ID, key: "demo", canonical_revision: 7 },
  requested_path: "/old",
  matched_path: "/old",
  locale: "en",
  locales: [],
  redirect: {
    source: "/old",
    target: "/new",
    status_code: 301,
    locale: null,
  },
};

test("selectReviewView: v2 renders the faithful frozen read projection", () => {
  const doc = document({
    snapshot: { ...document().snapshot, state_version: "review-snapshot/v2" },
  });
  const view = selectReviewView(doc, faithfulPage, WORKSPACE_ID, "/about");
  assert.equal(view.kind, "page");
  assert.equal(view.projection, faithfulPage);
});

test("selectReviewView: v2 null projection is a uniform refusal (no v1 fallback)", () => {
  const doc = document({
    snapshot: { ...document().snapshot, state_version: "review-snapshot/v2" },
    normalized_state: state({
      pages: [page({ slug: "about", effective_route: "/about" })],
    }),
  });
  assert.equal(selectReviewView(doc, null, WORKSPACE_ID, "/about").kind, "not_found");
  // the legacy mapping WOULD resolve that state; the refusal proves
  // selection is by the stored v2 fact, not by v1 renderability.
  assert.equal(projectionFromReviewDocument(doc, "/about").kind, "page");
});

test("selectReviewView: v2 redirects re-root internal targets, pass external", () => {
  const doc = document({
    snapshot: { ...document().snapshot, state_version: "review-snapshot/v2" },
  });
  const internal = selectReviewView(doc, faithfulRedirect, WORKSPACE_ID, "/old");
  assert.deepEqual(internal, {
    kind: "redirect",
    target: `/review/${WORKSPACE_ID}/new`,
    status_code: 301,
  });
  const external = selectReviewView(
    doc,
    {
      ...faithfulRedirect,
      redirect: { ...faithfulRedirect.redirect, target: "https://example.com" },
    },
    WORKSPACE_ID,
    "/old",
  );
  assert.equal(external.target, "https://example.com");
});

test("selectReviewView: v1 uses the legacy web-side projection (honest limitation)", () => {
  const doc = document({
    normalized_state: state({
      pages: [page({ slug: "about", effective_route: "/about" })],
    }),
  });
  const view = selectReviewView(doc, null, WORKSPACE_ID, "/about");
  assert.equal(view.kind, "page");
  assert.equal(view.projection.page.effective_route, "/about");
  const redirectView = selectReviewView(
    document({
      normalized_state: state({
        redirects: [
          {
            id: "r-1",
            site_id: SITE_ID,
            source_route: "/old",
            target: "/new",
            status_code: 301,
            locale: null,
          },
        ],
      }),
    }),
    null,
    WORKSPACE_ID,
    "/old",
  );
  assert.deepEqual(redirectView, {
    kind: "redirect",
    target: `/review/${WORKSPACE_ID}/new`,
    status_code: 301,
  });
});

test("selectReviewView: unknown stored state versions refuse uniformly", () => {
  for (const stateVersion of ["state/v1", "review-snapshot/v3", "", "V2"]) {
    const doc = document({
      snapshot: { ...document().snapshot, state_version: stateVersion },
      normalized_state: state({
        pages: [page({ slug: "about", effective_route: "/about" })],
      }),
    });
    assert.equal(
      selectReviewView(doc, faithfulPage, WORKSPACE_ID, "/about").kind,
      "not_found",
      `expected uniform refusal for stored state_version=${JSON.stringify(stateVersion)}`,
    );
  }
});

test("the structural gate accepts the trusted shape and rejects corruption", () => {
  assert.equal(isReviewDocument(document()), true);
  assert.equal(isReviewDocument({ ...document(), drift: {} }), false);
  assert.equal(
    isReviewDocument({
      ...document(),
      normalized_state: state({ pages: [{ ...page(), nodes: "not-an-array" }] }),
    }),
    false,
  );
  assert.equal(
    isReviewDocument({
      ...document(),
      metadata: {
        ...document().metadata,
        workspace: { ...document().metadata.workspace, title: 7 },
      },
    }),
    false,
  );
});

test("site addressing: captured key strips /s/<key>, direct site-local passes, malformed/foreign refuse", () => {
  const doc = document();
  // The generated-link form: the captured key is the only prefix stripped.
  assert.equal(siteLocalPath(doc, ["s", "demo", "guide"]), "/guide");
  assert.equal(siteLocalPath(doc, ["s", "demo"]), "/");
  // The redirect re-root form and plain site-local requests pass through.
  assert.equal(siteLocalPath(doc, ["guide", "sub"]), "/guide/sub");
  assert.equal(siteLocalPath(doc, []), "/");
  assert.equal(siteLocalPath(doc, undefined), "/");
  // A lone "s" is a malformed prefix fragment: uniform refusal, never a
  // fallback to a coincidentally retained /s route.
  assert.equal(siteLocalPath(doc, ["s"]), null);
  // A foreign binding is never reinterpreted as a site-local route.
  assert.equal(siteLocalPath(doc, ["s", "other", "guide"]), null);
  // Exact key match only: no case folding, no prefix match.
  assert.equal(siteLocalPath(doc, ["s", "Demo", "guide"]), null);
  assert.equal(siteLocalPath(doc, ["s", "dem", "guide"]), null);
});

test("site addressing: the captured key is the authority, never the live metadata key", () => {
  const base = document();
  const doc = {
    ...base,
    // 071 selects metadata.site.key LIVE from control.site: a deliberately
    // differing live value that must not become frozen addressing authority.
    metadata: {
      ...base.metadata,
      site: { id: SITE_ID, key: "live-other" },
    },
    normalized_state: state({
      site: {
        site_key: "demo",
        display_name: "Demo",
        default_locale: "en",
        component_catalog_version: "1",
      },
    }),
  };
  // The CAPTURED key resolves...
  assert.equal(siteLocalPath(doc, ["s", "demo", "guide"]), "/guide");
  // ...the differing LIVE metadata key is refused...
  assert.equal(siteLocalPath(doc, ["s", "live-other", "guide"]), null);
  // ...and direct site-local paths are unaffected by either value.
  assert.equal(siteLocalPath(doc, ["guide"]), "/guide");
});

/* ------------------------------------------------------------------ */
/* 083/5-b same-path read-only POST: strict bounded decode + selection */
/* ------------------------------------------------------------------ */

test("POST form decode: real UTF-8 form encoding round-trips, malformed input refuses", () => {
  // The native form encoder, accessed via globalThis (ES builtin) so the
  // test stays within the linted global set.
  const URLSearchParamsGlobal = globalThis.URLSearchParams;
  // Ordinary Unicode text round-trips exactly like real form encoding.
  const unicode = "Čebelica café Ελληνικά 日本語";
  const encoded = new URLSearchParamsGlobal({ ctl: "search-1", q: unicode }).toString();
  assert.deepEqual(
    decodePostedForm(encoded),
    new Map([
      ["ctl", "search-1"],
      ["q", unicode],
    ]),
  );
  // Plus/percent/space handling.
  assert.deepEqual(decodePostedForm("q=a+b"), new Map([["q", "a b"]]));
  assert.deepEqual(decodePostedForm("q=a%20b"), new Map([["q", "a b"]]));
  assert.deepEqual(decodePostedForm("q=a+b%20c"), new Map([["q", "a b c"]]));
  assert.deepEqual(
    decodePostedForm(new URLSearchParamsGlobal({ q: "é" }).toString()),
    new Map([["q", "é"]]),
  );
  // Malformed UTF-8 is refused, never accepted as a different string.
  assert.equal(decodePostedForm("q=%C3%28"), null);
  assert.equal(decodePostedForm("q=%C3"), null);
  assert.equal(decodePostedForm("q=%"), null);
  assert.equal(decodePostedForm("q=%G1"), null);
  assert.equal(decodePostedForm("q=%00"), null); // NUL
  assert.equal(decodePostedForm("q=%7f"), null); // DEL
  // Supported embedded form whitespace is preserved (the native encoding
  // of "Alpha TAB Beta" is Alpha%09Beta): the search/facet matchers keep
  // embedded whitespace, so the transport must not refuse it.
  assert.deepEqual(decodePostedForm("q=Alpha%09Beta"), new Map([["q", "Alpha\tBeta"]]));
  assert.deepEqual(
    decodePostedForm("q=A%0AB%0BC%0CD%0DE"),
    new Map([["q", "A\nB\u000bC\u000cD\rE"]]),
  );
  // NUL, DEL and every other C0 control byte still refuse in values...
  assert.equal(decodePostedForm("q=A%01B"), null);
  assert.equal(decodePostedForm("q=A%1FB"), null);
  // ...and control bytes in generated names always refuse.
  assert.equal(decodePostedForm("q%09=a"), null);
  // Raw non-ASCII, raw space: not valid urlencoded.
  assert.equal(decodePostedForm("q=é"), null);
  assert.equal(decodePostedForm("q= a"), null);
  // Structural strictness: uniform refusal, never a partial state.
  assert.equal(decodePostedForm(""), null);
  assert.equal(decodePostedForm("q"), null);
  assert.equal(decodePostedForm("=a"), null);
  assert.equal(decodePostedForm("a=&&b=c"), null);
  assert.equal(decodePostedForm("&a=b"), null);
  assert.equal(decodePostedForm("a=b&"), null);
  // Duplicates: ordinary names refuse (no silent drop).
  assert.equal(decodePostedForm("q=a&q=b"), null);
  // Special object names beyond the 8-byte generated-name transport
  // bound refuse at the name-length guard - uniform, never decoded.
  assert.equal(decodePostedForm("__proto__=a&__proto__=b"), null);
  assert.equal(decodePostedForm("constructor=a&constructor=b"), null);
  // A special object name WITHIN the transport bound is RETAINED in
  // the result for validation...
  const withSpecial = decodePostedForm("ctl=x&valueOf=a");
  assert.ok(withSpecial instanceof Map);
  assert.equal(withSpecial.has("valueOf"), true);
  assert.equal(withSpecial.get("valueOf"), "a");
  // ...while aggregate and control-count bounds refuse.
  assert.equal(
    decodePostedForm(`q=${"a".repeat(POST_FORM_MAX_BODY_LENGTH + 1)}`),
    null,
  );
  const manyFields = Array.from(
    { length: POST_FORM_MAX_FIELDS + 1 },
    (_, i) => `f${i}=1`,
  ).join("&");
  assert.equal(decodePostedForm(manyFields), null);
});

const collectionProjection = () => {
  const items = [
    {
      id: "i1",
      values: { title: "Alpha gadget", summary: "First", kind: "red", price: 10 },
    },
    {
      id: "i2",
      values: { title: "Beta gadget", summary: "Second", kind: "blue", price: 20 },
    },
    {
      id: "i3",
      values: { title: "Gamma café", summary: "Third", kind: "red", price: 5 },
    },
  ];
  const base = {
    schema_version: "1",
    parent_id: null,
    slot_key: "main",
    children: [],
  };
  const nodes = [
    {
      ...base,
      id: "heading-1",
      component_type: "Heading",
      order_key: 1,
      props: { level: 2, text: "T" },
    },
    {
      ...base,
      id: "search-1",
      component_type: "CollectionSearch",
      order_key: 2,
      props: { placeholder: "Search" },
    },
    {
      ...base,
      id: "section-1",
      component_type: "Section",
      order_key: 3,
      props: {},
      children: [
        {
          ...base,
          id: "filter-1",
          component_type: "CollectionFilter",
          parent_id: "section-1",
          slot_key: "default",
          order_key: 0,
          props: {
            facets: [
              { fieldKey: "kind", operator: "eq", value: "red" },
              { fieldKey: "price", operator: "gte", value: "10" },
            ],
          },
        },
      ],
    },
    // bound control with NO binding/meta: still in the trusted inventory.
    {
      ...base,
      id: "ghost-1",
      component_type: "CollectionSearch",
      order_key: 4,
      props: {},
    },
  ];
  return {
    composition: { schema_version: "site-composition/v1", catalog_version: "1", nodes },
    // bound-1 has binding/meta but NO node in the composition tree.
    bindings: { "search-1": items, "filter-1": items, "bound-1": items },
    binding_meta: {
      "search-1": {
        filter_fields: [
          { key: "title", primitive: "short_text" },
          { key: "summary", primitive: "long_text" },
        ],
      },
      "filter-1": {
        filter_fields: [
          { key: "kind", primitive: "enum" },
          { key: "price", primitive: "integer" },
        ],
      },
      "bound-1": { filter_fields: [{ key: "title", primitive: "short_text" }] },
    },
  };
};

/**
 * The EXACT generated field set of the fixture page's ONE shared form:
 * one name per bound control state slot (positions 0/1/2 in tree order
 * search-1/filter-1/ghost-1) - the generated name carries the bounded
 * deterministic position, never the node identifier; no ``ctl``, no
 * carried groups. A valid submission is exactly this set, with values
 * changed as needed.
 */
const FULL_DEFAULTS = {
  "c.0.q": "",
  "c.1.f0": "red",
  "c.1.f1": "10",
  "c.2.q": "",
};
const submission = (overrides = {}) => {
  const fields = new Map(Object.entries(FULL_DEFAULTS));
  for (const [name, value] of Object.entries(overrides)) fields.set(name, value);
  return fields;
};

test("POST control states: defaults render the trusted initial state, one state per control", () => {
  const projection = collectionProjection();
  const states = defaultControlStates(projection);
  assert.deepEqual([...states.keys()], ["search-1", "filter-1", "ghost-1"]);
  const search = states.get("search-1");
  assert.equal(search.kind, "search");
  assert.deepEqual(search.own, { q: "" });
  assert.equal(search.filtered.length, 3);
  // No carried hidden groups: each control state is represented once.
  assert.equal("hidden" in search, false);
  const filter = states.get("filter-1");
  assert.equal(filter.kind, "filter");
  assert.deepEqual(filter.own, { f0: "red", f1: "10" });
  // Trusted facet defaults: red and price >= 10.
  assert.deepEqual(
    filter.filtered.map((item) => item.id),
    ["i1"],
  );
  // A bound control without binding/meta renders no items, not an error.
  assert.equal(states.get("ghost-1").filtered.length, 0);
  // The generated form field set is exactly one name per state slot,
  // re-derived from the trusted inventory at its positions.
  const expected = new Set();
  for (const [position, node] of controlInventory(projection).entries()) {
    for (const name of controlFieldNames(node, position)) expected.add(name);
  }
  assert.deepEqual([...expected].sort(), Object.keys(FULL_DEFAULTS).sort());
  // A page without bound controls yields the empty map (total function).
  assert.equal(
    defaultControlStates({ composition: { nodes: [] }, bindings: {}, binding_meta: {} })
      .size,
    0,
  );
});

test("POST control selection: multi-control state survives successive submissions", () => {
  const projection = collectionProjection();
  // Submit search A (beta): the shared form carries EVERY control's
  // inputs in ONE body, so B (filter) stays at its trusted default.
  const step1 = selectPostedControls(projection, submission({ "c.0.q": "beta" }));
  assert.ok(step1);
  assert.equal(step1.submittedNodeId, undefined); // no single submitted control
  assert.deepEqual(step1.states.get("search-1").own, { q: "beta" });
  assert.deepEqual(
    step1.states.get("search-1").filtered.map((i) => i.id),
    ["i2"],
  );
  assert.deepEqual(step1.states.get("filter-1").own, { f0: "red", f1: "10" });
  assert.deepEqual(
    step1.states.get("filter-1").filtered.map((i) => i.id),
    ["i1"],
  );
  // Submit filter B (blue, >= 20) with A's state in the SAME form:
  // A must REMAIN.
  const step2 = selectPostedControls(
    projection,
    submission({
      "c.1.f0": "blue",
      "c.1.f1": "20",
      "c.0.q": "beta",
    }),
  );
  assert.ok(step2);
  assert.deepEqual(step2.states.get("search-1").own, { q: "beta" });
  assert.deepEqual(
    step2.states.get("search-1").filtered.map((i) => i.id),
    ["i2"],
  );
  assert.deepEqual(step2.states.get("filter-1").own, { f0: "blue", f1: "20" });
  assert.deepEqual(
    step2.states.get("filter-1").filtered.map((i) => i.id),
    ["i2"],
  );
  // Clear search A (empty query) with B's state in the form: B REMAINS.
  const step3 = selectPostedControls(
    projection,
    submission({ "c.1.f0": "blue", "c.1.f1": "20", "c.0.q": "" }),
  );
  assert.ok(step3);
  assert.deepEqual(step3.states.get("search-1").own, { q: "" });
  assert.equal(step3.states.get("search-1").filtered.length, 3);
  assert.deepEqual(step3.states.get("filter-1").own, { f0: "blue", f1: "20" });
  assert.deepEqual(
    step3.states.get("filter-1").filtered.map((i) => i.id),
    ["i2"],
  );
  // Unicode values round-trip exactly in the shared form.
  const step4 = selectPostedControls(
    projection,
    submission({
      "c.0.q": "café",
      "c.1.f0": "blue",
      "c.1.f1": "20",
    }),
  );
  assert.equal(step4.states.get("search-1").own["q"], "café");
  assert.deepEqual(
    step4.states.get("search-1").filtered.map((i) => i.id),
    ["i3"],
  );
});

test("POST control selection: unknown, foreign and tampered state refuses uniformly", () => {
  const projection = collectionProjection();
  // Extra field beyond the generated set: a facet index (at a real
  // position) the TRUSTED node does not declare.
  assert.equal(selectPostedControls(projection, submission({ "c.1.f3": "1" })), null);
  // A legacy per-control ``ctl`` name is no longer part of the form.
  assert.equal(selectPostedControls(projection, submission({ ctl: "search-1" })), null);
  // Authority-like special names are refused, never dropped. (An object
  // LITERAL cannot own a `__proto__` key; the decoded-Map form is the
  // real transport shape, so the name is set on the Map explicitly.)
  const authority = submission();
  authority.set("__proto__", "a");
  assert.equal(selectPostedControls(projection, authority), null);
  // A field for a control POSITION that is NOT on the page (the
  // fixture inventory has positions 0-2 only; 5 does not exist).
  assert.equal(selectPostedControls(projection, submission({ "c.5.q": "x" })), null);
  // Missing a field of the generated set (any control, own or not).
  const missingGhost = submission();
  missingGhost.delete("c.2.q");
  assert.equal(selectPostedControls(projection, missingGhost), null);
  const missingOwn = submission({ "c.0.q": "x" });
  missingOwn.delete("c.1.f0");
  assert.equal(selectPostedControls(projection, missingOwn), null);
  // Oversized own input / oversized value for another control.
  assert.equal(
    selectPostedControls(projection, submission({ "c.0.q": "a".repeat(257) })),
    null,
  );
  assert.equal(
    selectPostedControls(projection, submission({ "c.1.f1": "1".repeat(4097) })),
    null,
  );
  // A bound control without binding/meta selects fine and renders no
  // items.
  const ghost = selectPostedControls(projection, submission({ "c.2.q": "x" }));
  assert.ok(ghost);
  assert.equal(ghost.states.get("ghost-1").filtered.length, 0);
});

test("POST control transport: the catalog's admitted limits bound the shared form", () => {
  const makeProjection = (specs) => {
    const items = [{ id: "i1", values: { title: "T" } }];
    const nodes = specs.map((spec, index) => ({
      id: spec.id,
      component_type: spec.type,
      schema_version: "1",
      parent_id: null,
      slot_key: "main",
      order_key: index + 1,
      props: spec.type === "CollectionFilter" ? { facets: spec.facets } : {},
      children: [],
    }));
    const bindings = {};
    const binding_meta = {};
    for (const spec of specs) {
      bindings[spec.id] = items;
      binding_meta[spec.id] = {
        filter_fields: [{ key: "title", primitive: "short_text" }],
      };
    }
    return {
      composition: {
        schema_version: "site-composition/v1",
        catalog_version: "1",
        nodes,
      },
      bindings,
      binding_meta,
    };
  };
  const fullSubmission = (projection) => {
    const fields = new Map();
    for (const [position, node] of controlInventory(projection).entries()) {
      for (const name of controlFieldNames(node, position)) {
        fields.set(name, node.component_type === "CollectionSearch" ? "" : "v");
      }
    }
    return fields;
  };
  // The largest admitted inventory: 128 nodes, every one a bound
  // control (MAX_COMPONENTS_PER_PAGE admits no more nodes at all) -
  // supported interaction is preserved, no inert fallback.
  const ids = Array.from({ length: 128 }, (_, i) => `c${i}`);
  const searches = makeProjection(ids.map((id) => ({ id, type: "CollectionSearch" })));
  const states128 = defaultControlStates(searches);
  assert.equal(states128.size, 128);
  assert.ok(selectPostedControls(searches, fullSubmission(searches)));
  // The largest admitted GENERATED FORM: 128 four-facet filters ->
  // exactly POST_FORM_MAX_FIELDS fields.
  const facets4 = [0, 1, 2, 3].map((i) => ({
    fieldKey: `k${i}`,
    operator: "eq",
    value: "v",
  }));
  const filters = makeProjection(
    ids.map((id) => ({ id, type: "CollectionFilter", facets: facets4 })),
  );
  const full = fullSubmission(filters);
  assert.equal(full.size, POST_FORM_MAX_FIELDS);
  assert.ok(selectPostedControls(filters, full));
  // One field beyond the generated set refuses...
  const plusOne = fullSubmission(filters);
  plusOne.set("c.0.f4", "x");
  assert.equal(selectPostedControls(filters, plusOne), null);
  // ...and a retained special name (within the transport bound)
  // refuses at the verifier: uniform null, never a partial state.
  const withSpecial128 = fullSubmission(searches);
  withSpecial128.set("valueOf", "a");
  assert.equal(selectPostedControls(searches, withSpecial128), null);
  // ...and the decode cap refuses one field beyond the admitted maximum.
  const overParts = Array.from(
    { length: POST_FORM_MAX_FIELDS + 1 },
    (_, i) => `f${i}=1`,
  ).join("&");
  assert.equal(decodePostedForm(overParts), null);
  // The WORST admitted encoding: every facet value at 4096 decoded code
  // units, each a THREE-byte UTF-8 BMP character (nine percent-encoded
  // ASCII bytes per code unit). The names carry the bounded positions
  // (1-3 digits for the 128 admitted controls: 40 of 6 bytes, 360 of
  // 7, 112 of 8), and the global cap is derived from exactly these
  // name bytes, so this body sits EXACTLY on the cap; the 36-character
  // node identifiers never reach the wire. The body decodes, preserves
  // the exact Unicode, and is admitted. One more ASCII byte refuses at
  // the global length guard, and the interior encodings below stay
  // admitted.
  const euro = "%E2%82%AC"; // € U+20AC: 3 UTF-8 bytes -> 9 encoded bytes
  const maxIds = Array.from(
    { length: 128 },
    (_, i) => `n${String(i).padStart(35, "0")}`,
  );
  const maxFilters = makeProjection(
    maxIds.map((id) => ({ id, type: "CollectionFilter", facets: facets4 })),
  );
  const maxBody = [...fullSubmission(maxFilters).entries()]
    .map(([name]) => `${name}=${euro.repeat(FACET_INPUT_MAX_LENGTH)}`)
    .join("&");
  const worstNameBytes = 40 * 6 + 360 * 7 + 112 * 8;
  assert.equal(
    maxBody.length,
    worstNameBytes +
      POST_FORM_MAX_FIELDS +
      (POST_FORM_MAX_FIELDS - 1) +
      POST_FORM_MAX_FIELDS * FACET_INPUT_MAX_LENGTH * 9,
  );
  // Exact global boundary: the worst admitted body length equals the
  // derived cap itself (N is admitted, N+1 refuses below, and the
  // interior encodings stay admitted).
  assert.equal(maxBody.length, POST_FORM_MAX_BODY_LENGTH);
  const maxDecoded = decodePostedForm(maxBody);
  assert.ok(maxDecoded);
  assert.equal(maxDecoded.get("c.0.f0"), "\u20ac".repeat(FACET_INPUT_MAX_LENGTH));
  assert.ok(selectPostedControls(maxFilters, maxDecoded));
  // A real intermediate encoding also stays admitted: 600 euro
  // characters per value produce 2,769,479 encoded bytes.
  const euro600 = [...fullSubmission(maxFilters).entries()]
    .map(([name]) => `${name}=${euro.repeat(600)}`)
    .join("&");
  assert.equal(euro600.length, 2769479);
  assert.ok(selectPostedControls(maxFilters, decodePostedForm(euro600)));
  // N-9: one euro code unit removed from the last value - a valid
  // encoding strictly below the cap, still admitted at the length
  // guard.
  assert.ok(decodePostedForm(maxBody.slice(0, maxBody.length - 9)));
  // N+1: one ASCII byte beyond the cap refuses at the length guard.
  assert.equal(decodePostedForm(`${maxBody}a`), null);
  // A value beyond the per-part worst case (4097 decoded code units)
  // refuses at the part-length guard before any byte collection.
  const oversizedPart = `c.0.f0=${euro.repeat(FACET_INPUT_MAX_LENGTH + 1)}`;
  assert.equal(decodePostedForm(`${oversizedPart}&c.1.f0=v`), null);
  // The raw-bytes cap equals the body cap: a decodable body is
  // percent-encoded ASCII, exactly one raw byte per character.
  assert.equal(POST_FORM_MAX_RAW_BYTES, POST_FORM_MAX_BODY_LENGTH);
});
