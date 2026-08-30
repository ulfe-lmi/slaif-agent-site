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
  await page.reload();
  await expect(page.getByText("E2E Agent session")).toBeVisible();
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

test("human-agent-l4-session-preserves-limits-through-reload-and-revoke", async ({
  page,
}) => {
  const credential = secrets();
  const failures = observe(page, [/\/api\/agent\/v1\/session$/]);
  await login(page, credential);
  const siteLink = page.getByRole("link", { name: /SLAIF Demo Site/ }).first();
  const href = await siteLink.getAttribute("href");
  await page.goto(href!);
  await expectAdminUsable(page);
  await page.getByLabel("Delegation preset").selectOption("L4_SITE_ARCHITECT");
  await page.getByLabel("Session title").fill("E2E L4 Agent session");
  await page.getByText("Advanced source and resource restrictions").click();
  await page.getByLabel("Approved HTTP(S) origin").fill("https://example.com");
  await page.getByLabel("Resource constraints (JSON)").fill('{"max_items":100}');
  await page.getByRole("button", { name: "Create Agent session" }).click();
  const secret = page.locator(".one-time-secret code");
  await expect(secret).toHaveText(/^sas2_[^\s]+$/);
  const token = await secret.textContent();
  expect(token).toBeTruthy();
  const agent = await page.request.get("/api/agent/v1/session", {
    headers: { Authorization: `Bearer ${token!}` },
  });
  expect(agent.status()).toBe(200);
  const session = (await agent.json()) as {
    scopes: string[];
    resource_constraints: Record<string, unknown>;
  };
  expect(session.scopes).toContain("content-model:create");
  expect(session.resource_constraints).toEqual({ max_items: 100 });
  await page.getByRole("button", { name: "Dismiss" }).click();
  await page.reload();
  await expect(page.getByText("E2E L4 Agent session")).toBeVisible();
  await expect(page.locator(".one-time-secret")).toHaveCount(0);
  const revoke = page.getByRole("button", { name: "Revoke" }).last();
  await revoke.click();
  await expect(page.getByText("REVOKED")).toBeVisible();
  expect(
    (
      await page.request.get("/api/agent/v1/session", {
        headers: { Authorization: `Bearer ${token!}` },
      })
    ).status(),
  ).toBe(401);
  expect(failures()).toEqual([]);
});
