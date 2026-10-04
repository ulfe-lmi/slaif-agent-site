import { execFileSync } from "node:child_process";

import { createHash } from "node:crypto";

import { expect, test, type Page } from "@playwright/test";

import { expectAdminUsable, login, observe, secrets } from "./support";

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
  const hex = (value: Uint8Array) =>
    Array.from(value, (item) => item.toString(16).padStart(2, "0")).join("");
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
    const status = await workspaceStatus(page, siteId, workspaceId);
    if (status === "FREEZING") {
      freezingSamples += 1;
      // While the workspace is observably FREEZING, no snapshot may exist.
      expect(
        Number(
          psql(
            project,
            `SELECT count(*) FROM control.review_snapshot
              WHERE workspace_id = '${workspaceId}'`,
          ),
        ),
      ).toBe(0);
    }
    if (status === "REVIEW") return { freezingSamples };
    expect(["ACTIVE", "FREEZING"]).toContain(status);
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
