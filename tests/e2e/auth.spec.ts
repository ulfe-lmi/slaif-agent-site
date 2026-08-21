import { expect, test } from "@playwright/test";
import {
  expectAdminUsable,
  expectModalContained,
  login,
  observe,
  secrets,
} from "./support";

test("responsive-admin-keyboard-read-states-and-logout", async ({ page }) => {
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

  stage("login-dashboard");
  await login(page, credential);
  await expectAdminUsable(page);
  await page.emulateMedia({ reducedMotion: "reduce" });
  expect(
    await page.evaluate(() => matchMedia("(prefers-reduced-motion: reduce)").matches),
  ).toBe(true);

  stage("keyboard-focus");
  await page.keyboard.press("Tab");
  const focused = page.locator(":focus");
  await expect(focused).toBeVisible();
  expect(
    await focused.evaluate((element) => getComputedStyle(element).outlineStyle),
  ).not.toBe("none");

  stage("site-switcher-dialog");
  const trigger = page
    .getByRole("button", { name: "Choose site" })
    .filter({ visible: true });
  await trigger.click();
  const dialog = page.getByRole("dialog", { name: "Choose an authorized site" });
  await expect(dialog).toBeVisible();
  await expectModalContained(page, dialog, trigger);

  stage("site-overview-read");
  await trigger.click();
  await dialog.getByRole("link", { name: /SLAIF Demo Site/ }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("SLAIF Demo Site");
  await expectAdminUsable(page);

  stage("settings-read");
  await page.getByRole("link", { name: "Open site settings" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "SLAIF Demo Site settings",
  );
  await expect(page.getByText("Mappings configure routing only")).toBeVisible();
  await expectAdminUsable(page);

  stage("memberships-read");
  await page.goto(page.url().replace(/\/settings$/, "/memberships"));
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "SLAIF Demo Site memberships",
  );
  await expect(page.getByText(/VIEWER · ACTIVE/)).toBeVisible();
  await expectAdminUsable(page);

  stage("logout-revocation");
  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/admin");
  await expect(page).toHaveURL(/\/login$/);
  const failures = assertClean();
  stage(failures.length === 0 ? "browser-clean" : `browser-${failures.join("-")}`);
  expect(failures, "unexpected browser failure category").toEqual([]);
});
