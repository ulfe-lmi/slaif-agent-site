import { expect, test } from "@playwright/test";
import { expectUsable, observe, secrets } from "./support";

test("setup-desktop-phone-and-initialize", async ({ page }) => {
  const info = test.info();
  const stage = (description: string) => {
    info.annotations = [{ type: "stage", description }];
  };
  const credential = secrets();
  const assertClean = observe(page, [
    /\/api\/control\/v1\/setup$/,
    /\/api\/control\/v1\/session$/,
  ]);

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
