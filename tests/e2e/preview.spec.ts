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

  const redirectCases = [
    { suffix: "301", status: 301, target: "/preview/" + workspaceId + "/s/demo" },
    { suffix: "302", status: 302, target: "/preview/" + workspaceId + "/s/demo" },
    { suffix: "303", status: 303, target: "/preview/" + workspaceId + "/s/demo" },
    { suffix: "307", status: 307, target: "/preview/" + workspaceId + "/s/demo" },
    { suffix: "308", status: 308, target: "/preview/" + workspaceId + "/s/demo" },
    {
      suffix: "external",
      status: 301,
      target: "https://example.test/compose-target",
    },
  ] as const;
  for (const redirectCase of redirectCases) {
    const previewRedirect = await page.request.get(
      "/preview/" + workspaceId + "/s/demo/compose-redirect-" + redirectCase.suffix,
      { maxRedirects: 0 },
    );
    const previewBody = await previewRedirect.text();
    const bodyClass = previewBody.includes("Render resolution failed")
      ? "render-error"
      : previewBody.includes("NEXT_REDIRECT")
        ? "next-redirect-error"
        : previewBody.includes("Internal Server Error")
          ? "internal-error"
          : previewBody.length === 0
            ? "empty"
            : "other";
    test.info().annotations = [
      {
        type: "stage",
        description:
          "preview-redirect-" +
          redirectCase.suffix +
          "-" +
          previewRedirect.status() +
          "-" +
          bodyClass,
      },
    ];
    expect(previewRedirect.status(), previewBody).toBe(redirectCase.status);
    expect(previewRedirect.headers().location).toBe(redirectCase.target);
    expect(previewRedirect.headers()["cache-control"]).toBe("private, no-store");
    expect(previewRedirect.headers()["x-robots-tag"]).toBe(
      "noindex, nofollow, noarchive",
    );
    expect(previewRedirect.headers()["content-security-policy"]).toContain(
      "default-src 'self'",
    );
    expect(previewBody).not.toContain(credential.setupToken);
    expect(previewBody).not.toContain("sas2_session_");

    const canonicalRedirect = await page.request.get(
      "/s/demo/compose-canonical-" + redirectCase.suffix,
      { maxRedirects: 0 },
    );
    const canonicalTarget =
      redirectCase.suffix === "external" ? redirectCase.target : "/s/demo";
    expect(canonicalRedirect.status()).toBe(redirectCase.status);
    expect(canonicalRedirect.headers().location).toBe(canonicalTarget);
  }

  const canonical = await page.goto("/s/demo/");
  expect(canonical?.status()).toBe(200);
  await expect(page.getByRole("heading", { level: 1 })).not.toHaveText(
    "Compose preview overlay",
  );
  await expect(page.getByRole("heading", { level: 2 })).not.toHaveText(
    "Compose overlay heading",
  );
  expect(await page.locator("main").getAttribute("data-render-mode")).toBe("canonical");
  const previewOnlyCanonicalRedirect = await page.request.get(
    "/s/demo/compose-redirect",
    {
      maxRedirects: 0,
    },
  );
  expect(previewOnlyCanonicalRedirect.status()).toBe(404);

  expect(failures(), "unexpected preview browser failures").toEqual([]);
});
