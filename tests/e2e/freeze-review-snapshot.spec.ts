import { execFileSync } from "node:child_process";

import { createHash } from "node:crypto";

import { expect, test, type Page } from "@playwright/test";

import { expectAdminUsable, login, observe, secrets } from "./support";

function composeProject(): string {
  const project = process.env.SLAIF_E2E_COMPOSE_PROJECT;
  if (!project) throw new Error("missing SLAIF_E2E_COMPOSE_PROJECT");
  return project;
}

function docker(
  project: string,
  args: readonly string[],
  env?: Record<string, string>,
): string {
  return execFileSync("docker", args, {
    encoding: "utf8",
    env: { ...process.env, ...env },
  });
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

function b64url(value: Uint8Array): string {
  return Buffer.from(value).toString("base64url");
}

function sha256Hex(value: Uint8Array): string {
  return createHash("sha256").update(value).digest("hex");
}

/**
 * Seed one human session for an OIDC fixture user and return the exact
 * session cookie and matching CSRF token the trusted server expects.
 */
function seedHumanSession(
  project: string,
  userId: string,
): {
  cookie: string;
  csrfCookie: string;
  csrfToken: string;
} {
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
    cookie: `slaif_session=sas2_session_${publicHex}_${b64url(sessionSecret)}`,
    csrfCookie: `slaif_csrf=sas2_csrf_${b64url(csrfSecret)}`,
    csrfToken: `sas2_csrf_${b64url(csrfSecret)}`,
  };
}

const TINY_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ" +
    "AAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "base64",
);

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

function requiredString(value: unknown, label: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`unexpected ${label} in response`);
  }
  return value;
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
): Promise<string> {
  const csrf = await adminCsrf(page);
  const response = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/`,
    {
      headers: {
        "X-CSRF-Token": csrf,
        "Idempotency-Key": crypto.randomUUID(),
      },
      data: { title, delegation_preset: "L2_SITE_EDITOR" },
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
  extraHeaders: Record<string, string> = {},
): Promise<{ status: number; body: Record<string, unknown> }> {
  const csrf = await adminCsrf(page);
  const response = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/freeze/`,
    {
      headers: {
        "X-CSRF-Token": csrf,
        ...extraHeaders,
      },
    },
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
): Promise<{ status: number; code: string }> {
  const response = await page.request.post(`/api/agent/v1/pages/${pageId}/components`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Idempotency-Key": crypto.randomUUID(),
    },
    data: {
      component_type: "Heading",
      slot_key: "default",
      props: { text: "082 Freeze denied", level: 2 },
    },
  });
  const body = (await response.json()) as { error?: { code?: string } };
  return { status: response.status(), code: body.error?.code ?? "" };
}

async function waitForReview(
  page: Page,
  project: string,
  siteId: string,
  workspaceId: string,
): Promise<{ freezingSamples: number }> {
  const deadline = Date.now() + 240_000;
  let freezingSamples = 0;
  for (;;) {
    // The snapshot row and the FREEZING -> REVIEW transition commit in
    // one transaction, so no consistent read can ever observe a snapshot
    // row while the workspace status is still FREEZING. This single
    // statement enforces that invariant atomically (two separate reads
    // could legally straddle the commit and observe a transient skew).
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
    if (status === "FREEZING") freezingSamples += 1;
    if (status === "REVIEW") return { freezingSamples };
    expect(["ACTIVE", "FREEZING"]).toContain(status);
    if (Date.now() > deadline) throw new Error(`timeout at status ${status}`);
    await page.waitForTimeout(500);
  }
}

/**
 * Wait for a same-workspace RE-REVIEW to complete (084/1).
 *
 * The re-review re-freeze re-enters FREEZING while the retained prior
 * snapshot is still visible and the pointer still selects it, so the
 * first-freeze no-snapshot-during-FREEZING invariant that waitForReview
 * asserts does not hold here.  Completion instead commits the new
 * snapshot and the pointer move atomically, so one row read of the
 * (status, pointer) pair is the consistency proof: FREEZING implies
 * the prior pointer is unchanged, and REVIEW is reachable only with a
 * NEW pointer (the old snapshot stays retained under the old id).
 */
async function waitForReReviewCompletion(
  page: Page,
  project: string,
  workspaceId: string,
  priorSnapshotId: string,
): Promise<void> {
  const deadline = Date.now() + 240_000;
  for (;;) {
    const pair = psql(
      project,
      `SELECT status || '|' || coalesce(review_snapshot_id::text, '')
         FROM control.workspace WHERE id = '${workspaceId}'`,
    );
    const [status, pointer] = pair.split("|");
    if (status === "FREEZING") {
      expect(pointer).toBe(priorSnapshotId);
    }
    if (status === "REVIEW") {
      expect(pointer).not.toBe(priorSnapshotId);
      return;
    }
    expect(["FREEZING"]).toContain(status);
    if (Date.now() > deadline) throw new Error(`timeout at status ${status}`);
    await page.waitForTimeout(500);
  }
}

test("freeze-review-snapshot-freeze-to-review", async ({ page }) => {
  test.setTimeout(300_000);
  const credential = secrets();
  const project = composeProject();
  const failures = observe(page);

  await login(page, credential);
  await expectAdminUsable(page);
  const siteId = await demoSiteId(page);
  const adminId = psql(
    project,
    "SELECT id FROM control.user_account WHERE local_username_normalized = 'compose.admin'",
  );
  expect(adminId).toMatch(/^[0-9a-f-]{36}$/i);
  const baseline = {
    agentWorkspaces: Number(
      psql(
        project,
        `SELECT count(*) FROM control.workspace
          WHERE site_id = '${siteId}' AND actor_type = 'AGENT'
            AND created_by = '${adminId}'`,
      ),
    ),
    baseNodes: Number(
      psql(
        project,
        `SELECT count(*) FROM content.page_composition_base
          WHERE site_id = '${siteId}'`,
      ),
    ),
    browserRuns: Number(
      psql(
        project,
        `SELECT count(*) FROM control.browser_run WHERE site_id = '${siteId}'`,
      ),
    ),
  };
  const canonicalHomeHeading = psql(
    project,
    `SELECT props FROM content.page_composition_base
      WHERE site_id = '${siteId}' AND component_type = 'Heading' AND order_key = 0`,
  );

  // ------------------------------------------- agent workspace + capability
  const title = `082 E2E freeze ${randomHex(4)}`;
  const workspaceId = await createAgentWorkspace(page, siteId, title);
  const token = await createCapability(page, siteId, workspaceId);
  const homeId = await homePageId(page, token);

  // ------------------------------------------------ real long-running run
  const created = await page.request.post("/api/agent/v1/preview-runs", {
    headers: {
      Authorization: `Bearer ${token}`,
      "Idempotency-Key": crypto.randomUUID(),
    },
    data: {
      version: "browser-preview/v1",
      route: "/",
      target: "desktop-chromium",
      evidence: ["screenshot"],
    },
  });
  expect(created.status()).toBe(202);
  const runBody = (await created.json()) as {
    run_id: string;
    state: string;
  };
  expect(runBody.state).toBe("QUEUED");
  expect(
    psql(
      project,
      `SELECT count(*) FROM control.browser_run
        WHERE workspace_id = '${workspaceId}'
          AND state IN ('QUEUED','RUNNING')`,
    ),
  ).toBe("1");

  // ------------------------------------------------------------ human freeze
  const frozen = await freezeWorkspace(page, siteId, workspaceId);
  expect(frozen.status).toBe(202);
  expect(frozen.body).toMatchObject({ status: "FREEZING" });
  expect(typeof frozen.body.job_id).toBe("string");
  expect(
    psql(project, `SELECT status FROM control.workspace WHERE id = '${workspaceId}'`),
  ).toBe("FREEZING");
  expect(
    psql(
      project,
      `SELECT count(*) FROM control.capability
        WHERE workspace_id = '${workspaceId}' AND revoked_at IS NULL`,
    ),
  ).toBe("0");

  // ---------------------------------------- mutation after FREEZING is denied
  // Unknown and revoked capability tokens are both uniformly denied at
  // the authentication boundary (401 AUTHENTICATION_REQUIRED).
  const reference = await agentComponentWrite(
    page,
    homeId,
    `sas2_${randomHex(16)}_${randomHex(32)}`,
  );
  expect(reference.status).toBe(401);
  expect(reference.code).toBe("AUTHENTICATION_REQUIRED");
  const afterFreeze = await agentComponentWrite(page, homeId, token);
  expect(afterFreeze).toEqual(reference);

  // ----------------------------- REVIEW only after the snapshot exists
  await waitForReview(page, project, siteId, workspaceId);
  const snapshotCount = Number(
    psql(
      project,
      `SELECT count(*) FROM control.review_snapshot
        WHERE workspace_id = '${workspaceId}'`,
    ),
  );
  expect(snapshotCount).toBe(1);

  // -------------------------------------------------------- canonical psql
  const snapshotId = psql(
    project,
    `SELECT id FROM control.review_snapshot
      WHERE workspace_id = '${workspaceId}'`,
  );
  expect(snapshotId).toMatch(/^[0-9a-f-]{36}$/i);
  expect(
    psql(
      project,
      `SELECT review_snapshot_id = '${snapshotId}'::uuid
        FROM control.workspace WHERE id = '${workspaceId}'`,
    ),
  ).toBe("t");
  expect(
    psql(
      project,
      `SELECT digest = encode(sha256(convert_to(
         control.slaif_canonical_jsonb_text(payload), 'UTF8')), 'hex')
        FROM control.review_snapshot WHERE id = '${snapshotId}'`,
    ),
  ).toBe("t");
  // Freeze policy outcome: a run that reaches COMPLETED before the
  // bounded evidence deadline is attached as browser evidence; a run
  // still outstanding at the deadline is bounded-cancelled and
  // contributes no evidence. Both are valid policy outcomes.
  const runId = psql(
    project,
    `SELECT id FROM control.browser_run
      WHERE workspace_id = '${workspaceId}'`,
  );
  expect(runId).toMatch(/^[0-9a-f-]{36}$/i);
  const runState = psql(
    project,
    `SELECT state FROM control.browser_run WHERE id = '${runId}'`,
  );
  expect(["COMPLETED", "CANCELLED"]).toContain(runState);
  const storedEvidence = psql(
    project,
    `SELECT browser_evidence FROM control.review_snapshot
      WHERE workspace_id = '${workspaceId}'`,
  );
  if (runState === "CANCELLED") {
    expect(
      psql(
        project,
        `SELECT error_code || '|' || COALESCE(summary->>'cancelled_by_freeze','')
           FROM control.browser_run WHERE id = '${runId}'`,
      ),
    ).toBe("FREEZE_CANCEL|true");
    expect(storedEvidence).toBe("[]");
  } else {
    expect(storedEvidence).toBe(`[{"id": "${runId}"}]`);
  }
  expect(
    psql(
      project,
      `SELECT count(*) FROM control.browser_run
        WHERE site_id = '${siteId}' AND state IN ('QUEUED','RUNNING')
          AND workspace_id = '${workspaceId}'`,
    ),
  ).toBe("0");
  expect(
    psql(
      project,
      `SELECT count(*) FROM control.review_job
        WHERE workspace_id = '${workspaceId}'`,
    ),
  ).toBe("1");
  expect(
    psql(
      project,
      `SELECT status = 'SUCCEEDED'
        FROM control.review_job
        WHERE workspace_id = '${workspaceId}'`,
    ),
  ).toBe("t");

  // ------------------------------------------- snapshot immutability
  for (const role of ["slaif_agent_runtime", "slaif_editor_runtime"]) {
    const outcome = psqlExpectingFailure(
      project,
      `SET ROLE ${role};
       UPDATE control.review_snapshot
          SET digest = digest WHERE id = '${snapshotId}'`,
    );
    expect(outcome.code, role).not.toBe(0);
    expect(outcome.stderr, role).toContain(
      "permission denied for table review_snapshot",
    );
  }

  // ------------------------------------------------------------- baseline
  expect(
    Number(
      psql(
        project,
        `SELECT count(*) FROM control.workspace
          WHERE site_id = '${siteId}' AND actor_type = 'AGENT'
            AND created_by = '${adminId}'`,
      ),
    ),
  ).toBe(baseline.agentWorkspaces + 1);
  expect(
    Number(
      psql(
        project,
        `SELECT count(*) FROM content.page_composition_base
          WHERE site_id = '${siteId}'`,
      ),
    ),
  ).toBe(baseline.baseNodes);
  expect(
    Number(
      psql(
        project,
        `SELECT count(*) FROM control.browser_run WHERE site_id = '${siteId}'`,
      ),
    ),
  ).toBe(baseline.browserRuns + 1);
  expect(
    psql(
      project,
      `SELECT props FROM content.page_composition_base
        WHERE site_id = '${siteId}' AND component_type = 'Heading' AND order_key = 0`,
    ),
  ).toBe(canonicalHomeHeading);
  expect(failures(), "unexpected browser failure category").toEqual([]);
});

test("freeze-review-snapshot-fail-closed-negatives", async ({ page }) => {
  test.setTimeout(240_000);
  const credential = secrets();
  const project = composeProject();
  const failures = observe(page);

  await login(page, credential);
  await expectAdminUsable(page);
  const siteId = await demoSiteId(page);
  const title = `082 E2E negatives ${randomHex(4)}`;
  const workspaceId = await createAgentWorkspace(page, siteId, title);
  const csrf = await adminCsrf(page);

  // CSRF failure on the state-changing freeze: a valid session cookie
  // without the matching CSRF token is denied.
  const adminSession = (await page.context().cookies()).find(
    (cookie) => cookie.name === "slaif_session",
  );
  if (!adminSession) throw new Error("admin session cookie missing");
  const csrfless = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/freeze/`,
    { headers: { cookie: `slaif_session=${adminSession.value}` } },
  );
  expect(csrfless.status()).toBe(403);
  expect((await csrfless.json()) as { error: unknown }).toMatchObject({
    error: { code: "AUTHORIZATION_DENIED" },
  });

  // Nonmember: fixture one has no demo-site membership; the site layer
  // denies before any workspace resolution, uniformly across ids.
  const nonmember = seedHumanSession(project, credential.fixtureUserOne);
  const nonmemberFreeze = async (id: string) => {
    const response = await page.request.post(
      `/api/control/v1/sites/${siteId}/workspaces/${id}/freeze/`,
      {
        headers: {
          cookie: `${nonmember.cookie}; ${nonmember.csrfCookie}`,
          "X-CSRF-Token": nonmember.csrfToken,
        },
      },
    );
    expect(response.status()).toBeGreaterThanOrEqual(400);
    const body = (await response.json()) as {
      error: { code: string; message: string };
    };
    return { status: response.status(), code: body.error.code };
  };
  const nonmemberReference = await nonmemberFreeze(workspaceId);
  expect(nonmemberReference).toEqual({
    status: 404,
    code: "RESOURCE_NOT_FOUND",
  });
  expect(await nonmemberFreeze(crypto.randomUUID())).toEqual(nonmemberReference);

  // Wrong site: the exact site binding fails closed uniformly.
  const wrongSite = async (id: string) => {
    const response = await page.request.post(
      `/api/control/v1/sites/${crypto.randomUUID()}/workspaces/${id}/freeze/`,
      { headers: { "X-CSRF-Token": csrf } },
    );
    expect(response.status()).toBeGreaterThanOrEqual(400);
    const body = (await response.json()) as {
      error: { code: string; message: string };
    };
    return { status: response.status(), code: body.error.code };
  };
  const wrongSiteReference = await wrongSite(workspaceId);
  expect(wrongSiteReference).toEqual({
    status: 404,
    code: "RESOURCE_NOT_FOUND",
  });
  expect(await wrongSite(crypto.randomUUID())).toEqual(wrongSiteReference);

  // Crafted/malformed ids are rejected before any lookup.
  for (const crafted of ["not-a-uuid", "00000000-0000-4000-8000-0000000000001"]) {
    const response = await page.request.post(
      `/api/control/v1/sites/${siteId}/workspaces/${crafted}/freeze/`,
      { headers: { "X-CSRF-Token": csrf } },
    );
    expect(response.status()).toBe(422);
    expect((await response.json()) as { error: unknown }).toMatchObject({
      error: { code: "VALIDATION_ERROR" },
    });
  }

  // Re-freeze of a REVIEW workspace conflicts with a stable code.
  const frozen = await freezeWorkspace(page, siteId, workspaceId);
  expect(frozen.status).toBe(202);
  await waitForReview(page, project, siteId, workspaceId);
  const refrozen = await freezeWorkspace(page, siteId, workspaceId);
  expect(refrozen.status).toBe(409);
  expect((refrozen.body as { error: unknown }).error).toMatchObject({
    code: "RESOURCE_CONFLICT",
  });

  // The negative probes created exactly one job and one snapshot.
  expect(
    psql(
      project,
      `SELECT count(*) FROM control.review_job
        WHERE workspace_id = '${workspaceId}'`,
    ),
  ).toBe("1");
  expect(
    psql(
      project,
      `SELECT count(*) FROM control.review_snapshot
        WHERE workspace_id = '${workspaceId}'`,
    ),
  ).toBe("1");
  expect(failures(), "unexpected browser failure category").toEqual([]);
});

// ---------------------------------------------------------------------
// 083/4 A (public E2E half): freeze-time canonical revision coherence.
//
// W1 is created/edited at A (canonical revision 0); a different
// authorized workspace W2 publishes an unrelated change to B through
// the real human freeze + accept path; W1 then freezes. The frozen
// document retains B as its review base with the visible B-plus-W
// content and a byte-valid digest, W1's creation-time provenance stays
// A, the reviewed/current revisions agree in the review read model,
// and the public site (through the NGINX origin) shows B's published
// content while W1's overlay is still private.
// ---------------------------------------------------------------------

/**
 * Seed a dedicated run-unique site (privileged fixture seed only; the
 * proof itself uses public actors) with one published home page and a
 * Section + Heading base composition.
 */
function seedCoherenceSite(project: string): { siteId: string; siteKey: string } {
  const siteKey = `freezecoherence-${randomHex(4)}`;
  const siteId = crypto.randomUUID();
  const localeId = crypto.randomUUID();
  const pageId = crypto.randomUUID();
  const sectionId = crypto.randomUUID();
  const headingId = crypto.randomUUID();
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
     VALUES ('${siteId}'::uuid, '${siteKey}', '083/4 Freeze Coherence', 'en',
             'catalog-v1', 'ACTIVE');
     INSERT INTO control.site_membership
       (site_id, user_account_id, role_key, delegation_ceiling)
     VALUES ('${siteId}'::uuid, '${adminId}'::uuid, 'SITE_OWNER', 4);
     INSERT INTO content.site_locale_base
       (id, site_id, tag, enabled, is_default, position, metadata)
     VALUES ('${localeId}'::uuid, '${siteId}'::uuid, 'en', true, true, 0, '{}'::jsonb);
     INSERT INTO content.page_base
       (id, site_id, slug, title, status, locale, parent_id, route_template)
     VALUES ('${pageId}'::uuid, '${siteId}'::uuid, 'home', '083/4 Freeze Coherence',
             'PUBLISHED', 'en', NULL, NULL);
     INSERT INTO content.page_composition_base
       (id, site_id, page_id, component_type, schema_version, parent_id,
        slot_key, order_key, props)
     VALUES
       ('${sectionId}'::uuid, '${siteId}'::uuid, '${pageId}'::uuid,
        'Section', '1', NULL, 'default', 0, '{}'::jsonb),
       ('${headingId}'::uuid, '${siteId}'::uuid, '${pageId}'::uuid,
        'Heading', '1', '${sectionId}'::uuid, 'default', 0,
        '{"level":1,"text":"Freeze coherence"}'::jsonb);
     COMMIT;`,
  );
  return { siteId, siteKey };
}

function siteRevision(project: string, siteId: string): number {
  return Number(
    psql(project, `SELECT canonical_revision FROM control.site WHERE id = '${siteId}'`),
  );
}

async function writeHeading(
  page: Page,
  pageId: string,
  token: string,
  text: string,
): Promise<void> {
  const response = await page.request.post(`/api/agent/v1/pages/${pageId}/components`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Idempotency-Key": crypto.randomUUID(),
    },
    data: {
      component_type: "Heading",
      slot_key: "default",
      props: { text, level: 2 },
    },
  });
  expect(response.status()).toBe(201);
}

async function humanWriteHeading(
  page: Page,
  siteId: string,
  workspaceId: string,
  pageId: string,
  text: string,
): Promise<void> {
  const csrf = await adminCsrf(page);
  const response = await page.request.post(
    `/api/editor/v1/sites/${siteId}/pages/${pageId}/composition/components`,
    {
      headers: {
        "X-CSRF-Token": csrf,
        "X-Editor-Workspace": workspaceId,
        "Idempotency-Key": crypto.randomUUID(),
      },
      data: {
        component_type: "Heading",
        slot_key: "default",
        order_key: 1,
        props: { text, level: 2 },
      },
    },
  );
  expect(response.status()).toBe(201);
}

async function reviewSnapshot(
  page: Page,
  siteId: string,
  workspaceId: string,
): Promise<{
  id: string;
  digest: string;
  baseSiteRevision: number;
  driftEqual: boolean;
  driftCurrent: number;
  manifestDigest: string;
}> {
  const response = await page.request.get(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/review/`,
  );
  expect(response.status()).toBe(200);
  const body = (await response.json()) as {
    snapshot: {
      id: string;
      digest: string;
      base_site_revision: number;
    };
    drift: { current_site_revision: number; equal: boolean };
    manifest: { manifest_digest: string };
  };
  return {
    id: body.snapshot.id,
    digest: body.snapshot.digest,
    baseSiteRevision: body.snapshot.base_site_revision,
    driftEqual: body.drift.equal,
    driftCurrent: body.drift.current_site_revision,
    manifestDigest: body.manifest.manifest_digest,
  };
}

async function acceptWorkspace(
  page: Page,
  siteId: string,
  workspaceId: string,
): Promise<void> {
  const review = await reviewSnapshot(page, siteId, workspaceId);
  const csrf = await adminCsrf(page);
  const response = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/accept/`,
    {
      headers: {
        "X-CSRF-Token": csrf,
        "Idempotency-Key": crypto.randomUUID(),
      },
      data: {
        snapshot_id: review.id,
        digest: review.digest,
        manifest_digest: review.manifestDigest,
        acknowledge_summary: true,
      },
    },
  );
  expect(response.status()).toBe(202);
  // ACCEPTED commits in the same reviewer transaction as the canonical
  // revision increment, so the status poll is the completion proof.
  const deadline = Date.now() + 240_000;
  for (;;) {
    const status = await workspaceStatus(page, siteId, workspaceId);
    if (status === "ACCEPTED") return;
    if (
      status === "CONFLICTED" ||
      status === "REVIEW" ||
      status === "DISCARDED" ||
      status === "ACTIVE"
    ) {
      throw new Error(`accept left workspace at ${status}`);
    }
    if (Date.now() > deadline) throw new Error(`timeout at status ${status}`);
    await page.waitForTimeout(500);
  }
}

test("freeze-review-snapshot-two-workspace-revision-coherence", async ({ page }) => {
  test.setTimeout(600_000);
  const credential = secrets();
  const project = composeProject();
  const failures = observe(page);

  await login(page, credential);
  await expectAdminUsable(page);
  const { siteId, siteKey } = seedCoherenceSite(project);
  expect(siteRevision(project, siteId)).toBe(0);

  // ------------------------------------------- W1: created/edited at A
  // The W1 edit is the ordered HUMAN editorial proof: an authenticated
  // admin session writes through the Editor API with the workspace
  // binding (069 authorization) - no test-only actor, no hidden
  // canonical mutation.
  const adminId = psql(
    project,
    "SELECT id FROM control.user_account WHERE local_username_normalized = 'compose.admin'",
  );
  expect(adminId).toMatch(/^[0-9a-f-]{36}$/i);
  const ws1 = await createAgentWorkspace(page, siteId, `083/4 W1 ${randomHex(4)}`);
  const token1 = await createCapability(page, siteId, ws1);
  const homeId1 = await homePageId(page, token1);
  await humanWriteHeading(page, siteId, ws1, homeId1, "083/4 W1 marker");
  // The human write is a real COW change bound to W1's session, visible
  // to the same authenticated human through the Editor API.
  const humanRead = await page.request.get(
    `/api/editor/v1/sites/${siteId}/pages/${homeId1}/composition/`,
    { headers: { "X-Editor-Workspace": ws1 } },
  );
  expect(humanRead.status()).toBe(200);
  const humanNodes = (await humanRead.json()) as Array<{
    component_type: string;
    props: Record<string, unknown>;
  }>;
  expect(
    humanNodes.some(
      (node) =>
        node.component_type === "Heading" &&
        (node.props as { text?: string }).text === "083/4 W1 marker",
    ),
  ).toBe(true);
  // The 069 authorization surface records the human mutation.
  expect(
    psql(
      project,
      `SELECT bool_and(human_user_id = '${adminId}' AND site_id = '${siteId}')
         AND count(*) >= 1
       FROM audit.human_editor_mutation
       WHERE workspace_id = '${ws1}'`,
    ),
  ).toBe("t");
  expect(
    Number(
      psql(
        project,
        `SELECT base_site_revision FROM control.workspace
          WHERE id = '${ws1}'`,
      ),
    ),
  ).toBe(0);

  // --------------------------------- W2 publishes an unrelated change B
  const ws2 = await createAgentWorkspace(page, siteId, `083/4 W2 ${randomHex(4)}`);
  const token2 = await createCapability(page, siteId, ws2);
  const homeId2 = await homePageId(page, token2);
  await writeHeading(page, homeId2, token2, "083/4 W2 marker");
  const frozen2 = await freezeWorkspace(page, siteId, ws2);
  expect(frozen2.status).toBe(202);
  await waitForReview(page, project, siteId, ws2);
  await acceptWorkspace(page, siteId, ws2);
  expect(siteRevision(project, siteId)).toBe(1);

  // ------------------------------- W1 freezes after B: review base is B
  const frozen1 = await freezeWorkspace(page, siteId, ws1);
  expect(frozen1.status).toBe(202);
  await waitForReview(page, project, siteId, ws1);

  const snapshotBase = psql(
    project,
    `SELECT payload ->> 'base_site_revision'
      FROM control.review_snapshot WHERE workspace_id = '${ws1}'`,
  );
  expect(snapshotBase).toBe("1");
  const digestValid = psql(
    project,
    `SELECT digest = encode(sha256(convert_to(
       control.slaif_canonical_jsonb_text(payload), 'UTF8')), 'hex')
      FROM control.review_snapshot WHERE workspace_id = '${ws1}'`,
  );
  expect(digestValid).toBe("t");
  const w1InPayload = psql(
    project,
    `SELECT jsonb_path_exists(payload,
       '$.pages[*].nodes[*].** ? (@.component_type == "Heading"
         && @.props.text == "083/4 W1 marker")')
      FROM control.review_snapshot WHERE workspace_id = '${ws1}'`,
  );
  const w2InPayload = psql(
    project,
    `SELECT jsonb_path_exists(payload,
       '$.pages[*].nodes[*].** ? (@.component_type == "Heading"
         && @.props.text == "083/4 W2 marker")')
      FROM control.review_snapshot WHERE workspace_id = '${ws1}'`,
  );
  expect(w1InPayload).toBe("t");
  expect(w2InPayload).toBe("t");
  // W1's creation-time provenance is preserved (still A).
  expect(
    Number(
      psql(
        project,
        `SELECT base_site_revision FROM control.workspace
          WHERE id = '${ws1}'`,
      ),
    ),
  ).toBe(0);

  // Reviewed/current revisions agree before another publication.
  const review1 = await reviewSnapshot(page, siteId, ws1);
  expect(review1.baseSiteRevision).toBe(1);
  expect(review1.driftCurrent).toBe(1);
  expect(review1.driftEqual).toBe(true);

  // The real authenticated /review/<workspace>/ route renders the
  // coherent frozen content: base B's published heading plus W1's
  // human-edited overlay (stored-payload facts above complement this
  // rendered proof).
  await page.goto(`/review/${ws1}/`);
  const reviewBanner = page.locator(".review-banner");
  await expect(reviewBanner).toHaveAttribute("data-review-digest", review1.digest);
  await expect(reviewBanner).toHaveAttribute("data-review-equal", "true");
  // 083/5: the current head freezes v2 snapshots; the review route
  // renders them through the faithful frozen read (render mode
  // "review"), so the legacy v1 mapping's "preview" mode is no longer
  // the expected surface at the 076 head.
  await expect(page.locator("main.renderer-surface")).toHaveAttribute(
    "data-render-mode",
    "review",
  );
  await expect(
    page.getByRole("heading", { name: "Freeze coherence", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("083/4 W2 marker", { exact: true })).toBeVisible();
  await expect(page.getByText("083/4 W1 marker", { exact: true })).toBeVisible();

  // Public origin through NGINX: B's published content is public, W1's
  // overlay is still private.
  const publicSite = await page.request.get(`/s/${siteKey}`);
  expect(publicSite.status()).toBe(200);
  const publicHtml = await publicSite.text();
  expect(publicHtml).toContain("083/4 W2 marker");
  expect(publicHtml).not.toContain("083/4 W1 marker");
  expect(publicSite.headers()["cache-control"]).toBe(
    "private, no-cache, no-store, max-age=0, must-revalidate",
  );

  expect(failures(), "unexpected browser failure category").toEqual([]);
});

test("freeze-review-snapshot-faithful-frozen-review-v2", async ({ page }) => {
  test.setTimeout(300_000);
  const credential = secrets();
  const project = composeProject();
  const failures = observe(page);

  await login(page, credential);
  await expectAdminUsable(page);
  const siteId = await demoSiteId(page);

  // ------------------------- agent workspace with an explicit upload quota
  // L2_SITE_EDITOR: the fixture adds composition nodes, which need
  // component-structure:create (L2); L1_CONTENT_EDITOR allows the media
  // upload but fails closed on the component POSTs.
  const csrf = await adminCsrf(page);
  const workspaceResponse = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/`,
    {
      headers: { "X-CSRF-Token": csrf, "Idempotency-Key": crypto.randomUUID() },
      data: {
        title: `083/5 faithful review ${randomHex(4)}`,
        task_description: "Bounded faithful frozen review proof",
        delegation_preset: "L2_SITE_EDITOR",
        duration_hours: 1,
        request_quota: 200,
        mutation_quota: 50,
        delete_quota: 0,
        upload_quota: 2,
        browser_quota: 0,
        resource_constraints: {},
      },
    },
  );
  expect(workspaceResponse.status()).toBe(201);
  const workspaceBody = (await workspaceResponse.json()) as {
    workspace_id?: unknown;
  };
  const workspaceId = requiredString(workspaceBody.workspace_id, "workspace id");
  const capabilityResponse = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/capabilities/`,
    { headers: { "X-CSRF-Token": csrf, "Idempotency-Key": crypto.randomUUID() } },
  );
  expect(capabilityResponse.status()).toBe(201);
  const capability = (await capabilityResponse.json()) as { token?: unknown };
  const token = requiredString(capability.token, "capability token");
  const agentHeaders = { Authorization: `Bearer ${token}` } as const;
  const homeId = await homePageId(page, token);

  // ------------------------------------------------ agent media + components
  const pngDigest = sha256Hex(TINY_PNG);
  const upload = await page.request.post("/api/agent/v1/media/assets", {
    headers: { ...agentHeaders, "Idempotency-Key": crypto.randomUUID() },
    multipart: uploadForm(TINY_PNG, "faithful-proof.png", "image/png", {
      alt_text: "083/5 faithful review media",
    }),
  });
  expect(upload.status()).toBe(201);
  const uploadBody = (await upload.json()) as { record?: Record<string, unknown> };
  const mediaId = requiredString(uploadBody.record?.id, "media id");
  expect(uploadBody.record?.content_hash).toBe(pngDigest);

  const marker = `083/5 faithful marker ${randomHex(2)}`;
  const heading = await page.request.post(`/api/agent/v1/pages/${homeId}/components`, {
    headers: { ...agentHeaders, "Idempotency-Key": crypto.randomUUID() },
    data: {
      component_type: "Heading",
      slot_key: "default",
      props: { text: marker, level: 2 },
    },
  });
  expect(heading.status()).toBe(201);
  const image = await page.request.post(`/api/agent/v1/pages/${homeId}/components`, {
    headers: { ...agentHeaders, "Idempotency-Key": crypto.randomUUID() },
    data: {
      component_type: "Image",
      slot_key: "default",
      props: { mediaId, alt: "083/5 faithful review media" },
    },
  });
  expect(image.status()).toBe(201);

  // ------------------------------------------------------------- freeze + wait
  const frozen = await freezeWorkspace(page, siteId, workspaceId);
  expect(frozen.status).toBe(202);
  await waitForReview(page, project, siteId, workspaceId);
  const snapshotId = psql(
    project,
    `SELECT id FROM control.review_snapshot
      WHERE workspace_id = '${workspaceId}'`,
  );
  expect(snapshotId).toMatch(/^[0-9a-f-]{36}$/i);

  // ------------------------- stored payload: v2 state, pins, frozen media
  expect(
    psql(
      project,
      `SELECT payload->>'state_version'
        FROM control.review_snapshot WHERE id = '${snapshotId}'`,
    ),
  ).toBe("review-snapshot/v2");
  expect(
    psql(
      project,
      // PostgreSQL: || and -> share precedence (left-associative), so each
      // jsonb extraction is parenthesized before concatenation.
      `SELECT (payload->'workspace_versions'->>'puck') || '|' ||
             (payload->'workspace_versions'->>'catalog') || '|' ||
             (payload->'workspace_versions'->>'composition_schema')
        FROM control.review_snapshot WHERE id = '${snapshotId}'`,
    ),
  ).toBe("0.20.2|catalog-v1|site-composition/v1");
  expect(
    psql(
      project,
      // JSONPath: quote the UUID member (a bare uuid-like key starting with a
      // digit parses as a numeric literal), and ::text for the boolean || text
      // concatenation (there is no boolean || boolean operator).
      `SELECT jsonb_path_exists(payload,
         '$.media."${mediaId}"')::text || jsonb_path_exists(payload,
         '$.media_inventory[*] ? (@.id == "${mediaId}")')::text
        FROM control.review_snapshot WHERE id = '${snapshotId}'`,
    ),
  ).toBe("truetrue");

  // ------------------------- read model: exact v2 shape through the API
  const reviewResponse = await page.request.get(
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
  // The exact 18-key v2 normalized state (the six v2 additions over the
  // v1 document: workspace_versions, page_compositions, content,
  // proposals, media_inventory, plus the retained v1 facts).
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

  // ------------------------- faithful browser render of the v2 snapshot
  await page.goto(`/review/${workspaceId}/`);
  const reviewBanner = page.locator(".review-banner");
  await expect(reviewBanner).toHaveAttribute(
    "data-review-digest",
    reviewDoc.snapshot.digest,
  );
  await expect(reviewBanner).toHaveAttribute("data-review-equal", "true");
  // The faithful frozen read reports the review render mode (the legacy
  // v1 web mapping reported "preview").
  await expect(page.locator("main.renderer-surface")).toHaveAttribute(
    "data-render-mode",
    "review",
  );
  await expect(page.getByRole("heading", { name: marker, exact: true })).toBeVisible();
  const frozenMediaUrl = `/media/v1/review/${snapshotId}/assets/${mediaId}/content`;
  const reviewImage = page.locator(`img[src="${frozenMediaUrl}"]`);
  await expect(reviewImage).toBeVisible();
  await expect(reviewImage).toHaveCount(1);

  // ------------------------- frozen private bytes through the public path
  const mediaResponse = await page.request.get(frozenMediaUrl);
  expect(mediaResponse.status()).toBe(200);
  expect(mediaResponse.headers()["content-type"]).toBe("image/png");
  expect(Buffer.from(await mediaResponse.body()).equals(TINY_PNG)).toBe(true);

  // ------------------------- refusal without a human session
  // No credentials at all -> 401 (authentication boundary, matching the
  // integration contract for the frozen review byte route); a session that
  // is not authorized -> uniform 404 (no existence oracle).
  const browser = page.context().browser();
  if (!browser) throw new Error("browser context missing");
  const anonymous = await browser.newContext();
  const anonymousMedia = await anonymous.request.get(frozenMediaUrl);
  expect(anonymousMedia.status()).toBe(401);
  // No trailing slash: the slash-normalizing 308 would otherwise
  // precede the login 307 (same contract as the review-surface spec).
  const anonymousReview = await anonymous.request.get(`/review/${workspaceId}`, {
    maxRedirects: 0,
  });
  expect(anonymousReview.status()).toBe(307);
  expect(anonymousReview.headers()["location"]).toMatch(/\/login$/);
  await anonymous.close();

  // ------------------------- non-frozen workspace review is a uniform 404
  const activeResponse = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/`,
    {
      headers: { "X-CSRF-Token": csrf, "Idempotency-Key": crypto.randomUUID() },
      data: {
        title: `083/5 non-frozen ${randomHex(4)}`,
        delegation_preset: "L2_SITE_EDITOR",
      },
    },
  );
  expect(activeResponse.status()).toBe(201);
  const activeBody = (await activeResponse.json()) as { workspace_id: string };
  const activeReview = await page.request.get(
    `/api/control/v1/sites/${siteId}/workspaces/${activeBody.workspace_id}/review/`,
  );
  expect(activeReview.status()).toBe(404);
  const activeReviewPage = await page.request.get(
    `/review/${activeBody.workspace_id}/`,
  );
  expect(activeReviewPage.status()).toBe(404);

  expect(failures(), "unexpected browser failure category").toEqual([]);
});

// ---------------------------------------------------------------------
// 084/1 (public E2E half): one overlapping Heading edit reaches the real
// conflict gate through one same-workspace human re-review.
//
// W and X edit the SAME seeded Heading differently at revision A through
// real Agent HTTP PATCH (distinct capabilities, distinct operations).
// X is approved to canonical B through the real human accept; W's A
// approval then fails durably with SITE_REVISION_CHANGED. A human
// re-review of W (verified stale revision) atomically points the current
// review to a new W snapshot at B while the A snapshot and its evidence
// stay byte-for-byte. The old identity is refused without a new job, and
// approving W's B snapshot reaches the existing whole-session
// conflict_policy="error" boundary (BASE_ROW_CHANGED, CONFLICTED) with
// the public site unchanged through NGINX.
// ---------------------------------------------------------------------

async function patchAgentComponent(
  page: Page,
  componentId: string,
  token: string,
  props: Record<string, unknown>,
  expectedRowVersion: number,
): Promise<void> {
  const response = await page.request.patch(`/api/agent/v1/components/${componentId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      "Idempotency-Key": crypto.randomUUID(),
    },
    data: { props, expected_row_version: expectedRowVersion },
  });
  expect(response.status()).toBe(200);
}

async function pollWorkspaceStatus(
  page: Page,
  siteId: string,
  workspaceId: string,
  terminal: string[],
  timeoutMs: number,
): Promise<string> {
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    const status = await workspaceStatus(page, siteId, workspaceId);
    if (terminal.includes(status)) return status;
    if (Date.now() > deadline) throw new Error(`timeout at status ${status}`);
    await page.waitForTimeout(500);
  }
}

/**
 * Call the exact-id internal Render review route from inside the
 * compose web container (the same service the authenticated NGINX
 * review page uses server-side): the render service token from its
 * auth file, the real human session header, one exact snapshot id.
 * Fixture stack is disposable.  The human session value never enters
 * argv: the bare -e flags resolve it from the docker CLI child
 * process environment, and a child failure is rethrown sanitized
 * (the token file flow and the exact-id payload are unchanged).
 */
function internalRenderReview(
  project: string,
  humanSession: string,
  snapshotId: string,
): {
  status: number;
  body: {
    render_mode: string;
    composition: { nodes: readonly Record<string, unknown>[] };
  } | null;
} {
  const script = [
    'const fs = require("node:fs");',
    'const token = fs.readFileSync("/run/slaif-render-auth/render-token", "ascii").trim();',
    'fetch("http://render-api:8000/internal/render/v1/review", {',
    '  method: "POST",',
    "  headers: {",
    '    "content-type": "application/json",',
    '    "x-slaif-render-token": token,',
    '    "x-slaif-human-session": process.env.E2E_HUMAN_SESSION,',
    "  },",
    "  body: JSON.stringify({",
    '    authority: "review-proof.invalid",',
    '    path: "/",',
    "    snapshot_id: process.env.E2E_SNAPSHOT_ID,",
    "  }),",
    "}).then(async (res) => {",
    "  const text = await res.text();",
    '  process.stdout.write(String(res.status) + "\\n" + text);',
    "}).catch(() => {",
    '  process.stdout.write("0\\n");',
    "  process.exit(1);",
    "});",
  ].join("\n");
  let output: string;
  try {
    output = docker(
      project,
      [
        "exec",
        "-e",
        "E2E_HUMAN_SESSION",
        "-e",
        "E2E_SNAPSHOT_ID",
        `${project}-web-1`,
        "node",
        "-e",
        script,
      ],
      {
        E2E_HUMAN_SESSION: humanSession,
        E2E_SNAPSHOT_ID: snapshotId,
      },
    );
  } catch {
    throw new Error("internal render review exec failed");
  }
  const newline = output.indexOf("\n");
  if (newline < 0) throw new Error("internal render review output malformed");
  const status = Number(output.slice(0, newline));
  let body: {
    render_mode: string;
    composition: { nodes: readonly Record<string, unknown>[] };
  } | null;
  try {
    body = JSON.parse(output.slice(newline + 1)) as {
      render_mode: string;
      composition: { nodes: readonly Record<string, unknown>[] };
    } | null;
  } catch {
    body = null;
  }
  return { status, body };
}

function compositionHeadingTexts(nodes: readonly Record<string, unknown>[]): string[] {
  const texts: string[] = [];
  for (const node of nodes) {
    if (node.component_type === "Heading") {
      const props = node.props;
      if (props && typeof props === "object") {
        const text = (props as { text?: unknown }).text;
        if (typeof text === "string") texts.push(text);
      }
    }
    const children = node.children;
    if (Array.isArray(children)) {
      texts.push(
        ...compositionHeadingTexts(children as readonly Record<string, unknown>[]),
      );
    }
  }
  return texts;
}

test("freeze-review-snapshot-same-workspace-overlap-re-review", async ({ page }) => {
  test.setTimeout(900_000);
  const credential = secrets();
  const project = composeProject();
  const failures = observe(page);
  const W_TEXT = "084/1 W overlap edit";
  const X_TEXT = "084/1 X overlap edit";

  await login(page, credential);
  await expectAdminUsable(page);
  const { siteId, siteKey } = seedCoherenceSite(project);
  const headingId = psql(
    project,
    `SELECT id FROM content.page_composition_base
      WHERE site_id = '${siteId}' AND component_type = 'Heading'`,
  );
  expect(headingId).toMatch(/^[0-9a-f-]{36}$/i);
  const A = siteRevision(project, siteId);
  expect(A).toBe(0);
  const csrf = await adminCsrf(page);

  // ----------------------------- W and X edit the SAME Heading at A
  const wWs = await createAgentWorkspace(page, siteId, `084/1 W ${randomHex(4)}`);
  const wToken = await createCapability(page, siteId, wWs);
  const xWs = await createAgentWorkspace(page, siteId, `084/1 X ${randomHex(4)}`);
  const xToken = await createCapability(page, siteId, xWs);
  await patchAgentComponent(page, headingId, wToken, { level: 2, text: W_TEXT }, 1);
  await patchAgentComponent(page, headingId, xToken, { level: 1, text: X_TEXT }, 1);

  // Human freezes both against A (real human definer + worker).
  const frozenW = await freezeWorkspace(page, siteId, wWs);
  expect(frozenW.status).toBe(202);
  const frozenX = await freezeWorkspace(page, siteId, xWs);
  expect(frozenX.status).toBe(202);
  await waitForReview(page, project, siteId, wWs);
  await waitForReview(page, project, siteId, xWs);

  const wReview = await reviewSnapshot(page, siteId, wWs);
  const xReview = await reviewSnapshot(page, siteId, xWs);
  expect(wReview.baseSiteRevision).toBe(A);
  expect(xReview.baseSiteRevision).toBe(A);
  expect(wReview.driftEqual).toBe(true);
  expect(xReview.driftEqual).toBe(true);
  const wPayloadHash = (id: string): string =>
    psql(
      project,
      `SELECT encode(sha256(convert_to(
         control.slaif_canonical_jsonb_text(payload), 'UTF8')), 'hex')
        FROM control.review_snapshot WHERE id = '${id}'`,
    );
  const wPayloadBefore = wPayloadHash(wReview.id);
  expect(
    psql(
      project,
      `SELECT jsonb_path_exists(payload,
         '$.page_compositions[*] ? (@.id == "${headingId}"
           && @.props.text == "${W_TEXT}")')
        FROM control.review_snapshot WHERE id = '${wReview.id}'`,
    ),
  ).toBe("t");
  expect(
    psql(
      project,
      `SELECT jsonb_path_exists(payload,
         '$.page_compositions[*] ? (@.id == "${headingId}"
           && @.props.text == "${X_TEXT}")')
        FROM control.review_snapshot WHERE id = '${xReview.id}'`,
    ),
  ).toBe("t");

  // The real authenticated NGINX review renderer for W's A review:
  // the exact banner digest, coherent drift, W's overlay rendered,
  // X's (other-workspace) overlay absent.
  await page.goto(`/review/${wWs}/`);
  const reviewBanner = page.locator(".review-banner");
  await expect(reviewBanner).toHaveAttribute("data-review-digest", wReview.digest);
  await expect(reviewBanner).toHaveAttribute("data-review-equal", "true");
  await expect(page.locator("main.renderer-surface")).toHaveAttribute(
    "data-render-mode",
    "review",
  );
  await expect(page.getByRole("heading", { name: W_TEXT, exact: true })).toBeVisible();
  await expect(page.getByText(X_TEXT, { exact: true })).toHaveCount(0);

  // ------------------------- approve X: canonical B reflects X only
  await acceptWorkspace(page, siteId, xWs);
  const B = siteRevision(project, siteId);
  expect(B).toBe(A + 1);
  expect(
    psql(
      project,
      `SELECT (props ->> 'text') || '|' || row_version::text
        FROM content.page_composition_base WHERE id = '${headingId}'`,
    ),
  ).toBe(`${X_TEXT}|2`);

  // W's A-snapshot approval fails durably at the site-revision gate.
  const auditBefore = Number(psql(project, `SELECT count(*) FROM audit.promotion`));
  const outboxBefore = Number(
    psql(project, `SELECT count(*) FROM control.cache_outbox`),
  );
  const staleAccept = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/${wWs}/accept/`,
    {
      headers: { "X-CSRF-Token": csrf, "Idempotency-Key": crypto.randomUUID() },
      data: {
        snapshot_id: wReview.id,
        digest: wReview.digest,
        manifest_digest: wReview.manifestDigest,
        acknowledge_summary: true,
      },
    },
  );
  expect(staleAccept.status()).toBe(202);
  // The worker's durable outcome returns W to read-only review; the
  // shared accept helper treats that as a hard failure, so poll the
  // status tolerantly here.
  expect(await pollWorkspaceStatus(page, siteId, wWs, ["REVIEW"], 240_000)).toBe(
    "REVIEW",
  );
  expect(
    psql(
      project,
      `SELECT status || '|' || coalesce(error, '') FROM control.review_job
        WHERE workspace_id = '${wWs}' AND job_kind = 'ACCEPT'
        ORDER BY created_at DESC LIMIT 1`,
    ),
  ).toBe("FAILED|SITE_REVISION_CHANGED");
  expect(siteRevision(project, siteId)).toBe(B);
  expect(
    psql(
      project,
      `SELECT (props ->> 'text') || '|' || row_version::text
        FROM content.page_composition_base WHERE id = '${headingId}'`,
    ),
  ).toBe(`${X_TEXT}|2`);
  expect(Number(psql(project, `SELECT count(*) FROM audit.promotion`))).toBe(
    auditBefore,
  );
  expect(Number(psql(project, `SELECT count(*) FROM control.cache_outbox`))).toBe(
    outboxBefore,
  );

  // ------------------------- re-review gate negatives on the new route
  const reReviewUrl = `/api/control/v1/sites/${siteId}/workspaces/${wWs}/re-review/`;
  const adminSession = (await page.context().cookies()).find(
    (cookie) => cookie.name === "slaif_session",
  );
  if (!adminSession) throw new Error("admin session cookie missing");
  const csrfless = await page.request.post(reReviewUrl, {
    headers: { cookie: `slaif_session=${adminSession.value}` },
    data: { snapshot_id: wReview.id },
  });
  expect(csrfless.status()).toBe(403);
  expect((await csrfless.json()) as { error: unknown }).toMatchObject({
    error: { code: "AUTHORIZATION_DENIED" },
  });

  const nonmember = seedHumanSession(project, credential.fixtureUserOne);
  const nonmemberReReview = async (id: string) => {
    const response = await page.request.post(
      `/api/control/v1/sites/${siteId}/workspaces/${id}/re-review/`,
      {
        headers: {
          cookie: `${nonmember.cookie}; ${nonmember.csrfCookie}`,
          "X-CSRF-Token": nonmember.csrfToken,
        },
        data: { snapshot_id: wReview.id },
      },
    );
    const body = (await response.json()) as { error: { code: string } };
    return { status: response.status(), code: body.error.code };
  };
  const nonmemberReference = await nonmemberReReview(wWs);
  expect(nonmemberReference).toEqual({
    status: 404,
    code: "RESOURCE_NOT_FOUND",
  });
  expect(await nonmemberReReview(crypto.randomUUID())).toEqual(nonmemberReference);

  const wrongSite = await page.request.post(
    `/api/control/v1/sites/${crypto.randomUUID()}/workspaces/${wWs}/re-review/`,
    {
      headers: { "X-CSRF-Token": csrf },
      data: { snapshot_id: wReview.id },
    },
  );
  expect(wrongSite.status()).toBe(404);
  expect((await wrongSite.json()) as { error: unknown }).toMatchObject({
    error: { code: "RESOURCE_NOT_FOUND" },
  });

  // A named snapshot that is not the trusted current pointer is a typed
  // stale refusal, never a transition to a different (older) review.
  const staleNamed = await page.request.post(reReviewUrl, {
    headers: { "X-CSRF-Token": csrf, "Idempotency-Key": crypto.randomUUID() },
    data: { snapshot_id: xReview.id },
  });
  expect(staleNamed.status()).toBe(409);
  expect((await staleNamed.json()) as { error: unknown }).toMatchObject({
    error: { code: "RESOURCE_CONFLICT" },
  });

  // The strict body rejects anything beyond the exact one field.
  const overbodied = await page.request.post(reReviewUrl, {
    headers: { "X-CSRF-Token": csrf, "Idempotency-Key": crypto.randomUUID() },
    data: { snapshot_id: wReview.id, bogus: true },
  });
  expect(overbodied.status()).toBe(422);

  // ------------------------------ the real human re-review of W (verified)
  const reReview = await page.request.post(reReviewUrl, {
    headers: { "X-CSRF-Token": csrf, "Idempotency-Key": crypto.randomUUID() },
    data: { snapshot_id: wReview.id },
  });
  expect(reReview.status()).toBe(202);
  const reReviewBody = (await reReview.json()) as { job_id: string; status: string };
  expect(reReviewBody.status).toBe("FREEZING");
  // Re-review re-enters FREEZING while the retained A snapshot is
  // still visible under the unchanged pointer, so the first-freeze
  // wait invariant does not apply; the atomic (status, pointer) pair
  // read is the re-review completion proof instead.
  await waitForReReviewCompletion(page, project, wWs, wReview.id);

  const snapshotIds = psql(
    project,
    `SELECT id FROM control.review_snapshot
      WHERE workspace_id = '${wWs}' ORDER BY created_at, id`,
  )
    .split("\n")
    .filter(Boolean);
  expect(snapshotIds).toHaveLength(2);
  const w2Review = await reviewSnapshot(page, siteId, wWs);
  expect(w2Review.id).not.toBe(wReview.id);
  expect(w2Review.baseSiteRevision).toBe(B);
  expect(w2Review.driftEqual).toBe(true);
  expect(
    psql(
      project,
      `SELECT review_snapshot_id::text FROM control.workspace WHERE id = '${wWs}'`,
    ),
  ).toBe(w2Review.id);
  expect(
    psql(
      project,
      `SELECT digest = encode(sha256(convert_to(
         control.slaif_canonical_jsonb_text(payload), 'UTF8')), 'hex')
        FROM control.review_snapshot WHERE id = '${w2Review.id}'`,
    ),
  ).toBe("t");
  // W's pending edit is the review content at B: in the workspace view
  // the overlay covers the canonical B row of the shared component.
  expect(
    psql(
      project,
      `SELECT jsonb_path_exists(payload,
         '$.page_compositions[*] ? (@.id == "${headingId}"
           && @.props.text == "${W_TEXT}")')
        FROM control.review_snapshot WHERE id = '${w2Review.id}'`,
    ),
  ).toBe("t");
  // The A snapshot and its stored payload are retained byte-for-byte.
  expect(wPayloadHash(wReview.id)).toBe(wPayloadBefore);
  expect(
    psql(
      project,
      `SELECT digest = encode(sha256(convert_to(
         control.slaif_canonical_jsonb_text(payload), 'UTF8')), 'hex')
        FROM control.review_snapshot WHERE id = '${wReview.id}'`,
    ),
  ).toBe("t");

  // The real authenticated NGINX review renderer now follows the
  // trusted pointer to the B review: the exact banner digest,
  // coherent drift, W's overlay rendered over the B base.
  await page.goto(`/review/${wWs}/`);
  const reviewBanner2 = page.locator(".review-banner");
  await expect(reviewBanner2).toHaveAttribute("data-review-digest", w2Review.digest);
  await expect(reviewBanner2).toHaveAttribute("data-review-equal", "true");
  await expect(page.locator("main.renderer-surface")).toHaveAttribute(
    "data-render-mode",
    "review",
  );
  await expect(page.getByRole("heading", { name: W_TEXT, exact: true })).toBeVisible();
  await expect(page.getByText(X_TEXT, { exact: true })).toHaveCount(0);

  // The exact-id internal Render review path (the same authorized
  // route the review page uses server-side) still serves the EARLIER
  // frozen A review after the pointer moved to B, and serves the B
  // review too: the earlier frozen page remains available.
  const aRender = internalRenderReview(project, adminSession.value, wReview.id);
  expect(aRender.status).toBe(200);
  expect(aRender.body?.render_mode).toBe("review");
  const aTexts = compositionHeadingTexts(aRender.body?.composition.nodes ?? []);
  expect(aTexts).toContain(W_TEXT);
  expect(aTexts).not.toContain(X_TEXT);
  const bRender = internalRenderReview(project, adminSession.value, w2Review.id);
  expect(bRender.status).toBe(200);
  expect(bRender.body?.render_mode).toBe("review");
  const bTexts = compositionHeadingTexts(bRender.body?.composition.nodes ?? []);
  expect(bTexts).toContain(W_TEXT);
  expect(bTexts).not.toContain(X_TEXT);

  // Retained Heading facts: the unqualified read follows the trusted
  // pointer; the exact prior snapshot still renders with its ORIGINAL
  // evidence (both snapshots reviewed the same operation).
  const effectsNow = await page.request.get(
    `/api/control/v1/sites/${siteId}/workspaces/${wWs}/review/heading-effects/`,
  );
  expect(effectsNow.status()).toBe(200);
  const effectsNowBody = (await effectsNow.json()) as {
    status: string;
    snapshot_id: string;
    facts: unknown[];
  };
  expect(effectsNowBody.status).toBe("captured");
  expect(effectsNowBody.snapshot_id).toBe(w2Review.id);
  const effectsOld = await page.request.get(
    `/api/control/v1/sites/${siteId}/workspaces/${wWs}/review/heading-effects/` +
      `?snapshot_id=${wReview.id}`,
  );
  expect(effectsOld.status()).toBe(200);
  const effectsOldBody = (await effectsOld.json()) as {
    status: string;
    snapshot_id: string;
    facts: unknown[];
  };
  expect(effectsOldBody.status).toBe("captured");
  expect(effectsOldBody.snapshot_id).toBe(wReview.id);
  expect(effectsOldBody.facts).toEqual(effectsNowBody.facts);

  // ------------------------- the old identity is refused without a job
  const acceptJobCount = () =>
    Number(
      psql(
        project,
        `SELECT count(*) FROM control.review_job
          WHERE workspace_id = '${wWs}' AND job_kind = 'ACCEPT'`,
      ),
    );
  const jobsBeforeOld = acceptJobCount();
  const oldIdentity = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/${wWs}/accept/`,
    {
      headers: { "X-CSRF-Token": csrf, "Idempotency-Key": crypto.randomUUID() },
      data: {
        snapshot_id: wReview.id,
        digest: wReview.digest,
        manifest_digest: wReview.manifestDigest,
        acknowledge_summary: true,
      },
    },
  );
  expect(oldIdentity.status()).toBe(404);
  expect(acceptJobCount()).toBe(jobsBeforeOld);

  // --------- approving W's B snapshot reaches the existing conflict boundary
  const w2Accept = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/${wWs}/accept/`,
    {
      headers: { "X-CSRF-Token": csrf, "Idempotency-Key": crypto.randomUUID() },
      data: {
        snapshot_id: w2Review.id,
        digest: w2Review.digest,
        manifest_digest: w2Review.manifestDigest,
        acknowledge_summary: true,
      },
    },
  );
  expect(w2Accept.status()).toBe(202);
  expect(await pollWorkspaceStatus(page, siteId, wWs, ["CONFLICTED"], 240_000)).toBe(
    "CONFLICTED",
  );
  expect(
    psql(
      project,
      `SELECT status || '|' || coalesce(error, '') FROM control.review_job
        WHERE workspace_id = '${wWs}' AND job_kind = 'ACCEPT'
        ORDER BY created_at DESC LIMIT 1`,
    ),
  ).toBe("FAILED|BASE_ROW_CHANGED");
  expect(siteRevision(project, siteId)).toBe(B);
  expect(
    psql(
      project,
      `SELECT (props ->> 'text') || '|' || row_version::text
        FROM content.page_composition_base WHERE id = '${headingId}'`,
    ),
  ).toBe(`${X_TEXT}|2`);
  expect(Number(psql(project, `SELECT count(*) FROM audit.promotion`))).toBe(
    auditBefore,
  );
  expect(Number(psql(project, `SELECT count(*) FROM control.cache_outbox`))).toBe(
    outboxBefore,
  );

  // Public origin through NGINX: X's edit is public, W's is not.
  const publicSite = await page.request.get(`/s/${siteKey}`);
  expect(publicSite.status()).toBe(200);
  const publicHtml = await publicSite.text();
  expect(publicHtml).toContain(X_TEXT);
  expect(publicHtml).not.toContain(W_TEXT);

  expect(failures(), "unexpected browser failure category").toEqual([]);
});
