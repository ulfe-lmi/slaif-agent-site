import { execFileSync } from "node:child_process";

import { createHash } from "node:crypto";

import { expect, test, type Page } from "@playwright/test";

import { expectPrivateHeaders, login, observe, secrets } from "./support";

const TINY_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ" +
    "AAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "base64",
);

// Fixed compose-fixture identities created by tools/compose/e2e.sh.
const PARITY_SITE_ID = "12000000-0000-4000-8000-000000000300";
const PARITY_WORKSPACE_ID = "12000000-0000-4000-8000-000000000301";

const VIEWPORTS = [
  { name: "desktop", width: 1280, height: 800 },
  { name: "tablet", width: 820, height: 1180 },
  { name: "mobile", width: 375, height: 667 },
] as const;

function composeProject(): string {
  const project = process.env.SLAIF_E2E_COMPOSE_PROJECT;
  if (!project) throw new Error("missing SLAIF_E2E_COMPOSE_PROJECT");
  return project;
}

function docker(project: string, args: readonly string[]): string {
  return execFileSync("docker", args, { encoding: "utf8" });
}

function psql(project: string, sql: string): string {
  return docker(project, [
    "exec",
    `${project}-postgres-1`,
    "psql",
    "-U",
    "postgres",
    "-d",
    "slaif",
    "-Atc",
    sql,
  ]).trim();
}

function psqlExpectingFailure(
  project: string,
  sql: string,
): { code: number; stderr: string } {
  try {
    psql(project, sql);
    return { code: 0, stderr: "" };
  } catch (error) {
    const code = (error as { code?: number }).code ?? -1;
    const stderr = ((error as { stderr?: Buffer }).stderr ?? Buffer.from("")).toString(
      "utf8",
    );
    return { code: Number.isFinite(code) ? code : -1, stderr };
  }
}

function randomHex(bytes: number): string {
  const value = new Uint8Array(bytes);
  crypto.getRandomValues(value);
  return Array.from(value, (item) => item.toString(16).padStart(2, "0")).join("");
}

function sha256Hex(value: Uint8Array | string): string {
  return createHash("sha256").update(value).digest("hex");
}

/**
 * Seed one human session for an OIDC fixture user and return the exact
 * session cookie and matching CSRF token the trusted server expects.
 */
function seedHumanSession(
  project: string,
  userId: string,
): { cookie: string; csrfCookie: string; csrfToken: string } {
  const sessionSecret = new Uint8Array(32);
  crypto.getRandomValues(sessionSecret);
  const csrfSecret = new Uint8Array(32);
  crypto.getRandomValues(csrfSecret);
  const sessionId = crypto.randomUUID();
  const publicHex = randomHex(16);
  psql(
    project,
    `SELECT control.slaif_create_human_session(
       '${sessionId}'::uuid, 'sas2_${publicHex}',
       decode('${sha256Hex(sessionSecret)}', 'hex')::bytea,
       decode('${sha256Hex(csrfSecret)}', 'hex')::bytea,
       '${userId}'::uuid, 3600, 7200, 3600)`,
  );
  return {
    cookie: `slaif_session=sas2_session_${publicHex}_${Buffer.from(sessionSecret).toString("base64url")}`,
    csrfCookie: `slaif_csrf=sas2_csrf_${Buffer.from(csrfSecret).toString("base64url")}`,
    csrfToken: `sas2_csrf_${Buffer.from(csrfSecret).toString("base64url")}`,
  };
}

function uploadForm(
  file: Buffer,
  filename: string,
  mimeType: string,
  fields: Record<string, string> = {},
): FormData {
  const form = new FormData();
  form.append("file", new Blob([new Uint8Array(file)], { type: mimeType }), filename);
  for (const [key, value] of Object.entries(fields)) {
    form.append(key, value);
  }
  return form;
}

async function demoSiteId(page: Page): Promise<string> {
  const response = await page.request.get("/api/control/v1/me/sites");
  expect(response.status()).toBe(200);
  const sites = (await response.json()) as Array<{
    site_id: string;
    site_key: string;
  }>;
  const demo = sites.find((site) => site.site_key === "demo");
  if (!demo) throw new Error("demo site missing");
  return demo.site_id;
}

async function adminCsrf(page: Page): Promise<string> {
  const csrf = (await page.context().cookies()).find(
    (cookie) => cookie.name === "slaif_csrf",
  );
  if (!csrf) throw new Error("csrf cookie missing");
  return csrf.value;
}

async function createAgentWorkspace(
  page: Page,
  siteId: string,
  title: string,
  preset: string,
): Promise<string> {
  const csrf = await adminCsrf(page);
  const response = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/`,
    {
      headers: {
        "X-CSRF-Token": csrf,
        "Idempotency-Key": crypto.randomUUID(),
      },
      data: { title, delegation_preset: preset },
    },
  );
  expect(response.status()).toBe(201);
  const body = (await response.json()) as {
    workspace_id: string;
    status: string;
  };
  expect(body.status).toBe("ACTIVE");
  return body.workspace_id;
}

async function createCapability(
  page: Page,
  siteId: string,
  workspaceId: string,
): Promise<string> {
  const csrf = await adminCsrf(page);
  const response = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/capabilities/`,
    {
      headers: {
        "X-CSRF-Token": csrf,
        "Idempotency-Key": crypto.randomUUID(),
      },
    },
  );
  expect(response.status()).toBe(201);
  const body = (await response.json()) as { capability_id: string; token: string };
  expect(body.token).toMatch(/^sas2_[0-9a-f]+_[A-Za-z0-9_-]+$/);
  return body.token;
}

async function freezeWorkspace(
  page: Page,
  siteId: string,
  workspaceId: string,
): Promise<{ status: number; body: Record<string, unknown> }> {
  const csrf = await adminCsrf(page);
  const response = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/freeze/`,
    { headers: { "X-CSRF-Token": csrf } },
  );
  const body = (await response.json()) as Record<string, unknown>;
  return { status: response.status(), body };
}

async function workspaceStatus(
  page: Page,
  siteId: string,
  workspaceId: string,
): Promise<string> {
  const response = await page.request.get(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}`,
  );
  expect(response.status()).toBe(200);
  const body = (await response.json()) as { status: string };
  return body.status;
}

async function homePageId(page: Page, token: string): Promise<string> {
  const pages = await page.request.get("/api/agent/v1/pages", {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(pages.status()).toBe(200);
  const list = (await pages.json()) as Array<{ id: string; slug: string }>;
  const home = list.find((item) => item.slug === "home");
  expect(home).toBeTruthy();
  return home!.id;
}

async function agentComponentWrite(
  page: Page,
  pageId: string,
  token: string,
  text: string,
): Promise<{ status: number; code: string }> {
  const response = await page.request.post(`/api/agent/v1/pages/${pageId}/components`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Idempotency-Key": crypto.randomUUID(),
    },
    data: {
      component_type: "Heading",
      slot_key: "default",
      props: { text, level: 3 },
    },
  });
  const body = (await response.json()) as { error?: { code?: string } };
  return { status: response.status(), code: body.error?.code ?? "" };
}

/**
 * The snapshot row and the FREEZING -> REVIEW transition commit in one
 * transaction, so no consistent read can ever observe a snapshot row while
 * the workspace status is still FREEZING (atomic single-statement check).
 */
async function waitForReview(
  page: Page,
  project: string,
  siteId: string,
  workspaceId: string,
): Promise<void> {
  const deadline = Date.now() + 240_000;
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
    const status = await workspaceStatus(page, siteId, workspaceId);
    if (status === "REVIEW") return;
    expect(["ACTIVE", "FREEZING"]).toContain(status);
    if (Date.now() > deadline) throw new Error(`timeout at status ${status}`);
    await page.waitForTimeout(500);
  }
}

async function waitForRunCompletion(
  page: Page,
  token: string,
  runId: string,
): Promise<Array<{ artifact_id: string; kind: string; mime_type: string }>> {
  const deadline = Date.now() + 240_000;
  for (;;) {
    const response = await page.request.get(`/api/agent/v1/preview-runs/${runId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(response.status()).toBe(200);
    const body = (await response.json()) as {
      state: string;
      artifacts?: Array<{ artifact_id: string; kind: string; mime_type: string }>;
      error?: { code?: string; message?: string } | null;
    };
    if (body.state === "COMPLETED") {
      expect(body.artifacts?.length).toBeGreaterThan(0);
      return body.artifacts as Array<{
        artifact_id: string;
        kind: string;
        mime_type: string;
      }>;
    }
    if (["FAILED", "TIMED_OUT", "CANCELLED"].includes(body.state)) {
      throw new Error(
        `browser run ${body.state}: ${JSON.stringify(body.error ?? null)}`,
      );
    }
    if (Date.now() > deadline) throw new Error(`run stuck at ${body.state}`);
    await page.waitForTimeout(1000);
  }
}

async function expectNoOverflow(page: Page): Promise<void> {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(overflow, "horizontal overflow").toBe(false);
}

async function summaryGroupText(page: Page, heading: string): Promise<string> {
  const group = page.locator(".review-summary-group").filter({
    has: page.getByRole("heading", { level: 3, name: heading, exact: true }),
  });
  expect(await group.count(), heading).toBe(1);
  return (await group.innerText()).replace(/\s+/g, " ").trim();
}

test("review-surface-review-render-and-summary", async ({ page }) => {
  test.setTimeout(540_000);
  const credential = secrets();
  const project = composeProject();
  const failures = observe(page);

  await login(page, credential);
  const siteId = await demoSiteId(page);

  // ------------------------------------------- agent workspace + capability
  // L4: the fixture creates content-model types/fields (L4 scopes) in
  // addition to items/translations/composition/media (L1/L2 scopes).
  const title = `082 E2E review ${randomHex(4)}`;
  const workspaceId = await createAgentWorkspace(
    page,
    siteId,
    title,
    "L4_SITE_ARCHITECT",
  );
  const token = await createCapability(page, siteId, workspaceId);
  const homeId = await homePageId(page, token);
  const agentHeaders = { Authorization: `Bearer ${token}` };

  // ------------------------------------------ fixture content before freeze
  // 1. One media asset (private staging bytes for the review render).
  const mediaUpload = await page.request.post("/api/agent/v1/media/assets", {
    headers: { ...agentHeaders, "Idempotency-Key": crypto.randomUUID() },
    multipart: uploadForm(TINY_PNG, "review-proof.png", "image/png", {
      alt_text: "082 review media",
    }),
  });
  expect(mediaUpload.status()).toBe(201);
  const mediaUploadBody = (await mediaUpload.json()) as {
    record: Record<string, unknown>;
  };
  const mediaId = String(mediaUploadBody.record.id);
  expect(mediaId).toMatch(/^[0-9a-f-]{36}$/i);

  // 2. One content type + one localized field (the item/translation model).
  const typeCreated = await page.request.post("/api/agent/v1/content-model/types", {
    headers: { ...agentHeaders, "Idempotency-Key": crypto.randomUUID() },
    data: {
      key: "review-article",
      labels: { en: "Review article" },
      slug_pattern: "/review-article/{slug}",
    },
  });
  expect(typeCreated.status()).toBe(201);
  const typeId = String(
    ((await typeCreated.json()) as { record: Record<string, unknown> }).record.id,
  );
  expect(typeId).toMatch(/^[0-9a-f-]{36}$/i);
  const fieldCreated = await page.request.post(
    `/api/agent/v1/content-model/types/${typeId}/fields`,
    {
      headers: { ...agentHeaders, "Idempotency-Key": crypto.randomUUID() },
      data: {
        key: "headline",
        label: "Headline",
        field_type: "short_text",
        required: true,
        localized: true,
        position: 0,
      },
    },
  );
  expect(fieldCreated.status()).toBe(201);

  // 3. One item + one translation (the item/translation change).
  const itemCreated = await page.request.post(
    `/api/agent/v1/content-items/types/${typeId}`,
    {
      headers: { ...agentHeaders, "Idempotency-Key": crypto.randomUUID() },
      data: { type_id: typeId, slug: "first", status: "PUBLISHED", values: {} },
    },
  );
  expect(itemCreated.status()).toBe(201);
  const itemId = String(
    ((await itemCreated.json()) as { record: Record<string, unknown> }).record.id,
  );
  const translationCreated = await page.request.post(
    `/api/agent/v1/content-items/${itemId}/translations`,
    {
      headers: { ...agentHeaders, "Idempotency-Key": crypto.randomUUID() },
      data: { locale: "en", localized_values: { headline: "Frozen review article" } },
    },
  );
  expect(translationCreated.status()).toBe(201);

  // 4. One composition node change referencing the media, one plain node.
  const imageCreated = await page.request.post(
    `/api/agent/v1/pages/${homeId}/components`,
    {
      headers: { ...agentHeaders, "Idempotency-Key": crypto.randomUUID() },
      data: {
        component_type: "Image",
        slot_key: "default",
        props: { mediaId, alt: "082 review media" },
      },
    },
  );
  expect(imageCreated.status()).toBe(201);
  const headingCreated = await page.request.post(
    `/api/agent/v1/pages/${homeId}/components`,
    {
      headers: { ...agentHeaders, "Idempotency-Key": crypto.randomUUID() },
      data: {
        component_type: "Heading",
        slot_key: "default",
        props: { text: "082 Review heading", level: 3 },
      },
    },
  );
  expect(headingCreated.status()).toBe(201);

  // 5. One modified existing base row (page title: before/after diff).
  const homeDetail = await page.request.get(`/api/agent/v1/pages/${homeId}`, {
    headers: agentHeaders,
  });
  expect(homeDetail.status()).toBe(200);
  const homeRow = (await homeDetail.json()) as {
    title: string;
    row_version: number;
  };
  expect(homeRow.title).toBe("SLAIF Demo Site");
  const pageUpdated = await page.request.patch(`/api/agent/v1/pages/${homeId}`, {
    headers: { ...agentHeaders, "Idempotency-Key": crypto.randomUUID() },
    data: { title: "Frozen Home", expected_row_version: homeRow.row_version },
  });
  expect(pageUpdated.status()).toBe(200);

  // 6. One long-running preview run completed BEFORE the freeze so the
  //    frozen snapshot carries browser evidence with private artifacts.
  const created = await page.request.post("/api/agent/v1/preview-runs", {
    headers: { ...agentHeaders, "Idempotency-Key": crypto.randomUUID() },
    data: {
      version: "browser-preview/v1",
      // Browser previews resolve through the /s/{siteKey} site-path scheme
      // (the bare "/" path would require a public hostname binding).
      route: "/s/demo",
      target: "desktop-chromium",
      evidence: ["screenshot"],
    },
  });
  expect(created.status()).toBe(202);
  const runBody = (await created.json()) as { run_id: string; state: string };
  expect(runBody.state).toBe("QUEUED");
  const runArtifacts = await waitForRunCompletion(page, token, runBody.run_id);
  const screenshot = runArtifacts.find((item) => item.kind === "screenshot");
  expect(screenshot).toBeTruthy();

  // ------------------------------------------------------------- human freeze
  const frozen = await freezeWorkspace(page, siteId, workspaceId);
  expect(frozen.status).toBe(202);
  expect(frozen.body).toMatchObject({ status: "FREEZING" });
  await waitForReview(page, project, siteId, workspaceId);
  expect(
    psql(
      project,
      `SELECT count(*) FROM control.review_snapshot
        WHERE workspace_id = '${workspaceId}'`,
    ),
  ).toBe("1");

  // -------------------------------------------------------- canonical psql
  const digestPair = psql(
    project,
    `SELECT digest || '|' || encode(sha256(convert_to(
       control.slaif_canonical_jsonb_text(payload), 'UTF8')), 'hex')
     FROM control.review_snapshot WHERE workspace_id = '${workspaceId}'`,
  );
  const [digest, recomputedDigest] = digestPair.split("|") as [string, string];
  expect(digest).toMatch(/^[0-9a-f]{64}$/);
  expect(recomputedDigest).toBe(digest);
  const revisionWatermark = Number(
    psql(
      project,
      `SELECT revision_watermark FROM control.review_snapshot
        WHERE workspace_id = '${workspaceId}'`,
    ),
  );
  const baseSiteRevision = Number(
    psql(
      project,
      `SELECT payload->>'base_site_revision' FROM control.review_snapshot
        WHERE workspace_id = '${workspaceId}'`,
    ),
  );
  const canonicalRevision = Number(
    psql(project, `SELECT canonical_revision FROM control.site WHERE id = '${siteId}'`),
  );
  expect(baseSiteRevision).toBe(canonicalRevision);
  expect(
    psql(
      project,
      `SELECT browser_evidence FROM control.review_snapshot
        WHERE workspace_id = '${workspaceId}'`,
    ),
  ).toBe(`[{"id": "${runBody.run_id}"}]`);
  expect(
    psql(
      project,
      `SELECT status = 'SUCCEEDED' FROM control.review_job
        WHERE workspace_id = '${workspaceId}'`,
    ),
  ).toBe("t");

  // ------------------------------------------------- admin review UI (3x)
  const reviewUrl = `/admin/sites/${siteId}/workspaces/${workspaceId}/review`;
  for (const viewport of VIEWPORTS) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto(reviewUrl);
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(
      `${title} — frozen review`,
    );
    await expect(page.getByText(digest, { exact: true })).toBeVisible();
    await expect(
      page.getByText("Canonical unchanged since freeze", { exact: false }),
    ).toBeVisible();
    for (const section of [
      "Semantic timeline",
      "Resource diff",
      "Summaries",
      "Validation",
      "Browser evidence",
      "Metadata",
    ]) {
      await expect(
        page.getByRole("heading", { level: 2, name: section }),
      ).toBeVisible();
    }
    await expectNoOverflow(page);
  }

  // ------------------------------------------------- desktop DOM pins
  await page.setViewportSize({ width: 1280, height: 800 });
  await page.goto(reviewUrl);

  // Snapshot identity + versions.
  const identityCard = page.locator("article.admin-card").first();
  await expect(identityCard.getByText("COMPLETE", { exact: true })).toBeVisible();
  const identityFact = (label: string) =>
    identityCard.locator(`div:has(> dt:text-is("${label}")) > dd`);
  await expect(identityFact("Revision watermark")).toHaveText(
    String(revisionWatermark),
  );
  await expect(identityFact("Base site revision")).toHaveText(String(baseSiteRevision));
  await expect(
    page.getByRole("heading", { name: "Versions", exact: true }),
  ).toBeVisible();

  // Semantic timeline: exactly the seven fixture operations, in the
  // deterministic read-model order (asserted as a multiset).
  const timelineRows = page.locator("table.review-table tbody tr");
  // Media registration writes the immutable site-level base store (no
  // workspace COW change row), so the fixture yields seven operations.
  expect(await timelineRows.count()).toBe(7);
  const operationTypes: string[] = [];
  for (let index = 0; index < (await timelineRows.count()); index += 1) {
    operationTypes.push(
      (await timelineRows.nth(index).locator("td").nth(1).innerText()).trim(),
    );
  }
  // Field creation updates the type (content_type_changes) and the field
  // (field_definition_changes) in one operation, so it appears as a
  // combined entry.
  expect([...operationTypes].sort()).toEqual([
    "composition_nodes:upsert",
    "composition_nodes:upsert",
    "content_types:upsert",
    "content_types:upsert, fields:upsert",
    "items:upsert",
    "pages:upsert",
    "translations:upsert",
  ]);

  // Resource diff: bounded field-level before/after per family.
  const diffRoot = page.locator("section.review-section").filter({
    has: page.locator("h2#review-diff"),
  });
  await expect(
    diffRoot.getByRole("heading", {
      name: "Pages (added 0, modified 1, deleted 0)",
    }),
  ).toBeVisible();
  await expect(diffRoot.getByText("SLAIF Demo Site → Frozen Home")).toBeVisible();
  await expect(
    diffRoot.getByRole("heading", {
      name: "Composition nodes (added 2, modified 0, deleted 0)",
    }),
  ).toBeVisible();
  await expect(diffRoot.getByText("082 Review heading")).toBeVisible();
  await expect(diffRoot.getByText("082 review media").first()).toBeVisible();
  await expect(
    diffRoot.getByRole("heading", { name: "Items (added 1, modified 0, deleted 0)" }),
  ).toBeVisible();
  await expect(diffRoot.getByText("first").first()).toBeVisible();
  await expect(
    diffRoot.getByRole("heading", {
      name: "Translations (added 1, modified 0, deleted 0)",
    }),
  ).toBeVisible();
  // The added row renders as compact JSON truncated at 256 chars
  // (FIELD_PREVIEW_BYTES); localized_values sits past the cutoff, so pin
  // the item reference, which always renders within the visible prefix.
  await expect(diffRoot.getByText(`"item_id":"${itemId}"`)).toBeVisible();
  await expect(
    diffRoot.getByRole("heading", {
      name: "Content types (added 1, modified 0, deleted 0)",
    }),
  ).toBeVisible();
  await expect(diffRoot.getByText("review-article")).toBeVisible();
  await expect(
    diffRoot.getByRole("heading", { name: "Fields (added 1, modified 0, deleted 0)" }),
  ).toBeVisible();
  await expect(diffRoot.getByText("headline").first()).toBeVisible();
  // Media registration leaves no workspace COW change rows, so the
  // media family card must be absent from the resource diff.
  expect(await diffRoot.getByRole("heading", { name: /^Media assets/ }).count()).toBe(
    0,
  );
  await expect(
    diffRoot.getByText("Field-level diff is bounded to one level"),
  ).toBeVisible();

  // Summaries: every R3 group renders the fixture data.
  const summaries = page.locator("section.review-section").filter({
    has: page.locator("h2#review-summaries"),
  });
  for (const heading of [
    "Models",
    "Fields",
    "Mappings",
    "Items & relations",
    "Resource inventory",
    "Composition by component type",
    "Theme",
    "Navigation",
    "Redirects",
    "Media",
    "Responsive",
  ]) {
    await expect(
      summaries.getByRole("heading", { level: 3, name: heading, exact: true }),
    ).toBeVisible();
  }
  const modelsText = await summaryGroupText(page, "Models");
  expect(modelsText).toContain("content_types 1");
  const fieldsText = await summaryGroupText(page, "Fields");
  expect(fieldsText).toContain("total 1");
  const itemsText = await summaryGroupText(page, "Items & relations");
  expect(itemsText).toContain("items 1");
  expect(itemsText).toContain("relations 0");
  expect(itemsText).toContain("translations 1");
  const inventoryText = await summaryGroupText(page, "Resource inventory");
  expect(inventoryText).toContain("pages 1");
  expect(inventoryText).toContain("composition_nodes 4");
  expect(inventoryText).toContain("media_assets 1");
  expect(inventoryText).toContain("locales 1");
  const compositionText = await summaryGroupText(page, "Composition by component type");
  expect(compositionText).toContain("Heading 2");
  expect(compositionText).toContain("RichText 1");
  expect(compositionText).toContain("Image 1");
  const mediaText = await summaryGroupText(page, "Media");
  expect(mediaText).toContain("assets 1");
  expect(mediaText).toContain("references 1");
  const responsiveText = await summaryGroupText(page, "Responsive");
  expect(responsiveText).toContain("enabled_locales 1");
  expect(responsiveText).toContain("default_locale en");

  // Validation: the frozen report is rendered verbatim; no fixture warnings.
  const validationPre = page.locator("pre.review-validation-report");
  await expect(validationPre).toBeVisible();
  const validationText = await validationPre.innerText();
  expect(validationText).toContain('"pages_validated": 1');
  expect(validationText).toContain('"errors": []');
  expect(validationText).toContain('"cancelled_by_freeze": []');
  await expect(
    page.getByRole("heading", { name: "Warnings", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("No warnings.")).toBeVisible();

  // Browser evidence: the frozen run with its private artifact.
  const evidence = page.locator("section.review-section").filter({
    has: page.locator("h2#review-evidence"),
  });
  await expect(
    evidence.getByRole("heading", { name: `Run ${runBody.run_id}`, exact: false }),
  ).toBeVisible();
  const artifactUrl = `/api/agent/v1/preview-runs/${runBody.run_id}/artifacts/${screenshot!.artifact_id}`;
  await expect(evidence.locator("img.review-evidence-thumbnail")).toHaveAttribute(
    "src",
    artifactUrl,
  );
  await expect(evidence.locator(`a[href="${artifactUrl}"]`)).toBeVisible();

  // Metadata: workspace, revoked capability set, quota policy.
  const metadata = page.locator("section.review-section").filter({
    has: page.locator("h2#review-metadata"),
  });
  await expect(metadata.getByText(title, { exact: true })).toBeVisible();
  await expect(
    metadata.getByRole("heading", { name: "Revoked capabilities after freeze" }),
  ).toBeVisible();
  await expect(metadata.getByText(/\(revoked /)).toBeVisible();
  await expect(metadata.getByRole("heading", { name: "Quota policy" })).toBeVisible();
  await expect(
    metadata.getByRole("heading", { name: "Agent, session, and browser metadata" }),
  ).toBeVisible();

  // Actions: rendered-site entry point + back link; NO accept/discard,
  // NO Puck launch from the review surface.
  await expect(page.getByRole("link", { name: "View rendered site" })).toHaveAttribute(
    "href",
    `/review/${workspaceId}/`,
  );
  await expect(page.getByRole("link", { name: "Back to workspace" })).toHaveAttribute(
    "href",
    `/admin/sites/${siteId}/workspaces/${workspaceId}/edit`,
  );
  expect(
    await page.getByRole("button", { name: /accept|discard|publish/i }).count(),
  ).toBe(0);
  expect(await page.getByRole("link", { name: /edit in puck/i }).count()).toBe(0);
  expect(await page.locator("a[href*='puck']").count()).toBe(0);

  // ------------------------------- evidence retrieval through the 072 route
  // Human-session gate (the 082/2 read-only extension): the admin session
  // cookie alone resolves the private artifact; the browser already sends
  // it with page.request.
  const artifactList = await page.request.get(
    `/api/agent/v1/preview-runs/${runBody.run_id}/artifacts`,
  );
  expect(artifactList.status()).toBe(200);
  const listedArtifacts = (await artifactList.json()) as Array<{
    artifact_id: string;
    kind: string;
    mime_type: string;
  }>;
  expect(
    listedArtifacts.some((item) => item.artifact_id === screenshot!.artifact_id),
  ).toBe(true);
  const artifactBytes = await page.request.get(artifactUrl);
  expect(artifactBytes.status()).toBe(200);
  expect(artifactBytes.headers()["content-type"]).toBe("image/png");
  expect((await artifactBytes.body()).length).toBeGreaterThan(0);

  // Anonymous and nonmember callers never reach the private artifact:
  // no credentials -> the established 401 authentication boundary; a
  // session without site membership -> the uniform 404 (no oracle).
  const anonContext = await page.context().browser()!.newContext();
  const anonList = await anonContext.request.get(
    `/api/agent/v1/preview-runs/${runBody.run_id}/artifacts`,
  );
  expect(anonList.status()).toBe(401);
  await anonContext.close();
  const nonmember = seedHumanSession(project, credential.fixtureUserOne);
  const nonmemberList = await page.request.get(
    `/api/agent/v1/preview-runs/${runBody.run_id}/artifacts`,
    { headers: { cookie: nonmember.cookie } },
  );
  expect(nonmemberList.status()).toBe(404);

  // -------------------------------------------- /review/ render mode (3x)
  const renderUrl = `/review/${workspaceId}/`;
  for (const viewport of VIEWPORTS) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    await page.goto(renderUrl);
    const banner = page.locator(".review-banner");
    await expect(banner).toHaveAttribute("data-review-digest", digest);
    await expect(banner).toHaveAttribute("data-review-equal", "true");
    await expect(banner.getByText("FROZEN SNAPSHOT — read-only review")).toBeVisible();
    await expect(
      banner.getByText("Canonical unchanged since freeze.", { exact: true }),
    ).toBeVisible();
    await expect(banner.getByText(digest, { exact: true })).toBeVisible();
    // Pin each banner fact by its label: base == current == canonical
    // (no drift), watermark from the immutable snapshot row.
    const bannerFact = (label: string) =>
      banner.locator(`div:has(> dt:text-is("${label}")) > dd`);
    await expect(bannerFact("Base site revision")).toHaveText(
      String(canonicalRevision),
    );
    await expect(bannerFact("Current site revision")).toHaveText(
      String(canonicalRevision),
    );
    await expect(bannerFact("Revision watermark")).toHaveText(
      String(revisionWatermark),
    );
    await expect(page.locator("h1#page-title")).toHaveText("Frozen Home");
    await expect(page.locator("main.renderer-surface")).toHaveAttribute(
      "data-render-mode",
      "preview",
    );
    await expect(page.getByRole("heading", { name: "SLAIF Demo Site" })).toBeVisible();
    await expect(
      page.getByText("A trusted canonical page projection.", { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: "082 Review heading" }),
    ).toBeVisible();
    // Private staging media: the img src is the session-scoped private
    // path and the bytes actually load in the session.
    const image = page.locator("img.sl-image");
    await expect(image).toHaveAttribute(
      "src",
      `/media/v1/sites/${siteId}/assets/${mediaId}/content`,
    );
    await image.scrollIntoViewIfNeeded();
    await image.evaluate((element) => (element as HTMLImageElement).decode());
    expect(
      await image.evaluate((element) => (element as HTMLImageElement).naturalWidth),
    ).toBeGreaterThan(0);
    // The public media namespace is never used by the review render.
    expect(await page.content()).not.toContain("/media/public/");
    // No edit affordances, no Puck link, no admin navigation in the
    // frozen document; the banner is the only review chrome.
    expect(await page.locator("button").count()).toBe(0);
    expect(await page.getByRole("link", { name: /puck/i }).count()).toBe(0);
    expect(await page.locator("a[href*='/admin']").count()).toBe(0);
    await expectNoOverflow(page);
  }

  // Unknown slugs fail closed uniformly; the rendered page set is exactly
  // the snapshot fixture (one home page on the demo site).
  const missingRender = await page.request.get(`/review/${workspaceId}/does-not-exist`);
  expect(missingRender.status()).toBe(404);

  // Determinism: two loads of the same frozen render are byte-identical.
  const firstRender = await page.request.get(renderUrl);
  expect(firstRender.status()).toBe(200);
  expectPrivateHeaders(firstRender);
  const firstHash = sha256Hex(await firstRender.body());
  const secondRender = await page.request.get(renderUrl);
  expect(secondRender.status()).toBe(200);
  expectPrivateHeaders(secondRender);
  const secondHash = sha256Hex(await secondRender.body());
  expect(firstHash).toBe(secondHash);
  expect(firstHash).toMatch(/^[0-9a-f]{64}$/);

  expect(failures(), "unexpected browser failure category").toEqual([]);
});

test("review-surface-fail-closed-negatives", async ({ page }) => {
  test.setTimeout(300_000);
  const credential = secrets();
  const project = composeProject();
  // The frozen-workspace Puck-landing probe lets the browser's own
  // editor-pages fetch fail with the expected 503 (no editor surface).
  const failures = observe(page, [/\/api\/editor\/v1\//]);

  await login(page, credential);
  const siteId = await demoSiteId(page);
  const csrf = await adminCsrf(page);

  // ------------------------------------------- frozen workspace + fresh ws
  const frozenTitle = `082 E2E negatives ${randomHex(4)}`;
  const frozenWorkspaceId = await createAgentWorkspace(
    page,
    siteId,
    frozenTitle,
    "L4_SITE_ARCHITECT",
  );
  const token = await createCapability(page, siteId, frozenWorkspaceId);
  const homeId = await homePageId(page, token);
  expect(
    await agentComponentWrite(page, homeId, token, "082 Review negatives"),
  ).toEqual({ status: 201, code: "" });
  const frozen = await freezeWorkspace(page, siteId, frozenWorkspaceId);
  expect(frozen.status).toBe(202);
  await waitForReview(page, project, siteId, frozenWorkspaceId);
  const freshWorkspaceId = await createAgentWorkspace(
    page,
    siteId,
    `082 E2E active ${randomHex(4)}`,
    "L2_SITE_EDITOR",
  );
  const snapshotDigest = psql(
    project,
    `SELECT digest FROM control.review_snapshot
      WHERE workspace_id = '${frozenWorkspaceId}'`,
  );
  expect(snapshotDigest).toMatch(/^[0-9a-f]{64}$/);

  const reviewPath = (workspaceId: string, site: string = siteId) =>
    `/api/control/v1/sites/${site}/workspaces/${workspaceId}/review/`;

  // ------------------------------- uniform 404 gating matrix (no oracle)
  const nonmember = seedHumanSession(project, credential.fixtureUserOne);
  const viewer = seedHumanSession(project, credential.fixtureUserTwo);

  // The app-wide error envelope carries a per-request request_id (plus
  // null operation_id/details), so the uniform-denial comparison normalizes
  // to status + fixed code + fixed public message.
  async function reviewRead(
    workspaceId: string,
    headers: Record<string, string> = {},
    site: string = siteId,
  ): Promise<{ status: number; body: { code: string; message: string } }> {
    const response = await page.request.get(reviewPath(workspaceId, site), {
      headers,
    });
    const raw = (await response.json().catch(() => null)) as {
      error?: { code?: string; message?: string };
    } | null;
    return {
      status: response.status(),
      body: {
        code: raw?.error?.code ?? "",
        message: raw?.error?.message ?? "",
      },
    };
  }

  // The unknown-workspace read by a governor is the reference denial.
  const reference = await reviewRead(crypto.randomUUID());
  expect(reference).toEqual({
    status: 404,
    body: {
      code: "RESOURCE_NOT_FOUND",
      message: "The resource is not available.",
    },
  });

  // Nonmember: real vs random workspace ids are indistinguishable.
  const nonmemberReal = await reviewRead(frozenWorkspaceId, {
    cookie: nonmember.cookie,
  });
  expect(nonmemberReal).toEqual(reference);
  expect(await reviewRead(crypto.randomUUID(), { cookie: nonmember.cookie })).toEqual(
    reference,
  );

  // Viewer member (READ-only role): uniform denial, indistinguishable.
  expect(await reviewRead(frozenWorkspaceId, { cookie: viewer.cookie })).toEqual(
    reference,
  );
  expect(await reviewRead(crypto.randomUUID(), { cookie: viewer.cookie })).toEqual(
    reference,
  );

  // Wrong-site binding: real vs random workspace ids indistinguishable.
  expect(await reviewRead(frozenWorkspaceId, {}, crypto.randomUUID())).toEqual(
    reference,
  );
  expect(await reviewRead(crypto.randomUUID(), {}, crypto.randomUUID())).toEqual(
    reference,
  );

  // Cross-site: the parity fixture workspace (another site) and a real
  // workspace queried under another site both fail the same way.
  expect(await reviewRead(PARITY_WORKSPACE_ID, {}, PARITY_SITE_ID)).toEqual(reference);
  expect(await reviewRead(frozenWorkspaceId, {}, PARITY_SITE_ID)).toEqual(reference);

  // Fresh ACTIVE workspace without a snapshot: indistinguishable.
  expect(await reviewRead(freshWorkspaceId)).toEqual(reference);

  // Malformed/crafted path UUIDs are rejected at the framework layer.
  for (const crafted of ["not-a-uuid", "00000000-0000-4000-8000-0000000000001"]) {
    const response = await page.request.get(
      `/api/control/v1/sites/${siteId}/workspaces/${crafted}/review/`,
    );
    expect(response.status()).toBe(422);
    expect((await response.json()) as { error: unknown }).toMatchObject({
      error: { code: "VALIDATION_ERROR" },
    });
  }

  // ------------------------------- /review/ render: no snapshot -> 404
  // A member session with a valid workspace and no snapshot gets the
  // uniform 404 (no oracle, no login leak); an anonymous caller gets the
  // established 307 to /login.
  const noSnapshotRender = await page.request.get(`/review/${freshWorkspaceId}`);
  expect(noSnapshotRender.status()).toBe(404);
  const randomRender = await page.request.get(`/review/${crypto.randomUUID()}`);
  expect(randomRender.status()).toBe(404);
  const anonContext = await page.context().browser()!.newContext();
  const anonRender = await anonContext.request.get(`/review/${frozenWorkspaceId}`, {
    maxRedirects: 0,
  });
  expect(anonRender.status()).toBe(307);
  expect(anonRender.headers()["location"]).toMatch(/\/login$/);
  await anonContext.close();

  // ------------------------------------------- Puck on the frozen ws
  // The editor envelope asserts workspace ACTIVE: the frozen workspace is
  // denied exactly like an unknown one (uniform 503), while the fresh
  // ACTIVE workspace reads successfully.
  const compositionPath = `/api/editor/v1/sites/${siteId}/pages/${homeId}/composition/`;
  const puckDenied = async (workspaceId: string) => {
    const response = await page.request.get(compositionPath, {
      headers: { "X-Editor-Workspace": workspaceId },
    });
    expect(response.status()).toBeGreaterThanOrEqual(400);
    const body = (await response.json()) as { error: { code: string } };
    return body.error.code;
  };
  expect(await puckDenied(crypto.randomUUID())).toBe("SERVICE_UNAVAILABLE");
  expect(await puckDenied(frozenWorkspaceId)).toBe("SERVICE_UNAVAILABLE");
  const positivePuck = await page.request.get(compositionPath, {
    headers: { "X-Editor-Workspace": freshWorkspaceId },
  });
  expect(positivePuck.status()).toBe(200);

  // The Puck landing for the frozen workspace shows the stable not-
  // available state and renders no editor surface.
  await page.goto(`/admin/sites/${siteId}/workspaces/${frozenWorkspaceId}/edit`);
  await expect(
    page.getByText("This Agent workspace is not available for editing."),
  ).toBeVisible();
  expect(await page.getByRole("link", { name: /edit in puck/i }).count()).toBe(0);
  expect(
    await page.locator(".puck-trusted-component, [data-puck-component]").count(),
  ).toBe(0);

  // ------------------------------- agent mutation on REVIEW is denied
  // Revoked capability and unknown tokens are both uniformly denied at
  // the authentication boundary after the freeze revocation.
  const referenceDenial = await agentComponentWrite(
    page,
    homeId,
    `sas2_${randomHex(16)}_${randomHex(32)}`,
    "082 never",
  );
  expect(referenceDenial).toEqual({
    status: 401,
    code: "AUTHENTICATION_REQUIRED",
  });
  expect(await agentComponentWrite(page, homeId, token, "082 never")).toEqual(
    referenceDenial,
  );

  // ------------------------------- review read is side-effect-free
  const sideEffectFingerprint = (workspaceId: string): string =>
    psql(
      project,
      `SELECT (SELECT count(*) FROM content.page_changes) || '|' ||
             (SELECT count(*) FROM content.page_composition_changes) || '|' ||
             (SELECT count(*) FROM content.content_item_changes) || '|' ||
             (SELECT count(*) FROM content.field_definition_changes) || '|' ||
             (SELECT count(*) FROM content.content_type_changes) || '|' ||
             (SELECT count(*) FROM content.content_item_translation_changes) || '|' ||
             (SELECT count(*) FROM content.item_relation_changes) || '|' ||
             (SELECT count(*) FROM content.collection_view_changes) || '|' ||
             (SELECT count(*) FROM content.theme_changes) || '|' ||
             (SELECT count(*) FROM content.navigation_changes) || '|' ||
             (SELECT count(*) FROM content.navigation_item_changes) || '|' ||
             (SELECT count(*) FROM content.redirect_changes) || '|' ||
             (SELECT count(*) FROM content.media_asset_changes) || '|' ||
             (SELECT count(*) FROM content.site_global_region_changes) || '|' ||
             (SELECT count(*) FROM content.site_locale_changes) || '|' ||
             (SELECT count(*) FROM content.proposed_side_effect_changes) || '|' ||
             (SELECT count(*) FROM control.review_job) || '|' ||
             (SELECT count(*) FROM control.review_snapshot) || '|' ||
             (SELECT count(*) FROM control.capability) || '|' ||
             (SELECT count(*) FROM control.browser_run) || '|' ||
             (SELECT count(*) FROM control.browser_artifact) || '|' ||
             (SELECT count(*) FROM audit.browser_event) || '|' ||
             (SELECT row_to_json(w)::text FROM control.workspace w
               WHERE w.id = '${workspaceId}'::uuid) || '|' ||
             (SELECT canonical_revision FROM control.site
               WHERE id = '${siteId}'::uuid) || '|' ||
             (SELECT digest FROM control.review_snapshot
               WHERE workspace_id = '${workspaceId}'::uuid)`,
    );
  const before = sideEffectFingerprint(frozenWorkspaceId);
  for (let index = 0; index < 3; index += 1) {
    const documentRead = await page.request.get(reviewPath(frozenWorkspaceId));
    expect(documentRead.status()).toBe(200);
  }
  const after = sideEffectFingerprint(frozenWorkspaceId);
  expect(after).toBe(before);

  // ------------------------------- route-policy delta is reads-only
  // No state-changing method exists on the review path: every non-GET
  // verb is rejected at the routing layer (405), not as a CSRF failure
  // (403) or a mutation (2xx).
  for (const method of ["POST", "PATCH", "DELETE"] as const) {
    const response = await page.request.fetch(reviewPath(frozenWorkspaceId), {
      method,
      headers: { "X-CSRF-Token": csrf },
      data: {},
    });
    expect(response.status(), method).toBe(405);
  }
  // The read itself needs no CSRF token (established read-route policy):
  // a session-only caller (no CSRF cookie) still reads successfully.
  const adminSession = (await page.context().cookies()).find(
    (cookie) => cookie.name === "slaif_session",
  );
  if (!adminSession) throw new Error("admin session cookie missing");
  const sessionOnly = await page.context().browser()!.newContext();
  await sessionOnly.addCookies([
    { name: "slaif_session", value: adminSession.value, url: "http://localhost:8080/" },
  ]);
  const readWithoutCsrf = await sessionOnly.request.get(reviewPath(frozenWorkspaceId));
  expect(readWithoutCsrf.status()).toBe(200);
  await sessionOnly.close();

  // ------------------------------- snapshot grant matrix re-assertion
  // No long-lived role holds UPDATE/DELETE (or raw SELECT, except the
  // review worker's INSERT/SELECT) on the immutable snapshot.
  const grantMatrix = psql(
    project,
    `SELECT r.rolname || '|' ||
             has_table_privilege(r.rolname, 'control.review_snapshot', 'SELECT') || '|' ||
             has_table_privilege(r.rolname, 'control.review_snapshot', 'INSERT') || '|' ||
             has_table_privilege(r.rolname, 'control.review_snapshot', 'UPDATE') || '|' ||
             has_table_privilege(r.rolname, 'control.review_snapshot', 'DELETE')
       FROM pg_roles r
      WHERE r.rolname IN ('slaif_control', 'slaif_editor_runtime',
                         'slaif_agent_runtime', 'slaif_public_reader',
                         'slaif_preview_reader', 'slaif_reviewer',
                         'slaif_review_worker', 'slaif_scheduler',
                         'slaif_media', 'slaif_gc')
      ORDER BY r.rolname`,
  );
  const grants = new Map<string, string>();
  for (const line of grantMatrix.split("\n")) {
    if (line.split("|").length !== 5) throw new Error(`bad grant row: ${line}`);
    const [role, sel, ins, upd, del] = line.split("|") as [
      string,
      string,
      string,
      string,
      string,
    ];
    grants.set(role, `${sel}|${ins}|${upd}|${del}`);
  }
  // has_table_privilege booleans concatenate as true/false text.
  expect(grants.get("slaif_review_worker")).toBe("true|true|false|false");
  for (const role of [
    "slaif_control",
    "slaif_editor_runtime",
    "slaif_agent_runtime",
    "slaif_public_reader",
    "slaif_preview_reader",
    "slaif_reviewer",
    "slaif_scheduler",
    "slaif_media",
    "slaif_gc",
  ]) {
    expect(grants.get(role), role).toBe("false|false|false|false");
  }
  for (const [verb, statement] of [
    [
      "UPDATE",
      `UPDATE control.review_snapshot
         SET digest = digest
       WHERE workspace_id = '${frozenWorkspaceId}'::uuid`,
    ],
    [
      "DELETE",
      `DELETE FROM control.review_snapshot
       WHERE workspace_id = '${frozenWorkspaceId}'::uuid`,
    ],
  ] as const) {
    const outcome = psqlExpectingFailure(
      project,
      `SET ROLE slaif_agent_runtime;
       ${statement}`,
    );
    expect(outcome.code, verb).not.toBe(0);
    expect(outcome.stderr, verb).toContain(
      "permission denied for table review_snapshot",
    );
  }

  // The negative probes never touched the immutable snapshot.
  expect(
    psql(
      project,
      `SELECT digest FROM control.review_snapshot
        WHERE workspace_id = '${frozenWorkspaceId}'`,
    ),
  ).toBe(snapshotDigest);
  expect(failures(), "unexpected browser failure category").toEqual([]);
});
