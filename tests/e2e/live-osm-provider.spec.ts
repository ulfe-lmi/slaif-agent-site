/**
 * Live OSM provider observation — OAP 078-9-a, requirement R3.
 *
 * LOCAL-EXECUTION EVIDENCE ONLY. This spec is intentionally NOT
 * referenced by any `testMatch` project in `playwright.config.ts` and
 * is NOT invoked by `tools/compose/e2e.sh` or `smoke.sh`: the
 * deterministic CI contract stays hermetic (provider hosts are
 * route-mocked in `preview.spec.ts`). This spec runs against the real
 * OpenStreetMap embed endpoint with real network access and performs
 * no route mocking of `www.openstreetmap.org`.
 *
 * It requires the live provider (www.openstreetmap.org,
 * tile.openstreetmap.org, api.thunderforest.com) to be reachable. If
 * the provider is unavailable the spec fails — it never skips
 * silently — and the executor records the failure with same-host
 * probe output in the execution report.
 *
 * The spec asserts request host/path shapes only. It never embeds,
 * reads, logs, or references a provider API key: the Thunder Forest
 * key is supplied by the OSM embed bundle itself and stays inside the
 * provider's own requests.
 *
 * Per-layer screenshots and the observed upstream request list
 * (`evidence.json`) are written to the Playwright test-results
 * artifacts directory for the test (`testInfo.outputDir`), whose
 * location is governed by the `outputDir` of the Playwright config
 * (or `SLAIF_E2E_OUTPUT_DIR` in local execution).
 */

import { expect, test } from "@playwright/test";
import { writeFileSync } from "node:fs";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { login, secrets } from "./support";

const BBOX = { west: -12.5, south: 55, east: -12.4, north: 55.1 };
const BBOX_TEXT = "-12.5,55,-12.4,55.1";
const EMBED_BASE = "https://www.openstreetmap.org/export/embed.html";
const FRAME_SOURCES = {
  mapnik: `${EMBED_BASE}?bbox=${BBOX_TEXT}`,
  cyclemap: `${EMBED_BASE}?bbox=${BBOX_TEXT}&layer=cyclemap`,
  transportmap: `${EMBED_BASE}?bbox=${BBOX_TEXT}&layer=transportmap`,
} as const;
type Layer = keyof typeof FRAME_SOURCES;
const LAYERS = Object.keys(FRAME_SOURCES) as Layer[];

type Upstream = {
  method: string;
  host: string;
  path: string;
  status: number | null;
  frame: string | null;
};

const PROVIDER_HOSTS = new Set([
  "www.openstreetmap.org",
  "tile.openstreetmap.org",
  "api.thunderforest.com",
]);

function frameMatches(frameUrl: string | null, layer: Layer): boolean {
  if (!frameUrl || !frameUrl.startsWith(EMBED_BASE)) return false;
  try {
    const value = new URL(frameUrl).searchParams.get("layer") ?? "mapnik";
    return value === layer;
  } catch {
    return false;
  }
}

function layerUpstreamCondition(layer: Layer): (entry: Upstream) => boolean {
  return (entry) => {
    if (layer === "mapnik") return entry.host === "tile.openstreetmap.org";
    if (layer === "cyclemap")
      return entry.host === "api.thunderforest.com" && entry.path.startsWith("/cycle/");
    return (
      entry.host === "api.thunderforest.com" &&
      entry.path.startsWith("/styles/transport/")
    );
  };
}

test("live OSM embed: layer-specific upstreams, legacy cycle falls back to mapnik", async ({
  page,
}, testInfo) => {
  test.setTimeout(240_000);
  const credential = secrets();
  const tag = crypto.randomUUID();
  // Artifacts go to the Playwright test-results artifacts directory
  // (framework-managed; location governed by the config outputDir).
  const outDir = testInfo.outputDir;
  await mkdir(outDir, { recursive: true });

  const upstream: Upstream[] = [];
  page.on("response", (response) => {
    const request = response.request();
    let parsed: URL;
    try {
      parsed = new URL(request.url());
    } catch {
      return;
    }
    if (!PROVIDER_HOSTS.has(parsed.host)) return;
    // Record host + pathname only: query strings can carry the
    // provider-supplied key material, which must never enter artifacts.
    upstream.push({
      method: request.method(),
      host: parsed.host,
      path: parsed.pathname,
      status: response.status(),
      frame: request.frame()?.url() ?? null,
    });
  });

  // Workspace + capability + agent token (same pattern as preview.spec.ts).
  await login(page, credential);
  const sitesResponse = await page.request.get("/api/control/v1/me/sites");
  expect(sitesResponse.status()).toBe(200);
  const sites = (await sitesResponse.json()) as Array<{
    site_id: string;
    site_key: string;
  }>;
  const parity = sites.find((site) => site.site_key === "parity");
  expect(parity).toBeDefined();
  const csrf =
    (await page.context().cookies()).find((cookie) => cookie.name === "slaif_csrf")
      ?.value ?? "";
  expect(csrf).toBeTruthy();

  const workspacePath = `/api/control/v1/sites/${parity!.site_id}/workspaces/`;
  const workspaceCreate = await page.request.post(workspacePath, {
    headers: {
      "X-CSRF-Token": csrf,
      "Idempotency-Key": `oap-0789a-live-workspace-${tag}`,
    },
    data: {
      title: `OAP 078-9-a live OSM provider observation ${tag}`,
      task_description: "Live provider observation workspace",
      delegation_preset: "L4_SITE_ARCHITECT",
      duration_hours: 1,
      request_quota: 1000,
      mutation_quota: 200,
      delete_quota: 0,
      upload_quota: 0,
      browser_quota: 0,
    },
  });
  expect(workspaceCreate.status()).toBe(201);
  const workspace = (await workspaceCreate.json()) as {
    workspace_id?: unknown;
  };
  expect(typeof workspace.workspace_id).toBe("string");
  const workspaceId = workspace.workspace_id as string;
  const capabilityResponse = await page.request.post(
    `${workspacePath}${workspaceId}/capabilities/`,
    {
      headers: {
        "X-CSRF-Token": csrf,
        "Idempotency-Key": `oap-0789a-live-capability-${tag}`,
      },
    },
  );
  expect(capabilityResponse.status()).toBe(201);
  const agentToken = ((await capabilityResponse.json()) as { token?: unknown })
    .token as string;
  const agentHeaders = { Authorization: `Bearer ${agentToken}` };

  const pagesResponse = await page.request.get("/api/agent/v1/pages/", {
    headers: agentHeaders,
  });
  expect(pagesResponse.status()).toBe(200);
  const pages = (await pagesResponse.json()) as Array<{
    id?: unknown;
    slug?: unknown;
  }>;
  const homePage = pages.find((candidate) => candidate.slug === "home");
  expect(typeof homePage?.id).toBe("string");
  const compositionPath = `/api/agent/v1/pages/${homePage!.id as string}/components`;

  for (const layer of LAYERS) {
    const create = await page.request.post(compositionPath, {
      headers: {
        ...agentHeaders,
        "Idempotency-Key": `oap-0789a-live-${layer}-${tag}`,
      },
      data: {
        component_type: "MapBlock",
        slot_key: "default",
        props: {
          bbox: BBOX,
          ...(layer === "mapnik" ? {} : { layer }),
          title: `Live OSM ${layer}`,
        },
      },
    });
    expect(create.status(), `MapBlock create for ${layer}`).toBe(201);
  }

  const previewResponse = await page.goto(`/preview/${workspaceId}/s/parity/`);
  expect(previewResponse?.status()).toBe(200);
  const marker = upstream.length;

  for (const layer of LAYERS) {
    const src = FRAME_SOURCES[layer];
    // The cross-origin frame URL settles shortly after navigation; poll
    // for the frame instead of snapshotting at goto completion.
    let frame: import("@playwright/test").Frame | undefined;
    await expect
      .poll(
        () => {
          frame = page.frames().find((candidate) => candidate.url() === src);
          return frame !== undefined;
        },
        { timeout: 15_000, message: `map iframe frame for ${layer}` },
      )
      .toBe(true);
    await page.locator(`iframe.sl-embed--map[src="${src}"]`).scrollIntoViewIfNeeded();
    await expect
      .poll(() => frame!.title(), {
        timeout: 60_000,
        message: `OSM frame title for ${layer}`,
      })
      .toBe("OpenStreetMap Embedded");
    await expect
      .poll(
        () =>
          upstream
            .slice(marker)
            .filter((entry) => frameMatches(entry.frame, layer))
            .some(layerUpstreamCondition(layer)),
        { timeout: 90_000, message: `layer-specific upstream for ${layer}` },
      )
      .toBe(true);
    await page.screenshot({ path: testInfo.outputPath(`live-osm-${layer}.png`) });
  }

  // Provider-level negative control: the legacy identifier `cycle`
  // silently falls back to mapnik upstream.
  const negativeMarker = upstream.length;
  const negativeUrl = `${EMBED_BASE}?bbox=${BBOX_TEXT}&layer=cycle`;
  const negativeResponse = await page.goto(negativeUrl, {
    waitUntil: "domcontentloaded",
  });
  expect(negativeResponse?.status()).toBe(200);
  await expect
    .poll(
      () =>
        upstream
          .slice(negativeMarker)
          .some((entry) => entry.host === "tile.openstreetmap.org"),
      { timeout: 90_000, message: "legacy cycle fallback to mapnik tiles" },
    )
    .toBe(true);
  const thunderforestAfter = upstream
    .slice(negativeMarker)
    .filter((entry) => entry.host === "api.thunderforest.com");
  expect(
    thunderforestAfter,
    "legacy cycle must not reach the Thunder Forest upstream",
  ).toEqual([]);
  await page.screenshot({
    path: testInfo.outputPath("live-osm-legacy-cycle-fallback.png"),
  });

  const slim = (entries: Upstream[]) =>
    entries.map(({ method, host, path, status }) => ({
      method,
      host,
      path,
      status,
    }));
  const evidence = {
    generated_at: new Date().toISOString(),
    preview: `/preview/${workspaceId}/s/parity/`,
    layers: Object.fromEntries(
      LAYERS.map((layer) => [
        layer,
        slim(
          upstream.slice(marker).filter((entry) => frameMatches(entry.frame, layer)),
        ),
      ]),
    ),
    legacy_cycle_negative_control: slim(upstream.slice(negativeMarker)),
  };
  writeFileSync(path.join(outDir, "evidence.json"), JSON.stringify(evidence, null, 2));
});
