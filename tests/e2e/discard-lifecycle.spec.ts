import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";

import { expect, test, type Page } from "@playwright/test";

import { login, observe, secrets } from "./support";

const TINY_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ" +
    "AAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "base64",
);

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

function sha256Hex(value: Uint8Array | string): string {
  return createHash("sha256").update(value).digest("hex");
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

function randomHex(byteCount: number): string {
  return Array.from(crypto.getRandomValues(new Uint8Array(byteCount)))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

/**
 * Seed a dedicated run-unique site with a single published `home` page.
 * The discard proof never touches the canonical demo home: the workspace
 * is discarded, and the public render of this dedicated site must be
 * byte-identical before and after.
 */
function seedDedicatedSite(project: string): {
  siteId: string;
  siteKey: string;
} {
  const siteKey = `discardproof-${randomHex(4)}`;
  const siteId = crypto.randomUUID();
  const localeId = crypto.randomUUID();
  const pageId = crypto.randomUUID();
  const adminId = psql(
    project,
    "SELECT id FROM control.user_account WHERE local_username_normalized = 'compose.admin'",
  );
  expect(adminId).toMatch(/^[0-9a-f-]{36}$/);
  psql(
    project,
    `BEGIN;
     INSERT INTO control.site
       (id, site_key, display_name, default_locale, component_catalog_version, status)
     VALUES ('${siteId}'::uuid, '${siteKey}', '083 Discard Proof', 'en',
             'catalog-v1', 'ACTIVE');
     INSERT INTO control.site_membership
       (site_id, user_account_id, role_key, delegation_ceiling)
     VALUES ('${siteId}'::uuid, '${adminId}'::uuid, 'SITE_OWNER', 4);
     INSERT INTO content.site_locale_base
       (id, site_id, tag, enabled, is_default, position, metadata)
     VALUES ('${localeId}'::uuid, '${siteId}'::uuid, 'en', true, true, 0, '{}'::jsonb);
     INSERT INTO content.page_base
       (id, site_id, slug, title, status, locale, parent_id, route_template)
     VALUES ('${pageId}'::uuid, '${siteId}'::uuid, 'home', '083 Discard Proof',
             'PUBLISHED', 'en', NULL, NULL);
     COMMIT;`,
  );
  return { siteId, siteKey };
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

async function agentComponentWrite(
  page: Page,
  pageId: string,
  token: string,
  component: Record<string, unknown>,
): Promise<number> {
  const response = await page.request.post(`/api/agent/v1/pages/${pageId}/components`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Idempotency-Key": crypto.randomUUID(),
    },
    data: component,
  });
  return response.status();
}

/**
 * Real page DML in the COW session (the ADJ-4 limitation case): the
 * discard path never runs the foundation's dependency closure walk, so a
 * page-changing session is safe to discard and is deliberately included
 * here (order R7.3).
 */
async function agentPageTitleUpdate(
  page: Page,
  pageId: string,
  token: string,
  title: string,
): Promise<void> {
  const detail = await page.request.get(`/api/agent/v1/pages/${pageId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(detail.status()).toBe(200);
  const record = (await detail.json()) as { row_version?: number };
  if (!record.row_version) throw new Error("home page row_version missing");
  const response = await page.request.patch(`/api/agent/v1/pages/${pageId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Idempotency-Key": crypto.randomUUID(),
    },
    data: { title, expected_row_version: record.row_version },
  });
  expect(response.status()).toBe(200);
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

/**
 * The snapshot row and the FREEZING -> REVIEW transition commit in one
 * transaction: poll until no consistent read sees FREEZING+snapshot and
 * the workspace is REVIEW.
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

async function discardPost(
  page: Page,
  siteId: string,
  workspaceId: string,
  body: Record<string, unknown>,
): Promise<{ status: number; json: Record<string, unknown> }> {
  const csrf = await adminCsrf(page);
  const response = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/discard/`,
    {
      headers: { "X-CSRF-Token": csrf },
      data: body,
    },
  );
  let json: Record<string, unknown>;
  try {
    json = (await response.json()) as Record<string, unknown>;
  } catch {
    json = {};
  }
  return { status: response.status(), json };
}

/**
 * One dedicated site with a content+media workspace AND real page DML in
 * the COW session.
 */
async function seedContent(
  page: Page,
  project: string,
): Promise<{
  siteId: string;
  siteKey: string;
  workspaceId: string;
  token: string;
  mediaId: string;
  heading: string;
  pageId: string;
}> {
  const { siteId, siteKey } = seedDedicatedSite(project);
  const workspaceId = await createAgentWorkspace(
    page,
    siteId,
    "083 discard lifecycle",
    "L2_SITE_EDITOR",
  );
  const token = await createCapability(page, siteId, workspaceId);
  const tinyDigest = sha256Hex(TINY_PNG);
  const upload = await page.request.post("/api/agent/v1/media/assets", {
    headers: {
      Authorization: `Bearer ${token}`,
      "Idempotency-Key": crypto.randomUUID(),
    },
    multipart: uploadForm(TINY_PNG, "discard-proof.png", "image/png", {
      alt_text: "083 discard lifecycle media",
    }),
  });
  expect(upload.status()).toBe(201);
  const uploadBody = (await upload.json()) as {
    record?: { id?: string; content_hash?: string };
  };
  const mediaId = uploadBody.record?.id ?? "";
  expect(mediaId).toMatch(/^[0-9a-f-]{36}$/);
  expect(uploadBody.record?.content_hash).toBe(tinyDigest);
  const pages = await page.request.get("/api/agent/v1/pages", {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(pages.status()).toBe(200);
  const list = (await pages.json()) as Array<{ id: string; slug: string }>;
  const home = list.find((item) => item.slug === "home");
  if (!home) throw new Error("home page missing");
  // Run-unique heading: the canonical-row assertions below count nodes
  // with this exact text (exactly one).
  const heading = `083 discard lifecycle heading ${crypto.randomUUID().slice(0, 8)}`;
  const imageStatus = await agentComponentWrite(page, home.id, token, {
    component_type: "Image",
    slot_key: "default",
    props: { mediaId, alt: "083 discard lifecycle media" },
  });
  expect(imageStatus).toBe(201);
  const headingStatus = await agentComponentWrite(page, home.id, token, {
    component_type: "Heading",
    slot_key: "default",
    props: { text: heading, level: 3 },
  });
  expect(headingStatus).toBe(201);
  // Real page DML in the COW session (ADJ-4 case; discard-safe).
  await agentPageTitleUpdate(page, home.id, token, "083 discard lifecycle home");
  return { siteId, siteKey, workspaceId, token, mediaId, heading, pageId: home.id };
}

test.describe("discard lifecycle (083/2)", () => {
  test("positive: content+media+page-DML workspace freezes, discards end to end, canonical untouched", async ({
    page,
  }) => {
    test.setTimeout(300_000);
    const project = composeProject();
    const stopObserving = observe(page);
    await login(page, secrets());
    const { siteId, siteKey, workspaceId, mediaId } = await seedContent(page, project);
    const beforeRevision = Number(
      psql(
        project,
        "SELECT canonical_revision FROM control.site WHERE id = " + `'${siteId}'::uuid`,
      ),
    );
    // Canonical home render before the discard (public, canonical only).
    const publicBeforeResponse = await page.request.get(`/s/${siteKey}`);
    expect(publicBeforeResponse.status()).toBe(200);
    const publicBefore = await publicBeforeResponse.text();

    const freeze = await freezeWorkspace(page, siteId, workspaceId);
    expect(freeze.status).toBe(202);
    await waitForReview(page, project, siteId, workspaceId);

    // The discard control is present for REVIEW + COMPLETE.
    const reviewUrl = `/admin/sites/${siteId}/workspaces/${workspaceId}/review`;
    await page.goto(reviewUrl);
    const discardButton = page.getByRole("button", { name: "Discard pending work" });
    await expect(discardButton).toBeVisible();
    // The pending page DML is not canonical yet: the public render still
    // shows the seeded title.
    expect(publicBefore).not.toContain("083 discard lifecycle home");

    // Confirmation requires the acknowledgement (default unchecked).
    await discardButton.click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    const confirmButton = dialog.getByRole("button", { name: "Discard", exact: true });
    await expect(confirmButton).toBeDisabled();
    await dialog.getByRole("checkbox").check();
    await expect(confirmButton).toBeEnabled();

    const discardResponsePromise = page.waitForResponse(
      (response) =>
        response.url().includes(`/workspaces/${workspaceId}/discard/`) &&
        response.request().method() === "POST",
    );
    await confirmButton.click();
    const discardResponse = await discardResponsePromise;
    expect(discardResponse.status()).toBe(202);
    const discardJson = (await discardResponse.json()) as {
      job_id: string;
      status: string;
    };
    expect(discardJson.job_id).toMatch(/^[0-9a-f-]{36}$/);

    // The existing read route is polled by the control until the terminal
    // DISCARDED renders.
    await expect(
      page.getByText(
        "Discarded — the pending workspace work has been removed. The canonical site content is unchanged.",
      ),
    ).toBeVisible({
      timeout: 300_000,
    });

    // Durable effects of the single reviewer discard transaction.
    expect(
      psql(
        project,
        `SELECT status || '|' ||
            CASE WHEN discarded_at IS NOT NULL THEN 't' ELSE 'f' END
           FROM control.workspace WHERE id = '${workspaceId}'::uuid`,
      ),
    ).toBe("DISCARDED|t");
    expect(
      psql(
        project,
        `SELECT status || '|' ||
            CASE WHEN error IS NULL THEN 't' ELSE 'f' END
           FROM control.review_job WHERE id = '${discardJson.job_id}'::uuid`,
      ),
    ).toBe("SUCCEEDED|t");
    // The COW session is fully gone (the page-DML operation included).
    expect(
      psql(
        project,
        `SELECT (SELECT count(*) FROM content.page_composition_changes
                 WHERE session_id = '${workspaceId}'::uuid) || '|' ||
                (SELECT count(*) FROM content.page_changes
                 WHERE session_id = '${workspaceId}'::uuid)`,
      ),
    ).toBe("0|0");
    // The enqueue's capability revocation persisted.
    expect(
      psql(
        project,
        `SELECT count(*) FROM control.capability
          WHERE workspace_id = '${workspaceId}'::uuid AND revoked_at IS NOT NULL`,
      ),
    ).toBe("1");
    // No promotion, no outbox: discard is not publication.
    expect(
      psql(
        project,
        `SELECT (SELECT count(*) FROM audit.promotion
                 WHERE workspace_id = '${workspaceId}'::uuid) || '|' ||
                (SELECT count(*) FROM control.cache_outbox
                 WHERE workspace_id = '${workspaceId}'::uuid)`,
      ),
    ).toBe("0|0");
    // Canonical untouched: the site revision did not move.
    expect(
      psql(
        project,
        "SELECT canonical_revision FROM control.site WHERE id = " + `'${siteId}'::uuid`,
      ),
    ).toBe(String(beforeRevision));
    // The pending page DML never reached the canonical page row.
    expect(
      psql(
        project,
        `SELECT count(*) FROM content.page_base
          WHERE site_id = '${siteId}'::uuid AND title = '083 discard lifecycle home'`,
      ),
    ).toBe("0");
    // The workspace media is not public (no finalization in 083/2). The
    // asset row is private, and no media row of the dedicated site was
    // ever published. (A content-addressed public-fetch 404 is not a
    // valid shared-stack negative: a byte-identical hash published by
    // another site resolves publicly by design — the negative is pinned
    // hermetically at the asset-row and site level instead.)
    expect(
      psql(
        project,
        `SELECT public_status::text || '|' ||
            CASE WHEN published_at IS NULL THEN 't' ELSE 'f' END
           FROM content.media_asset_base WHERE id = '${mediaId}'::uuid`,
      ),
    ).toBe("private|t");
    expect(
      psql(
        project,
        `SELECT count(*) FROM content.media_asset_base
          WHERE site_id = '${siteId}'::uuid AND public_status = 'public'`,
      ),
    ).toBe("0");
    // The public render is byte-identical to the pre-discard bytes.
    const publicAfterResponse = await page.request.get(`/s/${siteKey}`);
    expect(publicAfterResponse.status()).toBe(200);
    expect(await publicAfterResponse.text()).toBe(publicBefore);

    // Duplicate discard after the terminal state: the stable 409 class
    // (pinned once).
    const duplicate = await discardPost(page, siteId, workspaceId, {
      acknowledge_discard: true,
    });
    expect(duplicate.status).toBe(409);

    // The terminal state renders the status panel, not the control.
    expect(
      await page.getByRole("button", { name: "Discard pending work" }).count(),
    ).toBe(0);

    expect(stopObserving()).toEqual([]);
  });

  test("negative: validation, terminal, and agent-capability denials; control absent off-state", async ({
    page,
    request,
  }) => {
    test.setTimeout(300_000);
    const project = composeProject();
    const stopObserving = observe(page, [/\/discard\/$/]);
    await login(page, secrets());
    const { siteId, workspaceId, token } = await seedContent(page, project);

    // Control absence while ACTIVE (no frozen snapshot available).
    await page.goto(`/admin/sites/${siteId}/workspaces/${workspaceId}/review`);
    expect(
      await page.getByRole("button", { name: "Discard pending work" }).count(),
    ).toBe(0);

    // Discard of a non-discardable (ACTIVE) workspace: the stable 409
    // class, no state change.
    const active = await discardPost(page, siteId, workspaceId, {
      acknowledge_discard: true,
    });
    expect(active.status).toBe(409);
    expect(await workspaceStatus(page, siteId, workspaceId)).toBe("ACTIVE");

    const freeze = await freezeWorkspace(page, siteId, workspaceId);
    expect(freeze.status).toBe(202);
    await waitForReview(page, project, siteId, workspaceId);

    // Strict body: acknowledge_discard=false / missing are rejected.
    const ackFalse = await discardPost(page, siteId, workspaceId, {
      acknowledge_discard: false,
    });
    expect(ackFalse.status).toBe(422);
    const ackMissing = await discardPost(page, siteId, workspaceId, {});
    expect(ackMissing.status).toBe(422);
    expect(await workspaceStatus(page, siteId, workspaceId)).toBe("REVIEW");

    // Agent capability token on the control discard route: uniform denial
    // (no discard surface exists for agents) and no state change.
    // Cookie-free request context (the `request` fixture does not share the
    // page's session jar).
    const agentPost = await request.post(
      `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/discard/`,
      {
        headers: { Authorization: `Bearer ${token}` },
        data: { acknowledge_discard: true },
      },
    );
    expect(agentPost.status()).toBe(401);
    expect(await workspaceStatus(page, siteId, workspaceId)).toBe("REVIEW");

    expect(stopObserving()).toEqual([]);
  });
});
