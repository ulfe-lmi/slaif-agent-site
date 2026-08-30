import { expect, test } from "@playwright/test";

import { expectAdminUsable, login, observe, secrets } from "./support";

test("human-agent-session-is-one-time-bound-and-revocable", async ({ page }) => {
  const credential = secrets();
  const failures = observe(page, [/\/api\/agent\/v1\/session$/]);
  await login(page, credential);
  const siteLink = page.getByRole("link", { name: /SLAIF Demo Site/ }).first();
  const href = await siteLink.getAttribute("href");
  expect(href).toMatch(/^\/admin\/sites\/[0-9a-f-]+$/);
  await page.goto(href!);
  await expectAdminUsable(page);
  await page.getByLabel("Delegation preset").selectOption("L1_CONTENT_EDITOR");
  await page.getByLabel("Session title").fill("E2E Agent session");
  await page.getByRole("button", { name: "Create Agent session" }).click();
  const secret = page.locator(".one-time-secret code");
  await expect(secret).toHaveText(/^sas2_[^\s]+$/);
  const token = await secret.textContent();
  expect(token).toBeTruthy();
  const agent = await page.request.get("/api/agent/v1/session", {
    headers: { Authorization: `Bearer ${token!}` },
  });
  expect(agent.status()).toBe(200);
  await page.getByRole("button", { name: "Dismiss" }).click();
  await expect(page.locator(".one-time-secret")).toHaveCount(0);
  const storage = await page.evaluate(() => ({
    local: JSON.stringify(localStorage),
    session: JSON.stringify(sessionStorage),
    cookies: document.cookie,
  }));
  expect(storage.local).not.toContain(token!);
  expect(storage.session).not.toContain(token!);
  expect(storage.cookies).not.toContain(token!);
  await page.getByRole("button", { name: "Revoke" }).first().click();
  expect(
    (
      await page.request.get("/api/agent/v1/session", {
        headers: { Authorization: `Bearer ${token!}` },
      })
    ).status(),
  ).toBe(401);
  expect(failures()).toEqual([]);
});
