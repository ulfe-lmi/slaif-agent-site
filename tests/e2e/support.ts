import {
  expect,
  type APIResponse,
  type Locator,
  type Page,
  type Response,
} from "@playwright/test";
import { readFileSync } from "node:fs";
import { classifyConsoleMessage, classifyConsoleSource } from "./observation";

export type Secrets = {
  setupToken: string;
  username: string;
  loginUsername: string;
  password: string;
  fixtureUserOne: string;
  fixtureUserTwo: string;
};

export function secrets(): Secrets {
  const path = process.env.SLAIF_E2E_SECRET_FILE;
  if (!path) throw new Error("missing bounded secret channel");
  return JSON.parse(readFileSync(path, "utf8")) as Secrets;
}

export function observe(page: Page, expectedFailures: RegExp[] = []) {
  const failures: string[] = [];
  page.on("console", (message) => {
    const source = message.location().url;
    if (
      message.type() === "error" &&
      !expectedFailures.some((pattern) => pattern.test(source))
    ) {
      failures.push(
        `console-${classifyConsoleSource(source, page.url())}-${classifyConsoleMessage(message.text())}`,
      );
    }
  });
  page.on("pageerror", () => failures.push("page"));
  page.on("requestfailed", (request) => {
    const cancelledByNavigation = /aborted|cancelled/i.test(
      request.failure()?.errorText ?? "",
    );
    if (!request.url().startsWith("data:") && !cancelledByNavigation) {
      failures.push("network");
    }
  });
  page.on("response", (response) => {
    if (
      response.status() >= 400 &&
      !expectedFailures.some((pattern) => pattern.test(response.url()))
    ) {
      failures.push("response");
    }
  });
  return () => [...new Set(failures)].sort();
}

export async function expectUsable(page: Page) {
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  );
  expect(overflow, "horizontal overflow").toBe(false);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
}

export async function expectAdminUsable(page: Page) {
  await expectUsable(page);
  await expect(page.getByRole("heading", { level: 1 })).toHaveCount(1);
  await expect(page.locator("header")).toBeVisible();
  await expect(page.getByRole("main")).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Administration" })).toBeAttached();
  await expect(page.getByRole("link", { name: "Skip to main content" })).toBeAttached();
  const critical = page.locator("button:visible, .site-list a:visible");
  for (let index = 0; index < (await critical.count()); index += 1) {
    const box = await critical.nth(index).boundingBox();
    expect(box?.height ?? 0, "44px critical target").toBeGreaterThanOrEqual(44);
  }
}

export async function expectModalContained(
  page: Page,
  dialog: Locator,
  trigger: Locator,
) {
  const background = page.locator("[data-admin-background-root]");
  await expect(dialog).toHaveAttribute("aria-modal", "true");
  await expect(background).toHaveAttribute("inert", "");
  const controls = dialog.locator(
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
  );
  const steps = (await controls.count()) + 2;
  for (let index = 0; index < steps; index += 1) {
    await page.keyboard.press("Tab");
    await expect(page.locator(":focus")).toBeVisible();
    expect(
      await page
        .locator(":focus")
        .evaluate((element) => Boolean(element.closest('[role="dialog"]'))),
    ).toBe(true);
  }
  for (let index = 0; index < steps; index += 1) {
    await page.keyboard.press("Shift+Tab");
    expect(
      await page
        .locator(":focus")
        .evaluate((element) => Boolean(element.closest('[role="dialog"]'))),
    ).toBe(true);
  }
  const backgroundControl = background.locator("button:visible, a:visible").first();
  await backgroundControl.evaluate((element) => element.focus());
  await expect(backgroundControl).not.toBeFocused();
  const box = await backgroundControl.boundingBox();
  if (box) await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2);
  expect(
    await page
      .locator(":focus")
      .evaluate((element) => Boolean(element.closest('[role="dialog"]'))),
  ).toBe(true);
  await page.keyboard.press("Escape");
  await expect(dialog).toBeHidden();
  await expect(background).not.toHaveAttribute("inert", "");
  await expect(trigger).toBeFocused();
}

export function expectPrivateHeaders(response: APIResponse | Response) {
  const headers = response.headers();
  expect(headers["cache-control"]).toBe("private, no-store");
  expect(headers["x-robots-tag"]).toBe("noindex, nofollow, noarchive");
  expect(headers["x-request-id"]).toMatch(/^[0-9a-f]{32}$/);
}

export async function login(page: Page, credential: Secrets) {
  await page.goto("/login");
  await page.getByLabel("Username").fill(credential.loginUsername);
  await page.getByLabel("Password").fill(credential.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByText("Authenticated session active.")).toBeVisible();
  await expect(page.getByText("Local administrator")).toBeVisible();
}
