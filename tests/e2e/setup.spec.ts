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
