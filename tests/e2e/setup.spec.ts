import { expect, test } from "@playwright/test";
import { expectUsable, observe, secrets } from "./support";

type Site = { site_id: string; site_key: string };
type Role = {
  role_key: string;
  default_delegation_ceiling: number;
  default_permissions: string[];
};
type Permission = {
  permission_key: string;
  category: string;
  agent_delegation_level: number | null;
  site_assignable: boolean;
  installation_only: boolean;
  system_only: boolean;
  role_keys: string[];
};
type Membership = {
  site_id: string;
  user_account_id: string;
  role_key: string;
  delegation_ceiling: number;
  effective_delegation_ceiling: number;
  status: "ACTIVE" | "INACTIVE";
  version: number;
  allow_permissions: string[];
  deny_permissions: string[];
  effective_permissions: string[];
  platform_administrator: boolean;
};

test("setup-desktop-phone-and-initialize", async ({ page }) => {
  const info = test.info();
  const stage = (description: string) => {
    info.annotations = [{ type: "stage", description }];
  };
  const credential = secrets();
  const assertClean = observe(page, [
    /\/api\/control\/v1\/setup$/,
    /\/api\/control\/v1\/session$/,
    /\/api\/control\/v1\/login$/,
    /\/api\/control\/v1\/sites\/[^/]+\/memberships/,
  ]);

  const assertPrivate = (response: Awaited<ReturnType<typeof page.request.get>>) => {
    const headers = response.headers();
    expect(headers["cache-control"]).toBe("private, no-store");
    expect(headers["x-robots-tag"]).toBe("noindex, nofollow, noarchive");
    expect(headers["x-request-id"]).toMatch(/^[0-9a-f]{32}$/);
  };
  const membershipBody = (
    role_key: string,
    delegation_ceiling: number,
    allow_permissions: string[] = [],
    deny_permissions: string[] = [],
  ) => ({ role_key, delegation_ceiling, allow_permissions, deny_permissions });

  stage("landing");
  await page.goto("/");
  await expect(page.getByRole("link", { name: "First-time setup" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Administrator sign in" })).toBeVisible();
  await expectUsable(page);

  stage("demo-routing-before-setup");
  await page.goto("/s/demo/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Site: demo");
  await expectUsable(page);
  await page.setViewportSize({ width: 320, height: 720 });
  await expectUsable(page);

  stage("setup-layout");
  await page.goto("/setup");
  await expect(page.getByText("Setup token ready.")).toBeVisible();
  await expectUsable(page);
  await page.setViewportSize({ width: 320, height: 720 });
  await expectUsable(page);
  await expect(
    page.getByRole("button", { name: "Create administrator" }),
  ).toBeEnabled();

  stage("setup-submit");
  await page.getByLabel("Setup token").fill(credential.setupToken);
  await page.getByLabel("Username").fill(credential.username);
  await page.getByLabel("Display name").fill("Compose Administrator");
  await page.getByLabel("Email (optional)").fill("compose@example.test");
  await page.getByLabel("Password").fill(credential.password);
  await page.getByRole("button", { name: "Create administrator" }).click();
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByText("Authenticated session active.")).toBeVisible();
  expect(page.url().includes(credential.setupToken), "secret URL boundary").toBe(false);
  expect(
    (await page.locator("body").innerText()).includes(credential.setupToken),
    "secret DOM boundary",
  ).toBe(false);
  expect(
    await page.evaluate(() => ({
      local: localStorage.length,
      session: sessionStorage.length,
    })),
  ).toEqual({ local: 0, session: 0 });

  stage("second-site-csrf");
  const csrfValue = (await page.context().cookies()).find(
    (cookie) => cookie.name === "slaif_csrf",
  )?.value;
  expect(csrfValue).toBeTruthy();
  const mutationHeaders = { "X-CSRF-Token": csrfValue! };
  stage("second-site-create");
  const created = await page.request.post("/api/control/v1/sites", {
    headers: mutationHeaders,
    data: {
      site_key: "second",
      display_name: "Second Site",
      default_locale: "sl-si",
    },
  });
  expect(created.status()).toBe(201);
  const second = (await created.json()) as { site_id: string };
  stage("second-site-domain");
  const mapping = await page.request.post(
    `/api/control/v1/sites/${second.site_id}/domains`,
    {
      headers: mutationHeaders,
      data: {
        hostname: "sites.test",
        path_prefix: "/team",
        is_primary: true,
      },
    },
  );
  expect(mapping.status()).toBe(201);
  stage("second-site-local-route");
  await page.goto("/s/second/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Site: second");
  stage("second-site-custom-route");
  const custom = await page.request.get("http://localhost:8080/team/page", {
    headers: { Host: "sites.test" },
  });
  expect(custom.status()).toBe(200);
  expect(await custom.text()).toMatch(/Site:.*second/s);

  stage("membership-catalogs");
  const rolesResponse = await page.request.get("/api/control/v1/roles");
  expect(rolesResponse.status()).toBe(200);
  assertPrivate(rolesResponse);
  const roles = (await rolesResponse.json()) as Role[];
  expect(
    Object.fromEntries(
      roles.map((role) => [role.role_key, role.default_delegation_ceiling]),
    ),
  ).toEqual({
    SITE_OWNER: 4,
    SITE_ARCHITECT: 4,
    SITE_DESIGNER: 3,
    SITE_EDITOR: 2,
    CONTENT_EDITOR: 1,
    REVIEWER: 0,
    VIEWER: 0,
  });
  const permissionsResponse = await page.request.get("/api/control/v1/permissions");
  expect(permissionsResponse.status()).toBe(200);
  assertPrivate(permissionsResponse);
  const permissions = (await permissionsResponse.json()) as Permission[];
  expect(permissions.length).toBeGreaterThan(80);
  expect(permissions.map((permission) => permission.permission_key)).toEqual(
    [...permissions.map((permission) => permission.permission_key)].sort(),
  );
  for (const permission of permissions) {
    expect(Object.keys(permission).sort()).toEqual([
      "agent_delegation_level",
      "category",
      "installation_only",
      "permission_key",
      "role_keys",
      "site_assignable",
      "system_only",
    ]);
    expect(permission.installation_only || permission.system_only).toBe(
      !permission.site_assignable,
    );
  }
  for (const role of roles) {
    expect(role.default_permissions).toEqual(
      permissions
        .filter((permission) => permission.role_keys.includes(role.role_key))
        .map((permission) => permission.permission_key),
    );
  }
  expect(
    permissions.find((permission) => permission.permission_key === "schema:migrate"),
  ).toMatchObject({ site_assignable: false, system_only: true });
  expect(
    permissions.find(
      (permission) => permission.permission_key === "installation:manage",
    ),
  ).toMatchObject({ site_assignable: false, installation_only: true });
  const catalogText = JSON.stringify({ roles, permissions });
  expect(catalogText).not.toMatch(
    /password|session|csrf|email|username|oidc|subject|user_account/i,
  );

  const sitesResponse = await page.request.get("/api/control/v1/sites");
  expect(sitesResponse.status()).toBe(200);
  const sites = (await sitesResponse.json()) as Site[];
  const demo = sites.find((site) => site.site_key === "demo");
  expect(demo).toBeTruthy();
  const sessionResponse = await page.request.get("/api/control/v1/session");
  const administrator = (await sessionResponse.json()) as { user_account_id: string };

  stage("membership-create-two-sites");
  const createMembership = async (
    siteId: string,
    target_user_id: string,
    body: ReturnType<typeof membershipBody>,
  ) => {
    const response = await page.request.post(
      `/api/control/v1/sites/${siteId}/memberships`,
      { headers: mutationHeaders, data: { target_user_id, ...body } },
    );
    expect(response.status()).toBe(201);
    assertPrivate(response);
    return (await response.json()) as Membership;
  };
  expect(
    await createMembership(
      demo!.site_id,
      credential.fixtureUserOne,
      membershipBody("CONTENT_EDITOR", 1),
    ),
  ).toMatchObject({ role_key: "CONTENT_EDITOR", delegation_ceiling: 1, version: 1 });
  expect(
    await createMembership(
      second.site_id,
      credential.fixtureUserOne,
      membershipBody("SITE_ARCHITECT", 4),
    ),
  ).toMatchObject({ role_key: "SITE_ARCHITECT", delegation_ceiling: 4, version: 1 });
  await createMembership(
    demo!.site_id,
    credential.fixtureUserTwo,
    membershipBody("VIEWER", 0),
  );

  stage("membership-site-isolation");
  for (const [siteId, role] of [
    [demo!.site_id, "CONTENT_EDITOR"],
    [second.site_id, "SITE_ARCHITECT"],
  ] as const) {
    const listed = await page.request.get(
      `/api/control/v1/sites/${siteId}/memberships`,
    );
    expect(listed.status()).toBe(200);
    assertPrivate(listed);
    const records = (await listed.json()) as Membership[];
    expect(
      records.find((record) => record.user_account_id === credential.fixtureUserOne),
    ).toMatchObject({ site_id: siteId, role_key: role, status: "ACTIVE", version: 1 });
    const exact = await page.request.get(
      `/api/control/v1/sites/${siteId}/memberships/${credential.fixtureUserOne}`,
    );
    expect(exact.status()).toBe(200);
    assertPrivate(exact);
    expect(await exact.json()).toMatchObject({ site_id: siteId, role_key: role });
  }
  const crossSite = await page.request.get(
    `/api/control/v1/sites/${second.site_id}/memberships/${credential.fixtureUserTwo}`,
  );
  expect(crossSite.status()).toBe(404);
  assertPrivate(crossSite);

  stage("membership-update-version-and-publication");
  const updated = await page.request.patch(
    `/api/control/v1/sites/${second.site_id}/memberships/${credential.fixtureUserOne}`,
    {
      headers: mutationHeaders,
      data: {
        expected_version: 1,
        status: "ACTIVE",
        ...membershipBody("SITE_ARCHITECT", 4, ["site:publish"]),
      },
    },
  );
  expect(updated.status()).toBe(200);
  assertPrivate(updated);
  const updatedMembership = (await updated.json()) as Membership;
  expect(updatedMembership).toMatchObject({
    version: 2,
    allow_permissions: ["site:publish"],
    status: "ACTIVE",
  });
  expect(updatedMembership.effective_permissions).toContain("site:publish");
  const stale = await page.request.patch(
    `/api/control/v1/sites/${second.site_id}/memberships/${credential.fixtureUserOne}`,
    {
      headers: mutationHeaders,
      data: {
        expected_version: 1,
        status: "ACTIVE",
        ...membershipBody("SITE_ARCHITECT", 4, ["site:publish"]),
      },
    },
  );
  expect(stale.status()).toBe(409);
  assertPrivate(stale);

  stage("membership-csrf-self-and-scope-negatives");
  const membershipPath = `/api/control/v1/sites/${second.site_id}/memberships/${credential.fixtureUserOne}`;
  const currentBody = {
    expected_version: 2,
    status: "ACTIVE",
    ...membershipBody("SITE_ARCHITECT", 4, ["site:publish"]),
  };
  for (const headers of [{}, { "X-CSRF-Token": "wrong-csrf-value" }]) {
    const denied = await page.request.patch(membershipPath, {
      headers,
      data: currentBody,
    });
    expect(denied.status()).toBe(403);
    assertPrivate(denied);
  }
  const unchanged = await page.request.get(membershipPath);
  expect(await unchanged.json()).toMatchObject({ version: 2, status: "ACTIVE" });
  const self = await page.request.post(
    `/api/control/v1/sites/${demo!.site_id}/memberships`,
    {
      headers: mutationHeaders,
      data: {
        target_user_id: administrator.user_account_id,
        ...membershipBody("SITE_OWNER", 4),
      },
    },
  );
  expect(self.status()).toBe(403);
  assertPrivate(self);
  const systemOverride = await page.request.patch(membershipPath, {
    headers: mutationHeaders,
    data: {
      expected_version: 2,
      status: "ACTIVE",
      ...membershipBody("SITE_ARCHITECT", 4, ["schema:migrate"]),
    },
  });
  expect(systemOverride.status()).toBe(403);
  assertPrivate(systemOverride);
  const invalidCeiling = await page.request.post(
    `/api/control/v1/sites/${second.site_id}/memberships`,
    {
      headers: mutationHeaders,
      data: {
        target_user_id: credential.fixtureUserTwo,
        ...membershipBody("VIEWER", 1),
      },
    },
  );
  expect(invalidCeiling.status()).toBe(422);
  assertPrivate(invalidCeiling);

  stage("membership-local-login-impossible");
  const fixtureLogin = await page.request.post("/api/control/v1/login", {
    data: {
      username: "compose-fixture-subject-one",
      password: credential.password,
    },
  });
  expect(fixtureLogin.status()).toBe(401);
  expect(fixtureLogin.headers()["set-cookie"]).toBeUndefined();

  stage("membership-semantic-deactivation");
  const deactivated = await page.request.delete(
    `${membershipPath}?expected_version=2`,
    { headers: mutationHeaders },
  );
  expect(deactivated.status()).toBe(200);
  assertPrivate(deactivated);
  expect(await deactivated.json()).toMatchObject({
    role_key: "SITE_ARCHITECT",
    delegation_ceiling: 4,
    status: "INACTIVE",
    version: 3,
    allow_permissions: ["site:publish"],
    effective_permissions: [],
  });
  stage("second-site-negative-routes");
  for (const [path, headers] of [
    ["/team-other", { Host: "sites.test" }],
    ["/", { Host: "unknown.test" }],
    ["/unknown", { Host: "unknown.test", "X-Site-ID": second.site_id }],
    ["/internal/render/v1/site-context", {}],
  ] as const) {
    expect(
      (await page.request.get(`http://localhost:8080${path}`, { headers })).status(),
    ).toBe(404);
  }
  stage("second-site-archive");
  const archived = await page.request.post(
    `/api/control/v1/sites/${second.site_id}/archive`,
    { headers: mutationHeaders },
  );
  expect(archived.status()).toBe(200);
  expect((await page.request.get("/s/second/")).status()).toBe(404);

  stage("authenticated-admin-return");
  await page.goto("/admin");
  await expect(page.getByText("Authenticated session active.")).toBeVisible();

  stage("cookie-policy");
  const cookies = await page.context().cookies();
  const session = cookies.find((cookie) => cookie.name === "slaif_session");
  const csrf = cookies.find((cookie) => cookie.name === "slaif_csrf");
  expect(
    session && {
      httpOnly: session.httpOnly,
      sameSite: session.sameSite,
      path: session.path,
      secure: session.secure,
    },
  ).toEqual({ httpOnly: true, sameSite: "Lax", path: "/", secure: false });
  expect(
    csrf && {
      httpOnly: csrf.httpOnly,
      sameSite: csrf.sameSite,
      path: csrf.path,
      secure: csrf.secure,
    },
  ).toEqual({ httpOnly: false, sameSite: "Lax", path: "/", secure: false });

  stage("logout-closure");
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login$/);
  stage("session-revocation");
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/login$/);
  stage("setup-closed");
  await page.goto("/setup");
  await expect(page.getByText("Setup is closed. Sign in instead.")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Create administrator" }),
  ).toBeDisabled();

  stage("token-replay");
  const replay = await page.request.post("/api/control/v1/setup", {
    data: {
      setup_token: credential.setupToken,
      username: "replay-admin",
      password: credential.password,
      display_name: "Replay Administrator",
      email: null,
    },
  });
  expect(replay.ok()).toBe(false);
  const failures = assertClean();
  stage(failures.length === 0 ? "browser-clean" : `browser-${failures.join("-")}`);
  expect(failures, "unexpected browser failure category").toEqual([]);
});
