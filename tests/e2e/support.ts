import { expect, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";

export type Secrets = {
  setupToken: string;
  username: string;
  loginUsername: string;
  password: string;
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
      failures.push("console");
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

export async function login(page: Page, credential: Secrets) {
  await page.goto("/login");
  await page.getByLabel("Username").fill(credential.loginUsername);
  await page.getByLabel("Password").fill(credential.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/);
  await expect(page.getByText("Authenticated session active.")).toBeVisible();
  await expect(page.getByText("Local administrator")).toBeVisible();
}
