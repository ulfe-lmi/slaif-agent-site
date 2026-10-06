import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";

import { expect, test, type Page } from "@playwright/test";

import { login, observe, secrets } from "./support";

const TINY_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ" +
    "AAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "base64",
);

// A second valid 1x1 PNG (different bytes -> different content digest):
// workspace B's media must be a distinct content-addressed object.
const TINY_PNG_B = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1Pe" +
    "AAAADElEQVR42mOo0DgBAAKEAWnXK+NbAAAAAElFTkSuQmCC",
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

/**
 * The edge (infra/nginx/nginx.conf) sets a per-request CSP nonce from
 * NGINX's `$request_id` and forwards the policy upstream; the web app
 * embeds that nonce in the rendered HTML in both the script/link
 * `nonce="..."` attribute form and the escaped RSC flight-payload form
 * (`\"nonce\":\"...\"`). A canonical byte-identity comparison across two
 * requests must therefore normalize the 32-hex-char nonce to a fixed
 * placeholder first; every other byte is still pinned exactly.
 */
function normalizeCspNonce(html: string): string {
  return html
    .replace(/nonce="[0-9a-f]{32}"/g, 'nonce="<nonce>"')
    .replace(/\\"nonce\\":\\"[0-9a-f]{32}\\"/g, '\\"nonce\\":\\"<nonce>\\"');
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
    const publicBefore = normalizeCspNonce(await publicBeforeResponse.text());

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
    // The public render is byte-identical to the pre-discard bytes
    // (modulo the per-request edge CSP nonce; see normalizeCspNonce).
    const publicAfterResponse = await page.request.get(`/s/${siteKey}`);
    expect(publicAfterResponse.status()).toBe(200);
    expect(normalizeCspNonce(await publicAfterResponse.text())).toBe(publicBefore);

    // Duplicate discard after the terminal state: the stable 409 class
    // (pinned once).
    const duplicate = await discardPost(page, siteId, workspaceId, {
      acknowledge_discard: true,
    });
    expect(duplicate.status).toBe(409);

    // The terminal state renders the status panel, not the control.
    // Control presence is a function of the read model (the established
    // 083/1 accept pattern: the in-session dialog lifetime ends with the
    // document re-fetch, and per-state control counts are pinned in the
    // review-surface contract), so re-fetch the review page first.
    await page.goto(reviewUrl);
    expect(
      await page.getByRole("button", { name: "Discard pending work" }).count(),
    ).toBe(0);
    await expect(
      page.getByText(
        "Discarded — the pending workspace work has been removed. The canonical site content is unchanged.",
        { exact: true },
      ),
    ).toBeVisible();

    expect(stopObserving()).toEqual([]);
  });

  test("post-accept discard preserves the published canonical (083/3)", async ({
    page,
  }) => {
    test.setTimeout(600_000);
    const project = composeProject();
    const stopObserving = observe(page);
    await login(page, secrets());
    const { siteId, siteKey } = seedDedicatedSite(project);
    const beforeRevision = Number(
      psql(
        project,
        "SELECT canonical_revision FROM control.site WHERE id = " + `'${siteId}'::uuid`,
      ),
    );

    // ---- Workspace A: unique heading + small unique image, accepted.
    const workspaceA = await createAgentWorkspace(
      page,
      siteId,
      "083/3 post-accept A",
      "L2_SITE_EDITOR",
    );
    const tokenA = await createCapability(page, siteId, workspaceA);
    const digestA = sha256Hex(TINY_PNG);
    const uploadA = await page.request.post("/api/agent/v1/media/assets", {
      headers: {
        Authorization: `Bearer ${tokenA}`,
        "Idempotency-Key": crypto.randomUUID(),
      },
      multipart: uploadForm(TINY_PNG, "post-accept-a.png", "image/png", {
        alt_text: "083/3 post-accept media A",
      }),
    });
    expect(uploadA.status()).toBe(201);
    const uploadBodyA = (await uploadA.json()) as {
      record?: { id?: string; content_hash?: string };
    };
    const mediaA = uploadBodyA.record?.id ?? "";
    expect(mediaA).toMatch(/^[0-9a-f-]{36}$/);
    expect(uploadBodyA.record?.content_hash).toBe(digestA);
    const pagesA = await page.request.get("/api/agent/v1/pages", {
      headers: { Authorization: `Bearer ${tokenA}` },
    });
    expect(pagesA.status()).toBe(200);
    const listA = (await pagesA.json()) as Array<{ id: string; slug: string }>;
    const homeA = listA.find((item) => item.slug === "home");
    if (!homeA) throw new Error("home page missing");
    const headingA = `083/3 post-accept A ${crypto.randomUUID().slice(0, 8)}`;
    const imageStatusA = await agentComponentWrite(page, homeA.id, tokenA, {
      component_type: "Image",
      slot_key: "default",
      props: { mediaId: mediaA, alt: "083/3 post-accept media A" },
    });
    expect(imageStatusA).toBe(201);
    const headingStatusA = await agentComponentWrite(page, homeA.id, tokenA, {
      component_type: "Heading",
      slot_key: "default",
      props: { text: headingA, level: 3 },
    });
    expect(headingStatusA).toBe(201);

    const freezeA = await freezeWorkspace(page, siteId, workspaceA);
    expect(freezeA.status).toBe(202);
    await waitForReview(page, project, siteId, workspaceA);

    // Accept A through the review surface (the worker publishes).
    const reviewUrlA = `/admin/sites/${siteId}/workspaces/${workspaceA}/review`;
    await page.goto(reviewUrlA);
    const acceptButton = page.getByRole("button", { name: /accept/i });
    await expect(acceptButton).toBeVisible();
    await acceptButton.click();
    const dialogA = page.getByRole("dialog");
    await expect(dialogA).toBeVisible();
    const confirmAccept = dialogA.getByRole("button", { name: "Accept", exact: true });
    await expect(confirmAccept).toBeDisabled();
    await dialogA.getByRole("checkbox").check();
    await expect(confirmAccept).toBeEnabled();
    const acceptResponsePromise = page.waitForResponse(
      (response) =>
        response.url().includes(`/workspaces/${workspaceA}/accept/`) &&
        response.request().method() === "POST",
    );
    await confirmAccept.click();
    const acceptResponse = await acceptResponsePromise;
    expect(acceptResponse.status()).toBe(202);
    await expect(
      page.getByText(
        "Accepted — the canonical content now matches the frozen snapshot.",
      ),
    ).toBeVisible({
      timeout: 300_000,
    });

    // Published state verified: the public HTML carries A's heading, A's
    // media re-hashes, and A's single outbox row is consumed.
    const publicAfterAcceptResponse = await page.request.get(`/s/${siteKey}`);
    expect(publicAfterAcceptResponse.status()).toBe(200);
    const publicAfterAccept = normalizeCspNonce(await publicAfterAcceptResponse.text());
    expect(publicAfterAccept).toContain(headingA);
    const mediaAFetch = await page.request.get(
      `/media/public/sha256/${digestA.slice(0, 2)}/${digestA.slice(2, 4)}/${digestA}`,
    );
    expect(mediaAFetch.status()).toBe(200);
    const bodyA = await mediaAFetch.body();
    expect(sha256Hex(bodyA)).toBe(digestA);
    expect(mediaAFetch.headers()["cache-control"]).toBe(
      "public, max-age=31536000, immutable",
    );
    const outboxDeadlineA = Date.now() + 30_000;
    let outboxStateA: string;
    for (;;) {
      outboxStateA = psql(
        project,
        `SELECT count(*)::text || '|' ||
            max(attempt_count)::text || '|' ||
            CASE WHEN max(last_error) IS NULL THEN 'null' ELSE max(last_error) END
             FROM control.cache_outbox
            WHERE workspace_id = '${workspaceA}'::uuid
              AND consumed_at IS NOT NULL`,
      );
      if (outboxStateA.startsWith("1|")) break;
      if (Date.now() > outboxDeadlineA) {
        throw new Error(`workspace A outbox not consumed: ${outboxStateA}`);
      }
      await page.waitForTimeout(1_000);
    }
    const [consumedA, attemptsA, lastErrorA] = outboxStateA.split("|");
    expect(consumedA).toBe("1");
    expect(Number(attemptsA)).toBeGreaterThanOrEqual(1);
    expect(lastErrorA).toBe("null");

    // ---- Workspace B (same site): different heading + different image.
    const workspaceB = await createAgentWorkspace(
      page,
      siteId,
      "083/3 post-accept B",
      "L2_SITE_EDITOR",
    );
    const tokenB = await createCapability(page, siteId, workspaceB);
    const digestB = sha256Hex(TINY_PNG_B);
    expect(digestB).not.toBe(digestA);
    const uploadB = await page.request.post("/api/agent/v1/media/assets", {
      headers: {
        Authorization: `Bearer ${tokenB}`,
        "Idempotency-Key": crypto.randomUUID(),
      },
      multipart: uploadForm(TINY_PNG_B, "post-accept-b.png", "image/png", {
        alt_text: "083/3 post-accept media B",
      }),
    });
    expect(uploadB.status()).toBe(201);
    const uploadBodyB = (await uploadB.json()) as {
      record?: { id?: string; content_hash?: string };
    };
    const mediaB = uploadBodyB.record?.id ?? "";
    expect(mediaB).toMatch(/^[0-9a-f-]{36}$/);
    expect(uploadBodyB.record?.content_hash).toBe(digestB);
    const pagesB = await page.request.get("/api/agent/v1/pages", {
      headers: { Authorization: `Bearer ${tokenB}` },
    });
    expect(pagesB.status()).toBe(200);
    const listB = (await pagesB.json()) as Array<{ id: string; slug: string }>;
    const homeB = listB.find((item) => item.slug === "home");
    if (!homeB) throw new Error("home page missing");
    const headingB = `083/3 post-accept B ${crypto.randomUUID().slice(0, 8)}`;
    const imageStatusB = await agentComponentWrite(page, homeB.id, tokenB, {
      component_type: "Image",
      slot_key: "default",
      props: { mediaId: mediaB, alt: "083/3 post-accept media B" },
    });
    expect(imageStatusB).toBe(201);
    const headingStatusB = await agentComponentWrite(page, homeB.id, tokenB, {
      component_type: "Heading",
      slot_key: "default",
      props: { text: headingB, level: 3 },
    });
    expect(headingStatusB).toBe(201);

    // Freeze B, then discard B with the typed (acknowledgement)
    // confirmation — the established discard pattern.
    const freezeB = await freezeWorkspace(page, siteId, workspaceB);
    expect(freezeB.status).toBe(202);
    await waitForReview(page, project, siteId, workspaceB);
    const reviewUrlB = `/admin/sites/${siteId}/workspaces/${workspaceB}/review`;
    await page.goto(reviewUrlB);
    const discardButton = page.getByRole("button", { name: "Discard pending work" });
    await expect(discardButton).toBeVisible();
    await discardButton.click();
    const dialogB = page.getByRole("dialog");
    await expect(dialogB).toBeVisible();
    const confirmDiscard = dialogB.getByRole("button", {
      name: "Discard",
      exact: true,
    });
    await expect(confirmDiscard).toBeDisabled();
    await dialogB.getByRole("checkbox").check();
    await expect(confirmDiscard).toBeEnabled();
    const discardResponsePromise = page.waitForResponse(
      (response) =>
        response.url().includes(`/workspaces/${workspaceB}/discard/`) &&
        response.request().method() === "POST",
    );
    await confirmDiscard.click();
    const discardResponse = await discardResponsePromise;
    expect(discardResponse.status()).toBe(202);
    const discardJson = (await discardResponse.json()) as {
      job_id: string;
      status: string;
    };
    expect(discardJson.job_id).toMatch(/^[0-9a-f-]{36}$/);
    await expect(
      page.getByText(
        "Discarded — the pending workspace work has been removed. The canonical site content is unchanged.",
      ),
    ).toBeVisible({
      timeout: 300_000,
    });

    // Durable effects: B is terminal DISCARDED, its job SUCCEEDED, its
    // capability revoked, and it emitted NO outbox row (A's single row
    // is the site's entire outbox).
    expect(
      psql(
        project,
        `SELECT status || '|' ||
            CASE WHEN discarded_at IS NOT NULL THEN 't' ELSE 'f' END
           FROM control.workspace WHERE id = '${workspaceB}'::uuid`,
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
    expect(
      psql(
        project,
        `SELECT count(*) FROM control.capability
          WHERE workspace_id = '${workspaceB}'::uuid AND revoked_at IS NOT NULL`,
      ),
    ).toBe("1");
    expect(
      psql(
        project,
        `SELECT (SELECT count(*) FROM control.cache_outbox
                 WHERE workspace_id = '${workspaceB}'::uuid) || '|' ||
                (SELECT count(*) FROM control.cache_outbox
                 WHERE site_id = '${siteId}'::uuid)`,
      ),
    ).toBe("0|1");
    // The canonical revision is exactly the accept's increment, and the
    // audit carries exactly A's one promotion (none from B).
    expect(
      psql(
        project,
        "SELECT canonical_revision FROM control.site WHERE id = " + `'${siteId}'::uuid`,
      ),
    ).toBe(String(beforeRevision + 1));
    expect(
      psql(
        project,
        `SELECT (SELECT count(*) FROM audit.promotion
                 WHERE site_id = '${siteId}'::uuid) || '|' ||
                (SELECT count(*) FROM audit.promotion
                 WHERE workspace_id = '${workspaceB}'::uuid)`,
      ),
    ).toBe("1|0");

    // Public surface: byte-identical to the post-accept bytes, A present,
    // B absent; A's media still byte-identical + immutable.
    const publicAfterDiscardResponse = await page.request.get(`/s/${siteKey}`);
    expect(publicAfterDiscardResponse.status()).toBe(200);
    const publicAfterDiscard = normalizeCspNonce(
      await publicAfterDiscardResponse.text(),
    );
    expect(publicAfterDiscard).toBe(publicAfterAccept);
    expect(publicAfterDiscard).toContain(headingA);
    expect(publicAfterDiscard).not.toContain(headingB);
    const mediaAFetchAfter = await page.request.get(
      `/media/public/sha256/${digestA.slice(0, 2)}/${digestA.slice(2, 4)}/${digestA}`,
    );
    expect(mediaAFetchAfter.status()).toBe(200);
    expect(sha256Hex(await mediaAFetchAfter.body())).toBe(digestA);
    expect(mediaAFetchAfter.headers()["cache-control"]).toBe(
      "public, max-age=31536000, immutable",
    );
    // B's media was never finalized: private, no published_at.
    expect(
      psql(
        project,
        `SELECT public_status::text || '|' ||
            CASE WHEN published_at IS NULL THEN 't' ELSE 'f' END
           FROM content.media_asset_base WHERE id = '${mediaB}'::uuid`,
      ),
    ).toBe("private|t");

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
