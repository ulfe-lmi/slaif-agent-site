import { expect, test } from "@playwright/test";
import { expectUsable, login, observe, secrets } from "./support";

test("login-admin-keyboard-error-and-logout", async ({ page }) => {
  const info = test.info();
  const stage = (description: string) => {
    info.annotations = [{ type: "stage", description }];
  };
  const credential = secrets();
  const assertClean = observe(page, [
    /\/api\/control\/v1\/login$/,
    /\/api\/control\/v1\/session$/,
  ]);

  stage("unauthenticated-redirect");
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/login$/);
  await expectUsable(page);

  stage("generic-error");
  await page.getByLabel("Username").fill(credential.loginUsername);
  await page.getByLabel("Password").fill("wrong-password");
  await page.getByRole("button", { name: "Sign in" }).dblclick();
  await expect(page.getByRole("status")).toHaveText(
    "The request could not be completed. Check the details and try again.",
  );
  await expect(page.getByRole("status")).toBeFocused();

  stage("login-admin");
  await login(page, credential);
  stage("keyboard-responsive");
  await page.keyboard.press("Tab");
  const focused = page.locator(":focus");
  await expect(focused).toBeVisible();
  expect(
    await focused.evaluate((element) => getComputedStyle(element).outlineStyle),
  ).not.toBe("none");
  await expectUsable(page);

  stage("logout-revocation");
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/login$/);
  const failures = assertClean();
  stage(failures.length === 0 ? "browser-clean" : `browser-${failures.join("-")}`);
  expect(failures, "unexpected browser failure category").toEqual([]);
});
