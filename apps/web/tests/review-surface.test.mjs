// 082/2 R2 web unit proof: the resolver's content source is exclusively the
// trusted read-model document. These tests exercise the pure mapping
// (projectionFromReviewDocument) against in-memory documents: page match,
// locale-prefix contract, frozen redirects, uniform not_found, session-scoped
// private media, navigation projection, determinism, and the structural gate.
import assert from "node:assert/strict";
import { test } from "node:test";

import {
  isReviewDocument,
  projectionFromReviewDocument,
  reviewRedirectTarget,
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
  state_version: "state/v1",
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
    digest: "sha256:0123456789abcdef",
    state_version: "state/v1",
    revision_watermark: 3,
    base_site_revision: 7,
    status: "COMPLETE",
    created_at: "2026-10-05T00:00:00Z",
    created_by: "human:reviewer",
    versions: { composition_schema: "composition-schema/v1", catalog: "1" },
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
