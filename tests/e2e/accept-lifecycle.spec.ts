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

async function seedContent(
  page: Page,
  siteId: string,
): Promise<{
  workspaceId: string;
  token: string;
  mediaId: string;
  heading: string;
}> {
  const workspaceId = await createAgentWorkspace(
    page,
    siteId,
    "083 accept lifecycle",
    "L2_SITE_EDITOR",
  );
  const token = await createCapability(page, siteId, workspaceId);
  const tinyDigest = sha256Hex(TINY_PNG);
  const upload = await page.request.post("/api/agent/v1/media/assets", {
    headers: {
      Authorization: `Bearer ${token}`,
      "Idempotency-Key": crypto.randomUUID(),
    },
    multipart: uploadForm(TINY_PNG, "accept-proof.png", "image/png", {
      alt_text: "083 accept lifecycle media",
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
  // Run-unique heading: the assertion below counts canonical nodes with
  // this exact text (exactly one), which holds on a fresh stack and stays
  // unambiguous on a reused one.
  const heading = `083 accept lifecycle heading ${crypto.randomUUID().slice(0, 8)}`;
  const imageStatus = await agentComponentWrite(page, home.id, token, {
    component_type: "Image",
    slot_key: "default",
    props: { mediaId, alt: "083 accept lifecycle media" },
  });
  expect(imageStatus).toBe(201);
  const headingStatus = await agentComponentWrite(page, home.id, token, {
    component_type: "Heading",
    slot_key: "default",
    props: { text: heading, level: 3 },
  });
  expect(headingStatus).toBe(201);
  return { workspaceId, token, mediaId, heading };
}

async function acceptBody(
  page: Page,
  siteId: string,
  workspaceId: string,
  digestOverride?: string,
): Promise<{
  snapshot_id: string;
  digest: string;
  acknowledge_summary: true;
}> {
  const response = await page.request.get(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/review/`,
  );
  expect(response.status()).toBe(200);
  const document = (await response.json()) as {
    snapshot: { id: string; digest: string };
  };
  return {
    snapshot_id: document.snapshot.id,
    digest: digestOverride ?? document.snapshot.digest,
    acknowledge_summary: true,
  };
}

async function postAccept(
  page: Page,
  siteId: string,
  workspaceId: string,
  body: Record<string, unknown>,
): Promise<{ status: number; json: Record<string, unknown> }> {
  const csrf = await adminCsrf(page);
  const response = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/accept/`,
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

test.describe("accept lifecycle (083/1)", () => {
  test("positive: content+media workspace freezes, accepts end to end, publishes once", async ({
    page,
  }) => {
    test.setTimeout(300_000);
    const project = composeProject();
    const stopObserving = observe(page);
    await login(page, secrets());
    const siteId = await demoSiteId(page);
    const { workspaceId, mediaId, heading } = await seedContent(page, siteId);
    const tinyDigest = sha256Hex(TINY_PNG);
    const beforeRevision = Number(
      psql(
        project,
        "SELECT canonical_revision FROM control.site WHERE id = " + `'${siteId}'::uuid`,
      ),
    );

    const freeze = await freezeWorkspace(page, siteId, workspaceId);
    expect(freeze.status).toBe(202);
    await waitForReview(page, project, siteId, workspaceId);

    // The accept control is present for REVIEW + COMPLETE + no drift.
    const reviewUrl = `/admin/sites/${siteId}/workspaces/${workspaceId}/review`;
    await page.goto(reviewUrl);
    const acceptButton = page.getByRole("button", { name: /accept/i });
    await expect(acceptButton).toBeVisible();
    expect(await page.getByRole("button", { name: /discard|publish/i }).count()).toBe(
      0,
    );

    // Confirmation requires the acknowledgement (default unchecked).
    await acceptButton.click();
    const dialog = page.getByRole("dialog");
    await expect(dialog).toBeVisible();
    const confirmButton = dialog.getByRole("button", { name: "Accept", exact: true });
    await expect(confirmButton).toBeDisabled();
    await dialog.getByRole("checkbox").check();
    await expect(confirmButton).toBeEnabled();

    const acceptResponsePromise = page.waitForResponse(
      (response) =>
        response.url().includes(`/workspaces/${workspaceId}/accept/`) &&
        response.request().method() === "POST",
    );
    await confirmButton.click();
    const acceptResponse = await acceptResponsePromise;
    expect(acceptResponse.status()).toBe(202);
    const acceptJson = (await acceptResponse.json()) as {
      job_id: string;
      status: string;
    };
    expect(acceptJson.job_id).toMatch(/^[0-9a-f-]{36}$/);

    // Poll the existing read route until the terminal ACCEPTED renders.
    // (Exactly one locator: the terminal message. The admin page renders two
    // role=status elements after accept — the page-level toast and the
    // accept action's own result span — so match the exact text.)
    await expect(
      page.getByText(
        "Accepted — the canonical content now matches the frozen snapshot.",
      ),
    ).toBeVisible({
      timeout: 300_000,
    });

    // The single promotion transaction's durable effects.
    expect(
      psql(
        project,
        "SELECT canonical_revision FROM control.site WHERE id = " + `'${siteId}'::uuid`,
      ),
    ).toBe(String(beforeRevision + 1));
    expect(
      psql(
        project,
        `SELECT status FROM control.workspace
            WHERE id = '${workspaceId}'::uuid`,
      ),
    ).toBe("ACCEPTED");
    expect(
      psql(
        project,
        `SELECT accepted_at IS NOT NULL FROM control.workspace
            WHERE id = '${workspaceId}'::uuid`,
      ),
    ).toBe("t");
    expect(
      psql(
        project,
        `SELECT status FROM control.review_job
            WHERE id = '${acceptJson.job_id}'::uuid`,
      ),
    ).toBe("SUCCEEDED");
    // PostgreSQL parses `||` tighter than `IS NOT NULL`, so the boolean
    // term is explicitly parenthesized (unparenthesized it collapses the
    // whole concatenation to a `t`/`f` result).
    const auditRow = psql(
      project,
      `SELECT site_id || '|' || workspace_id || '|' || snapshot_id || '|' ||
                job_id || '|' || digest || '|' || base_site_revision || '|' ||
                new_canonical_revision || '|' ||
                committed_operations::text || '|' ||
                CASE
                  WHEN actor_user_account_id IS NOT NULL THEN 't'
                  ELSE 'f'
                END
           FROM audit.promotion
          WHERE job_id = '${acceptJson.job_id}'::uuid`,
    );
    // site_id|workspace_id|snapshot_id|job_id|digest|base|new|ops|actor-present
    const auditFields = auditRow.split("|");
    expect(auditFields.length).toBe(9);
    expect(auditFields[0]).toBe(siteId);
    expect(auditFields[1]).toBe(workspaceId);
    expect(auditFields[2]).toMatch(/^[0-9a-f-]{36}$/);
    expect(auditFields[3]).toBe(acceptJson.job_id);
    expect(auditFields[4]).toMatch(/^[0-9a-f]{64}$/);
    expect(auditFields[5]).toBe(String(beforeRevision));
    expect(auditFields[6]).toBe(String(beforeRevision + 1));
    expect(Number(auditFields[7])).toBeGreaterThanOrEqual(1);
    expect(auditFields[8]).toBe("t");
    const auditDigest = auditFields[4];
    expect(
      psql(
        project,
        `SELECT event_kind || '|' || count(*)::text
             FROM control.cache_outbox
            WHERE workspace_id = '${workspaceId}'::uuid
            GROUP BY event_kind`,
      ),
    ).toBe(`WORKSPACE_ACCEPTED|1`);
    const outboxPayload = JSON.parse(
      psql(
        project,
        `SELECT payload::text FROM control.cache_outbox
            WHERE workspace_id = '${workspaceId}'::uuid
              AND event_kind = 'WORKSPACE_ACCEPTED'`,
      ),
    ) as {
      snapshot_id: string;
      digest: string;
      base_site_revision: number;
      new_canonical_revision: number;
      media_manifest: Array<{
        media_id: string;
        digest: string;
        public_key: string;
      }>;
    };
    expect(outboxPayload.digest).toBe(auditDigest);
    expect(outboxPayload.base_site_revision).toBe(beforeRevision);
    expect(outboxPayload.new_canonical_revision).toBe(beforeRevision + 1);
    expect(outboxPayload.media_manifest).toEqual([
      {
        media_id: mediaId,
        digest: tinyDigest,
        public_key: `public/sha256/${tinyDigest.slice(0, 2)}/${tinyDigest.slice(2, 4)}/${tinyDigest}`,
      },
    ]);

    // Canonical content now equals the frozen snapshot content.
    expect(
      psql(
        project,
        `SELECT count(*) FROM content.page_composition_base c
            JOIN content.page_base p ON p.id = c.page_id
           WHERE c.site_id = '${siteId}'::uuid
             AND p.slug = 'home'
             AND c.props ->> 'text' = '${heading}'`,
      ),
    ).toBe("1");
    // Public canonical home of the demo site: localhost-only /s/<site_key>
    // convention (render site resolver); the root path is the app landing.
    const publicSite = await page.request.get("/s/demo");
    expect(publicSite.status()).toBe(200);
    expect(await publicSite.text()).toContain(heading);

    // Public media bytes re-hash to the frozen digest; published_at set.
    const publicFetch = await page.request.get(
      `/media/public/sha256/${tinyDigest.slice(0, 2)}/${tinyDigest.slice(
        2,
        4,
      )}/${tinyDigest}`,
    );
    expect(publicFetch.status()).toBe(200);
    const body = await publicFetch.body();
    expect(sha256Hex(body)).toBe(tinyDigest);
    expect(
      psql(
        project,
        `SELECT public_status::text || '|'
             || CASE WHEN published_at IS NOT NULL THEN 't' ELSE 'f' END
             FROM content.media_asset_base WHERE id = '${mediaId}'::uuid`,
      ),
    ).toBe("public|t");

    // Duplicate accept after the terminal state: the stable 409 class.
    const duplicate = await postAccept(
      page,
      siteId,
      workspaceId,
      await acceptBody(page, siteId, workspaceId),
    );
    expect(duplicate.status).toBe(409);

    expect(stopObserving()).toEqual([]);
  });

  test("negative: digest mismatch and agent capability are uniform denials; drift removes the control", async ({
    page,
    request,
  }) => {
    test.setTimeout(300_000);
    const project = composeProject();
    const stopObserving = observe(page, [/\/accept\/$/]);
    await login(page, secrets());
    const siteId = await demoSiteId(page);
    const { workspaceId, token } = await seedContent(page, siteId);
    const freeze = await freezeWorkspace(page, siteId, workspaceId);
    expect(freeze.status).toBe(202);
    await waitForReview(page, project, siteId, workspaceId);

    // digest mismatch -> uniform 404 (indistinguishable from not-found).
    const body = await acceptBody(page, siteId, workspaceId);
    const wrongDigest = ("0".repeat(32) + body.digest.slice(32)).replace(
      /0/g,
      () => "f",
    );
    expect(wrongDigest).not.toBe(body.digest);
    const mismatch = await postAccept(page, siteId, workspaceId, {
      ...body,
      digest: wrongDigest,
    });
    expect(mismatch.status).toBe(404);
    // unknown snapshot id -> the SAME uniform 404 class (no oracle).
    const unknownSnapshot = await postAccept(page, siteId, workspaceId, {
      ...body,
      snapshot_id: crypto.randomUUID(),
    });
    expect(unknownSnapshot.status).toBe(404);
    expect(await workspaceStatus(page, siteId, workspaceId)).toBe("REVIEW");

    // Agent capability token on the control accept route: uniform denial
    // (no accept surface exists for agents) and no state change.
    // Cookie-free request context (the `request` fixture does not share the
    // page's session jar): a Bearer capability on the control accept route
    // is a uniform authentication denial (401), matching the route matrix.
    const agentPost = await request.post(
      `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/accept/`,
      {
        headers: { Authorization: `Bearer ${token}` },
        data: body,
      },
    );
    expect(agentPost.status()).toBe(401);
    expect(await workspaceStatus(page, siteId, workspaceId)).toBe("REVIEW");

    // Strict body: acknowledge_summary=false / missing are rejected.
    const ackFalse = await postAccept(page, siteId, workspaceId, {
      snapshot_id: body.snapshot_id,
      digest: body.digest,
      acknowledge_summary: false,
    });
    expect(ackFalse.status).toBe(422);
    const ackMissing = await postAccept(page, siteId, workspaceId, {
      snapshot_id: body.snapshot_id,
      digest: body.digest,
    });
    expect(ackMissing.status).toBe(422);
    expect(await workspaceStatus(page, siteId, workspaceId)).toBe("REVIEW");

    // Drift: a canonical revision bump (test authority) removes the
    // accept control and renders the re-review message.
    psql(
      project,
      `UPDATE control.site SET canonical_revision = canonical_revision + 1
          WHERE id = '${siteId}'::uuid`,
    );
    await page.goto(`/admin/sites/${siteId}/workspaces/${workspaceId}/review`);
    expect(await page.getByRole("button", { name: /accept/i }).count()).toBe(0);
    await expect(
      page.getByText("acceptance is blocked until re-freeze", {
        exact: false,
      }),
    ).toBeVisible();

    expect(stopObserving()).toEqual([]);
  });
});
