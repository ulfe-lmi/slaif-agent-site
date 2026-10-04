import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";

import { expect, test, type Page } from "@playwright/test";

import { expectAdminUsable, login, observe, secrets } from "./support";

const AGENT_HEADING_TEXT = "081 Agent workspace heading";

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
 * Seed one human session for an OIDC fixture user (they cannot use the local
 * /login flow) and return the exact session cookie the trusted server expects.
 */
function seedHumanSession(project: string, userId: string): string {
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
  return `slaif_session=sas2_session_${publicHex}_${b64url(sessionSecret)}`;
}

function seedAgentWorkspace(
  project: string,
  siteId: string,
  ownerId: string,
  status: "ACTIVE" | "REVOKED",
  expiresPast: boolean,
): string {
  const workspaceId = crypto.randomUUID();
  psql(
    project,
    `INSERT INTO control.workspace
       (id, site_id, created_by, delegator_id, actor_type, title,
        task_description, delegation_preset, effective_scopes, status,
        expires_at, created_at)
     VALUES ('${workspaceId}'::uuid, '${siteId}'::uuid, '${ownerId}'::uuid,
             '${ownerId}'::uuid, 'AGENT', '081 E2E negative fixture', '',
             'L2_SITE_EDITOR', '[]'::jsonb, '${status}',
             CURRENT_TIMESTAMP ${expiresPast ? "- interval '1 hour'" : "+ interval '1 hour'"},
             now())`,
  );
  return workspaceId;
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

type CompositionNode = {
  id: string;
  component_type: string;
  parent_id: string | null;
  slot_key: string;
  order_key: number;
  props: Record<string, unknown>;
};

function normalized(nodes: CompositionNode[]): CompositionNode[] {
  return [...nodes]
    .sort((a, b) => a.id.localeCompare(b.id))
    .map(({ id, component_type, parent_id, slot_key, order_key, props }) => ({
      id,
      component_type,
      parent_id,
      slot_key,
      order_key,
      props,
    }));
}

test("agent-workspace-puck-exact-workspace-convergence", async ({ page }) => {
  test.setTimeout(300_000);
  const credential = secrets();
  const project = composeProject();
  const sessionTitle = `081 E2E convergence ${test.info().project.name} ${randomHex(4)}`;
  const failures = observe(page);

  await login(page, credential);
  const siteId = await demoSiteId(page);
  const adminId = psql(
    project,
    "SELECT id FROM control.user_account WHERE local_username_normalized = 'compose.admin'",
  );
  expect(adminId).toMatch(/^[0-9a-f-]{36}$/i);

  const baseline = {
    humanWorkspaces: Number(
      psql(
        project,
        `SELECT count(*) FROM control.workspace
          WHERE site_id = '${siteId}' AND actor_type = 'HUMAN'
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
  };
  const canonicalHomeHeading = psql(
    project,
    `SELECT props FROM content.page_composition_base
      WHERE site_id = '${siteId}' AND component_type = 'Heading' AND order_key = 0`,
  );

  // ------------------------------------------- agent session + REST create
  await page.goto(`/admin/sites/${siteId}`);
  await expectAdminUsable(page);
  await page.getByLabel("Session title").fill(sessionTitle);
  await page.getByLabel("Delegation preset").selectOption("L2_SITE_EDITOR");
  await page.getByRole("button", { name: "Create Agent session" }).click();
  const secret = page.locator(".one-time-secret code");
  await expect(secret).toHaveText(/^sas2_[^\s]+$/);
  const token = (await secret.textContent()) ?? "";
  expect(token).toBeTruthy();
  await page.getByRole("button", { name: "Dismiss" }).click();
  await expect(page.locator(".one-time-secret")).toHaveCount(0);

  const workspacesResponse = await page.request.get(
    `/api/control/v1/sites/${siteId}/workspaces/`,
  );
  expect(workspacesResponse.status()).toBe(200);
  const workspaces = (await workspacesResponse.json()) as Array<{
    workspace_id: string;
    title: string;
    status: string;
  }>;
  const mine = workspaces.find((item) => item.title === sessionTitle);
  expect(mine).toBeTruthy();
  const agentWorkspaceId = mine!.workspace_id;
  expect(mine!.status).toBe("ACTIVE");

  const sessionRow = page
    .locator("li")
    .filter({ has: page.getByText(sessionTitle, { exact: true }) })
    .first();
  await expect(sessionRow).toContainText("ACTIVE");
  const openInPuck = sessionRow.getByRole("link", { name: "Open in Puck" });
  await expect(openInPuck).toBeVisible();
  expect((await openInPuck.getAttribute("href")) ?? "").toBe(
    `/admin/sites/${siteId}/workspaces/${agentWorkspaceId}/edit`,
  );

  const agentHeaders = { Authorization: `Bearer ${token}` };
  const agentSession = await page.request.get("/api/agent/v1/session", {
    headers: agentHeaders,
  });
  expect(agentSession.status()).toBe(200);
  const agentPages = await page.request.get("/api/agent/v1/pages", {
    headers: agentHeaders,
  });
  expect(agentPages.status()).toBe(200);
  const pages = (await agentPages.json()) as Array<{ id: string; slug: string }>;
  const home = pages.find((item) => item.slug === "home");
  expect(home).toBeTruthy();

  const created = await page.request.post(
    `/api/agent/v1/pages/${home!.id}/components`,
    {
      headers: { ...agentHeaders, "Idempotency-Key": crypto.randomUUID() },
      data: {
        component_type: "Heading",
        slot_key: "default",
        props: { text: AGENT_HEADING_TEXT, level: 2 },
      },
    },
  );
  expect(created.status()).toBe(201);
  const createdBody = (await created.json()) as {
    record: { id: string; component_type: string };
  };
  const agentHeadingId = createdBody.record.id;
  expect(agentHeadingId).toMatch(/^[0-9a-f-]{36}$/i);

  // ------------------------------------- human opens the exact workspace
  await openInPuck.click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    `Agent workspace: ${sessionTitle}`,
  );
  await expect(page.locator(".agent-workspace-banner__marker")).toHaveText(
    "Agent workspace",
  );
  const pageLink = page.getByRole("link", { name: /Edit in Puck/ });
  await expect(pageLink).toHaveCount(1);
  await expect(pageLink).toContainText("home");
  const editHref = (await pageLink.getAttribute("href")) ?? "";
  expect(editHref).toContain(`workspace=${agentWorkspaceId}`);
  expect(editHref).toContain(`workspaceTitle=${encodeURIComponent(sessionTitle)}`);

  await pageLink.click();
  await expect(
    page.getByRole("heading", { name: "Page composition", exact: true }).first(),
  ).toBeVisible();
  const banner = page.locator(".agent-workspace-banner");
  await expect(banner).toBeVisible();
  await expect(banner).toHaveText(new RegExp(`Agent workspace\\s*${sessionTitle}`));
  await expect(banner.locator(".agent-workspace-banner__marker")).toHaveText(
    "Agent workspace",
  );

  // The Agent-created component is visible in the exact workspace.
  await expect(page.getByText(AGENT_HEADING_TEXT).first()).toBeVisible();
  await expect(page.locator(".puck-trusted-component")).toHaveCount(3);

  // ------------------------------------------------ human reorders + saves
  // Puck wraps each component in its own data-puck-component div; the
  // trusted component div carries the same attribute once per node, so
  // order is read from those elements only.
  const componentOrder = () =>
    page
      .locator(".puck-trusted-component[data-puck-component]")
      .evaluateAll((items) =>
        items.map((item) => item.getAttribute("data-puck-component")),
      );
  await expect.poll(componentOrder).toContain(agentHeadingId);
  const orderBefore = await componentOrder();
  expect(orderBefore.indexOf(agentHeadingId)).toBe(orderBefore.length - 1);

  // Click the rendered Agent heading (the last top-level component).
  await page.locator(".puck-trusted-component").last().click();
  const moveUp = page.getByRole("button", { name: "Move up", exact: true });
  const moveDown = page.getByRole("button", { name: "Move down", exact: true });
  await expect(moveUp).toBeEnabled();
  await expect(moveDown).toBeDisabled();
  const save = page.waitForResponse(
    (response) =>
      response.request().method() !== "GET" &&
      response.url().includes(`/api/editor/v1/sites/${siteId}/pages/`) &&
      response.url().includes("/composition/"),
  );
  await moveUp.click();
  await expect
    .poll(() => componentOrder().then((order) => order.indexOf(agentHeadingId)))
    .toBe(orderBefore.length - 2);
  await page.getByRole("button", { name: "Save composition" }).click();
  const saved = await save;
  expect(saved.status()).toBe(200);
  await expect(
    page.getByText("Composition saved and reloaded from the server.", {
      exact: true,
    }),
  ).toBeVisible();

  // ----------------------------------------------------------- reload + reads
  await page.reload();
  await expect(banner).toBeVisible();
  await expect(page.locator(".puck-trusted-component")).toHaveCount(3);
  await expect(page.getByText(AGENT_HEADING_TEXT).first()).toBeVisible();

  const compositionPath = `/api/editor/v1/sites/${siteId}/pages/${home!.id}/composition/`;
  const humanRead = await page.request.get(compositionPath, {
    headers: { "X-Editor-Workspace": agentWorkspaceId },
  });
  expect(humanRead.status()).toBe(200);
  const humanNodes = (await humanRead.json()) as CompositionNode[];
  expect(humanNodes).toHaveLength(3);
  expect(humanNodes.find((node) => node.id === agentHeadingId)).toMatchObject({
    component_type: "Heading",
    parent_id: null,
    slot_key: "default",
    order_key: 1,
    props: { text: AGENT_HEADING_TEXT, level: 2 },
  });

  const agentRead = await page.request.get(
    `/api/agent/v1/pages/${home!.id}/components`,
    { headers: agentHeaders },
  );
  expect(agentRead.status()).toBe(200);
  const agentNodes = (await agentRead.json()) as CompositionNode[];
  expect(normalized(agentNodes)).toEqual(normalized(humanNodes));

  // -------------------------------------------------------------- preview
  const previewResponse = await page.goto(`/preview/${agentWorkspaceId}/s/demo/`);
  expect(previewResponse?.status()).toBe(200);
  await expect(page.getByText(AGENT_HEADING_TEXT).first()).toBeVisible();

  // ----------------------------------------------------------- canonical
  const canonicalResponse = await page.goto("/s/demo/");
  expect(canonicalResponse?.status()).toBe(200);
  await expect(page.getByText(AGENT_HEADING_TEXT)).toHaveCount(0);
  // The site page title (h1#page-title) and the canonical Heading
  // component (h2.renderer-heading) share the fixture text, so target the
  // level-2 composition heading specifically.
  await expect(
    page.getByRole("heading", { name: "SLAIF Demo Site", level: 2 }),
  ).toBeVisible();

  // ------------------------------------------------------------- database
  expect(
    Number(
      psql(
        project,
        `SELECT count(*) FROM control.workspace
          WHERE site_id = '${siteId}' AND actor_type = 'HUMAN'
            AND created_by = '${adminId}'`,
      ),
    ),
  ).toBe(baseline.humanWorkspaces);
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
    psql(
      project,
      `SELECT props FROM content.page_composition_base
        WHERE site_id = '${siteId}' AND component_type = 'Heading' AND order_key = 0`,
    ),
  ).toBe(canonicalHomeHeading);
  expect(
    Number(
      psql(
        project,
        `SELECT count(*) FROM content.page_composition_changes
          WHERE session_id = '${agentWorkspaceId}'`,
      ),
    ),
  ).toBeGreaterThan(0);
  expect(
    psql(
      project,
      `SELECT bool_and(human_user_id = '${adminId}' AND site_id = '${siteId}')
         AND count(*) >= 1
       FROM audit.human_editor_mutation
       WHERE workspace_id = '${agentWorkspaceId}'`,
    ),
  ).toBe("t");
  expect(
    Number(
      psql(
        project,
        `SELECT count(*) FROM control.human_editor_idempotency
          WHERE workspace_id = '${agentWorkspaceId}'`,
      ),
    ),
  ).toBeGreaterThan(0);
  expect(
    Number(
      psql(
        project,
        `SELECT count(*) FROM control.workspace
          WHERE site_id = '${siteId}' AND actor_type = 'AGENT'
            AND title = '${sessionTitle}'`,
      ),
    ),
  ).toBe(1);

  // --------------------------------------------- no capability in browser
  const storage = await page.evaluate(() => ({
    local: JSON.stringify(localStorage),
    session: JSON.stringify(sessionStorage),
    cookies: document.cookie,
  }));
  expect(storage.local).not.toContain(token);
  expect(storage.session).not.toContain(token);
  expect(storage.cookies).not.toContain(token);
  expect(failures(), "unexpected browser failure category").toEqual([]);
});

test("agent-workspace-puck-fail-closed-negatives", async ({ page }) => {
  test.setTimeout(180_000);
  const credential = secrets();
  const project = composeProject();
  const sessionTitle = `081 E2E negatives ${test.info().project.name} ${randomHex(4)}`;
  const failures = observe(page);

  await login(page, credential);
  const siteId = await demoSiteId(page);
  const adminId = psql(
    project,
    "SELECT id FROM control.user_account WHERE local_username_normalized = 'compose.admin'",
  );

  await page.goto(`/admin/sites/${siteId}`);
  await expectAdminUsable(page);
  await page.getByLabel("Session title").fill(sessionTitle);
  await page.getByLabel("Delegation preset").selectOption("L2_SITE_EDITOR");
  await page.getByRole("button", { name: "Create Agent session" }).click();
  await expect(page.locator(".one-time-secret code")).toHaveText(/^sas2_[^\s]+$/);
  await page.getByRole("button", { name: "Dismiss" }).click();
  await expect(page.locator(".one-time-secret")).toHaveCount(0);

  const workspacesResponse = await page.request.get(
    `/api/control/v1/sites/${siteId}/workspaces/`,
  );
  expect(workspacesResponse.status()).toBe(200);
  const workspaces = (await workspacesResponse.json()) as Array<{
    workspace_id: string;
    title: string;
    status: string;
  }>;
  const mine = workspaces.find((item) => item.title === sessionTitle);
  expect(mine).toBeTruthy();
  const agentWorkspaceId = mine!.workspace_id;
  const sessionRow = page
    .locator("li")
    .filter({ has: page.getByText(sessionTitle, { exact: true }) })
    .first();
  await expect(sessionRow.getByRole("link", { name: "Open in Puck" })).toBeVisible();

  const editorPages = (await (
    await page.request.get(`/api/editor/v1/sites/${siteId}/pages/`)
  ).json()) as Array<{ id: string; slug: string }>;
  const home = editorPages.find((item) => item.slug === "home");
  expect(home).toBeTruthy();
  const compositionPath = `/api/editor/v1/sites/${siteId}/pages/${home!.id}/composition/`;
  const componentPath = `${compositionPath}components`;

  async function denied(workspaceId: string): Promise<unknown> {
    const response = await page.request.get(compositionPath, {
      headers: { "X-Editor-Workspace": workspaceId },
    });
    expect(response.status()).toBe(503);
    const body = (await response.json()) as {
      error: { code: string; message: string };
    };
    return { code: body.error.code, message: body.error.message };
  }

  // The unknown-workspace denial is the non-leaking reference.
  const reference = await denied(crypto.randomUUID());
  expect(reference).toMatchObject({ code: "SERVICE_UNAVAILABLE" });

  // Positive pin: the owner reads the exact workspace successfully.
  const ownerRead = await page.request.get(compositionPath, {
    headers: { "X-Editor-Workspace": agentWorkspaceId },
  });
  expect(ownerRead.status()).toBe(200);

  // Forged workspace belonging to another site.
  const forgedSiteId = crypto.randomUUID();
  psql(
    project,
    `INSERT INTO control.site
       (id, site_key, display_name, default_locale, component_catalog_version, status)
     VALUES ('${forgedSiteId}'::uuid, '081neg-${randomHex(4)}', '081 Negative Fixture', 'en',
             'catalog-v1', 'ACTIVE')`,
  );
  const forgedWorkspaceId = seedAgentWorkspace(
    project,
    forgedSiteId,
    adminId,
    "ACTIVE",
    false,
  );
  expect(await denied(forgedWorkspaceId)).toEqual(reference);

  // Non-leaking workspace oracle per caller class. Headerless requests
  // keep the legacy HUMAN path (out of scope), so the oracle probes all
  // carry the header: the real workspace, an unknown one, and a forged
  // cross-site one must all yield the identical fail-closed denial for a
  // given caller.
  const probeDenial = async (
    cookie: string,
    workspaceId: string,
  ): Promise<{ status: number; code: string; message: string }> => {
    const response = await page.request.get(compositionPath, {
      headers: { "X-Editor-Workspace": workspaceId, cookie },
    });
    expect(response.status()).toBeGreaterThanOrEqual(400);
    const body = (await response.json()) as {
      error: { code: string; message: string };
    };
    return {
      status: response.status(),
      code: body.error.code,
      message: body.error.message,
    };
  };

  // Nonmember: fixture one has no demo-site membership; the site layer
  // denies before any workspace resolution.
  const nonmemberCookie = seedHumanSession(project, credential.fixtureUserOne);
  const nonmemberReference = await probeDenial(nonmemberCookie, agentWorkspaceId);
  expect(await probeDenial(nonmemberCookie, crypto.randomUUID())).toEqual(
    nonmemberReference,
  );
  expect(await probeDenial(nonmemberCookie, forgedWorkspaceId)).toEqual(
    nonmemberReference,
  );

  // Unauthorized member: fixture two is a demo-site VIEWER without the
  // workspace delegation; same uniform fail-closed denial across values.
  const unauthorizedCookie = seedHumanSession(project, credential.fixtureUserTwo);
  const unauthorizedReference = await probeDenial(unauthorizedCookie, agentWorkspaceId);
  expect(await probeDenial(unauthorizedCookie, crypto.randomUUID())).toEqual(
    unauthorizedReference,
  );
  expect(await probeDenial(unauthorizedCookie, forgedWorkspaceId)).toEqual(
    unauthorizedReference,
  );

  // Revoked and expired Agent workspaces.
  const revokedWorkspaceId = seedAgentWorkspace(
    project,
    siteId,
    adminId,
    "REVOKED",
    false,
  );
  expect(await denied(revokedWorkspaceId)).toEqual(reference);
  const expiredWorkspaceId = seedAgentWorkspace(
    project,
    siteId,
    adminId,
    "ACTIVE",
    true,
  );
  expect(await denied(expiredWorkspaceId)).toEqual(reference);

  // CSRF failure on a state-changing Agent-workspace mutation.
  const csrfless = await page.request.post(componentPath, {
    headers: {
      "Content-Type": "application/json",
      "X-Editor-Workspace": agentWorkspaceId,
      "Idempotency-Key": crypto.randomUUID(),
    },
    data: { component_type: "Section", slot_key: "default", props: {} },
  });
  expect(csrfless.status()).toBe(403);
  expect((await csrfless.json()) as { error: unknown }).toMatchObject({
    error: { code: "AUTHORIZATION_DENIED" },
  });

  // Crafted/malformed header values are rejected before any lookup.
  for (const crafted of [
    "not-a-uuid",
    "00000000-0000-4000-8000-0000000000001",
    "00000000000000000000000000000000",
  ]) {
    const response = await page.request.get(compositionPath, {
      headers: { "X-Editor-Workspace": crafted },
    });
    expect(response.status()).toBe(400);
    expect((await response.json()) as { error: unknown }).toMatchObject({
      error: { code: "MALFORMED_REQUEST" },
    });
  }

  // The denied flows created nothing.
  expect(
    psql(
      project,
      `SELECT count(*) FROM control.human_editor_idempotency
        WHERE workspace_id IN ('${forgedWorkspaceId}', '${revokedWorkspaceId}',
                               '${expiredWorkspaceId}')`,
    ),
  ).toBe("0");
  expect(failures(), "unexpected browser failure category").toEqual([]);

  // Fixture teardown: platform administrators see every site in
  // /me/sites ordered by site_key, so the forged cross-site fixture must
  // not outlive this test or it poisons later e2e phases that select a
  // site by position.
  psql(
    project,
    `DELETE FROM control.capability
      WHERE workspace_id = '${forgedWorkspaceId}';
     DELETE FROM audit.human_agent_session
      WHERE workspace_id = '${forgedWorkspaceId}';
     DELETE FROM control.workspace WHERE id = '${forgedWorkspaceId}';
     DELETE FROM control.site WHERE id = '${forgedSiteId}';`,
  );
});
