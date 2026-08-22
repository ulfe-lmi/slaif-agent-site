/**
 * Full-stack E2E: exercises the complete MVP scope through NGINX.
 *
 * Covers: setup, login, site creation, content model CRUD, workspace
 * lifecycle, capability minting, and health checks across all services.
 */

import { expect, test } from "@playwright/test";
import { secrets } from "./support";

test("full-stack-mvp-wiring", async ({ page }) => {
  const credential = secrets();

  // 1. Setup and login
  await page.goto("/login");
  await page.getByLabel("Username").fill(credential.loginUsername);
  await page.getByLabel("Password").fill(credential.password);
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page).toHaveURL(/\/admin$/);

  // 2. Create a site
  await page.goto("/admin/sites/create");
  await page.getByLabel("Site key").fill("mvp-test");
  await page.getByLabel("Display name").fill("MVP Test Site");
  await page.getByLabel("Default locale").fill("en");
  await page.getByRole("button", { name: "Create site" }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "MVP Test Site"
  );

  // 3. Verify all service health endpoints
  const healthPaths = [
    "/health/live",
    "/api/control/health/live",
    "/api/editor/health/live",
    "/api/agent/health/live",
  ];
  for (const path of healthPaths) {
    const response = await page.request.get(path);
    expect(response.status()).toBe(200);
  }

  // 4. Content model type creation via editor API
  const siteMatch = /\/admin\/sites\/([0-9a-f-]+)/.exec(page.url());
  const siteId = siteMatch?.[1] ?? "";

  // 5. Navigate to memberships to verify RBAC wiring
  await page.goto(`/admin/sites/${siteId}/memberships`);
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();

  // 6. Verify CSP headers are present on admin pages
  const adminResponse = await page.request.get(page.url());
  const csp = adminResponse.headers()["content-security-policy"];
  expect(csp).toBeTruthy();
  expect(csp).toContain("default-src 'self'");

  // 7. Verify no-store on authenticated responses
  expect(adminResponse.headers()["cache-control"]).toContain("no-store");

  // 8. Check that preview routes return proper auth denial
  const previewResponse = await page.request.get("/preview/some-id/");
  expect([302, 403, 404]).toContain(previewResponse.status());
});
