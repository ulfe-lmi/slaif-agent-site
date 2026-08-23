import {
  expect,
  test,
  type APIResponse,
  type Locator,
  type Page,
} from "@playwright/test";
import {
  expectAdminUsable,
  expectModalContained,
  expectPrivateHeaders,
  login,
  observe,
  secrets,
} from "./support";

type Membership = {
  version: number;
  status: "ACTIVE" | "INACTIVE";
  role_key: string;
  delegation_ceiling: number;
  allow_permissions: string[];
  deny_permissions: string[];
  effective_permissions: string[];
};

const fixtureUnknown = "12000000-0000-4000-8000-000000000099";

function responseStatus(response: APIResponse, expected: number) {
  expect(response.status()).toBe(expected);
  expectPrivateHeaders(response);
}

async function membershipCard(page: Locator | Page, userId: string) {
  const card = page.locator(".membership-card").filter({ hasText: userId });
  await expect(card).toBeVisible();
  return card;
}

test("governance-visible-workflows-negatives-and-privacy", async ({ page }) => {
  const info = test.info();
  const stage = (description: string) => {
    info.annotations = [{ type: "stage", description }];
  };
  const credential = secrets();
  const requestedUrls: string[] = [];
  page.on("request", (request) => requestedUrls.push(request.url()));
  const assertClean = observe(page, [
    /\/api\/control\/v1\/sites\/[^/]+\/memberships/,
    /\/api\/control\/v1\/sites\/[^/]+$/,
    /\/s\/governance/,
  ]);

  stage("dashboard-and-switcher");
  await login(page, credential);
  await expectAdminUsable(page);
  const switcherTrigger = page
    .getByRole("button", { name: "Choose site" })
    .filter({ visible: true });
  await switcherTrigger.click();
  const switcher = page.getByRole("dialog", { name: "Choose an authorized site" });
  await expect(switcher).toBeVisible();
  await expectModalContained(page, switcher, switcherTrigger, stage);

  stage("site-create-visible");
  await page.getByRole("link", { name: "Create a site" }).click();
  await page.getByLabel("Site key").fill("governance");
  await page.getByLabel("Display name").fill("Governance Site");
  await page.getByLabel("Default locale").fill("en");
  await page.getByRole("button", { name: "Create site" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Governance Site");
  const siteMatch = /\/admin\/sites\/([0-9a-f-]+)$/.exec(page.url());
  expect(siteMatch).toBeTruthy();
  const siteId = siteMatch![1];

  stage("profile-update-visible");
  await page.getByRole("link", { name: "Open site settings" }).click();
  await page.getByLabel("Display name").fill("Governance Evidence Site");
  await page.getByLabel("Default locale").fill("sl-si");
  await page.getByRole("button", { name: "Save profile" }).click();
  await expect(page.getByRole("status")).toHaveText("Profile updated.");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Governance Evidence Site settings",
  );

  stage("domain-secondary-add-visible");
  await page.getByLabel("Hostname").fill("routes.test");
  await page.getByLabel("Path prefix").fill("/secondary");
  await page.getByRole("button", { name: "Add domain" }).click();
  await expect(page.getByRole("status")).toHaveText("Domain saved.");
  await expect(page.getByText("routes.test/secondary")).toBeVisible();
  stage("domain-primary-add-visible");
  await page.getByLabel("Hostname").fill("governance.test");
  await page.getByLabel("Path prefix").fill("/primary");
  await page.getByLabel("Primary mapping").check();
  await page.getByRole("button", { name: "Add domain" }).click();
  await expect(page.getByRole("status")).toHaveText("Domain saved.");
  stage("domain-primary-replace-visible");
  const secondary = page.locator(".domain-list li").filter({
    hasText: "routes.test/secondary",
  });
  await secondary.getByRole("button", { name: "Make primary" }).click();
  await expect(page.getByRole("status")).toHaveText("Primary domain replaced.");
  await expect(secondary).toContainText("primary");
  stage("domain-remove-visible");
  const oldPrimary = page.locator(".domain-list li").filter({
    hasText: "governance.test/primary",
  });
  await oldPrimary.getByRole("button", { name: "Remove" }).click();
  await expect(page.getByRole("status")).toHaveText("Domain removed.");
  await expect(oldPrimary).toHaveCount(0);
  stage("domain-routes-visible");
  await page.goto("/s/governance/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Site: governance");
  const customRoute = await page.request.get("http://localhost:8080/secondary/page", {
    headers: { Host: "routes.test" },
  });
  expect(customRoute.status()).toBe(200);
  expect(await customRoute.text()).toMatch(/Site:.*governance/s);

  stage("membership-catalog-visible");
  await page.goto(`/admin/sites/${siteId}/memberships`);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Governance Evidence Site memberships",
  );
  const add = page.getByRole("heading", { name: "Add existing user" }).locator("..");
  await expect(add.getByRole("option", { name: "Architect" })).toBeAttached();
  await add.getByText("Advanced permission overrides").click();
  await expect(add.getByText("READ", { exact: true })).toBeVisible();
  await expect(add.getByText("L4 WRITE", { exact: true })).toBeVisible();
  await add.getByText("Nonassignable installation and system scopes").click();
  await expect(add.getByText(/schema:migrate/)).toBeVisible();

  stage("membership-add-visible");
  await add.getByLabel("Existing user UUID").fill(credential.fixtureUserOne);
  await add.getByLabel("Built-in role").selectOption("SITE_ARCHITECT");
  await add.getByLabel("Explicit delegation ceiling").selectOption("4");
  await add.getByRole("button", { name: "Add membership" }).click();
  await expect(page.getByRole("status")).toHaveText("Membership added.");
  let card = await membershipCard(page, credential.fixtureUserOne);
  await expect(card).toContainText("SITE_ARCHITECT · ACTIVE");
  await expect(card).toContainText("Version");
  await expect(card).toContainText("1");

  stage("membership-edit-publish-grant-visible");
  const editTrigger = card.getByRole("button", { name: "Edit membership" });
  await editTrigger.click();
  let edit = page.getByRole("dialog", { name: new RegExp("^Edit ") });
  await expectModalContained(page, edit, editTrigger, stage);
  await editTrigger.click();
  await edit.getByLabel("Built-in role").selectOption("SITE_DESIGNER");
  await edit.getByLabel("Explicit delegation ceiling").selectOption("3");
  await edit.getByLabel("Site publication override").selectOption("allow");
  const grantResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "PATCH" &&
      response.url().endsWith(`/memberships/${credential.fixtureUserOne}`),
  );
  await edit.getByRole("button", { name: "Save membership" }).click();
  const grant = await grantResponse;
  expect(grant.status()).toBe(200);
  expectPrivateHeaders(grant);
  await expect(edit).toBeHidden();
  await expect(page.locator("[data-admin-background-root]")).not.toHaveAttribute(
    "inert",
    "",
  );
  await expectAdminUsable(page);
  await expect(page.getByRole("status")).toHaveText("Membership updated.");
  card = await membershipCard(page, credential.fixtureUserOne);
  await expect(card).toContainText("SITE_DESIGNER · ACTIVE");
  await expect(card).toContainText("2");

  stage("membership-publish-deny-visible");
  await card.getByRole("button", { name: "Edit membership" }).click();
  edit = page.getByRole("dialog", { name: new RegExp("^Edit ") });
  await edit.getByLabel("Site publication override").selectOption("deny");
  const denyResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "PATCH" &&
      response.url().endsWith(`/memberships/${credential.fixtureUserOne}`),
  );
  await edit.getByRole("button", { name: "Save membership" }).click();
  const deny = await denyResponse;
  expect(deny.status()).toBe(200);
  expectPrivateHeaders(deny);
  await expect(edit).toBeHidden();
  await expect(page.getByRole("status")).toHaveText("Membership updated.");
  card = await membershipCard(page, credential.fixtureUserOne);
  await expect(card).toContainText("3");

  const cookies = await page.context().cookies();
  const csrf = cookies.find((cookie) => cookie.name === "slaif_csrf")?.value;
  expect(csrf).toBeTruthy();
  const headers = { "X-CSRF-Token": csrf! };
  const membershipPath = `/api/control/v1/sites/${siteId}/memberships/${credential.fixtureUserOne}`;
  const replacement = {
    role_key: "SITE_DESIGNER",
    delegation_ceiling: 3,
    allow_permissions: [],
    deny_permissions: ["site:publish"],
  };

  stage("stale-ui-conflict-recovery");
  await card.getByRole("button", { name: "Edit membership" }).click();
  edit = page.getByRole("dialog", { name: new RegExp("^Edit ") });
  const concurrent = await page.request.patch(membershipPath, {
    headers,
    data: { expected_version: 3, status: "ACTIVE", ...replacement },
  });
  responseStatus(concurrent, 200);
  const staleResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "PATCH" &&
      response.url().endsWith(`/memberships/${credential.fixtureUserOne}`),
  );
  await edit.getByRole("button", { name: "Save membership" }).click();
  const stale = await staleResponse;
  expect(stale.status()).toBe(409);
  expectPrivateHeaders(stale);
  await edit.getByRole("button", { name: "Cancel" }).click();
  await expect(page.getByRole("status")).toHaveText(
    "The membership changed. The current server state has been refreshed.",
  );
  card = await membershipCard(page, credential.fixtureUserOne);
  await expect(card).toContainText("4");

  stage("crafted-membership-negatives");
  const unchangedBody = {
    expected_version: 4,
    status: "ACTIVE",
    ...replacement,
  };
  for (const badHeaders of [{}, { "X-CSRF-Token": "wrong-csrf-value" }]) {
    responseStatus(
      await page.request.patch(membershipPath, {
        headers: badHeaders,
        data: unchangedBody,
      }),
      403,
    );
  }
  const session = (await (
    await page.request.get("/api/control/v1/session")
  ).json()) as { user_account_id: string };
  responseStatus(
    await page.request.post(`/api/control/v1/sites/${siteId}/memberships`, {
      headers,
      data: {
        target_user_id: session.user_account_id,
        role_key: "SITE_OWNER",
        delegation_ceiling: 4,
        allow_permissions: [],
        deny_permissions: [],
      },
    }),
    403,
  );
  responseStatus(
    await page.request.patch(membershipPath, {
      headers,
      data: {
        ...unchangedBody,
        allow_permissions: ["schema:migrate"],
        deny_permissions: [],
      },
    }),
    403,
  );
  responseStatus(
    await page.request.post(`/api/control/v1/sites/${siteId}/memberships`, {
      headers,
      data: {
        target_user_id: credential.fixtureUserTwo,
        role_key: "VIEWER",
        delegation_ceiling: 1,
        allow_permissions: [],
        deny_permissions: [],
      },
    }),
    422,
  );
  responseStatus(
    await page.request.get(
      `/api/control/v1/sites/${siteId}/memberships/${fixtureUnknown}`,
    ),
    404,
  );
  const unchanged = await page.request.get(membershipPath);
  responseStatus(unchanged, 200);
  expect((await unchanged.json()) as Membership).toMatchObject({
    version: 4,
    status: "ACTIVE",
    deny_permissions: ["site:publish"],
  });

  stage("cross-site-fixture-visible");
  await page.goto("/admin");
  const demoLink = page.locator(".site-list a").filter({ hasText: "SLAIF Demo Site" });
  await demoLink.click();
  await page.getByRole("link", { name: "Manage memberships" }).click();
  const demoAdd = page
    .getByRole("heading", { name: "Add existing user" })
    .locator("..");
  await demoAdd.getByLabel("Existing user UUID").fill(credential.fixtureUserTwo);
  await demoAdd.getByLabel("Built-in role").selectOption("VIEWER");
  await demoAdd.getByLabel("Explicit delegation ceiling").selectOption("0");
  await demoAdd.getByRole("button", { name: "Add membership" }).click();
  await expect(page.getByRole("status")).toHaveText("Membership added.");
  responseStatus(
    await page.request.get(
      `/api/control/v1/sites/${siteId}/memberships/${credential.fixtureUserTwo}`,
    ),
    404,
  );

  stage("semantic-deactivation-visible");
  await page.goto(`/admin/sites/${siteId}/memberships`);
  card = await membershipCard(page, credential.fixtureUserOne);
  const deactivateTrigger = card.getByRole("button", { name: "Deactivate" });
  await deactivateTrigger.click();
  const deactivate = page.getByRole("dialog", { name: /^Deactivate / });
  await expectModalContained(page, deactivate, deactivateTrigger, stage);
  await deactivateTrigger.click();
  await expect(deactivate).toContainText("does not delete");
  await deactivate.getByRole("button", { name: "Confirm deactivation" }).click();
  await expect(page.getByRole("status")).toHaveText("Membership deactivated.");
  card = await membershipCard(page, credential.fixtureUserOne);
  await expect(card).toContainText("SITE_DESIGNER · INACTIVE");
  await expect(card).toContainText("5");
  await expect(page.locator("[data-admin-background-root]")).not.toHaveAttribute(
    "inert",
    "",
  );
  await expectAdminUsable(page);

  stage("privacy-csp-edge");
  const adminResponse = await page.request.get(`/admin/sites/${siteId}`);
  expect(adminResponse.status()).toBe(200);
  const adminHeaders = adminResponse.headers();
  expect(adminHeaders["x-request-id"]).toMatch(/^[0-9a-f]{32}$/);
  const csp = adminHeaders["content-security-policy"];
  expect(csp).toContain("default-src 'self'");
  expect(csp).not.toMatch(/unsafe-inline|unsafe-eval|https?:|wss?:/);
  expectPrivateHeaders(await page.request.get(membershipPath));
  expect(
    await page.evaluate(() => ({
      local: localStorage.length,
      session: sessionStorage.length,
    })),
  ).toEqual({ local: 0, session: 0 });
  const body = await page.locator("body").innerText();
  for (const secret of [credential.setupToken, credential.password, csrf!]) {
    expect(body).not.toContain(secret);
    expect(page.url()).not.toContain(secret);
    expect(requestedUrls.join("\n")).not.toContain(secret);
  }

  stage("archive-dialog-keyboard-visible");
  await page.goto(`/admin/sites/${siteId}/settings`);
  const archiveTrigger = page.getByRole("button", {
    name: "Archive Governance Evidence Site",
  });
  await archiveTrigger.focus();
  await page.keyboard.press("Enter");
  const archive = page.getByRole("dialog", {
    name: "Archive Governance Evidence Site?",
  });
  await expect(archive).toBeVisible();
  await expectModalContained(page, archive, archiveTrigger, stage);
  await archiveTrigger.click();
  const archiveResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      response.url().endsWith(`/sites/${siteId}/archive`),
  );
  await archive.getByRole("button", { name: "Confirm archive" }).click();
  const archived = await archiveResponse;
  expect(archived.status()).toBe(200);
  expectPrivateHeaders(archived);
  await expect(archive).toBeHidden();
  await expect(page.locator("[data-admin-background-root]")).not.toHaveAttribute(
    "inert",
    "",
  );
  await expectAdminUsable(page);
  await expect(page.getByRole("status")).toHaveText(
    "Site archived. Routing is disabled.",
  );
  await page.getByRole("link", { name: "Back to overview" }).click();
  await expect(page.getByText("ARCHIVED", { exact: true })).toBeVisible();
  expect((await page.request.get("/s/governance/")).status()).toBe(404);

  stage("logout-relogin-persistence");
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await login(page, credential);
  await page.goto(`/admin/sites/${siteId}`);
  await expect(page.getByText("ARCHIVED", { exact: true })).toBeVisible();
  responseStatus(
    await page.request.get(`/api/control/v1/sites/${fixtureUnknown}/my-authority`),
    404,
  );
  await page.goto(`/admin/sites/${fixtureUnknown}`);
  await expect(
    page.getByText("This site is unavailable or you do not have access."),
  ).toBeVisible();

  const failures = assertClean();
  stage(
    failures.length === 0 ? "governance-clean" : `governance-${failures.join("-")}`,
  );
  expect(failures, "unexpected governance browser failure category").toEqual([]);
});

test("puck-editor-round-trip-through-human-editor-api", async ({ page }) => {
  const credential = secrets();
  const failures = observe(page);
  await login(page, credential);
  await page.goto("/admin");
  const demoLink = page.locator(".site-list a").filter({ hasText: "SLAIF Demo Site" });
  const href = await demoLink.getAttribute("href");
  const siteId = href?.split("/").at(-1) ?? "";
  expect(siteId).toMatch(/^[0-9a-f-]{36}$/i);

  const cookies = await page.context().cookies();
  const csrf = cookies.find((cookie) => cookie.name === "slaif_csrf")?.value;
  expect(csrf).toBeTruthy();
  const editorHeaders = (key = crypto.randomUUID()) => ({
    "X-CSRF-Token": csrf!,
    "Idempotency-Key": key,
  });
  const pageMutationKey = crypto.randomUUID();
  const pageResponse = await page.request.post(
    `/api/editor/v1/sites/${siteId}/pages/`,
    {
      headers: editorHeaders(pageMutationKey),
      data: {
        slug: "puck-editor",
        title: "Puck editor evidence",
        status: "DRAFT",
        locale: "en",
      },
    },
  );
  expect(pageResponse.status()).toBe(201);
  expectPrivateHeaders(pageResponse);
  const pageResponseBody = (await pageResponse.json()) as Record<string, unknown>;
  const pageRecord = pageResponseBody as { id: string };
  expect(pageRecord.id).toMatch(/^[0-9a-f-]{36}$/i);
  const pageReplay = await page.request.post(`/api/editor/v1/sites/${siteId}/pages/`, {
    headers: editorHeaders(pageMutationKey),
    data: {
      slug: "puck-editor",
      title: "Puck editor evidence",
      status: "DRAFT",
      locale: "en",
    },
  });
  expect(pageReplay.status()).toBe(201);
  expect(await pageReplay.json()).toEqual(pageResponseBody);
  const pageMismatch = await page.request.post(
    `/api/editor/v1/sites/${siteId}/pages/`,
    {
      headers: editorHeaders(pageMutationKey),
      data: {
        slug: "puck-editor-mismatch",
        title: "Must not be accepted",
        status: "DRAFT",
        locale: "en",
      },
    },
  );
  expect(pageMismatch.status()).toBe(409);

  const initialComponent = await page.request.post(
    `/api/editor/v1/sites/${siteId}/pages/${pageRecord.id}/composition/components`,
    {
      headers: editorHeaders(),
      data: {
        component_type: "Section",
        slot_key: "default",
        order_key: 0,
        props: { variant: "narrow" },
      },
    },
  );
  expect(initialComponent.status()).toBe(201);
  expectPrivateHeaders(initialComponent);
  const section = (await initialComponent.json()) as { id: string };

  const initialHeading = await page.request.post(
    `/api/editor/v1/sites/${siteId}/pages/${pageRecord.id}/composition/components`,
    {
      headers: editorHeaders(),
      data: {
        component_type: "Heading",
        slot_key: "default",
        order_key: 0,
        props: { text: "Puck heading", level: 2 },
      },
    },
  );
  expect(initialHeading.status()).toBe(201);
  expectPrivateHeaders(initialHeading);
  const headingRecord = (await initialHeading.json()) as { id: string };
  expect(headingRecord.id).toMatch(/^[0-9a-f-]{36}$/i);
  const movedHeading = await page.request.post(
    `/api/editor/v1/sites/${siteId}/pages/${pageRecord.id}/composition/components/${headingRecord.id}/move`,
    {
      headers: editorHeaders(),
      data: {
        new_parent_id: section.id,
        new_slot_key: "default",
        new_order_key: 0,
      },
    },
  );
  expect(movedHeading.status()).toBe(200);
  expectPrivateHeaders(movedHeading);

  const compositionPath = `/api/editor/v1/sites/${siteId}/pages/${pageRecord.id}/composition/`;
  const initialComposition = await page.request.get(compositionPath);
  expect(initialComposition.status()).toBe(200);
  expectPrivateHeaders(initialComposition);

  await page.goto(`/admin/sites/${siteId}/pages/${pageRecord.id}/edit`);
  await expect(
    page.getByRole("heading", { name: "Page composition", exact: true }).first(),
  ).toBeVisible();
  const headingComponent = page.locator('[data-puck-component="Heading"]');
  await expect(headingComponent).toHaveCount(1);
  await page.getByRole("button", { name: "Save composition" }).click();
  await expect(
    page.getByText("Composition saved and reloaded from the server.", { exact: true }),
  ).toBeVisible();

  const persisted = await page.request.get(compositionPath);
  expect(persisted.status()).toBe(200);
  expectPrivateHeaders(persisted);
  const persistedNodes = (await persisted.json()) as Array<{
    id: string;
    component_type: string;
    parent_id: string | null;
    slot_key: string;
    order_key: number;
    props: Record<string, unknown>;
  }>;
  const persistedHeading = persistedNodes.find(
    (node) => node.component_type === "Heading",
  );
  expect(persistedHeading).toMatchObject({
    parent_id: section.id,
    slot_key: "default",
    order_key: 0,
  });
  expect(persistedHeading?.props).not.toHaveProperty("id");

  await page.reload();
  await expect(page.locator('[data-puck-component="Heading"]')).toHaveCount(1);
  expect(failures(), "unexpected Puck browser failure category").toEqual([]);
});
