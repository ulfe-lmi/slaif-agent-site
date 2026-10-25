import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";

import {
  chromium,
  devices,
  expect,
  firefox,
  test,
  webkit,
  type APIRequestContext,
  type Browser,
  type BrowserContext,
  type Locator,
  type Page,
  type TestInfo,
} from "@playwright/test";

import { expectPrivateHeaders, login, observe, secrets, type Secrets } from "./support";

/**
 * 083/5-b RC2: faithful active-preview vs immutable-review parity across
 * the SIX existing stable engine/target pairings (the same engine and
 * device descriptors as the six dedicated Playwright device projects:
 * desktop-chromium, desktop-firefox, desktop-webkit, tablet,
 * mobile-chromium, mobile-webkit), through the public NGINX origin.
 *
 * Proof model (per the 2026-10-20 finish decision and the 2026-10-21
 * first independent source review):
 * - ONE run-unique site (trusted setup: site + two locale rows + the
 *   SITE_OWNER membership only); EVERY editorial fact - content model,
 *   items, translations, view, pages, components, media, theme, page
 *   style, redirect, navigation - is created through the REAL public
 *   Agent API on a public control-API workspace + capability.
 * - The collection view carries a REAL supported server-side filter
 *   (kind IN (News, Press)) and a pagination limit that both truncate
 *   the delivered set; the client facet/search interaction is proven
 *   separately on the deployed same-path POST form.
 * - Phase A renders the ACTIVE workspace preview (before any freeze) on
 *   all six pairings: every fingerprint is keyed by
 *   engine/target+route, every browser context holds a REAL human
 *   session established in that context, and per-route oracles assert
 *   the actual renderer markup (list, detail, related, document
 *   list, breadcrumbs, switcher, brand, region) plus the target-size
 *   computed CSS of the trusted renderer stylesheet.
 * - The workspace is then frozen through the real control freeze +
 *   review worker; the stored v2 snapshot is asserted (state version,
 *   digest coverage, frozen media descriptor + inventory binding).
 * - Phase B renders the IMMUTABLE review surface for the same six
 *   pairings; every engine/target+route fingerprint must equal the
 *   pre-freeze active fingerprint (media URLs are normalized to the
 *   actual media id - the private namespaces differ by design - and
 *   the frozen bytes must be byte-identical to the active bytes).
 * - The matrix records the actual engine/version/target per pairing and
 *   fails the test (hence the whole-smoke gate) for any missing or
 *   failed pairing.
 *
 * Budget: 600 s, the same explicit budget class as the existing
 * complex lifecycle specs (240..600 s); the measured per-phase wall
 * time is recorded in the test annotation.
 */

/**
 * The six stable pairings, exactly the config's device projects. Each
 * pairing really launches its engine and really applies its device
 * descriptor; the running engine version is recorded per pairing.
 */
const ORIGIN = "http://localhost:8080";

const MATRIX = [
  { engine: "chromium", target: "Desktop Chrome" },
  { engine: "firefox", target: "Desktop Firefox" },
  { engine: "webkit", target: "Desktop Safari" },
  { engine: "webkit", target: "iPad (gen 7)" },
  { engine: "chromium", target: "Pixel 5" },
  { engine: "webkit", target: "iPhone 13" },
] as const;
type MatrixPairing = (typeof MATRIX)[number];
type TargetName = MatrixPairing["target"];
type EngineName = "chromium" | "firefox" | "webkit";

/**
 * Target-size computed-CSS oracles for the non-default theme tokens
 * this fixture installs: content_width "lg" makes main
 * min(80rem, 100% - 2rem), and the header inner flex column-stacks at
 * 40rem (renderer-v1.css). Viewport widths are the named Playwright
 * device descriptors; root font size is the default 16px.
 */
const TARGET_SIZES: Record<TargetName, { width: string; headerDirection: string }> = {
  "Desktop Chrome": { width: "1248px", headerDirection: "row" },
  "Desktop Firefox": { width: "1248px", headerDirection: "row" },
  "Desktop Safari": { width: "1248px", headerDirection: "row" },
  // Installed Playwright 1.62.1 descriptor: 810x1080 (not 768-wide).
  "iPad (gen 7)": { width: "778px", headerDirection: "row" },
  "Pixel 5": { width: "361px", headerDirection: "column" },
  "iPhone 13": { width: "358px", headerDirection: "column" },
};

/**
 * Non-default responsive container oracles: the fixture posts the
 * design-system map {desktop: 3, tablet: 2, mobile: 1} onto a Columns
 * count; the renderer breakpoints (1024px tablet / 760px mobile in
 * renderer-v1.css) resolve it to the exact per-target computed grid
 * track count.
 */
const RESPONSIVE_TRACKS: Record<TargetName, number> = {
  "Desktop Chrome": 3,
  "Desktop Firefox": 3,
  "Desktop Safari": 3,
  "iPad (gen 7)": 2,
  "Pixel 5": 1,
  "iPhone 13": 1,
};

const TINY_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ" +
    "AAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "base64",
);

/** Bounded one-page PDF fixture (same construction as the 079/3 proofs). */
function makePdf(pages: number, seed: string): Buffer {
  const kids = Array.from({ length: pages }, (_, i) => `${3 + i} 0 R`).join(" ");
  const parts: string[] = [
    "%PDF-1.4\n",
    "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
    `2 0 obj\n<< /Type /Pages /Kids [${kids}] /Count ${pages} >>\nendobj\n`,
  ];
  for (let i = 0; i < pages; i += 1) {
    parts.push(
      `${3 + i} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents (${seed}-${i}) >>\nendobj\n`,
    );
  }
  parts.push(`trailer\n<< /Root 1 0 R /Size ${pages + 3} >>\n%%EOF\n`);
  return Buffer.from(parts.join(""), "latin1");
}

function sha256Hex(value: Uint8Array): string {
  return createHash("sha256").update(value).digest("hex");
}

function randomHex(bytes: number): string {
  const value = new Uint8Array(bytes);
  crypto.getRandomValues(value);
  return Array.from(value, (item) => item.toString(16).padStart(2, "0")).join("");
}

function composeProject(): string {
  const project = process.env.SLAIF_E2E_COMPOSE_PROJECT;
  if (!project) throw new Error("missing SLAIF_E2E_COMPOSE_PROJECT");
  return project;
}

function psql(project: string, sql: string): string {
  return execFileSync("docker", [
    "exec",
    `${project}-postgres-1`,
    "psql",
    "-U",
    "postgres",
    "-d",
    "slaif",
    "-Atc",
    sql,
  ])
    .toString("utf8")
    .trim();
}

/**
 * The G7 pending-operation inspection script, executed inside the
 * EXISTING Compose review-worker service container with its existing
 * Python environment and its own configured DSN-file credential
 * (compose.yaml review-worker environment, the product's
 * REVIEW_WORKER_DSN_FILE default).  It verifies the connection
 * identity exactly as the product's own worker verification does
 * (review_worker/worker.py), then calls the existing public
 * foundation operation-inspection API
 * (slaif_agent_site.agent_state.foundation.get_session_operations,
 * qualified agent-cow-postgresql 0.2.0).  No worker loop, no
 * promotion or discard call, no private FOUNDATION table or
 * undocumented SQL: the only SQL statements are the catalog identity
 * checks (current_database/session_user/current_user/pg_roles/
 * pg_has_role - exactly as the product's own worker verification
 * issues them) plus the single controlled SECDEF function call the
 * hardening grants the worker role.  Output: one pending COW
 * operation id per line (the bounded list only).
 */
const PENDING_OPERATIONS_INSPECTION = `
import asyncio
import asyncpg
import os
import sys
import uuid

from slaif_agent_site.agent_state.foundation import get_session_operations


class _Executor:
    def __init__(self, conn):
        self._conn = conn

    async def execute(self, sql):
        return [tuple(row) for row in await self._conn.fetch(sql)]


async def main():
    expected_db = os.environ["SLAIF_REVIEW_WORKER_EXPECTED_DATABASE"]
    expected_login = os.environ["SLAIF_REVIEW_WORKER_EXPECTED_LOGIN"]
    role = os.environ["SLAIF_REVIEW_WORKER_EXPECTED_PRIVILEGE_ROLE"]
    # python -c passes everything after the script as argv: with the
    # "--" separator the id is argv[2]; select it deliberately and
    # validate it BEFORE any database contact.
    args = sys.argv[1:]
    if args and args[0] == "--":
        args = args[1:]
    if len(args) != 1:
        raise RuntimeError("expected exactly one workspace id argument")
    try:
        workspace_id = uuid.UUID(args[0])
    except ValueError:
        raise RuntimeError("workspace id argument is not a UUID") from None
    dsn = open(
        os.environ["SLAIF_REVIEW_WORKER_DSN_FILE"], encoding="ascii"
    ).read().strip()
    conn = await asyncpg.connect(dsn)
    try:
        row = await conn.fetchrow(
            "SELECT current_database()::text, session_user::text, "
            "current_user::text, ARRAY("
            "SELECT target.rolname::text FROM pg_catalog.pg_roles target "
            "WHERE target.rolname = ANY($1::text[]) "
            "AND pg_catalog.pg_has_role(session_user, target.oid, 'MEMBER') "
            "ORDER BY target.rolname)",
            [role],
        )
        if (
            tuple(row[:3]) != (expected_db, expected_login, expected_login)
            or tuple(row[3]) != (role,)
        ):
            raise RuntimeError("review-worker credential identity mismatch")
        operations = await get_session_operations(
            _Executor(conn), workspace_id, schema="content"
        )
        print("\\n".join(str(operation) for operation in operations))
    finally:
        await conn.close()


asyncio.run(main())
`;

/**
 * G7 helper: the pending COW operation ids of one workspace (its COW
 * session) in the content schema, observed through the existing public
 * foundation API from the existing review-worker service environment.
 */
function pendingOperations(project: string, workspaceId: string): string[] {
  const raw = execFileSync("docker", [
    "exec",
    `${project}-review-worker-1`,
    "python",
    "-c",
    PENDING_OPERATIONS_INSPECTION,
    "--",
    workspaceId,
  ])
    .toString("utf8")
    .trim();
  return raw === "" ? [] : raw.split("\n");
}

/**
 * Trusted SETUP facts only (the proof itself uses public actors): the
 * run-unique site, its two locale rows and the admin membership. Site
 * profile facts are human-Control-only, so they are seeded directly;
 * every editorial family is created through the public Agent API.
 */
function seedParitySite(project: string): { siteId: string; siteKey: string } {
  const siteKey = `fpar-${randomHex(4)}`;
  const siteId = crypto.randomUUID();
  const enLocaleId = crypto.randomUUID();
  const slLocaleId = crypto.randomUUID();
  const adminId = psql(
    project,
    "SELECT id FROM control.user_account WHERE local_username_normalized = 'compose.admin'",
  );
  expect(adminId).toMatch(/^[0-9a-f-]{36}$/i);
  psql(
    project,
    `BEGIN;
     INSERT INTO control.site
       (id, site_key, display_name, default_locale, component_catalog_version, status)
     VALUES ('${siteId}'::uuid, '${siteKey}', 'Frozen Parity', 'en',
             'catalog-v1', 'ACTIVE');
     INSERT INTO control.site_membership
       (site_id, user_account_id, role_key, delegation_ceiling)
     VALUES ('${siteId}'::uuid, '${adminId}'::uuid, 'SITE_OWNER', 4);
     INSERT INTO content.site_locale_base
       (id, site_id, tag, enabled, is_default, position, metadata)
     VALUES
       ('${enLocaleId}'::uuid, '${siteId}'::uuid, 'en', true, true, 0, '{}'::jsonb),
       ('${slLocaleId}'::uuid, '${siteId}'::uuid, 'sl-SI', true, false, 1, '{}'::jsonb);
     COMMIT;`,
  );
  return { siteId, siteKey };
}

interface ListItem {
  t: string;
  s: string;
}
const EN_ITEMS: ListItem[] = [
  { t: "Alpha briefing", s: "Alpha summary" },
  { t: "Beta dispatch", s: "Beta summary" },
  { t: "Gamma notes", s: "Gamma summary" },
  { t: "Delta letter", s: "Delta summary" },
];
// delta deliberately has NO sl-SI translation: the frozen and active
// surfaces must both fall back to the en value (locale fallback parity).
const SL_ITEMS: ListItem[] = [
  { t: "Prvi članek", s: "Prvi povzetek" },
  { t: "Drugi članek", s: "Drugi povzetek" },
  { t: "Tretji članek", s: "Tretji povzetek" },
  { t: "Delta letter", s: "Delta summary" },
];
const SLUGS = ["alpha", "beta", "gamma", "delta"];
const KINDS = ["News", "Press", "Blog", "News"];
const RANKS = [4, 3, 2, 1];
/**
 * The view's REAL supported server-side filter is kind IN (News,
 * Press): alpha(4), beta(3) and delta(1) pass, gamma(Blog) is refused.
 * The pagination limit of 2 then delivers only alpha+beta to the
 * list/search/filter bindings, while the detail binding (exact slug
 * match) still resolves every FILTER-PASSING item - including delta,
 * which is filtered out of the lists but not of its own route.
 */
const FILTERED = [0, 1, 3];
const DELIVERED = [0, 1];

interface MediaIds {
  png: string;
  pdf: string;
}

interface RouteFacts {
  h1: string;
  lang: string;
  renderMode: string;
  theme: string[];
  computed: {
    background: string;
    color: string;
    fontFamily: string;
    fontSize: string;
    width: string;
    headerDirection: string;
  };
  headings: string[];
  paragraphs: string[];
  lists: Array<{ component: string; items: string[] }>;
  detail: { heading: string; body: string } | null;
  images: string[];
  docs: Array<{ label: string; media: string }>;
  columns: { classes: string; tracks: number } | null;
  crumbs: string[];
  switcher: Array<{ tag: string; current: boolean; route: string | null }>;
  brand: { label: string; route: string } | null;
  regionLinks: Array<{ label: string; route: string }>;
}

/**
 * One serialized DOM pass: content of main.renderer-surface plus the
 * region/switcher chrome of .renderer-page. Every href is resolved
 * against the page URL and re-rooted to the SITE-LOCAL route (the
 * surface's own base prefix stripped), so active preview and frozen
 * review fingerprints are directly comparable; media URLs are reduced
 * to their ACTUAL media id (the private namespaces differ by design).
 */
async function collectFacts(page: Page, base: string): Promise<RouteFacts> {
  return page.evaluate((siteBase: string): RouteFacts => {
    const text = (element: Element | null | undefined): string =>
      element?.textContent ?? "";
    const normalize = (href: string): string | null => {
      try {
        const url = new URL(href, location.href);
        if (url.origin !== location.origin) return null;
        if (url.pathname.startsWith("/media/v1/")) {
          const match = url.pathname.match(/\/assets\/([^/]+)\/content$/);
          return match ? `media:${match[1]}` : url.pathname;
        }
        return url.pathname.startsWith(siteBase)
          ? url.pathname.slice(siteBase.length) || "/"
          : url.pathname;
      } catch {
        return null;
      }
    };
    const main = document.querySelector("main.renderer-surface");
    if (!main) throw new Error("renderer surface missing");
    const theme = main.className
      .split(/\s+/)
      .filter((className) => className.startsWith("renderer-theme-"))
      .sort();
    const computedStyle = getComputedStyle(main);
    const regionRoot = document.querySelector(".renderer-page");
    const headerInner = document.querySelector(
      ".renderer-region-header .renderer-region-inner",
    );
    const brandEl = regionRoot?.querySelector<HTMLAnchorElement>(
      "a.renderer-region-brand",
    );
    const brand = brandEl
      ? {
          label: text(brandEl),
          route: normalize(brandEl.getAttribute("href") ?? "") ?? "",
        }
      : null;
    const detailEl = main.querySelector("article.renderer-collection-detail");
    const columnsEl = main.querySelector<HTMLDivElement>(".renderer-columns");
    return {
      h1: text(main.querySelector("h1#page-title")),
      lang: main.getAttribute("lang") ?? "",
      renderMode: main.getAttribute("data-render-mode") ?? "",
      theme,
      computed: {
        background: computedStyle.backgroundColor,
        color: computedStyle.color,
        fontFamily: computedStyle.fontFamily,
        fontSize: computedStyle.fontSize,
        width: computedStyle.width,
        headerDirection: headerInner ? getComputedStyle(headerInner).flexDirection : "",
      },
      headings: Array.from(main.querySelectorAll("h2, h3")).map((h) => text(h).trim()),
      paragraphs: Array.from(main.querySelectorAll("p")).map((p) => text(p).trim()),
      lists: Array.from(main.querySelectorAll("ul.renderer-collection-list")).map(
        (ul) => ({
          component:
            ul.closest("[data-component]")?.getAttribute("data-component") ?? "unknown",
          items: Array.from(ul.querySelectorAll("li")).map((li) =>
            [text(li.querySelector("h2")), text(li.querySelector("p"))].join("|"),
          ),
        }),
      ),
      detail: detailEl
        ? {
            heading: text(detailEl.querySelector("h2")).trim(),
            body: text(detailEl.querySelector("p")).trim(),
          }
        : null,
      images: Array.from(main.querySelectorAll("img")).map(
        (img) => normalize(img.getAttribute("src") ?? "") ?? "",
      ),
      docs: Array.from(main.querySelectorAll(".sl-doclist__link")).map((a) => ({
        label: text(a.querySelector(".sl-doclist__label")),
        media: normalize(a.getAttribute("href") ?? "") ?? "",
      })),
      columns: columnsEl
        ? {
            classes: columnsEl.className,
            tracks: getComputedStyle(columnsEl)
              .gridTemplateColumns.split(" ")
              .filter(Boolean).length,
          }
        : null,
      crumbs: Array.from(
        regionRoot?.querySelectorAll(".renderer-region-breadcrumbs li") ?? [],
      ).map((li) => text(li).trim()),
      switcher: Array.from(
        regionRoot?.querySelectorAll(
          ".renderer-region-language .renderer-region-language-item",
        ) ?? [],
      ).map((item) => {
        const link = item.querySelector("a");
        return {
          tag: text(item).trim(),
          current: item.querySelector('[aria-current="true"]') !== null,
          route: link ? normalize(link.getAttribute("href") ?? "") : null,
        };
      }),
      brand,
      regionLinks: Array.from(
        regionRoot?.querySelectorAll(".renderer-region-links a") ?? [],
      ).map((a) => ({
        label: text(a),
        route: normalize(a.getAttribute("href") ?? "") ?? "",
      })),
    };
  }, base);
}

/**
 * Normalized cross-surface content fingerprint (render mode is surface
 * chrome, asserted separately; media URLs already reduced to ids).
 */
function contentKey(facts: RouteFacts): string {
  return JSON.stringify({
    h1: facts.h1,
    lang: facts.lang,
    theme: facts.theme,
    computed: facts.computed,
    headings: facts.headings,
    paragraphs: facts.paragraphs,
    lists: facts.lists,
    detail: facts.detail,
    images: facts.images,
    docs: facts.docs,
    columns: facts.columns,
    crumbs: facts.crumbs,
    switcher: facts.switcher,
    brand: facts.brand,
    regionLinks: facts.regionLinks,
  });
}

const ROUTES = [
  "/",
  "/sl-SI",
  "/news",
  "/sl-SI/news",
  "/news/alpha",
  "/sl-SI/news/alpha",
  "/news/delta",
  "/sl-SI/news/delta",
] as const;
type RouteName = (typeof ROUTES)[number];

function localeOf(route: RouteName): "en" | "sl-SI" {
  return route.startsWith("/sl-SI") ? "sl-SI" : "en";
}

// Non-default theme tokens installed by the fixture (all nine tokens of
// the resolved page style, exact sorted class list).
const SITE_THEME_CLASSES = [
  "renderer-theme-family--serif",
  "renderer-theme-gap--md",
  "renderer-theme-palette--meadow",
  "renderer-theme-radius--md",
  "renderer-theme-scale--spacious",
  "renderer-theme-shadow--sm",
  "renderer-theme-spacing--md",
  "renderer-theme-weight--regular",
  "renderer-theme-width--lg",
];
const ITEM_EN_THEME_CLASSES = [
  "renderer-theme-family--mono",
  "renderer-theme-gap--md",
  "renderer-theme-palette--ember",
  "renderer-theme-radius--md",
  "renderer-theme-scale--spacious",
  "renderer-theme-shadow--sm",
  "renderer-theme-spacing--md",
  "renderer-theme-weight--regular",
  "renderer-theme-width--lg",
];

function assertExpected(
  route: RouteName,
  facts: RouteFacts,
  media: MediaIds,
  siteKey: string,
  phase: "preview" | "review",
): void {
  const locale = localeOf(route);
  const items = locale === "en" ? EN_ITEMS : SL_ITEMS;
  const item = (index: number): string => `${items[index]!.t}|${items[index]!.s}`;
  const expected = DELIVERED.map((i) => item(i));
  if (route === "/" || route === "/sl-SI") {
    expect(facts.h1, "home title").toBe(
      locale === "en" ? "Parity home" : "Domača stran",
    );
    expect(facts.lang).toBe(locale);
    expect(facts.headings).toEqual([
      locale === "en" ? "Home marker EN" : "Oznaka domače",
    ]);
    expect(facts.paragraphs).toEqual([]);
    expect(facts.lists).toEqual([]);
    expect(facts.detail).toBeNull();
    expect(facts.images).toEqual([`media:${media.png}`]);
    expect(facts.docs).toEqual([{ label: "Field brief", media: `media:${media.pdf}` }]);
    expect(facts.columns).toBeNull();
    expect(facts.crumbs).toEqual([]);
  } else if (route === "/news" || route === "/sl-SI/news") {
    expect(facts.h1).toBe(locale === "en" ? "Parity news" : "Novice");
    expect(facts.lang).toBe(locale);
    // Two bound controls in composition order: the search list then the
    // filter list, each holding the SAME server-delivered two items in
    // rank order (the server filter and pagination apply to both).
    expect(facts.headings).toEqual([
      items[0]!.t,
      items[1]!.t,
      items[0]!.t,
      items[1]!.t,
    ]);
    expect(facts.paragraphs).toEqual([
      items[0]!.s,
      items[1]!.s,
      items[0]!.s,
      items[1]!.s,
    ]);
    expect(facts.lists).toEqual([
      { component: "CollectionSearch", items: expected },
      { component: "CollectionFilter", items: expected },
    ]);
    expect(facts.detail).toBeNull();
    expect(facts.images).toEqual([]);
    expect(facts.docs).toEqual([]);
    // The non-default responsive container renders the exact stored
    // desktop/tablet/mobile class map (the per-target computed track
    // count is asserted in assertStyle).
    expect(facts.columns, "responsive container present").not.toBeNull();
    expect(facts.columns!.classes).toBe(
      "renderer-columns renderer-columns--3 renderer-columns--tablet-2 renderer-columns--mobile-1 renderer-gap--md renderer-align--stretch",
    );
    expect(facts.crumbs).toEqual([]);
  } else {
    const slug = route.split("/").pop()!;
    const index = SLUGS.indexOf(slug);
    expect(index, "known slug").toBeGreaterThanOrEqual(0);
    const related = FILTERED.filter((candidate) => candidate !== index);
    expect(facts.h1).toBe(locale === "en" ? "Article" : "Članek");
    expect(facts.lang).toBe(locale);
    // Component-specific order: the bound Heading, the CollectionDetail
    // article title, the RelatedItems heading, then its list titles.
    expect(facts.headings).toEqual([
      locale === "en" ? "Article body EN" : "Osnova članka",
      items[index]!.t,
      "Related",
      ...related.map((i) => items[i]!.t),
    ]);
    expect(facts.paragraphs).toEqual([
      items[index]!.s,
      ...related.map((i) => items[i]!.s),
    ]);
    expect(facts.lists).toEqual([
      { component: "RelatedItems", items: related.map((i) => item(i)) },
    ]);
    expect(facts.detail).toEqual({
      heading: items[index]!.t,
      body: items[index]!.s,
    });
    expect(facts.images).toEqual([]);
    expect(facts.docs).toEqual([]);
    expect(facts.columns).toBeNull();
    expect(facts.crumbs).toEqual([
      locale === "en" ? "Parity news" : "Novice",
      locale === "en" ? "Article" : "Članek",
    ]);
  }
  // Surface chrome common to every route of one phase.
  expect(facts.renderMode).toBe(phase);
  expect(facts.switcher.map((s) => s.tag)).toEqual(["en", "sl-SI"]);
  expect(facts.switcher.find((s) => s.tag === locale)?.current).toBe(true);
  const counterpart = locale === "en" ? "sl-SI" : "en";
  expect(facts.switcher.find((s) => s.tag === counterpart)?.current).toBe(false);
  // The default-locale home counterpart of the sl-SI home route is the
  // concrete "/" (the renderer re-roots to the stored route, and an
  // empty prefix-strip is home), never an empty string.
  const counterpartRoute =
    counterpart === "en"
      ? route === "/"
        ? "/"
        : route.startsWith("/sl-SI")
          ? route.slice("/sl-SI".length) || "/"
          : route
      : route === "/"
        ? "/sl-SI"
        : `/sl-SI${route}`;
  expect(facts.switcher.find((s) => s.tag === counterpart)?.route).toBe(
    counterpartRoute,
  );
  // The region brand is the anchor itself (label = site key, target =
  // the site root); the default synthesized header nav carries exactly
  // the one internal root entry.
  expect(facts.brand).toEqual({ label: siteKey, route: "/" });
  expect(facts.regionLinks).toEqual([{ label: siteKey, route: "/" }]);
}

function assertStyle(route: RouteName, facts: RouteFacts, target: TargetName): void {
  const sizes = TARGET_SIZES[target];
  const itemPage = route === "/news/alpha" || route === "/news/delta";
  expect(facts.theme, "resolved page-style tokens").toEqual(
    itemPage ? ITEM_EN_THEME_CLASSES : SITE_THEME_CLASSES,
  );
  const c = facts.computed;
  expect(c.fontSize, "non-default scale token").toBe("17px");
  expect(c.width, `content width at ${target}`).toBe(sizes.width);
  expect(c.headerDirection, `header stack at ${target}`).toBe(sizes.headerDirection);
  if (itemPage) {
    expect(c.background, "page override wins").toBe("rgb(255, 247, 237)");
    expect(c.color).toBe("rgb(66, 32, 6)");
    expect(c.fontFamily).toContain("ui-monospace");
  } else {
    expect(c.background, "site theme applied").toBe("rgb(240, 248, 241)");
    expect(c.color).toBe("rgb(18, 53, 29)");
    expect(c.fontFamily).toContain("Georgia");
  }
  if (route === "/news" || route === "/sl-SI/news") {
    expect(facts.columns, "responsive container present").not.toBeNull();
    expect(facts.columns!.tracks, `responsive tracks at ${target}`).toBe(
      RESPONSIVE_TRACKS[target],
    );
  } else {
    expect(facts.columns, `no container at ${route}`).toBeNull();
  }
}

/**
 * 083-6-a R3 observational document sentinel: every committed main
 * document re-runs context init scripts, so a fresh per-document UUID on
 * window is a fixed, secret-free document-identity marker.  It grants no
 * product browser capability or authority; the controls sequence asserts
 * it is installed (boolean) before each click and that it CHANGED after
 * each same-path POST, proving a genuinely fresh main document even when
 * the URL is unchanged.  The per-document UUID crosses to the test
 * process for the pre/post comparison only and is never logged; all
 * diagnostic output is boolean/fixed-enum.
 */
const DOC_SENTINEL_KEY = "__slaif_fpar_doc";

async function installDocumentSentinel(context: BrowserContext): Promise<void> {
  await context.addInitScript((key: string) => {
    (window as unknown as Record<string, unknown>)[key] =
      globalThis.crypto.randomUUID();
  }, DOC_SENTINEL_KEY);
}

/** Non-empty sentinel value, or null when missing (safe rejection). */
function readSentinel(page: Page): Promise<string | null> {
  return page.evaluate((key: string) => {
    const doc = (window as unknown as Record<string, unknown>)[key];
    return typeof doc === "string" && doc.length > 0 ? doc : null;
  }, DOC_SENTINEL_KEY);
}

/**
 * 083-6-a R2: fixed-enum classification of a failed control leg.
 * Maps the pinned Playwright 1.62.1 error `name` identifiers (stable in
 * the frozen coreBundle) to a fixed enum; never surfaces the raw error
 * message, cause or Playwright call log.
 */
function safeDiagnosticClass(error: unknown): string {
  if (!(error instanceof Error)) return "unknown";
  switch (error.name) {
    case "TimeoutError":
      return "timeout";
    case "TargetClosedError":
      return "target-closed";
    case "AbortError":
      return "aborted";
    default:
      return "error";
  }
}

/**
 * Submit the ONE shared same-path native form through its real POST
 * round-trip (real native button click; no manual POST, forced click,
 * reload/goto workaround, sleep or retry).  The POST-response waiter AND
 * the POSTed-document navigation waiter are both registered BEFORE the
 * click so the submission cannot slip between actions.  Response
 * matching binds the main frame / navigation request, method and same
 * expected URL (R3), and the post-POST document identity must be
 * fresh (the sentinel changed) even when the URL is unchanged.
 *
 * 083-6-a R2 bounded diagnostics: every leg is observable independently
 * (fixed enums/booleans/relative durations only; no URLs, IDs, DOM,
 * bodies or raw call logs).  Each leg carries an explicit diagnostic
 * deadline of at most 30000ms (R4) so any pending stall yields an
 * attributed leg error before the global 600s budget.  On first failure
 * the operation is FROZEN (the first-failure leg state is snapshotted
 * before abort/drain; no late leg or cleanup overwrites it), pending
 * sibling waits are aborted through an actual AbortSignal and drained in
 * a bounded way, and only a sanitized fixed-class/leg/flags error
 * propagates (class is a fixed whitelist, never the raw message, cause
 * or Playwright call log).  Leg states: 0 pending, 1 settled-ok,
 * 2 settled-rejected.
 */
async function submitControlForm(
  page: Page,
  button: Locator,
  op: "a" | "b" | "c",
  onOp?: (op: string, flags?: string) => void,
): Promise<void> {
  const current = page.url();
  // The pre-click identity must itself be proven a non-empty string; a
  // missing marker is safely rejected (never a fallback that could make
  // the post-POST "changed" comparison vacuous).
  const docBefore = await readSentinel(page);
  if (typeof docBefore !== "string" || docBefore.length === 0)
    throw new Error("controls sentinel rejected: not a non-empty string before click");
  onOp?.(`submit-${op}`);
  const startedAt = Date.now();
  let failed = false;
  let firstLeg: string | null = null;
  let firstFlags: string | null = null;
  let legR = 0;
  let legN = 0;
  let legC = 0;
  // Observed response facts (numeric status + two booleans only): kept
  // in common state so the heartbeat, freeze and first-failure lines
  // retain them after the transient submit-response marker is replaced.
  let respStatus = "";
  let respNavReq = "";
  let respMainFrame = "";
  const respEvidence = () =>
    respStatus === ""
      ? ""
      : ` status=${respStatus} navreq=${respNavReq} mainframe=${respMainFrame}`;
  const stateFlags = () =>
    onOp?.(
      `submit-${op}`,
      `r=${legR} n=${legN} c=${legC}${respEvidence()} t=${Date.now() - startedAt}ms`,
    );
  const annotate = () => {
    if (!failed) stateFlags();
  };
  const freeze = (leg: string) => {
    if (failed) return;
    failed = true;
    firstLeg = leg;
    // Snapshot the FIRST-failure leg state before any abort/drain can
    // mutate sibling leg states.
    firstFlags = `r=${legR} n=${legN} c=${legC}${respEvidence()} t=${Date.now() - startedAt}ms`;
    stateFlags();
  };
  const heartbeat = setInterval(annotate, 5_000);
  const abort = new AbortController();
  try {
    const responsePromise = page
      .waitForResponse(
        // R3: bind the main-frame navigation request, the POST method
        // and the same expected URL; an iframe/fetch or unrelated
        // same-URL response is not accepted.
        (candidate) =>
          candidate.request().method() === "POST" &&
          candidate.url() === current &&
          candidate.request().isNavigationRequest() &&
          candidate.frame() === page.mainFrame(),
        { timeout: 30_000, signal: abort.signal },
      )
      .then(
        (response) => {
          if (!failed) {
            legR = 1;
            respStatus = String(response.status());
            respNavReq = response.request().isNavigationRequest() ? "1" : "0";
            respMainFrame = response.frame() === page.mainFrame() ? "1" : "0";
            annotate();
            onOp?.(
              "submit-response",
              `op=${op} status=${respStatus} navreq=${respNavReq} mainframe=${respMainFrame} t=${Date.now() - startedAt}ms`,
            );
          }
          return response;
        },
        (error: unknown) => {
          legR = 2;
          freeze("resp");
          throw error;
        },
      );
    const navigationPromise = page
      .waitForNavigation({ waitUntil: "load", timeout: 30_000, signal: abort.signal })
      .then(
        () => {
          if (!failed) {
            legN = 1;
            annotate();
          }
        },
        (error: unknown) => {
          legN = 2;
          freeze("nav");
          throw error;
        },
      );
    const clickPromise = button.click({ timeout: 30_000, signal: abort.signal }).then(
      () => {
        if (!failed) {
          legC = 1;
          annotate();
        }
      },
      (error: unknown) => {
        legC = 2;
        freeze("click");
        throw error;
      },
    );
    let submitFailure: Error | undefined;
    try {
      const [response] = await Promise.all([
        responsePromise,
        navigationPromise,
        clickPromise,
      ]);
      expect(response.status(), "same-path control POST status").toBe(200);
    } catch (error) {
      // Freeze first-failure state, stop the heartbeat, then abort the
      // pending sibling waits (the actual AbortSignal rejects them
      // immediately) and drain them in a bounded way.  Only a sanitized
      // fixed-enum-class/leg/flags error propagates - never the raw
      // message, cause or Playwright call log (which can carry private
      // URLs); the sanitized error is therefore thrown from function
      // scope, not with the caught error attached.
      clearInterval(heartbeat);
      if (!failed) {
        // The status assertion failed: all legs settled ok.
        failed = true;
        firstLeg = "status";
        firstFlags = `r=${legR} n=${legN} c=${legC}${respEvidence()} t=${Date.now() - startedAt}ms`;
      }
      abort.abort();
      await Promise.allSettled([responsePromise, navigationPromise, clickPromise]);
      const klass = safeDiagnosticClass(error);
      submitFailure = new Error(
        `controls submit-${op} failed leg=${firstLeg} class=${klass} ${firstFlags}`,
      );
    }
    if (submitFailure !== undefined) throw submitFailure;
    // R3 freshness: an unchanged URL does not mean the same document.
    // The raw per-document marker is passed in for the comparison only
    // and is never logged; only the boolean results cross back to the
    // test process as diagnostic output.
    const docFresh = await page.evaluate(
      (arg: { key: string; before: string }) => {
        const doc = (window as unknown as Record<string, unknown>)[arg.key];
        return {
          installed: typeof doc === "string" && doc.length > 0,
          changed: typeof doc === "string" && doc !== arg.before,
        };
      },
      { key: DOC_SENTINEL_KEY, before: docBefore },
    );
    expect(docFresh.installed, "document sentinel observable after POST").toBe(true);
    expect(docFresh.changed, "same-path POST produced a fresh main document").toBe(
      true,
    );
  } finally {
    clearInterval(heartbeat);
  }
}

async function formSequence(
  page: Page,
  url: string,
  onOp?: (op: string, flags?: string) => void,
): Promise<void> {
  // Deployed same-path POST interaction: the ONE shared native form
  // carries every bound control exactly once; successive submissions
  // must preserve the other control's state (multi-control parity).
  onOp?.("goto");
  await page.goto(url);
  onOp?.("form");
  await expect(page.locator("form#slaif-page-control-form")).toHaveCount(1);
  onOp?.("state");
  const searchInput = page.locator("input.renderer-collection-search-input");
  const facetInputs = page.locator("input.renderer-collection-filter-input");
  expect(await facetInputs.count()).toBe(2);
  expect(await facetInputs.nth(0).inputValue()).toBe("News, Press, Blog");
  expect(await facetInputs.nth(1).inputValue()).toBe("1");
  const listTitles = (component: string): Promise<string[]> =>
    page
      .locator(`[data-component="${component}"] ul.renderer-collection-list li h2`)
      .allTextContents();
  // The server-delivered default set (both surfaces, both phases).
  const delivered = ["Alpha briefing", "Beta dispatch"];
  // A: search "beta" -> only Beta in search; filter state untouched.
  onOp?.("fill-a");
  await searchInput.fill("beta");
  await submitControlForm(
    page,
    page.locator("button.renderer-collection-search-submit"),
    "a",
    onOp,
  );
  onOp?.("assert-a");
  expect(await listTitles("CollectionSearch")).toEqual(["Beta dispatch"]);
  expect(await listTitles("CollectionFilter")).toEqual(delivered);
  // B: facet kind=Press -> filter narrows; the search state is retained.
  onOp?.("fill-b");
  await facetInputs.nth(0).fill("Press");
  await submitControlForm(
    page,
    page.locator("button.renderer-collection-filter-submit"),
    "b",
    onOp,
  );
  onOp?.("assert-b");
  expect(await listTitles("CollectionSearch")).toEqual(["Beta dispatch"]);
  expect(await listTitles("CollectionFilter")).toEqual(["Beta dispatch"]);
  expect(await facetInputs.nth(0).inputValue()).toBe("Press");
  // C: clear search -> search restores its default set; the filter
  // state stays posted (no reset of the other control).
  onOp?.("fill-c");
  await searchInput.fill("");
  await submitControlForm(
    page,
    page.locator("button.renderer-collection-search-submit"),
    "c",
    onOp,
  );
  onOp?.("assert-c");
  expect(await listTitles("CollectionSearch")).toEqual(delivered);
  expect(await listTitles("CollectionFilter")).toEqual(["Beta dispatch"]);
}

/**
 * RC2 canonical controlled interaction: the PUBLISHED surface hydrates
 * the SAME bounded collection controls (identical markup, identical
 * bounded semantics) under the documented canonical client transport -
 * the RSC client state filters LIVE and the same-path form submission
 * is suppressed client-side (no network I/O, no state change, no new
 * authority).  The private surfaces use the ONE shared native page
 * form instead (formSequence); this sequence pins the transport
 * difference explicitly (the private shared form must be ABSENT here)
 * and proves the same bounded interaction sequence - search "beta",
 * facet kind=Press, clear search - with the exact item/order state at
 * every step and the other control's state retained, while every
 * suppressed submission is proven to navigate nowhere and POST nothing.
 */
async function canonicalControlSequence(page: Page, url: string): Promise<void> {
  await page.goto(url);
  await expect(page.locator("form#slaif-page-control-form")).toHaveCount(0);
  await expect(page.locator("form.renderer-collection-search-form")).toHaveCount(1);
  await expect(page.locator("form.renderer-collection-filter-form")).toHaveCount(1);
  let postCount = 0;
  page.on("request", (request) => {
    if (request.method() === "POST") postCount += 1;
  });
  const searchInput = page.locator("input.renderer-collection-search-input");
  const facetInputs = page.locator("input.renderer-collection-filter-input");
  expect(await facetInputs.count()).toBe(2);
  expect(await facetInputs.nth(0).inputValue()).toBe("News, Press, Blog");
  expect(await facetInputs.nth(1).inputValue()).toBe("1");
  const listTitles = (component: string): Promise<string[]> =>
    page
      .locator(`[data-component="${component}"] ul.renderer-collection-list li h2`)
      .allTextContents();
  // The server-delivered default set (same bounded fixture view).
  const delivered = ["Alpha briefing", "Beta dispatch"];
  // Suppressed submission: the click must not navigate or POST.
  const suppressedSubmit = async (button: Locator): Promise<void> => {
    const before = page.url();
    await button.click({ noWaitAfter: true });
    await expect(page).toHaveURL(before);
  };
  // A: search "beta" -> only Beta in search; filter state untouched.
  await searchInput.fill("beta");
  await suppressedSubmit(page.locator("button.renderer-collection-search-submit"));
  expect(await listTitles("CollectionSearch")).toEqual(["Beta dispatch"]);
  expect(await listTitles("CollectionFilter")).toEqual(delivered);
  // B: facet kind=Press -> filter narrows; the search state is retained.
  await facetInputs.nth(0).fill("Press");
  await suppressedSubmit(page.locator("button.renderer-collection-filter-submit"));
  expect(await listTitles("CollectionSearch")).toEqual(["Beta dispatch"]);
  expect(await listTitles("CollectionFilter")).toEqual(["Beta dispatch"]);
  expect(await facetInputs.nth(0).inputValue()).toBe("Press");
  // C: clear search -> search restores its default set; the filter
  // state stays (no reset of the other control).
  await searchInput.fill("");
  await suppressedSubmit(page.locator("button.renderer-collection-search-submit"));
  expect(await listTitles("CollectionSearch")).toEqual(delivered);
  expect(await listTitles("CollectionFilter")).toEqual(["Beta dispatch"]);
  expect(postCount, "suppressed canonical submissions make no network I/O").toBe(0);
}

async function navigationProof(
  page: Page,
  base: string,
  onOp?: (op: string, flags?: string) => void,
): Promise<void> {
  // Real link navigation on the deployed surface (no test handlers);
  // every switch carries concrete href AND destination-URL evidence in
  // both directions on both the static and dynamic routes.  The
  // renderer's privacy contract emits RELATIVE hrefs on the preview
  // surface (the private workspace identifier never enters the page
  // HTML) and site-rooted absolute hrefs on the review surface
  // (regionHref); both exact forms are pinned, and the browser's own
  // resolution plus the final page URL prove the concrete destination.
  // 083-6-a: operation-level bounded diagnostics (R2) on every leg.
  const isPreview = base.startsWith("/preview/");
  const siteKey = base.slice(base.lastIndexOf("/s/") + 3);
  const hrefFor = (currentRoute: string, target: string): string => {
    const targetPath = target === "/" ? "" : target.replace(/^\//, "");
    if (!isPreview) return targetPath ? `${base}/${targetPath}` : base;
    const current = currentRoute === "/" ? "" : currentRoute.replace(/^\//, "");
    const depth = current ? current.split("/").length : 0;
    if (depth === 0) return targetPath ? `${siteKey}/${targetPath}` : siteKey;
    const ups = "../".repeat(depth - 1);
    return targetPath ? `${ups}${targetPath}` : `${ups}./`;
  };
  // Forward on the STATIC route (home): the concrete counterpart href.
  onOp?.("home-goto");
  await page.goto(base);
  onOp?.("home-href");
  const slHome = page
    .locator(".renderer-region-language-item", { hasText: "sl-SI" })
    .locator("a");
  expect(await slHome.getAttribute("href"), "static switcher href").toBe(
    hrefFor("/", "/sl-SI"),
  );
  onOp?.("home-click");
  await slHome.click();
  onOp?.("home-load");
  await page.waitForLoadState();
  onOp?.("home-check");
  expect(page.url(), "static switch destination").toBe(`${ORIGIN}${base}/sl-SI`);
  expect(await page.locator("h1#page-title").innerText()).toBe("Domača stran");
  expect(await page.locator("main.renderer-surface").getAttribute("lang")).toBe(
    "sl-SI",
  );
  // Forward on the DYNAMIC route: the concrete (brace-free) href must
  // resolve the requested slug in the counterpart locale.
  onOp?.("detail-goto");
  await page.goto(`${base}/news/alpha`);
  onOp?.("detail-href");
  const slItem = page
    .locator(".renderer-region-language-item", { hasText: "sl-SI" })
    .locator("a");
  expect(await slItem.getAttribute("href"), "dynamic switcher href").toBe(
    hrefFor("/news/alpha", "/sl-SI/news/alpha"),
  );
  onOp?.("detail-click");
  await slItem.click();
  onOp?.("detail-load");
  await page.waitForLoadState();
  onOp?.("detail-check");
  expect(page.url(), "dynamic switch destination").toBe(
    `${ORIGIN}${base}/sl-SI/news/alpha`,
  );
  expect(await page.locator("h1#page-title").innerText()).toBe("Članek");
  expect(await page.locator("main.renderer-surface").getAttribute("lang")).toBe(
    "sl-SI",
  );
  // The bound item rendered in the counterpart locale (detail body).
  onOp?.("detail-body");
  expect(await page.locator("article.renderer-collection-detail h2").innerText()).toBe(
    "Prvi članek",
  );
  // The bound item's counterpart-locale SUMMARY (the addressed item's
  // localized body, not only its title).
  expect(await page.locator("article.renderer-collection-detail p").innerText()).toBe(
    "Prvi povzetek",
  );
  // Reverse on the SAME dynamic route back to the default locale.
  onOp?.("reverse-href");
  const enItem = page
    .locator(".renderer-region-language-item", { hasText: "en" })
    .locator("a");
  expect(await enItem.getAttribute("href"), "reverse switcher href").toBe(
    hrefFor("/sl-SI/news/alpha", "/news/alpha"),
  );
  onOp?.("reverse-click");
  await enItem.click();
  onOp?.("reverse-load");
  await page.waitForLoadState();
  onOp?.("reverse-check");
  expect(page.url(), "reverse switch destination").toBe(`${ORIGIN}${base}/news/alpha`);
  expect(await page.locator("h1#page-title").innerText()).toBe("Article");
  expect(await page.locator("main.renderer-surface").getAttribute("lang")).toBe("en");
  // The reverse click returned the DEFAULT-locale bound item: the
  // addressed item's title AND body, not only the page title/lang.
  expect(await page.locator("article.renderer-collection-detail h2").innerText()).toBe(
    "Alpha briefing",
  );
  expect(await page.locator("article.renderer-collection-detail p").innerText()).toBe(
    "Alpha summary",
  );
  // The region brand anchor itself navigates to the site root.
  onOp?.("brand-goto");
  await page.goto(`${base}/news/alpha`);
  onOp?.("brand");
  const brand = page.locator("a.renderer-region-brand");
  await expect(brand).toHaveCount(1);
  await expect(brand).toHaveText(/fpar-[0-9a-f]{8}/);
  onOp?.("brand-click");
  await brand.click();
  onOp?.("brand-load");
  await page.waitForLoadState();
  onOp?.("brand-check");
  expect(await page.locator("h1#page-title").innerText()).toBe("Parity home");
}

/**
 * Uniform-refusal negatives on the deployed surface for one phase:
 * foreign site key, lone-s path, literal-brace route, and the
 * detail of the filter-excluded item (the server filter is a real
 * content effect, not a fixture decoration).
 */
async function assertRefusals(
  api: APIRequestContext,
  base: string,
  siteKey: string,
  phase: string,
): Promise<void> {
  // Canonical slashless forms: the framework's trailing-slash 308
  // normalization fires before app routing, so refusal probes must use
  // the path form that actually reaches the resolver.
  const foreign = base.replace(`s/${siteKey}`, "s/foreign-0835b");
  expect(
    (await api.get(foreign, { maxRedirects: 0 })).status(),
    `${phase} foreign site key`,
  ).toBe(404);
  const lone = base.replace(`s/${siteKey}`, "s");
  expect(
    (await api.get(lone, { maxRedirects: 0 })).status(),
    `${phase} lone s path`,
  ).toBe(404);
  expect(
    (await api.get(`${base}/news/%7Bslug%7D`, { maxRedirects: 0 })).status(),
    `${phase} literal brace route`,
  ).toBe(404);
  expect(
    (await api.get(`${base}/news/gamma`, { maxRedirects: 0 })).status(),
    `${phase} filter-excluded detail`,
  ).toBe(404);
}

interface PhaseResult {
  keys: Map<string, string>;
  combos: Array<{ engine: EngineName; target: TargetName; version: string }>;
}

/**
 * 600s ceiling diagnostics: keeps exactly ONE `stage` annotation
 * (the CI SafeReporter reads the first via find) and replaces its
 * description in place at each phase boundary, so a timeout reports
 * the last reached stage.  The description carries ONLY phase,
 * engine, target, route ordinal, action and cumulative ms - no URLs,
 * IDs, tokens or growing annotation list.
 */
type StageDetail = {
  engine?: string;
  target?: string;
  route?: number;
  action?: string;
  /** 083-6-a R2: fixed-enum operation within an action leg. */
  op?: string;
  /** 083-6-a R2: bounded fixed-enum/boolean/relative-ms evidence. */
  flags?: string;
};
function makeStageTracker(info: TestInfo) {
  const startedAt = Date.now();
  return (phase: string, detail?: StageDetail): void => {
    const entry = {
      type: "stage",
      description: [
        `phase=${phase}`,
        detail?.engine ? `engine=${detail.engine}` : "",
        detail?.target ? `target=${detail.target}` : "",
        detail?.route !== undefined ? `route=${detail.route}` : "",
        `action=${detail?.action ?? "enter"}`,
        detail?.op ? `op=${detail.op}` : "",
        detail?.flags ? detail.flags : "",
        `elapsed=${Date.now() - startedAt}ms`,
      ]
        .filter(Boolean)
        .join(" "),
    };
    const index = info.annotations.findIndex((a) => a.type === "stage");
    if (index >= 0) info.annotations[index] = entry;
    else info.annotations.push(entry);
  };
}

async function runPhase(
  browsers: Record<EngineName, Browser>,
  phase: "preview" | "review",
  base: string,
  media: MediaIds,
  siteKey: string,
  credential: Secrets,
  snapshotDigest: string | null,
  onStage?: (detail: StageDetail) => void,
): Promise<PhaseResult> {
  const keys = new Map<string, string>();
  const combos: PhaseResult["combos"] = [];
  for (const pairing of MATRIX) {
    onStage?.({
      engine: pairing.engine,
      target: pairing.target,
      action: "combo",
    });
    const context = await browsers[pairing.engine].newContext({
      ...devices[pairing.target],
      baseURL: "http://localhost:8080",
    });
    await installDocumentSentinel(context);
    const page = await context.newPage();
    const failures = observe(page);
    let bodyFailed = false;
    let firstError: unknown = undefined;
    // Bounded op-level diagnostic sink: fixed-enum op + optional
    // bounded flags; exactOptionalPropertyTypes keeps undefined out of
    // the stage detail.
    const opStage = (action: string, op: string, flags?: string): void => {
      const detail: StageDetail = {
        engine: pairing.engine,
        target: pairing.target,
        action,
        op,
      };
      if (flags !== undefined) detail.flags = flags;
      onStage?.(detail);
    };
    try {
      // A REAL current human session in THIS context: fresh browser
      // contexts hold no cookies of their own, and the private pages
      // and same-path POST form require the session.
      await login(page, credential);
      let routeOrdinal = 0;
      for (const route of ROUTES) {
        onStage?.({
          engine: pairing.engine,
          target: pairing.target,
          route: routeOrdinal,
          action: "route",
        });
        routeOrdinal += 1;
        const response = await page.goto(`${base}${route}`);
        expect(response?.status(), `${phase} ${pairing.target} ${route}`).toBe(200);
        expectPrivateHeaders(response!);
        const facts = await collectFacts(page, base);
        assertExpected(route, facts, media, siteKey, phase);
        assertStyle(route, facts, pairing.target);
        if (phase === "review" && route === "/") {
          const banner = page.locator(".review-banner");
          await expect(banner).toHaveAttribute(
            "data-review-digest",
            snapshotDigest ?? "",
          );
          await expect(banner).toHaveAttribute("data-review-equal", "true");
        }
        keys.set(`${pairing.engine}/${pairing.target} :: ${route}`, contentKey(facts));
      }
      onStage?.({
        engine: pairing.engine,
        target: pairing.target,
        action: "controls",
      });
      await formSequence(page, `${base}/news`, (op, flags) =>
        opStage("controls", op, flags),
      );
      onStage?.({
        engine: pairing.engine,
        target: pairing.target,
        action: "locale-nav",
      });
      await navigationProof(page, base, (op, flags) =>
        opStage("locale-nav", op, flags),
      );
    } catch (error) {
      bodyFailed = true;
      firstError = error;
    } finally {
      // Failure priority body > collector > close: the original
      // collector assertion is retained whenever the body passed, and a
      // close failure still fails the pairing when body and collector
      // passed; no later failure ever replaces an earlier first failure
      // (which is rethrown from function scope after cleanup).
      if (!bodyFailed) {
        try {
          expect(failures(), `${phase} ${pairing.engine}/${pairing.target}`).toEqual(
            [],
          );
        } catch (error) {
          firstError = error;
        }
      }
      try {
        await context.close();
      } catch (error) {
        if (firstError === undefined) firstError = error;
      }
    }
    if (firstError !== undefined) {
      // Body/collector/close paths only throw Error objects; the fixed
      // fallback keeps the throw typed without embedding an
      // unclassified raw value.
      if (firstError instanceof Error) throw firstError;
      throw new Error("unclassified pairing failure");
    }
    combos.push({
      engine: pairing.engine,
      target: pairing.target,
      version: browsers[pairing.engine].version(),
    });
  }
  return { keys, combos };
}

/**
 * RC2 published-canonical INITIAL fixture (honest label: trusted test
 * setup, NOT online publication evidence).  The PUBLISHED canonical
 * surface of the run-unique parity site carries no dynamic-locale
 * detail content of its own (the W1 editorial lives in the terminal-
 * discarded COW workspace, and W2 published only the unrelated theme
 * fact), so the canonical locale-navigation criterion installs a
 * bounded run-unique mirror of the parity fixture directly into the
 * canonical base tables through the same trusted psql setup authority
 * seedParitySite uses above.  No workspace is created, nothing is
 * frozen or accepted, the site revision does not move, and no W1
 * private asset is referenced: this is initial canonical test data
 * for the render path only, bounded to this proof.
 */
function seedCanonicalFixture(project: string, siteId: string, tag: string): void {
  const typeId = crypto.randomUUID();
  const viewId = crypto.randomUUID();
  const homeEnId = crypto.randomUUID();
  const homeSlId = crypto.randomUUID();
  const newsEnId = crypto.randomUUID();
  const newsSlId = crypto.randomUUID();
  const itemEnId = crypto.randomUUID();
  const itemSlId = crypto.randomUUID();
  const fields = [
    {
      id: crypto.randomUUID(),
      key: "title",
      label: "Title",
      type: "short_text",
      localized: true,
      position: 0,
      validation: "{}",
    },
    {
      id: crypto.randomUUID(),
      key: "summary",
      label: "Summary",
      type: "long_text",
      localized: true,
      position: 1,
      validation: "{}",
    },
    {
      id: crypto.randomUUID(),
      key: "rank",
      label: "Rank",
      type: "integer",
      localized: false,
      position: 2,
      validation: "{}",
    },
    {
      id: crypto.randomUUID(),
      key: "kind",
      label: "Kind",
      type: "enum",
      localized: false,
      position: 3,
      validation: '{"choices":["News","Press","Blog"]}',
    },
  ];
  const items = [
    { id: crypto.randomUUID(), slug: "alpha", values: '{"rank":4,"kind":"News"}' },
    { id: crypto.randomUUID(), slug: "beta", values: '{"rank":3,"kind":"Press"}' },
    { id: crypto.randomUUID(), slug: "gamma", values: '{"rank":2,"kind":"Blog"}' },
    { id: crypto.randomUUID(), slug: "delta", values: '{"rank":1,"kind":"News"}' },
  ];
  // delta deliberately has NO sl-SI translation (same locale fallback
  // semantics as the W1 fixture): the sl-SI detail must render the en
  // values.
  const translations = [
    ...items.map((item, index) => ({
      id: crypto.randomUUID(),
      itemId: item.id,
      locale: "en",
      values: `{"title":"${EN_ITEMS[index]!.t}","summary":"${EN_ITEMS[index]!.s}"}`,
    })),
    ...items.slice(0, 3).map((item, index) => ({
      id: crypto.randomUUID(),
      itemId: item.id,
      locale: "sl-SI",
      values: `{"title":"${SL_ITEMS[index]!.t}","summary":"${SL_ITEMS[index]!.s}"}`,
    })),
  ];
  const filterProps = `{"viewId":"${viewId}","facets":[{"fieldKey":"kind","operator":"in","value":"News, Press, Blog"},{"fieldKey":"rank","operator":"gte","value":"1"}]}`;
  const searchProps = `{"viewId":"${viewId}","placeholder":"Search stories","limit":10}`;
  const detailProps = `{"viewId":"${viewId}"}`;
  const relatedProps = `{"viewId":"${viewId}","heading":"Related","limit":8}`;
  const columnsProps = '{"count":{"desktop":3,"tablet":2,"mobile":1},"gap":"md"}';
  const compositionRows = [
    {
      page: homeEnId,
      type: "Heading",
      order: 0,
      props: '{"text":"Home marker EN","level":2}',
    },
    {
      page: homeSlId,
      type: "Heading",
      order: 0,
      props: '{"text":"Oznaka domače","level":2}',
    },
    { page: newsEnId, type: "CollectionSearch", order: 0, props: searchProps },
    { page: newsEnId, type: "CollectionFilter", order: 1, props: filterProps },
    { page: newsEnId, type: "Columns", order: 2, props: columnsProps },
    { page: newsSlId, type: "CollectionSearch", order: 0, props: searchProps },
    { page: newsSlId, type: "CollectionFilter", order: 1, props: filterProps },
    { page: newsSlId, type: "Columns", order: 2, props: columnsProps },
    {
      page: itemEnId,
      type: "Heading",
      order: 0,
      props: '{"text":"Article body EN","level":2}',
    },
    { page: itemEnId, type: "CollectionDetail", order: 1, props: detailProps },
    { page: itemEnId, type: "RelatedItems", order: 2, props: relatedProps },
    {
      page: itemSlId,
      type: "Heading",
      order: 0,
      props: '{"text":"Osnova članka","level":2}',
    },
    { page: itemSlId, type: "CollectionDetail", order: 1, props: detailProps },
    { page: itemSlId, type: "RelatedItems", order: 2, props: relatedProps },
  ];
  psql(
    project,
    `BEGIN;
     INSERT INTO content.content_type_base
       (id, site_id, key, labels, slug_pattern, status, definition_version, settings)
     VALUES ('${typeId}'::uuid, '${siteId}'::uuid, 'oap_fparc_${tag}',
             '{"en":"Parity article"}'::jsonb, '/fparc-${tag}/{slug}', 'ACTIVE', 1, '{}'::jsonb);
     INSERT INTO content.field_definition_base
       (id, site_id, type_id, key, label, field_type, required, localized,
        cardinality, position, validation, ui_options, definition_version)
     VALUES
       ${fields.map((f) => `('${f.id}'::uuid, '${siteId}'::uuid, '${typeId}'::uuid, '${f.key}', '${f.label}', '${f.type}', true, ${f.localized}, 1, ${f.position}, '${f.validation}'::jsonb, '{}'::jsonb, 1)`).join(",\n       ")};
     INSERT INTO content.content_item_base
       (id, site_id, type_id, slug, status, type_definition_version, values)
     VALUES
       ${items.map((it) => `('${it.id}'::uuid, '${siteId}'::uuid, '${typeId}'::uuid, '${it.slug}', 'PUBLISHED', 1, '${it.values}'::jsonb)`).join(",\n       ")};
     INSERT INTO content.content_item_translation_base
       (id, site_id, item_id, locale, localized_values)
     VALUES
       ${translations.map((t) => `('${t.id}'::uuid, '${siteId}'::uuid, '${t.itemId}'::uuid, '${t.locale}', '${t.values}'::jsonb)`).join(",\n       ")};
     INSERT INTO content.collection_view_base
       (id, site_id, type_id, key, filter_spec, sort_spec, projection_spec,
        pagination_spec, definition_version, row_version)
     VALUES ('${viewId}'::uuid, '${siteId}'::uuid, '${typeId}'::uuid,
             'fpar-viewc-${tag}',
             '{"field":"kind","op":"in","value":["News","Press"]}'::jsonb,
             '{"field":"rank","direction":"desc"}'::jsonb,
             '{"fields":["title","summary","rank","kind"]}'::jsonb,
             '{"limit":2,"offset":0}'::jsonb, 1, 1);
     INSERT INTO content.page_base
       (id, site_id, slug, title, status, locale, parent_id, route_template)
     VALUES
       ('${homeEnId}'::uuid, '${siteId}'::uuid, 'home', 'Parity home', 'PUBLISHED', 'en', NULL, NULL),
       ('${homeSlId}'::uuid, '${siteId}'::uuid, 'home', 'Domača stran', 'PUBLISHED', 'sl-SI', NULL, NULL),
       ('${newsEnId}'::uuid, '${siteId}'::uuid, 'news', 'Parity news', 'PUBLISHED', 'en', NULL, NULL),
       ('${newsSlId}'::uuid, '${siteId}'::uuid, 'news', 'Novice', 'PUBLISHED', 'sl-SI', NULL, NULL),
       ('${itemEnId}'::uuid, '${siteId}'::uuid, 'item', 'Article', 'PUBLISHED', 'en', '${newsEnId}'::uuid, '{slug}'),
       ('${itemSlId}'::uuid, '${siteId}'::uuid, 'item', 'Članek', 'PUBLISHED', 'sl-SI', '${newsSlId}'::uuid, '{slug}');
     INSERT INTO content.page_composition_base
       (site_id, page_id, component_type, schema_version, slot_key, order_key, props)
     VALUES
       ${compositionRows.map((c) => `('${siteId}'::uuid, '${c.page}'::uuid, '${c.type}', '1', 'default', ${c.order}, '${c.props}'::jsonb)`).join(",\n       ")};
     COMMIT;`,
  );
  expect(
    psql(
      project,
      `SELECT (SELECT count(*) FROM content.content_type_base WHERE site_id='${siteId}'::uuid) || '|' ||
              (SELECT count(*) FROM content.field_definition_base WHERE site_id='${siteId}'::uuid) || '|' ||
              (SELECT count(*) FROM content.content_item_base WHERE site_id='${siteId}'::uuid) || '|' ||
              (SELECT count(*) FROM content.content_item_translation_base WHERE site_id='${siteId}'::uuid) || '|' ||
              (SELECT count(*) FROM content.collection_view_base WHERE site_id='${siteId}'::uuid) || '|' ||
              (SELECT count(*) FROM content.page_base WHERE site_id='${siteId}'::uuid) || '|' ||
              (SELECT count(*) FROM content.page_composition_base WHERE site_id='${siteId}'::uuid)`,
    ),
    "canonical fixture row census",
  ).toBe("1|4|4|7|1|6|14");
}

/**
 * Canonical per-route oracle: the PUBLISHED surface must carry the
 * exact same content contract as the parity fixture (titles, bodies,
 * server-delivered list sets, locale fallback, switcher/brand chrome)
 * while the surface chrome reports data-render-mode=canonical.  Theme
 * and computed-style tokens are intentionally NOT asserted here: the
 * canonical site theme is the W2-published token set, a different
 * (valid) theme from the W1 workspace styles.
 */
function assertCanonical(route: RouteName, facts: RouteFacts, siteKey: string): void {
  const locale = localeOf(route);
  const items = locale === "en" ? EN_ITEMS : SL_ITEMS;
  const item = (index: number): string => `${items[index]!.t}|${items[index]!.s}`;
  const expected = DELIVERED.map((i) => item(i));
  expect(facts.renderMode, "canonical render mode").toBe("canonical");
  if (route === "/" || route === "/sl-SI") {
    expect(facts.h1, "canonical home title").toBe(
      locale === "en" ? "Parity home" : "Domača stran",
    );
    expect(facts.lang).toBe(locale);
    expect(facts.headings).toEqual([
      locale === "en" ? "Home marker EN" : "Oznaka domače",
    ]);
    expect(facts.paragraphs).toEqual([]);
    expect(facts.lists).toEqual([]);
    expect(facts.detail).toBeNull();
    expect(facts.images).toEqual([]);
    expect(facts.docs).toEqual([]);
    expect(facts.columns).toBeNull();
    expect(facts.crumbs).toEqual([]);
  } else if (route === "/news" || route === "/sl-SI/news") {
    expect(facts.h1).toBe(locale === "en" ? "Parity news" : "Novice");
    expect(facts.lang).toBe(locale);
    expect(facts.headings).toEqual([
      items[0]!.t,
      items[1]!.t,
      items[0]!.t,
      items[1]!.t,
    ]);
    expect(facts.paragraphs).toEqual([
      items[0]!.s,
      items[1]!.s,
      items[0]!.s,
      items[1]!.s,
    ]);
    expect(facts.lists).toEqual([
      { component: "CollectionSearch", items: expected },
      { component: "CollectionFilter", items: expected },
    ]);
    expect(facts.detail).toBeNull();
    expect(facts.images).toEqual([]);
    expect(facts.docs).toEqual([]);
    expect(facts.columns, "canonical responsive container present").not.toBeNull();
    expect(facts.columns!.classes).toBe(
      "renderer-columns renderer-columns--3 renderer-columns--tablet-2 renderer-columns--mobile-1 renderer-gap--md renderer-align--stretch",
    );
    expect(facts.crumbs).toEqual([]);
  } else {
    const slug = route.split("/").pop()!;
    const index = SLUGS.indexOf(slug);
    expect(index, "known canonical slug").toBeGreaterThanOrEqual(0);
    const related = FILTERED.filter((candidate) => candidate !== index);
    expect(facts.h1).toBe(locale === "en" ? "Article" : "Članek");
    expect(facts.lang).toBe(locale);
    expect(facts.headings).toEqual([
      locale === "en" ? "Article body EN" : "Osnova članka",
      items[index]!.t,
      "Related",
      ...related.map((i) => items[i]!.t),
    ]);
    expect(facts.paragraphs).toEqual([
      items[index]!.s,
      ...related.map((i) => items[i]!.s),
    ]);
    expect(facts.lists).toEqual([
      { component: "RelatedItems", items: related.map((i) => item(i)) },
    ]);
    expect(facts.detail).toEqual({ heading: items[index]!.t, body: items[index]!.s });
    expect(facts.images).toEqual([]);
    expect(facts.docs).toEqual([]);
    expect(facts.columns).toBeNull();
    expect(facts.crumbs).toEqual([
      locale === "en" ? "Parity news" : "Novice",
      locale === "en" ? "Article" : "Članek",
    ]);
  }
  // Surface chrome common to every canonical route: the two-locale
  // switcher with the concrete counterpart route (site-rooted absolute
  // href re-rooted to the site-local form), the brand anchor, and the
  // synthesized root nav entry.
  expect(facts.switcher.map((s) => s.tag)).toEqual(["en", "sl-SI"]);
  expect(facts.switcher.find((s) => s.tag === locale)?.current).toBe(true);
  const counterpart = locale === "en" ? "sl-SI" : "en";
  expect(facts.switcher.find((s) => s.tag === counterpart)?.current).toBe(false);
  const counterpartRoute =
    counterpart === "en"
      ? route === "/"
        ? "/"
        : route.startsWith("/sl-SI")
          ? route.slice("/sl-SI".length) || "/"
          : route
      : route === "/"
        ? "/sl-SI"
        : `/sl-SI${route}`;
  expect(facts.switcher.find((s) => s.tag === counterpart)?.route).toBe(
    counterpartRoute,
  );
  expect(facts.brand).toEqual({ label: siteKey, route: "/" });
  expect(facts.regionLinks).toEqual([{ label: siteKey, route: "/" }]);
}

/**
 * RC2 published-canonical matrix: the SAME six engine/target pairings
 * (existing launch machinery, device descriptors verbatim) render the
 * PUBLISHED /s/<siteKey> surface anonymously through the public NGINX
 * origin.  Per pairing: every canonical route is oracle-checked for
 * data-render-mode=canonical, the selected-locale lang/body, the
 * concrete brace-free switcher hrefs and the locale fallback; then
 * the hydrated bounded collection controls (canonicalControlSequence:
 * live client state, suppressed same-path submissions - the canonical
 * transport of the same supported controls) and the
 * forward/reverse link-click locale navigation (navigationProof) run
 * on the public surface itself.  No human session is established: the
 * canonical site is the public surface by design.
 */
async function canonicalPhase(
  browsers: Record<EngineName, Browser>,
  base: string,
  siteKey: string,
  onStage?: (detail: StageDetail) => void,
): Promise<PhaseResult> {
  const keys = new Map<string, string>();
  const combos: PhaseResult["combos"] = [];
  for (const pairing of MATRIX) {
    onStage?.({
      engine: pairing.engine,
      target: pairing.target,
      action: "combo",
    });
    const context = await browsers[pairing.engine].newContext({
      ...devices[pairing.target],
      baseURL: ORIGIN,
    });
    const page = await context.newPage();
    const failures = observe(page);
    try {
      let routeOrdinal = 0;
      for (const route of ROUTES) {
        onStage?.({
          engine: pairing.engine,
          target: pairing.target,
          route: routeOrdinal,
          action: "route",
        });
        routeOrdinal += 1;
        const response = await page.goto(`${base}${route}`);
        expect(response?.status(), `canonical ${pairing.target} ${route}`).toBe(200);
        if (route === "/") {
          // Public canonical pages are never edge-cached (the same
          // force-dynamic contract the 083/1 accept proof pins on the
          // public canonical HTML).
          expect(response!.headers()["cache-control"]).toBe(
            "private, no-cache, no-store, max-age=0, must-revalidate",
          );
        }
        const facts = await collectFacts(page, base);
        assertCanonical(route, facts, siteKey);
        keys.set(`${pairing.engine}/${pairing.target} :: ${route}`, contentKey(facts));
      }
      onStage?.({
        engine: pairing.engine,
        target: pairing.target,
        action: "controls",
      });
      await canonicalControlSequence(page, `${base}/news`);
      onStage?.({
        engine: pairing.engine,
        target: pairing.target,
        action: "locale-nav",
      });
      await navigationProof(page, base);
    } finally {
      expect(failures(), `canonical ${pairing.engine}/${pairing.target}`).toEqual([]);
      await context.close();
    }
    combos.push({
      engine: pairing.engine,
      target: pairing.target,
      version: browsers[pairing.engine].version(),
    });
  }
  return { keys, combos };
}

test("frozen-review-parity-six-stable-pairings", async () => {
  // Same explicit budget class as the existing complex lifecycle specs
  // (240..600 s); the measured phase wall time is annotated below.
  test.setTimeout(600_000);
  const credential = secrets();
  const project = composeProject();
  const tag = randomHex(4);
  const idem = () => `fpar-${tag}-${crypto.randomUUID().slice(0, 8)}`;
  // 600s ceiling diagnostics: the single in-place-replaced stage marker.
  const stage = makeStageTracker(test.info());
  stage("setup");
  let bodyCompleted = false;

  const browsers: Record<EngineName, Browser> = {
    chromium: await chromium.launch(),
    firefox: await firefox.launch(),
    webkit: await webkit.launch(),
  };
  try {
    // ------------------------------------------------------------- login
    // A real browser session for the API phase: the authenticated
    // browser context holds the session/CSRF cookies and its bound
    // request context sends them on every control/agent call (the same
    // wiring the established e2e specs use).
    const setupContext = await browsers.chromium.newContext({
      baseURL: "http://localhost:8080",
    });
    const setupPage = await setupContext.newPage();
    stage("setup", { action: "login" });
    await login(setupPage, credential);
    const contextCookies = await setupContext.cookies();
    const csrf = contextCookies.find((c) => c.name === "slaif_csrf")?.value;
    expect(csrf, "csrf cookie").toBeTruthy();
    const api = setupPage.request;

    // ------------------------------------------------------- trusted setup
    stage("setup", { action: "seed" });
    const { siteId, siteKey } = seedParitySite(project);

    const workspaceResponse = await api.post(
      `/api/control/v1/sites/${siteId}/workspaces/`,
      {
        headers: { "X-CSRF-Token": csrf!, "Idempotency-Key": `fpar-${tag}-workspace` },
        data: {
          title: `083/5-b parity ${tag}`,
          task_description: "Bounded frozen review parity proof",
          delegation_preset: "L4_SITE_ARCHITECT",
          duration_hours: 2,
          request_quota: 1000,
          mutation_quota: 200,
          delete_quota: 0,
          upload_quota: 4,
          // Small bounded browser-run allowance: the capability mints
          // browser_max_runs from this workspace quota (038), so a real
          // positive worker run requires at least one.
          browser_quota: 1,
          resource_constraints: { delete_enabled: false, max_deletes: 0 },
        },
      },
    );
    expect(workspaceResponse.status()).toBe(201);
    const workspaceId = ((await workspaceResponse.json()) as { workspace_id: string })
      .workspace_id;
    const capabilityResponse = await api.post(
      `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/capabilities/`,
      { headers: { "X-CSRF-Token": csrf!, "Idempotency-Key": `fpar-${tag}-cap` } },
    );
    expect(capabilityResponse.status()).toBe(201);
    const token = ((await capabilityResponse.json()) as { token: string }).token;
    const agent = (path: string, body: unknown) =>
      api.post(path, {
        headers: { Authorization: `Bearer ${token}`, "Idempotency-Key": idem() },
        data: body,
      });
    const agentRecord = async (path: string, body: unknown) => {
      const response = await agent(path, body);
      expect(response.status(), path).toBe(201);
      return (await response.json()) as { record: Record<string, unknown> };
    };
    const component = (
      pageId: string,
      componentType: string,
      props: Record<string, unknown>,
    ) =>
      agent(`/api/agent/v1/pages/${pageId}/components`, {
        component_type: componentType,
        slot_key: "default",
        props,
      });

    // ------------------------------------------------- public Agent capture
    stage("api", { action: "capture" });
    const newsSlug = `fpar-${tag}`;
    const typeDoc = await agentRecord("/api/agent/v1/content-model/types", {
      key: `oap_fpar_${tag}`,
      labels: { en: "Parity article" },
      slug_pattern: `/${newsSlug}/{slug}`,
      settings: {},
    });
    const typeId = String(typeDoc.record.id);
    const fieldSpecs = [
      { key: "title", label: "Title", field_type: "short_text", localized: true },
      { key: "summary", label: "Summary", field_type: "long_text", localized: true },
      { key: "rank", label: "Rank", field_type: "integer", localized: false },
      {
        key: "kind",
        label: "Kind",
        field_type: "enum",
        localized: false,
        validation: { choices: ["News", "Press", "Blog"] },
      },
    ];
    for (let index = 0; index < fieldSpecs.length; index += 1) {
      const field = fieldSpecs[index]!;
      await agentRecord(`/api/agent/v1/content-model/types/${typeId}/fields`, {
        key: field.key,
        label: field.label,
        field_type: field.field_type,
        localized: field.localized,
        required: true,
        position: index,
        ...(field.validation ? { validation: field.validation } : {}),
      });
    }
    const itemIds: string[] = [];
    for (let index = 0; index < 4; index += 1) {
      const itemDoc = await agentRecord(`/api/agent/v1/content-items/types/${typeId}`, {
        type_id: typeId,
        slug: SLUGS[index]!,
        status: "PUBLISHED",
        values: { rank: RANKS[index], kind: KINDS[index] },
      });
      itemIds.push(String(itemDoc.record.id));
      await agentRecord(`/api/agent/v1/content-items/${itemIds[index]}/translations`, {
        locale: "en",
        localized_values: {
          title: EN_ITEMS[index]!.t,
          summary: EN_ITEMS[index]!.s,
        },
      });
      if (index < 3) {
        await agentRecord(
          `/api/agent/v1/content-items/${itemIds[index]}/translations`,
          {
            locale: "sl-SI",
            localized_values: {
              title: SL_ITEMS[index]!.t,
              summary: SL_ITEMS[index]!.s,
            },
          },
        );
      }
    }
    const viewDoc = await agentRecord(
      `/api/agent/v1/collection-views/types/${typeId}`,
      {
        type_id: typeId,
        key: `fpar-view-${tag}`,
        // REAL supported server-side filter (kind IN (News, Press)) plus a
        // pagination limit that truncates the three passing candidates to
        // the two delivered list items.
        filter_spec: { field: "kind", op: "in", value: ["News", "Press"] },
        sort_spec: { field: "rank", direction: "desc" },
        projection_spec: { fields: ["title", "summary", "rank", "kind"] },
        pagination_spec: { limit: 2, offset: 0 },
      },
    );
    const viewId = String(viewDoc.record.id);

    const pageCreate = (body: Record<string, unknown>) =>
      agentRecord("/api/agent/v1/pages/", body);
    const pageId = (doc: { record: Record<string, unknown> }): string =>
      String(doc.record.id);
    const homeEn = pageId(
      await pageCreate({
        slug: "home",
        title: "Parity home",
        status: "PUBLISHED",
        locale: "en",
      }),
    );
    const homeSl = pageId(
      await pageCreate({
        slug: "home",
        title: "Domača stran",
        status: "PUBLISHED",
        locale: "sl-SI",
      }),
    );
    const newsEn = pageId(
      await pageCreate({
        slug: "news",
        title: "Parity news",
        status: "PUBLISHED",
        locale: "en",
      }),
    );
    const newsSl = pageId(
      await pageCreate({
        slug: "news",
        title: "Novice",
        status: "PUBLISHED",
        locale: "sl-SI",
      }),
    );
    const itemEn = pageId(
      await pageCreate({
        slug: "item",
        title: "Article",
        status: "PUBLISHED",
        locale: "en",
        parent_id: newsEn,
        route_template: "{slug}",
      }),
    );
    const itemSl = pageId(
      await pageCreate({
        slug: "item",
        title: "Članek",
        status: "PUBLISHED",
        locale: "sl-SI",
        parent_id: newsSl,
        route_template: "{slug}",
      }),
    );

    const mediaUpload = (file: Buffer, filename: string, mime: string, alt?: string) =>
      api.post("/api/agent/v1/media/assets", {
        headers: { Authorization: `Bearer ${token}`, "Idempotency-Key": idem() },
        multipart: (() => {
          const form = new FormData();
          form.append(
            "file",
            new Blob([new Uint8Array(file)], { type: mime }),
            filename,
          );
          if (alt) form.append("alt_text", alt);
          return form;
        })(),
      });
    const pngDigest = sha256Hex(TINY_PNG);
    const pdfBytes = makePdf(1, `fpar-${tag}`);
    const pdfDigest = sha256Hex(pdfBytes);
    const pngUpload = await mediaUpload(
      TINY_PNG,
      "parity-proof.png",
      "image/png",
      "Parity proof image",
    );
    expect(pngUpload.status()).toBe(201);
    const pngUploadBody = (await pngUpload.json()) as {
      record: Record<string, unknown>;
    };
    expect(pngUploadBody.record.content_hash).toBe(pngDigest);
    const pngMediaId = String(pngUploadBody.record.id);
    const pdfUpload = await mediaUpload(
      pdfBytes,
      "parity-brief.pdf",
      "application/pdf",
    );
    expect(pdfUpload.status()).toBe(201);
    const pdfUploadBody = (await pdfUpload.json()) as {
      record: Record<string, unknown>;
    };
    expect(pdfUploadBody.record.content_hash).toBe(pdfDigest);
    const pdfMediaId = String(pdfUploadBody.record.id);
    const media: MediaIds = { png: pngMediaId, pdf: pdfMediaId };

    for (const [pageIdValue, textValue] of [
      [homeEn, "Home marker EN"],
      [homeSl, "Oznaka domače"],
    ] as const) {
      const heading = await component(pageIdValue, "Heading", {
        text: textValue,
        level: 2,
      });
      expect(heading.status()).toBe(201);
    }
    for (const pageIdValue of [homeEn, homeSl]) {
      for (const response of [
        await component(pageIdValue, "Image", {
          mediaId: pngMediaId,
          alt: "Parity proof image",
        }),
        await component(pageIdValue, "DocumentList", {
          items: [{ mediaId: pdfMediaId, label: "Field brief" }],
        }),
      ]) {
        expect(response.status()).toBe(201);
      }
    }
    for (const pageIdValue of [newsEn, newsSl]) {
      for (const response of [
        await component(pageIdValue, "CollectionSearch", {
          viewId,
          placeholder: "Search stories",
          limit: 10,
        }),
        await component(pageIdValue, "CollectionFilter", {
          viewId,
          facets: [
            { fieldKey: "kind", operator: "in", value: "News, Press, Blog" },
            { fieldKey: "rank", operator: "gte", value: "1" },
          ],
        }),
      ]) {
        expect(response.status()).toBe(201);
      }
      // Non-default responsive container (the existing supported
      // desktop/tablet/mobile form): created with a scalar count, then
      // posted as the design-system responsive map through the real
      // component design PATCH (the proven product update path).
      const columnsDoc = await agentRecord(
        `/api/agent/v1/pages/${pageIdValue}/components`,
        {
          component_type: "Columns",
          slot_key: "default",
          props: { count: 2, gap: "md" },
        },
      );
      const columnsPatch = await api.patch(
        `/api/agent/v1/components/${String(columnsDoc.record.id)}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            "Idempotency-Key": idem(),
          },
          data: {
            props: { count: { desktop: 3, tablet: 2, mobile: 1 }, gap: "md" },
            expected_row_version: 1,
          },
        },
      );
      expect(columnsPatch.status(), "responsive design PATCH").toBe(200);
      expect(
        (
          (await columnsPatch.json()) as {
            record: { props: Record<string, unknown> };
          }
        ).record.props.count,
      ).toEqual({ desktop: 3, tablet: 2, mobile: 1 });
    }
    for (const [pageIdValue, headingText] of [
      [itemEn, "Article body EN"],
      [itemSl, "Osnova članka"],
    ] as const) {
      for (const response of [
        await component(pageIdValue, "Heading", { text: headingText, level: 2 }),
        await component(pageIdValue, "CollectionDetail", { viewId }),
        await component(pageIdValue, "RelatedItems", {
          viewId,
          heading: "Related",
          limit: 8,
        }),
      ]) {
        expect(response.status()).toBe(201);
      }
    }

    // ------------------------------------------- non-default style + region
    const themeResponse = await api.get("/api/agent/v1/theme", {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(themeResponse.status()).toBe(200);
    const theme = (await themeResponse.json()) as { row_version: number };
    const themePatch = await api.patch("/api/agent/v1/theme", {
      headers: { Authorization: `Bearer ${token}`, "Idempotency-Key": idem() },
      data: {
        palette: { preset: "meadow" },
        typography: { family: "serif", scale: "spacious" },
        layout: { content_width: "lg" },
        expected_row_version: theme.row_version,
      },
    });
    expect(themePatch.status()).toBe(200);
    const styleResponse = await api.get(`/api/agent/v1/pages/${itemEn}/style`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(styleResponse.status()).toBe(200);
    const style = (await styleResponse.json()) as { row_version: number };
    const stylePatch = await api.patch(`/api/agent/v1/pages/${itemEn}/style`, {
      headers: { Authorization: `Bearer ${token}`, "Idempotency-Key": idem() },
      data: {
        palette: { preset: "ember" },
        typography: { family: "mono" },
        expected_row_version: style.row_version,
      },
    });
    expect(stylePatch.status()).toBe(200);

    // ------------------------------------------------- redirect + navigation
    const redirectResponse = await agent("/api/agent/v1/redirects", {
      source_route: `/old-${newsSlug}`,
      target: "/news",
      status_code: 301,
    });
    expect(redirectResponse.status()).toBe(201);
    const navigationDoc = await agentRecord("/api/agent/v1/navigation", {
      key: `fpar-nav-${tag}`,
      label: "Main",
      labels: { en: "Main", "sl-SI": "Glavni" },
      settings: {},
    });
    const navigationId = String(navigationDoc.record.id);
    for (const [pageIdValue, label] of [
      [homeEn, "Home"],
      [newsEn, "News"],
    ] as const) {
      const itemResponse = await agent(
        `/api/agent/v1/navigation/${navigationId}/items`,
        {
          page_id: pageIdValue,
          target_kind: "PAGE",
          target_value: pageIdValue,
          labels: { en: label, "sl-SI": label },
        },
      );
      expect(itemResponse.status()).toBe(201);
    }

    const previewBase = `/preview/${workspaceId}/s/${siteKey}`;
    const reviewBase = `/review/${workspaceId}/s/${siteKey}`;

    // ----------------------------------------------------------- phase A
    stage("phaseA", { action: "enter" });
    const phaseAStart = Date.now();
    const previewPhase = await runPhase(
      browsers,
      "preview",
      previewBase,
      media,
      siteKey,
      credential,
      null,
      (detail) => stage("phaseA", detail),
    );
    const phaseADurationMs = Date.now() - phaseAStart;
    stage("api", { action: "preview-media" });

    // active private bytes BEFORE freeze (workspace-scoped namespace)
    const previewPng = await api.get(
      `/media/v1/sites/${siteId}/workspaces/${workspaceId}/preview/assets/${pngMediaId}/content`,
    );
    expect(previewPng.status()).toBe(200);
    expect(previewPng.headers()["cache-control"]).toBe("private, no-store");
    expect(previewPng.headers()["x-robots-tag"]).toBe("noindex, nofollow, noarchive");
    expect(Buffer.from(await previewPng.body()).equals(TINY_PNG)).toBe(true);
    const previewPdf = await api.get(
      `/media/v1/sites/${siteId}/workspaces/${workspaceId}/preview/assets/${pdfMediaId}/content`,
    );
    expect(previewPdf.status()).toBe(200);
    expect(Buffer.from(await previewPdf.body()).equals(pdfBytes)).toBe(true);

    // ----------------------------------------------- confined worker run
    // BEFORE freeze, the actual deployed confined browser worker
    // renders the bound active preview in a real browser and digests
    // the bound media bytes inside the worker process. This is the RC4
    // private IMAGE+DOCUMENT byte proof from an actual TypeScript run —
    // not a manually signed ASGI simulation.
    // The bound route is the site-key form /s/<siteKey>, the same shape
    // the human flow uses: the existing SiteResolver local branch
    // resolves the run-unique site from the authority host without any
    // domain row, and the signed credential binds exactly that route.
    stage("worker", { action: "run" });
    const runCreated = await api.post("/api/agent/v1/preview-runs", {
      headers: { Authorization: `Bearer ${token}`, "Idempotency-Key": idem() },
      data: {
        version: "browser-preview/v1",
        route: `/s/${siteKey}`,
        target: "desktop-chromium",
        evidence: ["screenshot"],
      },
    });
    expect(runCreated.status()).toBe(202);
    const runBody = (await runCreated.json()) as { run_id: string; state: string };
    expect(runBody.state).toBe("QUEUED");
    const runId = runBody.run_id;
    // Product quota enforcement: the single bounded allowance is now
    // consumed, so the next run request for the same capability is
    // refused at the run-create guard (429).
    const runOver = await api.post("/api/agent/v1/preview-runs", {
      headers: { Authorization: `Bearer ${token}`, "Idempotency-Key": idem() },
      data: {
        version: "browser-preview/v1",
        route: `/s/${siteKey}`,
        target: "desktop-chromium",
        evidence: ["screenshot"],
      },
    });
    expect(runOver.status()).toBe(429);
    interface BoundMediaSummary {
      refsSeen: number;
      nodesVisited: number;
      walkLimitReached: boolean;
      candidates: number;
      omittedOverLimit: number;
      reads: Array<{
        mediaId: string;
        assetType: string;
        sha256: string;
        sizeBytes: number;
        contentType: string;
      }>;
      failures: Array<{ mediaId: string; status: string }>;
    }
    stage("worker", { action: "wait-complete" });
    let boundMedia: BoundMediaSummary | undefined;
    const runDeadline = Date.now() + 240_000;
    for (;;) {
      const runState = await api.get(`/api/agent/v1/preview-runs/${runId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      expect(runState.status()).toBe(200);
      const stateBody = (await runState.json()) as {
        state: string;
        summary?: { boundMedia?: BoundMediaSummary };
      };
      if (stateBody.state === "COMPLETED") {
        boundMedia = stateBody.summary?.boundMedia;
        break;
      }
      if (
        stateBody.state === "FAILED" ||
        stateBody.state === "TIMED_OUT" ||
        stateBody.state === "CANCELLED"
      ) {
        throw new Error(`worker run terminated ${stateBody.state}`);
      }
      if (Date.now() > runDeadline) throw new Error("worker run deadline");
      await new Promise((resolve) => setTimeout(resolve, 2_000));
    }
    expect(boundMedia, "boundMedia summary").toBeDefined();
    expect(boundMedia!.walkLimitReached).toBe(false);
    expect(boundMedia!.failures).toEqual([]);
    const workerPng = boundMedia!.reads.find((r) => r.mediaId === pngMediaId);
    const workerPdf = boundMedia!.reads.find((r) => r.mediaId === pdfMediaId);
    expect(workerPng?.assetType, "image read present").toBe("image");
    expect(workerPng?.sha256).toBe(pngDigest);
    expect(workerPng?.sizeBytes).toBe(TINY_PNG.length);
    expect(workerPng?.contentType).toBe("image/png");
    expect(workerPdf?.assetType, "document read present").toBe("document");
    expect(workerPdf?.sha256).toBe(pdfDigest);
    expect(workerPdf?.sizeBytes).toBe(pdfBytes.length);
    expect(workerPdf?.contentType).toBe("application/pdf");
    // Trusted backing: the stored run row is COMPLETED and its stored
    // summary retains both exact asset digests.
    expect(
      psql(project, `SELECT state FROM control.browser_run WHERE id = '${runId}'`),
    ).toBe("COMPLETED");
    expect(
      psql(
        project,
        `SELECT count(*) FROM control.browser_run
          WHERE id = '${runId}'
            AND summary::text LIKE '%${pngDigest}%'
            AND summary::text LIKE '%${pdfDigest}%'`,
      ),
    ).toBe("1");

    // active preview redirect (preview-rooted location) + anonymous
    const previewRedirect = await api.get(`${previewBase}/old-${newsSlug}`, {
      maxRedirects: 0,
    });
    expect(previewRedirect.status()).toBe(301);
    expect(previewRedirect.headers()["location"]).toBe(`${previewBase}/news`);
    const anonymous = await browsers.chromium.newContext();
    // Actual route semantics differ by path form: the framework's
    // trailing-slash normalization is a 308 to the exact slashless
    // path, and the app's anonymous auth redirect is a 307 with a
    // relative same-origin /login destination on the canonical
    // (slashless) path. Both are pinned separately.
    const anonSlash = await anonymous.request.get(`${previewBase}/`, {
      maxRedirects: 0,
    });
    expect(anonSlash.status()).toBe(308);
    expect(anonSlash.headers()["location"]).toBe(`${previewBase}`);
    const anonPreview = await anonymous.request.get(`${previewBase}`, {
      maxRedirects: 0,
    });
    expect(anonPreview.status()).toBe(307);
    // Exact relative destination: the public client resolves it
    // against its own origin, so an internal bind origin in the
    // Location header would fail this assertion.
    expect(anonPreview.headers()["location"]).toBe("/login");
    // Public login reachability on the public origin.
    expect((await anonymous.request.get("/login")).status()).toBe(200);
    // Actual following (redirects enabled): the editorial redirect
    // chain must land on the intended delivered list content, not
    // merely present a shaped Location header.
    const followedPreview = await api.get(`${previewBase}/old-${newsSlug}`);
    expect(followedPreview.status(), "preview redirect follow").toBe(200);
    expect(followedPreview.url()).toBe(`${ORIGIN}${previewBase}/news`);
    expect(await followedPreview.text()).toContain(
      '<h1 id="page-title">Parity news</h1>',
    );
    await assertRefusals(api, previewBase, siteKey, "preview");

    // ------------------------------------------------------------ freeze
    stage("freeze", { action: "request" });
    const freeze = await api.post(
      `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/freeze/`,
      { headers: { "X-CSRF-Token": csrf! } },
    );
    expect(freeze.status()).toBe(202);
    stage("freeze", { action: "wait-review" });
    const deadline = Date.now() + 240_000;
    let status = "";
    for (;;) {
      expect(
        Number(
          psql(
            project,
            `SELECT count(*) FROM control.review_snapshot
              WHERE workspace_id = '${workspaceId}'
                AND EXISTS (SELECT 1 FROM control.workspace w
                            WHERE w.id = '${workspaceId}'::uuid
                              AND w.status = 'FREEZING')`,
          ),
        ),
      ).toBe(0);
      const workspace = await api.get(
        `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}`,
      );
      expect(workspace.status()).toBe(200);
      status = ((await workspace.json()) as { status: string }).status;
      if (status === "REVIEW") break;
      expect(["ACTIVE", "FREEZING"]).toContain(status);
      if (Date.now() > deadline) throw new Error(`timeout at ${status}`);
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    const snapshotId = psql(
      project,
      `SELECT id FROM control.review_snapshot WHERE workspace_id = '${workspaceId}'`,
    );
    expect(snapshotId).toMatch(/^[0-9a-f-]{36}$/i);
    expect(
      psql(
        project,
        `SELECT payload->>'state_version' FROM control.review_snapshot
          WHERE id = '${snapshotId}'`,
      ),
    ).toBe("review-snapshot/v2");
    expect(
      psql(
        project,
        `SELECT digest = encode(sha256(convert_to(
           control.slaif_canonical_jsonb_text(payload), 'UTF8')), 'hex')
          FROM control.review_snapshot WHERE id = '${snapshotId}'`,
      ),
    ).toBe("t");
    // Every one of the four media-binding predicates must hold
    // (map membership for both ids AND retained inventory rows).
    expect(
      psql(
        project,
        `SELECT jsonb_path_exists(payload, '$.media."${pngMediaId}"')
              AND jsonb_path_exists(payload, '$.media."${pdfMediaId}"')
              AND jsonb_path_exists(payload, '$.media_inventory[*] ? (@.id == "${pngMediaId}")')
              AND jsonb_path_exists(payload, '$.media_inventory[*] ? (@.id == "${pdfMediaId}")')
          FROM control.review_snapshot WHERE id = '${snapshotId}'`,
      ),
    ).toBe("t");
    // The stored frozen descriptors bind the ACTUAL uploaded digests.
    expect(
      psql(
        project,
        `SELECT (payload->'media'->'${pngMediaId}'->>'content_hash') = '${pngDigest}'
          AND (payload->'media'->'${pdfMediaId}'->>'content_hash') = '${pdfDigest}'
          FROM control.review_snapshot WHERE id = '${snapshotId}'`,
      ),
    ).toBe("t");
    // RC2 browser-evidence sibling binding: the stored v2 snapshot
    // carries the NONEMPTY browser_evidence of the SAME completed run
    // on the SAME workspace (the 076 completion gate admits only
    // COMPLETED runs of the frozen workspace, so a missing, foreign
    // or non-terminal run id cannot substitute).
    expect(
      psql(
        project,
        `SELECT count(*) FROM control.review_snapshot
          WHERE id = '${snapshotId}'
            AND browser_evidence = '[{"id":"${runId}"}]'::jsonb
            AND workspace_id = '${workspaceId}'::uuid
            AND site_id = '${siteId}'::uuid`,
      ),
      "stored v2 browser_evidence binds the selected completed run",
    ).toBe("1");
    expect(
      psql(
        project,
        `SELECT count(*) FROM control.browser_run
          WHERE id = '${runId}'
            AND workspace_id = '${workspaceId}'::uuid
            AND site_id = '${siteId}'::uuid
            AND state = 'COMPLETED'`,
      ),
      "completed run row is bound to the same workspace/site",
    ).toBe("1");

    // ------------------------------------------------------------- review
    stage("review", { action: "read" });
    const reviewResponse = await api.get(
      `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/review/`,
    );
    expect(reviewResponse.status()).toBe(200);
    const reviewDoc = (await reviewResponse.json()) as {
      snapshot: { id: string; digest: string; state_version: string };
      drift: { equal: boolean };
      normalized_state: Record<string, unknown>;
    };
    expect(reviewDoc.snapshot.id).toBe(snapshotId);
    expect(reviewDoc.snapshot.state_version).toBe("review-snapshot/v2");
    expect(reviewDoc.drift.equal).toBe(true);
    expect(Object.keys(reviewDoc.normalized_state).sort()).toEqual([
      "base_site_revision",
      "content",
      "locales",
      "media",
      "media_inventory",
      "navigation",
      "operation_watermark",
      "page_compositions",
      "pages",
      "proposals",
      "redirects",
      "regions",
      "site",
      "site_id",
      "state_version",
      "theme",
      "workspace_id",
      "workspace_versions",
    ]);

    // -------------------------------------------------------- phase B
    stage("phaseB", { action: "enter" });
    const phaseBStart = Date.now();
    const reviewPhase = await runPhase(
      browsers,
      "review",
      reviewBase,
      media,
      siteKey,
      credential,
      reviewDoc.snapshot.digest,
      (detail) => stage("phaseB", detail),
    );
    const phaseBDurationMs = Date.now() - phaseBStart;

    // frozen private bytes (snapshot-scoped namespace) are byte-identical
    const frozenPng = await api.get(
      `/media/v1/review/${snapshotId}/assets/${pngMediaId}/content`,
    );
    expect(frozenPng.status()).toBe(200);
    expect(frozenPng.headers()["content-type"]).toBe("image/png");
    expect(frozenPng.headers()["cache-control"]).toBe("private, no-store");
    expect(frozenPng.headers()["x-robots-tag"]).toBe("noindex, nofollow, noarchive");
    expect(Buffer.from(await frozenPng.body()).equals(TINY_PNG)).toBe(true);
    const frozenPdf = await api.get(
      `/media/v1/review/${snapshotId}/assets/${pdfMediaId}/content`,
    );
    expect(frozenPdf.status()).toBe(200);
    expect(frozenPdf.headers()["content-type"]).toBe("application/pdf");
    expect(Buffer.from(await frozenPdf.body()).equals(pdfBytes)).toBe(true);

    // frozen redirect (review-rooted, site-local re-root form)
    const reviewRedirect = await api.get(`${reviewBase}/old-${newsSlug}`, {
      maxRedirects: 0,
    });
    expect(reviewRedirect.status()).toBe(301);
    expect(reviewRedirect.headers()["location"]).toBe(`/review/${workspaceId}/news`);
    // Actual following on the frozen surface: the site-local re-rooted
    // Location must reach the same delivered frozen list content.
    const followedReview = await api.get(`${reviewBase}/old-${newsSlug}`);
    expect(followedReview.status(), "review redirect follow").toBe(200);
    expect(followedReview.url()).toBe(`${ORIGIN}/review/${workspaceId}/news`);
    expect(await followedReview.text()).toContain(
      '<h1 id="page-title">Parity news</h1>',
    );
    // anonymous frozen review: page login redirect, bytes 401 (no oracle)
    // Same two-step route semantics on the frozen surface: 308
    // trailing-slash normalization, then 307 anonymous auth redirect
    // with the exact relative same-origin /login destination on the
    // canonical slashless path.
    const anonReviewSlash = await anonymous.request.get(`${reviewBase}/`, {
      maxRedirects: 0,
    });
    expect(anonReviewSlash.status()).toBe(308);
    expect(anonReviewSlash.headers()["location"]).toBe(`${reviewBase}`);
    const anonReview = await anonymous.request.get(`${reviewBase}`, {
      maxRedirects: 0,
    });
    expect(anonReview.status()).toBe(307);
    expect(anonReview.headers()["location"]).toBe("/login");
    expect((await anonymous.request.get("/login")).status()).toBe(200);
    const anonBytes = await anonymous.request.get(
      `/media/v1/review/${snapshotId}/assets/${pngMediaId}/content`,
    );
    expect(anonBytes.status()).toBe(401);
    await assertRefusals(api, reviewBase, siteKey, "review");
    await anonymous.close();

    // --------------------- RC3 unrelated post-freeze publication + terminal
    // A second authorized workspace of the SAME site publishes UNRELATED
    // content through the real qualified path (public agent mutations ->
    // real freeze -> real human accept).  Only the separately named
    // current-revision/drift metadata of W1 may move: the stored payload
    // bytes/digest/domain values, the frozen route/query projections and
    // the rendered output stay exact, before AND after W1's real terminal
    // discard with pending cleanup (retained reads repeat).
    // R2 retained-row proof: the EXACT stored snapshot row bytes (all
    // columns, including the browser_evidence/media_references/
    // normalized_state sibling columns) are the retention unit -
    // payload|digest alone would not bind the stored siblings.
    const w1StoredRow = (): string =>
      psql(
        project,
        `SELECT id::text || '|' || workspace_id::text || '|' ||
               site_id::text || '|' || status || '|' ||
               revision_watermark::text || '|' || versions::text || '|' ||
               normalized_state::text || '|' || validation_report::text || '|' ||
               media_references::text || '|' || browser_evidence::text || '|' ||
               payload::text || '|' || digest || '|' || created_by || '|' ||
               created_at::text
         FROM control.review_snapshot WHERE id = '${snapshotId}'`,
      );
    const w1StoredBefore = w1StoredRow();
    expect(w1StoredBefore.length, "W1 stored capture").toBeGreaterThan(64);
    const revisionBefore = Number(
      psql(
        project,
        `SELECT canonical_revision FROM control.site WHERE id = '${siteId}'`,
      ),
    );
    stage("w2", { action: "create" });
    const w2Created = await api.post(`/api/control/v1/sites/${siteId}/workspaces/`, {
      headers: { "X-CSRF-Token": csrf!, "Idempotency-Key": `fpar-${tag}-w2` },
      data: {
        title: `083/5-b parity unrelated ${tag}`,
        task_description: "RC3 unrelated post-freeze publication",
        delegation_preset: "L4_SITE_ARCHITECT",
        duration_hours: 2,
        request_quota: 100,
        mutation_quota: 10,
        delete_quota: 0,
        upload_quota: 0,
        browser_quota: 0,
        resource_constraints: { delete_enabled: false, max_deletes: 0 },
      },
    });
    expect(w2Created.status(), "W2 workspace create").toBe(201);
    const w2Id = ((await w2Created.json()) as { workspace_id: string }).workspace_id;
    const w2Cap = await api.post(
      `/api/control/v1/sites/${siteId}/workspaces/${w2Id}/capabilities/`,
      { headers: { "X-CSRF-Token": csrf!, "Idempotency-Key": `fpar-${tag}-w2cap` } },
    );
    expect(w2Cap.status(), "W2 capability").toBe(201);
    const w2Token = ((await w2Cap.json()) as { token: string }).token;
    // ADJ-4 (documented 083/1 known foundation limitation): the
    // composite page_base (site_id, locale) FK breaks the foundation
    // get_cow_dependencies closure walk, so an ACCEPT session must be
    // page-DML-free. W2 therefore publishes an unrelated THEME fact:
    // theme_changes carries only the single-column site FK to
    // control.site, which the closure walk handles.
    const w2ThemeGet = await api.get("/api/agent/v1/theme", {
      headers: { Authorization: `Bearer ${w2Token}` },
    });
    expect(w2ThemeGet.status(), "W2 theme read").toBe(200);
    const w2ThemeRecord = (await w2ThemeGet.json()) as {
      palette: { preset: string };
      row_version: number;
    };
    expect(w2ThemeRecord.palette.preset, "default theme preset").toBe("ocean");
    expect(w2ThemeRecord.row_version, "theme row version").toBeGreaterThan(0);
    stage("w2", { action: "theme" });
    const w2ThemePatch = await api.patch("/api/agent/v1/theme", {
      headers: {
        Authorization: `Bearer ${w2Token}`,
        "Idempotency-Key": `fpar-${tag}-w2theme`,
      },
      data: {
        palette: { preset: "ember" },
        expected_row_version: w2ThemeRecord.row_version,
      },
    });
    expect(w2ThemePatch.status(), "W2 unrelated theme update").toBe(200);
    const w2ThemeResult = (await w2ThemePatch.json()) as {
      record: { palette: { preset: string } };
      action: string;
    };
    expect(w2ThemeResult.record.palette.preset, "theme change landed").toBe("ember");
    expect(w2ThemeResult.action, "theme action").toBe("THEME_UPDATED");
    stage("w2", { action: "freeze" });
    const w2Freeze = await api.post(
      `/api/control/v1/sites/${siteId}/workspaces/${w2Id}/freeze/`,
      { headers: { "X-CSRF-Token": csrf! } },
    );
    expect(w2Freeze.status(), "W2 freeze").toBe(202);
    stage("w2", { action: "freeze-wait" });
    let w2Status = "";
    const w2FreezeDeadline = Date.now() + 240_000;
    for (;;) {
      const w2Doc = await api.get(`/api/control/v1/sites/${siteId}/workspaces/${w2Id}`);
      expect(w2Doc.status(), "W2 workspace read").toBe(200);
      w2Status = ((await w2Doc.json()) as { status: string }).status;
      if (w2Status === "REVIEW") break;
      expect(["ACTIVE", "FREEZING"]).toContain(w2Status);
      if (Date.now() > w2FreezeDeadline)
        throw new Error(`W2 freeze timeout at ${w2Status}`);
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    const w2Split = psql(
      project,
      `SELECT id || '|' || digest FROM control.review_snapshot WHERE workspace_id = '${w2Id}'`,
    ).split("|");
    const w2SnapshotId = w2Split[0]!;
    const w2Digest = w2Split[1]!;
    expect(w2SnapshotId, "W2 snapshot id").toMatch(/^[0-9a-f-]{36}$/i);
    // Re-authenticate immediately before the two recent-auth-gated
    // transitions (the existing 900s window, same authority).
    stage("w2", { action: "reauth" });
    await login(setupPage, credential);
    const refreshedCsrf = (await setupContext.cookies()).find(
      (c) => c.name === "slaif_csrf",
    )?.value;
    expect(refreshedCsrf, "refreshed csrf cookie").toBeTruthy();
    stage("w2", { action: "accept" });
    const w2Accept = await api.post(
      `/api/control/v1/sites/${siteId}/workspaces/${w2Id}/accept/`,
      {
        headers: { "X-CSRF-Token": refreshedCsrf! },
        data: {
          snapshot_id: w2SnapshotId,
          digest: w2Digest,
          acknowledge_summary: true,
        },
      },
    );
    expect(w2Accept.status(), "W2 accept").toBe(202);
    stage("w2", { action: "accept-wait" });
    let w2Terminal = "";
    const w2AcceptDeadline = Date.now() + 240_000;
    for (;;) {
      const w2Doc = await api.get(`/api/control/v1/sites/${siteId}/workspaces/${w2Id}`);
      expect(w2Doc.status(), "W2 workspace read").toBe(200);
      w2Terminal = ((await w2Doc.json()) as { status: string }).status;
      if (w2Terminal === "ACCEPTED") break;
      // Product state machine (accept_job): REVIEW -> ACCEPT_QUEUED
      // -> PROMOTING -> ACCEPTED; all three pre-terminal states are
      // legitimate while the job drains.
      expect(["REVIEW", "ACCEPT_QUEUED", "PROMOTING"]).toContain(w2Terminal);
      if (Date.now() > w2AcceptDeadline)
        throw new Error(`W2 accept timeout at ${w2Terminal}`);
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    const revisionAfter = Number(
      psql(
        project,
        `SELECT canonical_revision FROM control.site WHERE id = '${siteId}'`,
      ),
    );
    expect(revisionAfter, "publication advanced the site revision").toBe(
      revisionBefore + 1,
    );
    // W1 stored state is exact (the whole stored row, siblings
    // included); only the named drift metadata moved.
    expect(w1StoredRow(), "frozen stored row bytes exact after W2").toBe(
      w1StoredBefore,
    );
    expect(
      psql(
        project,
        // PG 18.6 resolver: a bare jsonb ->> || jsonb ->> chain fails
        // operator resolution (text ->> unknown); the ::text casts are
        // runtime no-ops that satisfy the resolver.
        `SELECT (payload->>'site_id')::text || '|' ||
               (payload->>'workspace_id')::text
          FROM control.review_snapshot WHERE id = '${snapshotId}'`,
      ),
      "frozen domain values exact",
    ).toBe(`${siteId}|${workspaceId}`);
    const w1DriftDoc = await api.get(
      `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/review/`,
    );
    expect(w1DriftDoc.status(), "W1 retained review read").toBe(200);
    const w1Drift = (
      (await w1DriftDoc.json()) as {
        drift: {
          equal: boolean;
          current_site_revision: number;
          base_site_revision: number;
        };
      }
    ).drift;
    expect(w1Drift.equal, "drift metadata moved").toBe(false);
    expect(w1Drift.current_site_revision).toBe(revisionAfter);
    expect(w1Drift.base_site_revision).toBe(revisionBefore);
    // Frozen route/query/domain projections and rendered output stay
    // byte-identical: the query form, the alternate site-binding URL
    // form, and the static/dynamic routes re-render the exact phase-B
    // fingerprints.
    const rc3Context = await browsers.chromium.newContext({ baseURL: ORIGIN });
    await installDocumentSentinel(rc3Context);
    const rc3Page = await rc3Context.newPage();
    await login(rc3Page, credential);
    const phaseBKey = (route: RouteName): string => {
      const key = reviewPhase.keys.get(`chromium/Desktop Chrome :: ${route}`);
      if (key === undefined) throw new Error(`missing phase B key ${route}`);
      return key;
    };
    const recheck = async (url: string, route: RouteName): Promise<void> => {
      const response = await rc3Page.goto(url);
      expect(response?.status(), `RC3 ${route}`).toBe(200);
      expectPrivateHeaders(response!);
      expect(contentKey(await collectFacts(rc3Page, reviewBase)), `RC3 ${route}`).toBe(
        phaseBKey(route),
      );
    };
    await recheck(`${reviewBase}/news/alpha?rc3=${tag}`, "/news/alpha");
    await recheck(`/review/${workspaceId}/news/alpha`, "/news/alpha");
    await recheck(`${reviewBase}/`, "/");
    await recheck(`${reviewBase}/news`, "/news");
    await recheck(`${reviewBase}/sl-SI/news/alpha`, "/sl-SI/news/alpha");
    // Banner: the exact same digest, the named drift flag flipped.
    await expect(rc3Page.locator(".review-banner")).toHaveAttribute(
      "data-review-digest",
      reviewDoc.snapshot.digest,
    );
    await expect(rc3Page.locator(".review-banner")).toHaveAttribute(
      "data-review-equal",
      "false",
    );
    // RC3 retained supported controls AFTER the unrelated W2
    // publication: the deployed W1 review surface still carries the
    // real same-path collection controls (search + facet state
    // retention across submissions) and the concrete two-direction
    // locale link navigation.  The ignored ?rc3= marker re-checked
    // above is only an invariance marker; these real interactions are
    // the retained supported-control proof for the post-W2 surface.
    await formSequence(rc3Page, `${reviewBase}/news`);
    await navigationProof(rc3Page, reviewBase);

    // G7 before-control (same inspection mechanism, exact W1 id):
    // the existing public foundation operation-inspection API sees
    // W1's pending COW operations NONEMPTY before its real terminal
    // discard, so the after-empty proof cannot be vacuous (an
    // always-empty or wrong-workspace helper would fail here).
    stage("terminal", { action: "pending-check" });
    const pendingBefore = pendingOperations(project, workspaceId);
    for (const operation of pendingBefore)
      expect(operation, "W1 pending operation id").toMatch(/^[0-9a-f-]{36}$/i);
    expect(
      pendingBefore.length,
      "W1 pending operations nonempty before discard",
    ).toBeGreaterThan(0);
    // Real terminal discard of W1 + repeated retained checks.
    stage("terminal", { action: "discard" });
    const w1Discard = await api.post(
      `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/discard/`,
      {
        headers: { "X-CSRF-Token": refreshedCsrf! },
        data: { acknowledge_discard: true },
      },
    );
    expect(w1Discard.status(), "W1 discard").toBe(202);
    stage("terminal", { action: "cleanup-wait" });
    let w1Terminal = "";
    const w1DiscardDeadline = Date.now() + 240_000;
    for (;;) {
      const w1Doc = await api.get(
        `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}`,
      );
      expect(w1Doc.status(), "W1 workspace read").toBe(200);
      w1Terminal = ((await w1Doc.json()) as { status: string }).status;
      if (w1Terminal === "DISCARDED") break;
      // Product state machine (discard_job): REVIEW -> DISCARD_QUEUED
      // -> DISCARDING -> DISCARDED; both queued states are legitimate
      // while the terminal cleanup runs.
      expect(["REVIEW", "DISCARD_QUEUED", "DISCARDING"]).toContain(w1Terminal);
      if (Date.now() > w1DiscardDeadline)
        throw new Error(`W1 discard timeout at ${w1Terminal}`);
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    expect(
      psql(
        project,
        `SELECT count(*) FROM control.workspace
          WHERE id = '${workspaceId}' AND status = 'DISCARDED'
            AND discarded_at IS NOT NULL`,
      ),
      "terminal discard state",
    ).toBe("1");
    // G7 after-proof (SAME inspection mechanism and exact W1 id):
    // the pending COW operations are EMPTY after the real terminal
    // discard + pending cleanup.  The product's discard_job runs the
    // foundation session discard in-transaction BEFORE the DISCARDED
    // status/drift facts, so this actual operation-set read - not the
    // terminal status, timestamps, watermark or stored history - is
    // the emptiness proof.
    const pendingAfter = pendingOperations(project, workspaceId);
    expect(pendingAfter, "W1 pending operations after discard").toEqual([]);
    // Retained: stored bytes unchanged and the frozen read/output
    // repeat exactly after the terminal discard + pending cleanup.
    expect(w1StoredRow(), "retained stored row bytes exact").toBe(w1StoredBefore);
    await recheck(`${reviewBase}/news/alpha`, "/news/alpha");
    await recheck(`${reviewBase}/`, "/");
    await expect(rc3Page.locator(".review-banner")).toHaveAttribute(
      "data-review-digest",
      reviewDoc.snapshot.digest,
    );
    // Terminal retained supported controls (after the REAL W1
    // terminal discard + pending cleanup, on the SAME W1 review
    // surface, before its context closes): the missing selected-
    // locale list/detail routes re-render exactly, and the real
    // same-path collection controls plus the concrete two-direction
    // locale link navigation still operate on the retained frozen
    // surface.  The canonical-matrix proof below is a SEPARATE
    // criterion on the published surface and does not substitute
    // for these retained frozen-surface interactions.
    await recheck(`${reviewBase}/news`, "/news");
    await recheck(`${reviewBase}/sl-SI/news`, "/sl-SI/news");
    await recheck(`${reviewBase}/sl-SI/news/alpha`, "/sl-SI/news/alpha");
    await formSequence(rc3Page, `${reviewBase}/news`);
    await navigationProof(rc3Page, reviewBase);
    // G6 post-terminal byte assertions (label: NOT G7): after the
    // actual W1 terminal discard, BOTH retained frozen media byte
    // URLs (IMAGE + DOCUMENT) are re-fetched through the existing
    // public-edge authenticated client/session and must return the
    // exact original uploaded bytes with the private frozen-
    // namespace headers.  Terminal status alone does not prove an
    // empty pending operation set.
    stage("terminal", { action: "post-bytes" });
    const postTerminalPng = await api.get(
      `/media/v1/review/${snapshotId}/assets/${pngMediaId}/content`,
    );
    expect(postTerminalPng.status(), "W1 post-terminal png status").toBe(200);
    expect(postTerminalPng.headers()["content-type"]).toBe("image/png");
    expect(postTerminalPng.headers()["cache-control"]).toBe("private, no-store");
    expect(postTerminalPng.headers()["x-robots-tag"]).toBe(
      "noindex, nofollow, noarchive",
    );
    expect(
      Buffer.from(await postTerminalPng.body()).equals(TINY_PNG),
      "W1 post-terminal png bytes exact",
    ).toBe(true);
    const postTerminalPdf = await api.get(
      `/media/v1/review/${snapshotId}/assets/${pdfMediaId}/content`,
    );
    expect(postTerminalPdf.status(), "W1 post-terminal pdf status").toBe(200);
    expect(postTerminalPdf.headers()["content-type"]).toBe("application/pdf");
    expect(postTerminalPdf.headers()["cache-control"]).toBe("private, no-store");
    expect(postTerminalPdf.headers()["x-robots-tag"]).toBe(
      "noindex, nofollow, noarchive",
    );
    expect(
      Buffer.from(await postTerminalPdf.body()).equals(pdfBytes),
      "W1 post-terminal pdf bytes exact",
    ).toBe(true);
    await rc3Context.close();

    // ------------------------------------- cross-surface parity + matrix
    // Every engine/target+route fingerprint must be identical between
    // the pre-freeze active and the immutable review surfaces.
    expect(previewPhase.keys.size).toBe(MATRIX.length * ROUTES.length);
    expect(reviewPhase.keys.size).toBe(MATRIX.length * ROUTES.length);
    for (const key of previewPhase.keys.keys()) {
      expect(reviewPhase.keys.get(key), `parity ${key}`).toBe(
        previewPhase.keys.get(key),
      );
    }
    expect(previewPhase.combos).toHaveLength(MATRIX.length);
    expect(reviewPhase.combos).toHaveLength(MATRIX.length);
    const pairs = new Set(previewPhase.combos.map((c) => `${c.engine}/${c.target}`));
    expect(pairs.size).toBe(MATRIX.length);
    for (const combo of previewPhase.combos) {
      expect(combo.version, `${combo.engine}/${combo.target} version`).toBeTruthy();
    }
    test.info().annotations.push(
      {
        type: "frozen-parity-matrix",
        description: previewPhase.combos
          .map((c) => `${c.engine}@${c.version}:${c.target}`)
          .join(","),
      },
      {
        type: "frozen-parity-timings",
        description: `phaseA=${phaseADurationMs}ms phaseB=${phaseBDurationMs}ms`,
      },
    );
    // ------------------------------------- RC2 published-canonical
    // Honest INITIAL canonical test-data setup (trusted psql fixture
    // authority, the same seed pattern as seedParitySite above): the
    // PUBLISHED /s/<siteKey> surface had no dynamic-locale detail
    // content, so the missing canonical locale-navigation criterion
    // installs a bounded run-unique mirror of the parity fixture
    // directly into the canonical base tables.  This is test-data
    // setup, NOT online publication evidence: no workspace, freeze,
    // accept or revision change, and no W1 private asset is
    // referenced (W1 is terminal-discarded; its private media never
    // enters this fixture).
    const canonicalBase = `/s/${siteKey}`;
    stage("canonical", { action: "seed" });
    seedCanonicalFixture(project, siteId, tag);
    const canonicalSetup = await api.get(canonicalBase);
    expect(canonicalSetup.status(), "canonical setup render").toBe(200);
    expect(await canonicalSetup.text()).toContain("Home marker EN");
    // ALL SIX actual engine/device pairings on the actually published
    // surface, plus the retained supported controls and the
    // forward/reverse locale link clicks repeated per pairing AFTER
    // the real W1 terminal discard + pending cleanup.
    stage("canonical", { action: "enter" });
    const canonicalProof = await canonicalPhase(
      browsers,
      canonicalBase,
      siteKey,
      (detail) => stage("canonical", detail),
    );
    expect(canonicalProof.keys.size).toBe(MATRIX.length * ROUTES.length);
    expect(canonicalProof.combos).toHaveLength(MATRIX.length);
    const canonicalPairs = new Set(
      canonicalProof.combos.map((c) => `${c.engine}/${c.target}`),
    );
    expect(canonicalPairs.size).toBe(MATRIX.length);
    for (const combo of canonicalProof.combos) {
      expect(
        combo.version,
        `canonical ${combo.engine}/${combo.target} version`,
      ).toBeTruthy();
    }
    test.info().annotations.push(
      {
        type: "canonical-matrix",
        description: canonicalProof.combos
          .map((c) => `${c.engine}@${c.version}:${c.target}`)
          .join(","),
      },
      {
        type: "canonical-fixture",
        description:
          "honest initial canonical test-data seed (trusted psql setup; not online publication evidence)",
      },
    );
    bodyCompleted = true;
  } finally {
    if (bodyCompleted) stage("cleanup", { action: "close" });
    for (const browser of Object.values(browsers)) await browser.close();
  }
});
