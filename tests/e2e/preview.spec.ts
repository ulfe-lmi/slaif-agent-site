import { expect, test } from "@playwright/test";
import { login, observe, secrets } from "./support";

async function rendererEvidence(page: import("@playwright/test").Page) {
  return page.evaluate(() => {
    const styles = (selector: string) => {
      const element = document.querySelector(selector);
      if (!(element instanceof HTMLElement)) throw new Error(`missing ${selector}`);
      const style = getComputedStyle(element);
      return {
        backgroundColor: style.backgroundColor,
        borderRadius: style.borderRadius,
        borderTopColor: style.borderTopColor,
        borderTopStyle: style.borderTopStyle,
        borderTopWidth: style.borderTopWidth,
        boxSizing: style.boxSizing,
        className: element.getAttribute("class"),
        display: style.display,
        fontSize: style.fontSize,
        fontWeight: style.fontWeight,
        gap: style.gap,
        gridTemplateColumns: style.gridTemplateColumns,
        letterSpacing: style.letterSpacing,
        lineHeight: style.lineHeight,
        marginBottom: style.marginBottom,
        marginTop: style.marginTop,
        minHeight: style.minHeight,
        paddingBottom: style.paddingBottom,
        paddingLeft: style.paddingLeft,
        paddingRight: style.paddingRight,
        paddingTop: style.paddingTop,
      };
    };
    const stylesheet = document.querySelector(
      'link[rel="stylesheet"][href="/renderer-v1.css"]',
    );
    return {
      detail: styles('[data-component="CollectionDetail"] .renderer-collection-detail'),
      detailHeading: styles(
        '[data-component="CollectionDetail"] .renderer-collection-detail h2',
      ),
      detailSummary: styles(
        '[data-component="CollectionDetail"] .renderer-collection-detail p',
      ),
      grid: styles('[data-component="Grid"] .renderer-grid'),
      gridArticle: styles(
        '[data-component="CollectionGrid"] .renderer-collection article',
      ),
      gridHeading: styles(
        '[data-component="CollectionGrid"] .renderer-collection article h2',
      ),
      gridSummary: styles(
        '[data-component="CollectionGrid"] .renderer-collection article p',
      ),
      listArticle: styles(
        '[data-component="CollectionList"] .renderer-collection article',
      ),
      listHeading: styles(
        '[data-component="CollectionList"] .renderer-collection article h2',
      ),
      listSummary: styles(
        '[data-component="CollectionList"] .renderer-collection article p',
      ),
      stylesheetCount: document.querySelectorAll(
        'link[rel="stylesheet"][href="/renderer-v1.css"]',
      ).length,
      stylesheetLoaded:
        stylesheet instanceof HTMLLinkElement && stylesheet.sheet !== null,
      surfaceLang: document
        .querySelector("main.renderer-surface")
        ?.getAttribute("lang"),
      title: styles("#page-title"),
    };
  });
}

test("authenticated-preview-renders-overlay-and-keeps-canonical-unchanged", async ({
  page,
}) => {
  const workspaceId = process.env.SLAIF_E2E_PREVIEW_WORKSPACE_ID;
  if (!workspaceId) throw new Error("missing preview fixture channel");
  const credential = secrets();
  const failures = observe(page);

  await login(page, credential);
  await page.setViewportSize({ width: 1440, height: 900 });
  const response = await page.goto(`/preview/${workspaceId}/s/parity/`);
  expect(response).not.toBeNull();
  if (response?.status() !== 200) {
    const body = await response?.text();
    const bodyClass = body?.includes("NEXT_NOT_FOUND")
      ? "next-not-found"
      : body?.includes("Render resolution failed")
        ? "render-error"
        : body?.includes("Internal Server Error")
          ? "internal-error"
          : body?.length === 0
            ? "empty"
            : "other";
    test.info().annotations = [
      {
        type: "stage",
        description: `preview-status-${response?.status()}-${bodyClass}`,
      },
    ];
    throw new Error(`preview-status-${response?.status()}-body-${bodyClass}`);
  }
  expect(response?.headers()["cache-control"]).toContain("no-store");
  expect(response?.headers()["x-robots-tag"]).toContain("noindex");
  expect(response?.headers()["content-security-policy"]).toContain(
    "default-src 'self'",
  );
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Compose preview overlay",
  );
  await expect(
    page.locator('[data-component="Heading"] .renderer-heading').first(),
  ).toHaveText("Compose overlay heading");
  expect(await page.locator("main").getAttribute("data-render-mode")).toBe("preview");
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.locator("main.renderer-surface")).toHaveAttribute("lang", "en");
  expect(await page.title()).toBe("Compose preview overlay");
  await expect(
    page.locator('link[rel="stylesheet"][href="/renderer-v1.css"]'),
  ).toHaveCount(1);
  const stylesheet = await page.request.get("/renderer-v1.css");
  expect(stylesheet.status()).toBe(200);
  expect(await stylesheet.text()).toContain(".renderer-collection-detail");
  const previewDesktop = await rendererEvidence(page);
  expect(previewDesktop.stylesheetCount).toBe(1);
  expect(previewDesktop.stylesheetLoaded).toBe(true);
  expect(previewDesktop.surfaceLang).toBe("en");
  expect(previewDesktop.title.boxSizing).toBe("border-box");
  expect(previewDesktop.listArticle.borderTopStyle).toBe("solid");
  expect(previewDesktop.listArticle.paddingTop).toBe("24px");
  expect(previewDesktop.grid.display).toBe("grid");
  expect(previewDesktop.detail.borderTopStyle).toBe("solid");

  const previewHtml = await page.content();
  expect(previewHtml).not.toMatch(
    /[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/i,
  );
  expect(previewHtml).not.toMatch(/__next_f|self\.__next_f|_rsc=|NEXT_DATA/i);

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

  await page.setViewportSize({ width: 390, height: 800 });
  await page.reload();
  const previewMobile = await rendererEvidence(page);
  expect(previewMobile.stylesheetCount).toBe(1);
  expect(previewMobile.stylesheetLoaded).toBe(true);
  expect(previewMobile.grid.gridTemplateColumns).not.toContain(",");
  expect(previewMobile.listArticle.gridTemplateColumns).toBe("none");
  expect(previewMobile.detail.paddingTop).toBe("24px");
  expect(previewMobile.surfaceLang).toBe("en");
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.reload();

  const redirectCases = [
    { suffix: "301", status: 301, target: "/preview/" + workspaceId + "/s/parity" },
    { suffix: "302", status: 302, target: "/preview/" + workspaceId + "/s/parity" },
    { suffix: "303", status: 303, target: "/preview/" + workspaceId + "/s/parity" },
    { suffix: "307", status: 307, target: "/preview/" + workspaceId + "/s/parity" },
    { suffix: "308", status: 308, target: "/preview/" + workspaceId + "/s/parity" },
    {
      suffix: "external",
      status: 301,
      target: "https://example.test/compose-target",
    },
  ] as const;
  for (const redirectCase of redirectCases) {
    const previewRedirect = await page.request.get(
      "/preview/" + workspaceId + "/s/parity/compose-redirect-" + redirectCase.suffix,
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
      "/s/parity/compose-canonical-" + redirectCase.suffix,
      { maxRedirects: 0 },
    );
    const canonicalTarget =
      redirectCase.suffix === "external" ? redirectCase.target : "/s/parity";
    expect(canonicalRedirect.status()).toBe(redirectCase.status);
    expect(canonicalRedirect.headers().location).toBe(canonicalTarget);
  }

  const canonical = await page.goto("/s/parity/");
  expect(canonical?.status()).toBe(200);
  await expect(page.getByRole("heading", { level: 1 })).not.toHaveText(
    "Compose preview overlay",
  );
  await expect(
    page.locator('[data-component="Heading"] .renderer-heading').first(),
  ).not.toHaveText("Compose overlay heading");
  expect(await page.locator("main").getAttribute("data-render-mode")).toBe("canonical");
  await expect(page.locator("main.renderer-surface")).toHaveAttribute("lang", "en");
  const canonicalDesktop = await rendererEvidence(page);
  expect(canonicalDesktop).toEqual(previewDesktop);
  await page.setViewportSize({ width: 390, height: 800 });
  await page.reload();
  const canonicalMobile = await rendererEvidence(page);
  expect(canonicalMobile).toEqual(previewMobile);

  const localizedPreview = await page.goto(
    `/preview/${workspaceId}/s/parity/sl-si/parity/`,
  );
  expect(localizedPreview?.status()).toBe(200);
  await expect(page.locator("html")).toHaveAttribute("lang", "sl-SI");
  await expect(page.locator("main.renderer-surface")).toHaveAttribute("lang", "sl-SI");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Slovenska domača stran",
  );
  await expect(page.locator("body")).toContainText("Prvi članek");
  const localizedPreviewEvidence = await rendererEvidence(page);
  expect(localizedPreviewEvidence.surfaceLang).toBe("sl-SI");

  const localizedCanonical = await page.goto("/s/parity/sl-si/parity/");
  expect(localizedCanonical?.status()).toBe(200);
  await expect(page.locator("html")).toHaveAttribute("lang", "en");
  await expect(page.locator("main.renderer-surface")).toHaveAttribute("lang", "sl-SI");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Slovenska domača stran",
  );
  await expect(page.locator("body")).toContainText("Prvi članek");
  expect(await rendererEvidence(page)).toEqual(localizedPreviewEvidence);

  await page.goto("/admin");
  await expect(page.locator(".admin-shell")).toBeVisible();
  await expect(
    page.locator('link[rel="stylesheet"][href="/renderer-v1.css"]'),
  ).toHaveCount(0);
  await page.goto("/login");
  await expect(page.locator(".auth-card")).toBeVisible();
  await expect(
    page.locator('link[rel="stylesheet"][href="/renderer-v1.css"]'),
  ).toHaveCount(0);
  await expect(page.locator("main.renderer-surface")).toHaveCount(0);

  const previewOnlyCanonicalRedirect = await page.request.get(
    "/s/parity/compose-redirect",
    {
      maxRedirects: 0,
    },
  );
  expect(previewOnlyCanonicalRedirect.status()).toBe(404);

  expect(failures(), "unexpected preview browser failures").toEqual([]);
});
