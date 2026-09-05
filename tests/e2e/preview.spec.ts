import { expect, test } from "@playwright/test";
import { login, observe, secrets } from "./support";

test("authenticated-preview-renders-overlay-and-keeps-canonical-unchanged", async ({
  page,
}) => {
  const workspaceId = process.env.SLAIF_E2E_PREVIEW_WORKSPACE_ID;
  if (!workspaceId) throw new Error("missing preview fixture channel");
  const credential = secrets();
  const failures = observe(page);

  await login(page, credential);
  const response = await page.goto(`/preview/${workspaceId}/s/demo/`);
  expect(response).not.toBeNull();
  expect(response?.status()).toBe(200);
  expect(response?.headers()["cache-control"]).toContain("no-store");
  expect(response?.headers()["x-robots-tag"]).toContain("noindex");
  expect(response?.headers()["content-security-policy"]).toContain(
    "default-src 'self'",
  );
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Compose preview overlay",
  );
  await expect(page.getByRole("heading", { level: 2 })).toHaveText(
    "Compose overlay heading",
  );
  expect(await page.locator("main").getAttribute("data-render-mode")).toBe("preview");

  const storage = await page.evaluate(() => ({
    cookies: document.cookie,
    local: localStorage.length,
    session: sessionStorage.length,
  }));
  expect(storage.local).toBe(0);
  expect(storage.session).toBe(0);
  expect(storage.cookies).not.toContain("sas2_session_");
  expect(page.url()).not.toContain("sas2_session_");
  expect(await page.locator("body").innerText()).not.toContain(credential.setupToken);

  const previewRedirect = await page.request.get(
    `/preview/${workspaceId}/s/demo/compose-redirect`,
    { maxRedirects: 0 },
  );
  expect(previewRedirect.status(), await previewRedirect.text()).toBe(301);
  expect(previewRedirect.headers().location).toBe(`/preview/${workspaceId}/s/demo`);

  const canonical = await page.goto("/s/demo/");
  expect(canonical?.status()).toBe(200);
  await expect(page.getByRole("heading", { level: 1 })).not.toHaveText(
    "Compose preview overlay",
  );
  await expect(page.getByRole("heading", { level: 2 })).not.toHaveText(
    "Compose overlay heading",
  );
  expect(await page.locator("main").getAttribute("data-render-mode")).toBe("canonical");
  const canonicalRedirect = await page.request.get("/s/demo/compose-redirect", {
    maxRedirects: 0,
  });
  expect(canonicalRedirect.status()).toBe(404);

  expect(failures(), "unexpected preview browser failures").toEqual([]);
});
