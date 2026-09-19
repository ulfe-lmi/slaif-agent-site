import { expect, test } from "@playwright/test";
import { expectPrivateHeaders, login, observe, secrets } from "./support";
import {
  DATE_PRIMITIVES,
  IN_LIST_ENTRY_MAX_LENGTH,
  IN_LIST_MAX_ENTRIES,
  NUMERIC_PRIMITIVES,
  SEARCH_TEXT_PRIMITIVES,
  TEXT_PRIMITIVES,
  dateValue,
  itemTitle,
  itemValues,
  matchesAllFacets,
  matchesFacet,
  matchesSearch,
  numericValue,
  splitInList,
  stringValue,
} from "../../apps/web/src/renderer/bounded-collection-filter";

/**
 * Browser-side contracts for the bounded in-memory collection filtering
 * components (OAP 078-7-a).
 *
 * Proof model (documented in the order's report):
 * - The workspace preview route is a flight-free server-rendered document
 *   (established contract: no `__next_f`/`NEXT_DATA`, no client bundle).
 *   The bounded client-state components therefore render their static
 *   initial-state variants there: the same bounded markup, the same pure
 *   fixed-operator logic, no client state. This spec asserts that SSR
 *   contract exactly (markup, bounded limits, initial visible sets,
 *   RelatedItems detail-route-only semantics, no token/ID leakage).
 * - The 256/4096 input-processing caps are asserted on the real product
 *   input elements through the browser's native `maxlength` semantics.
 * - The filtering semantics themselves are exercised IN THE BROWSER with
 *   the real renderer logic: the compiled functions of
 *   `bounded-collection-filter.ts` are serialized from the Node side and
 *   injected into the page; a small harness wires the real input elements
 *   to recompute the visible list over the real projected items using the
 *   same two-step wiring the React components document (cap input, then
 *   filter the pre-fetched bounded array). No network I/O, no
 *   persistence, no URL mutation.
 */

type AgentDocument = {
  record?: Record<string, unknown>;
};

type Item = { id: string; slug: string; values: Record<string, unknown> };

const FIXTURE_ITEMS: Array<{
  slug: string;
  title: string;
  summary: string;
  rank: number;
  kind: string;
}> = [
  {
    slug: "alpha",
    title: "Alpha briefing",
    summary: "Alpha summary",
    rank: 4,
    kind: "News",
  },
  {
    slug: "beta",
    title: "Beta dispatch",
    summary: "Beta summary",
    rank: 3,
    kind: "Press",
  },
  {
    slug: "gamma",
    title: "Gamma notes",
    summary: "Gamma summary",
    rank: 2,
    kind: "Blog",
  },
  {
    slug: "delta",
    title: "Delta letter",
    summary: "Delta summary",
    rank: 1,
    kind: "News",
  },
];

const FIXTURE_FACETS: Array<{ fieldKey: string; operator: string; value: string }> = [
  { fieldKey: "title", operator: "contains", value: "a" },
  { fieldKey: "rank", operator: "gte", value: "1" },
  { fieldKey: "kind", operator: "in", value: "News, Press, Blog" },
];

const FIXTURE_FIELDS: Array<{ key: string; primitive: string }> = [
  { key: "title", primitive: "short_text" },
  { key: "summary", primitive: "long_text" },
  { key: "rank", primitive: "integer" },
  { key: "kind", primitive: "enum" },
];

/**
 * Serialize the real renderer logic module into a browser-side IIFE. The
 * functions are the transpiled Node-side exports of
 * `bounded-collection-filter.ts`; their bodies reference only the other
 * serialized helpers and the injected constants, so the IIFE is
 * self-contained.
 */
function serializedLogicModule(): string {
  const setSource = (name: string, value: Set<string>): string =>
    `const ${name} = new Set(${JSON.stringify([...value])});`;
  return [
    "(function () {",
    "if (window.__slaifFilter) return;",
    setSource("TEXT_PRIMITIVES", TEXT_PRIMITIVES),
    setSource("SEARCH_TEXT_PRIMITIVES", SEARCH_TEXT_PRIMITIVES),
    setSource("NUMERIC_PRIMITIVES", NUMERIC_PRIMITIVES),
    setSource("DATE_PRIMITIVES", DATE_PRIMITIVES),
    `const IN_LIST_MAX_ENTRIES = ${IN_LIST_MAX_ENTRIES};`,
    `const IN_LIST_ENTRY_MAX_LENGTH = ${IN_LIST_ENTRY_MAX_LENGTH};`,
    stringValue.toString(),
    numericValue.toString(),
    dateValue.toString(),
    itemValues.toString(),
    itemTitle.toString(),
    splitInList.toString(),
    matchesSearch.toString(),
    matchesFacet.toString(),
    matchesAllFacets.toString(),
    "window.__slaifFilter = { itemValues: itemValues, itemTitle: itemTitle, matchesSearch: matchesSearch, matchesFacet: matchesFacet, matchesAllFacets: matchesAllFacets };",
    "})();",
  ].join("\n");
}

/**
 * Harness that mirrors the documented component wiring (cap input, then
 * filter the pre-fetched bounded array with the real logic) over the SSR
 * markup. It performs no I/O and mutates only the rendered list/empty
 * state of the two bounded components.
 */
function wiringHarness(): string {
  return `(function () {
  if (window.__slaifWired) return;
  var L = window.__slaifFilter;
  var D = window.__slaifData;
  function resultsList(root, indexes, emptyClass) {
    var ul = root.querySelector("ul.renderer-collection-list");
    if (!ul) return;
    ul.innerHTML = "";
    indexes.forEach(function (i) {
      var item = D.items[i];
      var values = L.itemValues(item);
      var li = document.createElement("li");
      var article = document.createElement("article");
      var h2 = document.createElement("h2");
      h2.textContent = L.itemTitle(item);
      var p = document.createElement("p");
      var summary = typeof values.summary === "string" && values.summary !== ""
        ? values.summary
        : typeof values.description === "string"
          ? values.description
          : "";
      p.textContent = summary;
      article.appendChild(h2);
      article.appendChild(p);
      li.appendChild(article);
      ul.appendChild(li);
    });
    var empty = root.querySelector("." + emptyClass);
    if (indexes.length === 0) {
      if (!empty) {
        empty = document.createElement("p");
        empty.className = emptyClass;
        root.appendChild(empty);
      }
      empty.textContent = "No results";
      empty.hidden = false;
      ul.hidden = true;
    } else if (empty) {
      empty.hidden = true;
      ul.hidden = false;
    } else {
      ul.hidden = false;
    }
  }
  var searchRoot = document.querySelector('[data-component="CollectionSearch"]');
  if (searchRoot) {
    var searchInput = searchRoot.querySelector("input.renderer-collection-search-input");
    searchInput.addEventListener("input", function () {
      var query = searchInput.value.slice(0, 256);
      var indexes = [];
      D.items.forEach(function (item, i) {
        if (L.matchesSearch(item, D.fields, query)) indexes.push(i);
      });
      resultsList(searchRoot, indexes, "renderer-collection-search-empty");
      window.__slaifSearchRuns = (window.__slaifSearchRuns || 0) + 1;
    });
  }
  var filterRoot = document.querySelector('[data-component="CollectionFilter"]');
  if (filterRoot) {
    var inputs = Array.prototype.slice.call(
      filterRoot.querySelectorAll("input.renderer-collection-filter-input")
    );
    var active = D.facets.map(function (facet) {
      return { fieldKey: facet.fieldKey, operator: facet.operator, value: facet.value };
    });
    inputs.forEach(function (input, i) {
      input.addEventListener("input", function () {
        active[i].value = input.value.slice(0, 4096);
        var indexes = [];
        D.items.forEach(function (item, j) {
          if (L.matchesAllFacets(item, D.fields, active)) indexes.push(j);
        });
        resultsList(filterRoot, indexes, "renderer-collection-filter-empty");
        window.__slaifFilterRuns = (window.__slaifFilterRuns || 0) + 1;
      });
    });
  }
  window.__slaifWired = true;
})();`;
}

async function agentCreate(
  page: import("@playwright/test").Page,
  token: string,
  path: string,
  key: string,
  body: unknown,
) {
  const response = await page.request.post(path, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Idempotency-Key": key,
    },
    data: JSON.parse(JSON.stringify(body)) as unknown,
  });
  expect(response.status()).toBe(201);
  return (await response.json()) as AgentDocument;
}

test("bounded-client-filtering-contracts", async ({ page }) => {
  const credential = secrets();
  const failures = observe(page);
  const tag = crypto.randomUUID();

  await login(page, credential);
  const sites = (await (
    await page.request.get("/api/control/v1/me/sites")
  ).json()) as Array<{ site_id: string; site_key: string }>;
  const demo = sites.find((site) => site.site_key === "demo");
  expect(demo).toBeDefined();
  const csrf =
    (await page.context().cookies()).find((cookie) => cookie.name === "slaif_csrf")
      ?.value ?? "";
  expect(csrf).toBeTruthy();

  const workspacePath = `/api/control/v1/sites/${demo!.site_id}/workspaces/`;
  const workspaceResponse = await page.request.post(workspacePath, {
    headers: {
      "X-CSRF-Token": csrf,
      "Idempotency-Key": `oap-0787a-filter-workspace-${tag}`,
    },
    data: {
      title: `OAP 078-7-a filtering ${tag}`,
      task_description: "Bounded client filtering proof",
      delegation_preset: "L4_SITE_ARCHITECT",
      duration_hours: 1,
      request_quota: 1000,
      mutation_quota: 200,
      delete_quota: 0,
      upload_quota: 0,
      browser_quota: 0,
      resource_constraints: { delete_enabled: false, max_deletes: 0 },
    },
  });
  expect(workspaceResponse.status()).toBe(201);
  const workspace = (
    (await workspaceResponse.json()) as {
      workspace_id?: unknown;
    }
  ).workspace_id as string;
  const capabilityResponse = await page.request.post(
    `${workspacePath}${workspace}/capabilities/`,
    {
      headers: {
        "X-CSRF-Token": csrf,
        "Idempotency-Key": `oap-0787a-filter-capability-${tag}`,
      },
    },
  );
  expect(capabilityResponse.status()).toBe(201);
  const capability = (await capabilityResponse.json()) as {
    capability_id?: unknown;
    token?: unknown;
  };
  const agentToken = capability.token as string;

  const newsSlug = `filter-${tag.slice(0, 8)}`;
  const typeDocument = await agentCreate(
    page,
    agentToken,
    "/api/agent/v1/content-model/types",
    `oap-0787a-filter-type-${tag}`,
    {
      key: `oap_filter_${tag.slice(0, 8)}`,
      labels: { en: "Filter proof" },
      slug_pattern: `/${newsSlug}/{slug}`,
      settings: {},
    },
  );
  const typeId = typeDocument.record?.id as string;
  const fields: Array<{
    key: string;
    label: string;
    field_type: string;
    localized: boolean;
    validation?: { choices: string[] };
  }> = [
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
  for (let index = 0; index < fields.length; index += 1) {
    const field = fields[index]!;
    await agentCreate(
      page,
      agentToken,
      `/api/agent/v1/content-model/types/${typeId}/fields`,
      `oap-0787a-filter-field-${field.key}-${tag}`,
      {
        key: field.key,
        label: field.label,
        field_type: field.field_type,
        localized: field.localized,
        required: true,
        position: index,
        ...(field.validation ? { validation: field.validation } : {}),
      },
    );
  }
  for (const item of FIXTURE_ITEMS) {
    const created = await agentCreate(
      page,
      agentToken,
      `/api/agent/v1/content-items/types/${typeId}`,
      `oap-0787a-filter-item-${item.slug}-${tag}`,
      {
        type_id: typeId,
        slug: item.slug,
        status: "PUBLISHED",
        values: { rank: item.rank, kind: item.kind },
      },
    );
    const itemId = created.record?.id as string;
    await agentCreate(
      page,
      agentToken,
      `/api/agent/v1/content-items/${itemId}/translations`,
      `oap-0787a-filter-translation-${item.slug}-${tag}`,
      {
        locale: "en",
        localized_values: { title: item.title, summary: item.summary },
      },
    );
  }
  const viewDocument = await agentCreate(
    page,
    agentToken,
    `/api/agent/v1/collection-views/types/${typeId}`,
    `oap-0787a-filter-view-${tag}`,
    {
      type_id: typeId,
      key: `oap-filter-${tag.slice(0, 8)}`,
      filter_spec: {},
      sort_spec: { field: "rank", direction: "desc" },
      projection_spec: { fields: ["title", "summary", "rank", "kind"] },
      pagination_spec: { limit: 10, offset: 0 },
    },
  );
  const viewId = viewDocument.record?.id as string;
  const listingDocument = await agentCreate(
    page,
    agentToken,
    "/api/agent/v1/pages/",
    `oap-0787a-filter-listing-${tag}`,
    {
      slug: newsSlug,
      title: "Filter proof",
      status: "PUBLISHED",
      locale: "en",
    },
  );
  const listingId = listingDocument.record?.id as string;
  const detailDocument = await agentCreate(
    page,
    agentToken,
    "/api/agent/v1/pages/",
    `oap-0787a-filter-detail-${tag}`,
    {
      slug: "item",
      title: "Filter detail",
      status: "PUBLISHED",
      locale: "en",
      parent_id: listingId,
      route_template: "{slug}",
    },
  );
  const detailId = detailDocument.record?.id as string;
  await agentCreate(
    page,
    agentToken,
    `/api/agent/v1/pages/${listingId}/components`,
    `oap-0787a-filter-search-${tag}`,
    {
      component_type: "CollectionSearch",
      slot_key: "default",
      props: {
        viewId,
        placeholder: "Search stories",
        limit: 10,
      },
    },
  );
  await agentCreate(
    page,
    agentToken,
    `/api/agent/v1/pages/${listingId}/components`,
    `oap-0787a-filter-filter-${tag}`,
    {
      component_type: "CollectionFilter",
      slot_key: "default",
      props: {
        viewId,
        facets: FIXTURE_FACETS,
      },
    },
  );
  await agentCreate(
    page,
    agentToken,
    `/api/agent/v1/pages/${detailId}/components`,
    `oap-0787a-filter-detail-node-${tag}`,
    {
      component_type: "CollectionDetail",
      slot_key: "default",
      props: { viewId },
    },
  );
  await agentCreate(
    page,
    agentToken,
    `/api/agent/v1/pages/${detailId}/components`,
    `oap-0787a-filter-related-${tag}`,
    {
      component_type: "RelatedItems",
      slot_key: "default",
      props: { viewId, heading: "Related", limit: 8 },
    },
  );

  const preview = `/preview/${workspace}/s/demo/${newsSlug}`;
  const listingResponse = await page.goto(preview);
  expectPrivateHeaders(listingResponse!);
  expect(listingResponse?.status()).toBe(200);

  // --- SSR contract on the flight-free preview surface -------------------
  const search = page.locator('[data-component="CollectionSearch"]');
  const searchInput = search.locator("input.renderer-collection-search-input");
  expect(await searchInput.getAttribute("maxlength")).toBe("256");
  expect(await search.getByText("Search stories").count()).toBe(1);
  const searchListings = search.locator("ul.renderer-collection-list li");
  // Initial state: empty query matches the whole pre-fetched bounded set,
  // in view sort order (rank desc).
  expect(await searchListings.count()).toBe(4);
  for (let index = 0; index < FIXTURE_ITEMS.length; index += 1) {
    expect(await searchListings.nth(index).locator("h2").innerText()).toBe(
      FIXTURE_ITEMS[index]!.title,
    );
  }

  const filter = page.locator('[data-component="CollectionFilter"]');
  const facetInputs = filter.locator("input.renderer-collection-filter-input");
  expect(await facetInputs.count()).toBe(3);
  expect(await facetInputs.nth(0).getAttribute("maxlength")).toBe("4096");
  expect(await filter.locator(".renderer-collection-filter-facet").count()).toBe(3);
  const filterListings = filter.locator("ul.renderer-collection-list li");
  // Initial permissive facet values match all four projected items.
  expect(await filterListings.count()).toBe(4);

  // RelatedItems renders nothing on the top-level route.
  expect(await page.locator(".renderer-related").count()).toBe(0);

  // --- Bounded filtering semantics, executed in the browser ---------------
  // The SSR markup above proves the initial visible sets; the harness now
  // wires the real inputs to the real renderer logic over the real
  // projected items (same cap-then-filter wiring the components document).
  const projectedItems: Item[] = FIXTURE_ITEMS.map((item, index) => ({
    id: String(index),
    slug: item.slug,
    values: {
      title: item.title,
      summary: item.summary,
      rank: item.rank,
      kind: item.kind,
    },
  }));
  const harnessData = {
    items: projectedItems,
    fields: FIXTURE_FIELDS,
    facets: FIXTURE_FACETS,
  };
  // The preview page carries a strict script-src CSP; the harness is
  // therefore served as a same-origin script through a spec-local route
  // interception (no product change, CSP stays enforced). The data payload
  // is passed through CDP evaluation, which is CSP-independent.
  const harnessUrl = "/__0787a-filter-harness.js";
  const harnessSource = `${serializedLogicModule()}\n${wiringHarness()}`;
  await page.evaluate((data) => {
    (window as unknown as { __slaifData: unknown }).__slaifData = data;
  }, harnessData);
  await page.route(`**${harnessUrl}`, async (route) => {
    await route.fulfill({ contentType: "text/javascript", body: harnessSource });
  });
  await page.addScriptTag({ url: harnessUrl });
  expect(
    await page.evaluate(() => (window as { __slaifWired?: boolean }).__slaifWired),
  ).toBe(true);

  // CollectionSearch: input -> filtered list (real logic, in-browser).
  await searchInput.fill("gamma");
  await expect(searchListings).toHaveCount(1);
  await expect(searchListings.nth(0).locator("h2")).toHaveText("Gamma notes");
  // Empty-result state.
  await searchInput.fill("zzz-no-match");
  await expect(search.locator("p.renderer-collection-search-empty")).toHaveText(
    "No results",
  );
  expect(await searchListings.count()).toBe(0);
  // Input processing is capped at 256 characters: 300 keystrokes leave
  // exactly 256 characters in the real product input (native maxlength).
  await searchInput.fill("");
  expect(await searchListings.count()).toBe(4);
  await searchInput.type("x".repeat(300));
  expect((await searchInput.inputValue()).length).toBe(256);
  await expect(search.locator("p.renderer-collection-search-empty")).toHaveText(
    "No results",
  );
  // Clearing restores the full bounded set.
  await searchInput.fill("");
  await expect(searchListings).toHaveCount(4);

  // CollectionFilter: integer operator (rank gte 3 keeps rank 4 and 3).
  await facetInputs.nth(1).fill("3");
  await expect(filterListings).toHaveCount(2);
  expect(await filterListings.nth(0).locator("h2").innerText()).toBe("Alpha briefing");
  expect(await filterListings.nth(1).locator("h2").innerText()).toBe("Beta dispatch");
  // Text operator: title contains alpha narrows to the single match.
  await facetInputs.nth(0).fill("alpha");
  await expect(filterListings).toHaveCount(1);
  await expect(filterListings.nth(0).locator("h2")).toHaveText("Alpha briefing");
  // Enum operator: kind in Press keeps only the Press item.
  await facetInputs.nth(0).fill("a");
  await facetInputs.nth(2).fill("Press");
  await expect(filterListings).toHaveCount(1);
  await expect(filterListings.nth(0).locator("h2")).toHaveText("Beta dispatch");
  // Fail-closed: an enum entry outside the item values matches nothing.
  await facetInputs.nth(2).fill("Zzz");
  await expect(filter.locator("p.renderer-collection-filter-empty")).toHaveText(
    "No results",
  );
  expect(await filterListings.count()).toBe(0);
  // Restoring the permissive vocabulary restores the bounded set.
  await facetInputs.nth(2).fill("News, Press, Blog");
  await expect(filterListings).toHaveCount(2);

  // --- RelatedItems: detail-route-only, current item excluded -------------
  const detailResponse = await page.goto(`${preview}/alpha`);
  expectPrivateHeaders(detailResponse!);
  expect(detailResponse?.status()).toBe(200);
  const related = page.locator(".renderer-related");
  expect(await related.count()).toBe(1);
  await expect(related.locator("h2").first()).toHaveText("Related");
  const relatedListings = related.locator("ul.renderer-collection-list li");
  // The current route item is excluded server-side from the related set.
  expect(await relatedListings.count()).toBe(3);
  expect(await relatedListings.nth(0).locator("h2").innerText()).toBe("Beta dispatch");
  expect(await relatedListings.nth(2).locator("h2").innerText()).toBe("Delta letter");
  const detailTitle = page.locator('[data-component="CollectionDetail"] h2');
  await expect(detailTitle).toHaveText("Alpha briefing");
  const relatedText = await related.innerText();
  expect(relatedText).not.toContain("Alpha briefing");

  // Back on the top level the related section is absent again.
  await page.goto(preview);
  expect(await page.locator(".renderer-related").count()).toBe(0);
  expect(failures(), "unexpected filtering browser failures").toEqual([]);
});
