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
  await expectUsable(page);

  stage("demo-routing-before-setup");
  await page.goto("/s/demo/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Site: demo");
  await page.setViewportSize({ width: 320, height: 720 });
  await expectUsable(page);

  stage("setup-visible-workflow");
  await page.goto("/setup");
  await expect(page.getByText("Setup token ready.")).toBeVisible();
  await page.getByLabel("Setup token").fill(credential.setupToken);
  await page.getByLabel("Username").fill(credential.username);
  await page.getByLabel("Display name").fill("Compose Administrator");
  await page.getByLabel("Email (optional)").fill("compose@example.test");
  await page.getByLabel("Password").fill(credential.password);
  await page.getByRole("button", { name: "Create administrator" }).click();
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByText("Authenticated session active.")).toBeVisible();
  expect(page.url()).not.toContain(credential.setupToken);
  expect(await page.locator("body").innerText()).not.toContain(credential.setupToken);
  expect(
    await page.evaluate(() => ({
      local: localStorage.length,
      session: sessionStorage.length,
    })),
  ).toEqual({ local: 0, session: 0 });

  stage("setup-closed");
  await page.goto("/setup");
  await expect(page.getByText("Setup is closed. Sign in instead.")).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Create administrator" }),
  ).toBeDisabled();

  const failures = assertClean();
  stage(failures.length === 0 ? "browser-clean" : `browser-${failures.join("-")}`);
  expect(failures, "unexpected browser failure category").toEqual([]);
});
