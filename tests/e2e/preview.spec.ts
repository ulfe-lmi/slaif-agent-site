import { expect, test } from "@playwright/test";
import { expectPrivateHeaders, login, observe, secrets } from "./support";

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

type ThemeOutput = {
  className: string;
  backgroundColor: string;
  color: string;
  fontFamily: string;
  fontSize: string;
  fontWeight: string;
  width: string;
  paddingTop: string;
  gridGap: string;
  borderRadius: string;
  boxShadow: string;
};

async function renderedThemeOutput(
  page: import("@playwright/test").Page,
): Promise<ThemeOutput> {
  return page.locator("main.renderer-surface").evaluate((root) => {
    const grid = document.querySelector(".renderer-grid");
    const article = document.querySelector(".renderer-collection article");
    if (
      !(root instanceof HTMLElement) ||
      !(grid instanceof HTMLElement) ||
      !(article instanceof HTMLElement)
    )
      throw new Error("agent-theme-computed-elements-missing");
    const rootStyle = getComputedStyle(root);
    const gridStyle = getComputedStyle(grid);
    const articleStyle = getComputedStyle(article);
    return {
      className: root.className,
      backgroundColor: rootStyle.backgroundColor,
      color: rootStyle.color,
      fontFamily: rootStyle.fontFamily,
      fontSize: rootStyle.fontSize,
      fontWeight: rootStyle.fontWeight,
      width: rootStyle.width,
      paddingTop: rootStyle.paddingTop,
      gridGap: gridStyle.gap,
      borderRadius: articleStyle.borderRadius,
      boxShadow: articleStyle.boxShadow,
    };
  });
}

function assertThemeOutput(
  output: ThemeOutput,
  expected: {
    palette: string;
    family: string;
    scale: string;
    weight: string;
    width: string;
    spacing: string;
    gap: string;
    radius: string;
    shadow: string;
    background: string;
    color: string;
    fontFamily: string;
    fontSize: string;
    fontWeight: string;
    contentWidth: string;
    paddingTop: string;
    gridGap: string;
    borderRadius: string;
    boxShadow: string;
  },
) {
  for (const [group, value] of [
    ["palette", expected.palette],
    ["family", expected.family],
    ["scale", expected.scale],
    ["weight", expected.weight],
    ["width", expected.width],
    ["spacing", expected.spacing],
    ["gap", expected.gap],
    ["radius", expected.radius],
    ["shadow", expected.shadow],
  ] as const) {
    expect(output.className).toContain(`renderer-theme-${group}--${value}`);
  }
  expect(output.backgroundColor).toBe(expected.background);
  expect(output.color).toBe(expected.color);
  expect(output.fontFamily).toContain(expected.fontFamily);
  expect(output.fontSize).toBe(expected.fontSize);
  expect(output.fontWeight).toBe(expected.fontWeight);
  expect(output.width).toBe(expected.contentWidth);
  expect(output.paddingTop).toBe(expected.paddingTop);
  expect(output.gridGap).toBe(expected.gridGap);
  expect(output.borderRadius).toBe(expected.borderRadius);
  expect(output.boxShadow).toBe(expected.boxShadow);
}

function canonicalRendererFingerprint(body: string) {
  const match = body.match(
    /<main class="([^"]*renderer-surface[^"]*)"[^>]*data-render-mode="canonical"[^>]*>([\s\S]*)<\/main>/,
  );
  if (!match) throw new Error("canonical-renderer-fingerprint-missing");
  return { className: match[1], content: match[2] };
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

test("renderer local design follows the documented responsive cascade", async ({
  page,
}) => {
  const response = await page.goto("/s/parity/");
  expect(response?.status()).toBe(200);
  await expect(
    page.locator('link[rel="stylesheet"][href="/renderer-v1.css"]'),
  ).toHaveCount(1);
  await page.evaluate(() => {
    const root = document.createElement("div");
    root.id = "local-design-evidence";
    root.innerHTML = `
      <section id="local-section" class="renderer-section renderer-section--narrow"></section>
      <div id="local-grid" class="renderer-grid renderer-grid--4 renderer-grid--tablet-2"></div>
      <div id="local-spacer" class="renderer-spacer renderer-spacer--md renderer-spacer--mobile-xl"></div>
      <a id="local-button" class="renderer-button renderer-button--secondary renderer-button--mobile-primary">Button</a>
      <div id="local-image" class="renderer-image-placeholder renderer-image-placeholder--16-9 renderer-image-placeholder--mobile-auto"></div>
    `;
    document.body.append(root);
  });
  const evidence = () =>
    page.evaluate(() => {
      const style = (id: string) => {
        const element = document.getElementById(id);
        if (!(element instanceof HTMLElement)) throw new Error(`missing-${id}`);
        const computed = getComputedStyle(element);
        return {
          maxWidth: computed.maxWidth,
          gridTemplateColumns: computed.gridTemplateColumns,
          minHeight: computed.minHeight,
          backgroundColor: computed.backgroundColor,
          color: computed.color,
          aspectRatio: computed.aspectRatio,
        };
      };
      return {
        section: style("local-section"),
        grid: style("local-grid"),
        spacer: style("local-spacer"),
        button: style("local-button"),
        image: style("local-image"),
      };
    });

  await page.setViewportSize({ width: 1440, height: 800 });
  const desktop = await evidence();
  expect(desktop.section.maxWidth).toBe("768px");
  expect(desktop.grid.gridTemplateColumns.split(" ")).toHaveLength(4);
  expect(desktop.image.aspectRatio).toBe("16 / 9");

  await page.setViewportSize({ width: 900, height: 800 });
  const tablet = await evidence();
  expect(tablet.grid.gridTemplateColumns.split(" ")).toHaveLength(2);

  await page.setViewportSize({ width: 390, height: 800 });
  const mobile = await evidence();
  expect(mobile.grid.gridTemplateColumns.split(" ")).toHaveLength(2);
  expect(mobile.spacer.minHeight).toBe("32px");
  expect(mobile.button.backgroundColor).toBe("rgb(168, 197, 56)");
  expect(mobile.button.color).toBe("rgb(8, 19, 23)");
  expect(mobile.image.minHeight).toBe("192px");
  expect(mobile.image.aspectRatio).toBe("auto");
});

test("renderer theme tokens preserve local precedence and semantic contrast", async ({
  page,
}) => {
  const response = await page.goto("/s/parity/");
  expect(response?.status()).toBe(200);
  await page.evaluate(() => {
    const surface = document.querySelector("main.renderer-surface");
    if (!(surface instanceof HTMLElement)) throw new Error("theme-surface-missing");
    const probe = document.createElement("div");
    probe.id = "theme-token-evidence";
    probe.innerHTML = `
      <div id="theme-grid" class="renderer-grid renderer-grid--2 renderer-gap--none renderer-gap--mobile-sm">grid</div>
      <a id="theme-primary" class="renderer-button renderer-button--primary" href="/">Primary</a>
      <a id="theme-secondary" class="renderer-button renderer-button--secondary" href="/">Secondary</a>
      <a id="theme-ghost" class="renderer-button renderer-button--ghost" href="/">Ghost</a>
    `;
    surface.append(probe);
  });
  await page.setViewportSize({ width: 1280, height: 800 });

  const paletteEvidence = async (palette: "ocean" | "meadow" | "ember") =>
    page.evaluate((nextPalette) => {
      const surface = document.querySelector("main.renderer-surface");
      if (!(surface instanceof HTMLElement)) throw new Error("theme-surface-missing");
      for (const token of ["ocean", "meadow", "ember"])
        surface.classList.remove(`renderer-theme-palette--${token}`);
      surface.classList.add(`renderer-theme-palette--${nextPalette}`);
      const rootStyle = getComputedStyle(surface);
      const rgb = (value: string): [number, number, number] => {
        const match = value.match(
          /^rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*[\d.]+)?\s*\)$/,
        );
        if (!match) throw new Error(`non-solid-color:${value}`);
        return [Number(match[1]), Number(match[2]), Number(match[3])];
      };
      const luminance = (value: string) => {
        const channels = rgb(value).map((channel) => {
          const normalized = channel / 255;
          return normalized <= 0.03928
            ? normalized / 12.92
            : ((normalized + 0.055) / 1.055) ** 2.4;
        });
        return 0.2126 * channels[0]! + 0.7152 * channels[1]! + 0.0722 * channels[2]!;
      };
      const contrast = (foreground: string, background: string) => {
        const foregroundLuminance = luminance(foreground);
        const backgroundLuminance = luminance(background);
        return (
          (Math.max(foregroundLuminance, backgroundLuminance) + 0.05) /
          (Math.min(foregroundLuminance, backgroundLuminance) + 0.05)
        );
      };
      const role = (id: string) => {
        const element = document.getElementById(id);
        if (!(element instanceof HTMLElement)) throw new Error(`missing-${id}`);
        const style = getComputedStyle(element);
        const background = style.backgroundColor.startsWith("rgba(0, 0, 0, 0)")
          ? rootStyle.backgroundColor
          : style.backgroundColor;
        return {
          background,
          color: style.color,
          contrast: contrast(style.color, background),
        };
      };
      return {
        palette: nextPalette,
        background: rootStyle.backgroundColor,
        color: rootStyle.color,
        roles: {
          primary: role("theme-primary"),
          secondary: role("theme-secondary"),
          ghost: role("theme-ghost"),
        },
      };
    }, palette);

  const expected = {
    ocean: { background: "rgb(11, 28, 34)", color: "rgb(244, 247, 248)" },
    meadow: { background: "rgb(240, 248, 241)", color: "rgb(18, 53, 29)" },
    ember: { background: "rgb(255, 247, 237)", color: "rgb(66, 32, 6)" },
  } as const;
  for (const palette of ["ocean", "meadow", "ember"] as const) {
    const evidence = await paletteEvidence(palette);
    expect(evidence.background).toBe(expected[palette].background);
    expect(evidence.color).toBe(expected[palette].color);
    expect(evidence.roles.primary.contrast).toBeGreaterThanOrEqual(4.5);
    expect(evidence.roles.secondary.contrast).toBeGreaterThanOrEqual(4.5);
    expect(evidence.roles.ghost.contrast).toBeGreaterThanOrEqual(4.5);
  }

  const configured = await page.evaluate(() => {
    const surface = document.querySelector("main.renderer-surface");
    const grid = document.getElementById("theme-grid");
    if (!(surface instanceof HTMLElement) || !(grid instanceof HTMLElement))
      throw new Error("theme-computed-elements-missing");
    surface.className = [
      "renderer-surface",
      "renderer-theme-palette--meadow",
      "renderer-theme-family--serif",
      "renderer-theme-scale--spacious",
      "renderer-theme-weight--bold",
      "renderer-theme-width--xl",
      "renderer-theme-spacing--lg",
      "renderer-theme-gap--lg",
      "renderer-theme-radius--lg",
      "renderer-theme-shadow--md",
    ].join(" ");
    const rootStyle = getComputedStyle(surface);
    const gridStyle = getComputedStyle(grid);
    return {
      family: rootStyle.fontFamily,
      fontSize: rootStyle.fontSize,
      fontWeight: rootStyle.fontWeight,
      width: rootStyle.width,
      paddingTop: rootStyle.paddingTop,
      gridGap: gridStyle.gap,
    };
  });
  expect(configured.family).toContain("Georgia");
  expect(configured.fontSize).toBe("17px");
  expect(configured.fontWeight).toBe("700");
  expect(configured.width).toBe("1248px");
  expect(configured.paddingTop).toBe("64px");
  expect(configured.gridGap).toBe("0px");

  await page.setViewportSize({ width: 390, height: 800 });
  await expect
    .poll(() =>
      page.evaluate(() => {
        const grid = document.getElementById("theme-grid");
        if (!(grid instanceof HTMLElement)) throw new Error("theme-grid-missing");
        return getComputedStyle(grid).gap;
      }),
    )
    .toBe("8px");

  const reset = await page.evaluate(() => {
    const surface = document.querySelector("main.renderer-surface");
    if (!(surface instanceof HTMLElement)) throw new Error("theme-surface-missing");
    surface.className = [
      "renderer-surface",
      "renderer-theme-palette--ocean",
      "renderer-theme-family--system",
      "renderer-theme-scale--balanced",
      "renderer-theme-weight--regular",
      "renderer-theme-width--md",
      "renderer-theme-spacing--md",
      "renderer-theme-gap--md",
      "renderer-theme-radius--md",
      "renderer-theme-shadow--sm",
    ].join(" ");
    const style = getComputedStyle(surface);
    return {
      background: style.backgroundColor,
      color: style.color,
      fontSize: style.fontSize,
      fontWeight: style.fontWeight,
    };
  });
  expect(reset).toEqual({
    background: "rgb(11, 28, 34)",
    color: "rgb(244, 247, 248)",
    fontSize: "16px",
    fontWeight: "400",
  });
});

test("human-editor-theme-is-preview-scoped-and-computed", async ({ page }) => {
  const workspaceId = process.env.SLAIF_E2E_PREVIEW_WORKSPACE_ID;
  if (!workspaceId) throw new Error("missing preview fixture channel");
  const credential = secrets();
  const failures = observe(page);

  await login(page, credential);
  const sitesResponse = await page.request.get("/api/control/v1/me/sites");
  expect(sitesResponse.status()).toBe(200);
  const sites = (await sitesResponse.json()) as Array<{
    site_id: string;
    site_key: string;
  }>;
  const parity = sites.find((site) => site.site_key === "parity");
  expect(parity).toBeDefined();
  const csrf = (await page.context().cookies()).find(
    (cookie) => cookie.name === "slaif_csrf",
  )?.value;
  expect(csrf).toBeTruthy();
  const themeResponse = await page.request.patch(
    `/api/editor/v1/sites/${parity!.site_id}/theme`,
    {
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf!,
        "Idempotency-Key": crypto.randomUUID(),
      },
      data: {
        palette: { preset: "meadow" },
        typography: { family: "serif", scale: "spacious", weight: "bold" },
        layout: { content_width: "xl", spacing: "lg", grid_gap: "sm" },
        shape: { radius: "lg", shadow: "md" },
      },
    },
  );
  expect(themeResponse.status()).toBe(200);
  const savedTheme = (await themeResponse.json()) as {
    row_version: number;
    palette: { preset: string };
    typography: { family: string; scale: string; weight: string };
    layout: { content_width: string; spacing: string; grid_gap: string };
    shape: { radius: string; shadow: string };
  };
  expect(savedTheme).toMatchObject({
    row_version: 2,
    palette: { preset: "meadow" },
    typography: { family: "serif", scale: "spacious", weight: "bold" },
    layout: { content_width: "xl", spacing: "lg", grid_gap: "sm" },
    shape: { radius: "lg", shadow: "md" },
  });

  await page.setViewportSize({ width: 1440, height: 900 });
  const previewResponse = await page.goto(`/preview/${workspaceId}/s/parity/`);
  expect(previewResponse?.status()).toBe(200);
  const previewTheme = await page.locator("main.renderer-surface").evaluate((root) => {
    const rootStyle = getComputedStyle(root);
    const grid = document.querySelector(".renderer-grid");
    const article = document.querySelector(".renderer-collection article");
    if (!(grid instanceof HTMLElement) || !(article instanceof HTMLElement))
      throw new Error("theme-computed-elements-missing");
    const gridStyle = getComputedStyle(grid);
    const articleStyle = getComputedStyle(article);
    return {
      className: root.getAttribute("class"),
      backgroundColor: rootStyle.backgroundColor,
      color: rootStyle.color,
      fontFamily: rootStyle.fontFamily,
      fontSize: rootStyle.fontSize,
      fontWeight: rootStyle.fontWeight,
      width: rootStyle.width,
      paddingTop: rootStyle.paddingTop,
      gridGap: gridStyle.gap,
      borderRadius: articleStyle.borderRadius,
      boxShadow: articleStyle.boxShadow,
    };
  });
  expect(previewTheme.className).toContain("renderer-theme-palette--meadow");
  expect(previewTheme.className).toContain("renderer-theme-family--serif");
  expect(previewTheme.className).toContain("renderer-theme-scale--spacious");
  expect(previewTheme.className).toContain("renderer-theme-weight--bold");
  expect(previewTheme.className).toContain("renderer-theme-width--xl");
  expect(previewTheme.className).toContain("renderer-theme-spacing--lg");
  expect(previewTheme.className).toContain("renderer-theme-gap--sm");
  expect(previewTheme.className).toContain("renderer-theme-radius--lg");
  expect(previewTheme.className).toContain("renderer-theme-shadow--md");
  expect(previewTheme.backgroundColor).toBe("rgb(240, 248, 241)");
  expect(previewTheme.color).toBe("rgb(18, 53, 29)");
  expect(previewTheme.fontFamily).toContain("Georgia");
  expect(previewTheme.fontSize).toBe("17px");
  expect(previewTheme.fontWeight).toBe("700");
  expect(previewTheme.width).toBe("1408px");
  expect(previewTheme.paddingTop).toBe("64px");
  expect(previewTheme.gridGap).toBe("16px");
  expect(previewTheme.borderRadius).toBe("20px");
  expect(previewTheme.boxShadow).not.toBe("none");

  const canonicalResponse = await page.goto("/s/parity/");
  expect(canonicalResponse?.status()).toBe(200);
  const canonicalClass = await page
    .locator("main.renderer-surface")
    .getAttribute("class");
  expect(canonicalClass).toContain("renderer-theme-palette--ocean");
  expect(canonicalClass).not.toContain("renderer-theme-palette--meadow");
  const resetTheme = await page.request.patch(
    `/api/editor/v1/sites/${parity!.site_id}/theme`,
    {
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrf!,
        "Idempotency-Key": crypto.randomUUID(),
      },
      data: {
        palette: { preset: "ocean" },
        typography: { family: "system", scale: "balanced", weight: "regular" },
        layout: { content_width: "md", spacing: "md", grid_gap: "md" },
        shape: { radius: "md", shadow: "sm" },
      },
    },
  );
  expect(resetTheme.status()).toBe(200);
  expect(failures(), "unexpected theme browser failures").toEqual([]);
});

test("agent-theme-patch-renders-in-the-same-authorized-workspace", async ({ page }) => {
  const credential = secrets();
  const failures = observe(page);
  const tag = crypto.randomUUID();

  await login(page, credential);
  const sitesResponse = await page.request.get("/api/control/v1/me/sites");
  expect(sitesResponse.status()).toBe(200);
  const sites = (await sitesResponse.json()) as Array<{
    site_id: string;
    site_key: string;
  }>;
  const parity = sites.find((site) => site.site_key === "parity");
  const demo = sites.find((site) => site.site_key === "demo");
  expect(parity).toBeDefined();
  expect(demo).toBeDefined();
  const csrf =
    (await page.context().cookies()).find((cookie) => cookie.name === "slaif_csrf")
      ?.value ?? "";
  expect(csrf).toBeTruthy();

  const workspacePath = `/api/control/v1/sites/${parity!.site_id}/workspaces/`;
  const createWorkspace = async (title: string, key: string) => {
    const response = await page.request.post(workspacePath, {
      headers: { "X-CSRF-Token": csrf, "Idempotency-Key": key },
      data: {
        title,
        task_description: "Bounded Agent theme output proof",
        delegation_preset: "L4_SITE_ARCHITECT",
        duration_hours: 1,
        request_quota: 1000,
        mutation_quota: 200,
        delete_quota: 50,
        upload_quota: 0,
        browser_quota: 1,
        resource_constraints: { delete_enabled: true, max_deletes: 50 },
      },
    });
    expect(response.status()).toBe(201);
    const document = (await response.json()) as { workspace_id?: unknown };
    expect(typeof document.workspace_id).toBe("string");
    return document.workspace_id as string;
  };
  const agentWorkspace = await createWorkspace(
    `OAP 078-s Agent theme ${tag}`,
    `oap-078s-agent-workspace-${tag}`,
  );
  const defaultWorkspace = await createWorkspace(
    `OAP 078-s default control ${tag}`,
    `oap-078s-default-workspace-${tag}`,
  );
  const capabilityResponse = await page.request.post(
    `${workspacePath}${agentWorkspace}/capabilities/`,
    {
      headers: {
        "X-CSRF-Token": csrf,
        "Idempotency-Key": `oap-078s-agent-capability-${tag}`,
      },
    },
  );
  expect(capabilityResponse.status()).toBe(201);
  const capability = (await capabilityResponse.json()) as {
    capability_id?: unknown;
    token?: unknown;
  };
  expect(typeof capability.capability_id).toBe("string");
  expect(typeof capability.token).toBe("string");
  const capabilityId = capability.capability_id as string;
  const agentToken = capability.token as string;

  const initialThemeResponse = await page.request.get("/api/agent/v1/theme", {
    headers: { Authorization: `Bearer ${agentToken}` },
  });
  expect(initialThemeResponse.status()).toBe(200);
  const initialTheme = (await initialThemeResponse.json()) as {
    row_version?: unknown;
  };
  expect(initialTheme.row_version).toBe(1);
  const themeBody = {
    expected_row_version: 1,
    palette: { preset: "meadow" },
    typography: { family: "serif", scale: "spacious", weight: "bold" },
    layout: { content_width: "xl", spacing: "lg", grid_gap: "sm" },
    shape: { radius: "lg", shadow: "md" },
  };
  const themeUpdateResponse = await page.request.patch("/api/agent/v1/theme", {
    headers: {
      Authorization: `Bearer ${agentToken}`,
      "Idempotency-Key": `oap-078s-agent-theme-${tag}`,
    },
    data: themeBody,
  });
  expect(themeUpdateResponse.status()).toBe(200);
  const themeUpdate = (await themeUpdateResponse.json()) as {
    record?: Record<string, unknown>;
  };
  expect(themeUpdate.record).toMatchObject({
    row_version: 2,
    palette: { preset: "meadow" },
    typography: { family: "serif", scale: "spacious", weight: "bold" },
    layout: { content_width: "xl", spacing: "lg", grid_gap: "sm" },
    shape: { radius: "lg", shadow: "md" },
  });

  const canonicalBefore = await page.request.get("/s/parity/");
  expect(canonicalBefore.status()).toBe(200);
  const canonicalBeforeBody = await canonicalBefore.text();
  const canonicalBeforeFingerprint = canonicalRendererFingerprint(canonicalBeforeBody);
  expect(canonicalBeforeBody).toContain("renderer-theme-palette--ocean");
  const otherSiteBefore = await page.request.get("/s/demo");
  expect(otherSiteBefore.status()).toBe(200);
  const otherSiteBeforeBody = await otherSiteBefore.text();
  const otherSiteBeforeFingerprint = canonicalRendererFingerprint(otherSiteBeforeBody);
  await page.setViewportSize({ width: 1440, height: 900 });
  const defaultBefore = await page.goto(`/preview/${defaultWorkspace}/s/parity/`);
  expectPrivateHeaders(defaultBefore!);
  const defaultBeforeOutput = await renderedThemeOutput(page);

  await page.setViewportSize({ width: 1440, height: 900 });
  const agentPreviewPath = `/preview/${agentWorkspace}/s/parity/`;
  const agentPreview = await page.goto(agentPreviewPath);
  expectPrivateHeaders(agentPreview!);
  expect(agentPreview?.status()).toBe(200);
  const expectedAgentOutput = {
    palette: "meadow",
    family: "serif",
    scale: "spacious",
    weight: "bold",
    width: "xl",
    spacing: "lg",
    gap: "sm",
    radius: "lg",
    shadow: "md",
    background: "rgb(240, 248, 241)",
    color: "rgb(18, 53, 29)",
    fontFamily: "Georgia",
    fontSize: "17px",
    fontWeight: "700",
    contentWidth: "1408px",
    paddingTop: "64px",
    gridGap: "16px",
    borderRadius: "20px",
    boxShadow: "rgba(0, 0, 0, 0.18) 0px 8px 24px 0px",
  };
  const actualAgentOutput = await renderedThemeOutput(page);
  assertThemeOutput(actualAgentOutput, expectedAgentOutput);

  const routePattern = `**${agentPreviewPath}`;
  await page.route(routePattern, async (route) => {
    const upstream = await route.fetch();
    const wrongTheme = (await upstream.text())
      .replaceAll("renderer-theme-palette--meadow", "renderer-theme-palette--ocean")
      .replaceAll("renderer-theme-family--serif", "renderer-theme-family--system")
      .replaceAll("renderer-theme-scale--spacious", "renderer-theme-scale--balanced")
      .replaceAll("renderer-theme-weight--bold", "renderer-theme-weight--regular")
      .replaceAll("renderer-theme-width--xl", "renderer-theme-width--md")
      .replaceAll("renderer-theme-spacing--lg", "renderer-theme-spacing--md")
      .replaceAll("renderer-theme-gap--sm", "renderer-theme-gap--md")
      .replaceAll("renderer-theme-radius--lg", "renderer-theme-radius--md")
      .replaceAll("renderer-theme-shadow--md", "renderer-theme-shadow--sm");
    await route.fulfill({ response: upstream, body: wrongTheme });
  });
  try {
    const negativePreview = await page.goto(agentPreviewPath);
    expectPrivateHeaders(negativePreview!);
    const negativeOutput = await renderedThemeOutput(page);
    let detectedWrongOutput = false;
    try {
      assertThemeOutput(negativeOutput, expectedAgentOutput);
    } catch {
      detectedWrongOutput = true;
    }
    expect(detectedWrongOutput).toBe(true);
  } finally {
    await page.unroute(routePattern);
  }
  const restoredPreview = await page.goto(agentPreviewPath);
  expectPrivateHeaders(restoredPreview!);
  assertThemeOutput(await renderedThemeOutput(page), expectedAgentOutput);

  const pagesResponse = await page.request.get("/api/agent/v1/pages/", {
    headers: { Authorization: `Bearer ${agentToken}` },
  });
  expect(pagesResponse.status()).toBe(200);
  const pages = (await pagesResponse.json()) as Array<{
    id?: unknown;
    slug?: unknown;
  }>;
  const otherPageCreate = await page.request.post("/api/agent/v1/pages/", {
    headers: {
      Authorization: `Bearer ${agentToken}`,
      "Idempotency-Key": `oap-078y-untouched-page-${tag}`,
    },
    data: { slug: `untouched-${tag}`, title: "Untouched page", locale: "en" },
  });
  expect(otherPageCreate.status()).toBe(201);
  const otherPageCreateBody = (await otherPageCreate.json()) as {
    record?: { id?: unknown };
  };
  expect(typeof otherPageCreateBody.record?.id).toBe("string");
  const otherPageId = otherPageCreateBody.record!.id as string;
  const otherPageStyleBeforeResponse = await page.request.get(
    `/api/agent/v1/pages/${otherPageId}/style`,
    { headers: { Authorization: `Bearer ${agentToken}` } },
  );
  expect(otherPageStyleBeforeResponse.status()).toBe(200);
  const otherPageStyleBefore = (await otherPageStyleBeforeResponse.json()) as Record<
    string,
    unknown
  >;
  const homePage = pages.find((candidate) => candidate.slug === "home");
  expect(typeof homePage?.id).toBe("string");
  const homePageId = homePage?.id as string;
  const pageStylePath = `/api/agent/v1/pages/${homePageId}/style`;
  const initialPageStyle = await page.request.get(pageStylePath, {
    headers: { Authorization: `Bearer ${agentToken}` },
  });
  expect(initialPageStyle.status()).toBe(200);
  const initialPageStyleRecord = (await initialPageStyle.json()) as {
    row_version?: unknown;
    overrides?: unknown;
  };
  expect(initialPageStyleRecord.overrides).toEqual({});
  expect(initialPageStyleRecord.row_version).toBe(1);
  const pageStyleUpdate = await page.request.patch(pageStylePath, {
    headers: {
      Authorization: `Bearer ${agentToken}`,
      "Idempotency-Key": `oap-078w-page-style-${tag}`,
    },
    data: {
      expected_row_version: 1,
      palette: { preset: "ember" },
      typography: { family: "system", scale: "compact", weight: "regular" },
      layout: { content_width: "sm", spacing: "sm", grid_gap: "lg" },
      shape: { radius: "none", shadow: "none" },
      reset_tokens: [],
    },
  });
  expect(pageStyleUpdate.status()).toBe(200);
  const pageStyleUpdateBody = (await pageStyleUpdate.json()) as {
    action?: unknown;
    record?: { row_version?: unknown; overrides?: unknown };
  };
  expect(pageStyleUpdateBody.action).toBe("PAGE_STYLE_UPDATED");
  expect(pageStyleUpdateBody.record).toMatchObject({
    row_version: 2,
    overrides: {
      palette: { preset: "ember" },
      typography: { family: "system", scale: "compact", weight: "regular" },
      layout: { content_width: "sm", spacing: "sm", grid_gap: "lg" },
      shape: { radius: "none", shadow: "none" },
    },
  });
  const pageStylePreview = await page.goto(agentPreviewPath);
  expectPrivateHeaders(pageStylePreview!);
  assertThemeOutput(await renderedThemeOutput(page), {
    palette: "ember",
    family: "system",
    scale: "compact",
    weight: "regular",
    width: "sm",
    spacing: "sm",
    gap: "lg",
    radius: "none",
    shadow: "none",
    background: "rgb(255, 247, 237)",
    color: "rgb(66, 32, 6)",
    fontFamily: "Inter",
    fontSize: "15px",
    fontWeight: "400",
    contentWidth: "768px",
    paddingTop: "24px",
    // The page-style gap class is present, but the existing component-local
    // gap remains authoritative at the rendered component.
    gridGap: "16px",
    borderRadius: "0px",
    boxShadow: "none",
  });
  const pageStyleReset = await page.request.patch(pageStylePath, {
    headers: {
      Authorization: `Bearer ${agentToken}`,
      "Idempotency-Key": `oap-078w-page-style-reset-${tag}`,
    },
    data: {
      expected_row_version: 2,
      reset_tokens: [
        "palette.preset",
        "typography.family",
        "typography.scale",
        "typography.weight",
        "layout.content_width",
        "layout.spacing",
        "layout.grid_gap",
        "shape.radius",
        "shape.shadow",
      ],
    },
  });
  expect(pageStyleReset.status()).toBe(200);
  const pageStyleResetBody = (await pageStyleReset.json()) as {
    record?: { row_version?: unknown; overrides?: unknown };
  };
  expect(pageStyleResetBody.record).toMatchObject({
    row_version: 3,
    overrides: {},
  });
  const inheritedPageStylePreview = await page.goto(agentPreviewPath);
  expectPrivateHeaders(inheritedPageStylePreview!);
  assertThemeOutput(await renderedThemeOutput(page), expectedAgentOutput);

  const partialPageStyleUpdate = await page.request.patch(pageStylePath, {
    headers: {
      Authorization: `Bearer ${agentToken}`,
      "Idempotency-Key": `oap-078y-page-style-partial-${tag}`,
    },
    data: {
      expected_row_version: 3,
      palette: { preset: "ember" },
      typography: { family: "mono" },
      layout: { content_width: "sm" },
      shape: { radius: "none" },
      reset_tokens: [],
    },
  });
  expect(partialPageStyleUpdate.status()).toBe(200);
  const partialPageStyleBody = (await partialPageStyleUpdate.json()) as {
    action?: unknown;
    record?: { row_version?: unknown; overrides?: unknown };
  };
  expect(partialPageStyleBody).toMatchObject({
    action: "PAGE_STYLE_UPDATED",
    record: {
      row_version: 4,
      overrides: {
        palette: { preset: "ember" },
        typography: { family: "mono" },
        layout: { content_width: "sm" },
        shape: { radius: "none" },
      },
    },
  });
  const partialExpected = {
    palette: "ember",
    family: "mono",
    scale: "spacious",
    weight: "bold",
    width: "sm",
    spacing: "lg",
    gap: "sm",
    radius: "none",
    shadow: "md",
    background: "rgb(255, 247, 237)",
    color: "rgb(66, 32, 6)",
    fontFamily: "ui-monospace",
    fontSize: "17px",
    fontWeight: "700",
    contentWidth: "768px",
    paddingTop: "64px",
    gridGap: "16px",
    borderRadius: "0px",
    boxShadow: "rgba(0, 0, 0, 0.18) 0px 8px 24px 0px",
  };
  const partialPreview = await page.goto(agentPreviewPath);
  expectPrivateHeaders(partialPreview!);
  assertThemeOutput(await renderedThemeOutput(page), partialExpected);

  const inheritedOnlyRoute = `**${agentPreviewPath}`;
  await page.route(inheritedOnlyRoute, async (route) => {
    const upstream = await route.fetch();
    const inheritedOnlyPage = (await upstream.text())
      .replaceAll("renderer-theme-palette--ember", "renderer-theme-palette--meadow")
      .replaceAll("renderer-theme-family--mono", "renderer-theme-family--serif")
      .replaceAll("renderer-theme-width--sm", "renderer-theme-width--xl")
      .replaceAll("renderer-theme-radius--none", "renderer-theme-radius--lg");
    await route.fulfill({ response: upstream, body: inheritedOnlyPage });
  });
  try {
    const inheritedOnlyPreview = await page.goto(agentPreviewPath);
    expectPrivateHeaders(inheritedOnlyPreview!);
    let rejectedInheritedOnly = false;
    try {
      assertThemeOutput(await renderedThemeOutput(page), partialExpected);
    } catch {
      rejectedInheritedOnly = true;
    }
    expect(rejectedInheritedOnly).toBe(true);
  } finally {
    await page.unroute(inheritedOnlyRoute);
  }
  const restoredPartialPreview = await page.reload();
  expectPrivateHeaders(restoredPartialPreview!);
  assertThemeOutput(await renderedThemeOutput(page), partialExpected);

  const changedInheritedTheme = await page.request.patch("/api/agent/v1/theme", {
    headers: {
      Authorization: `Bearer ${agentToken}`,
      "Idempotency-Key": `oap-078y-page-style-theme-change-${tag}`,
    },
    data: {
      expected_row_version: 2,
      typography: { scale: "compact", weight: "regular" },
      layout: { spacing: "sm", grid_gap: "lg" },
      shape: { shadow: "none" },
    },
  });
  expect(changedInheritedTheme.status()).toBe(200);
  const changedInheritedThemeBody = (await changedInheritedTheme.json()) as {
    record?: Record<string, unknown>;
  };
  expect(changedInheritedThemeBody.record).toMatchObject({
    row_version: 3,
    palette: { preset: "meadow" },
    typography: { family: "serif", scale: "compact", weight: "regular" },
    layout: { content_width: "xl", spacing: "sm", grid_gap: "lg" },
    shape: { radius: "lg", shadow: "none" },
  });
  const partialAfterThemeExpected = {
    ...partialExpected,
    scale: "compact",
    weight: "regular",
    spacing: "sm",
    gap: "lg",
    shadow: "none",
    fontSize: "15px",
    fontWeight: "400",
    paddingTop: "24px",
    boxShadow: "none",
  };
  const partialAfterTheme = await page.goto(agentPreviewPath);
  expectPrivateHeaders(partialAfterTheme!);
  assertThemeOutput(await renderedThemeOutput(page), partialAfterThemeExpected);
  const explicitAfterTheme = await page.request.get(pageStylePath, {
    headers: { Authorization: `Bearer ${agentToken}` },
  });
  expect(await explicitAfterTheme.json()).toMatchObject({
    row_version: 4,
    overrides: {
      palette: { preset: "ember" },
      typography: { family: "mono" },
      layout: { content_width: "sm" },
      shape: { radius: "none" },
    },
  });

  const resumedInheritance = await page.request.patch(pageStylePath, {
    headers: {
      Authorization: `Bearer ${agentToken}`,
      "Idempotency-Key": `oap-078y-page-style-reset-palette-${tag}`,
    },
    data: { expected_row_version: 4, reset_tokens: ["palette.preset"] },
  });
  expect(resumedInheritance.status()).toBe(200);
  const resumedInheritanceBody = (await resumedInheritance.json()) as {
    record?: Record<string, unknown>;
  };
  expect(resumedInheritanceBody.record).toMatchObject({
    row_version: 5,
    overrides: {
      typography: { family: "mono" },
      layout: { content_width: "sm" },
      shape: { radius: "none" },
    },
    resolved: { palette: { preset: "meadow" } },
  });
  const resumedExpected = {
    ...partialAfterThemeExpected,
    palette: "meadow",
    family: "mono",
    background: "rgb(240, 248, 241)",
    color: "rgb(18, 53, 29)",
  };
  const resumedPreview = await page.goto(agentPreviewPath);
  expectPrivateHeaders(resumedPreview!);
  assertThemeOutput(await renderedThemeOutput(page), resumedExpected);
  const otherPageStyleAfter = await page.request.get(
    `/api/agent/v1/pages/${otherPageId}/style`,
    { headers: { Authorization: `Bearer ${agentToken}` } },
  );
  const otherPageStyleAfterBody = (await otherPageStyleAfter.json()) as {
    row_version?: unknown;
    overrides?: unknown;
    resolved?: { palette?: { preset?: unknown } };
  };
  expect(otherPageStyleBefore).toMatchObject({ row_version: 1, overrides: {} });
  expect(otherPageStyleAfterBody).toMatchObject({
    row_version: 1,
    overrides: {},
    resolved: { palette: { preset: "meadow" } },
  });

  const untouchedPreview = await page.goto(`/preview/${defaultWorkspace}/s/parity/`);
  expectPrivateHeaders(untouchedPreview!);
  const defaultOutput = await renderedThemeOutput(page);
  expect(defaultOutput).toEqual(defaultBeforeOutput);
  const expectedDefaultOutput = {
    palette: "ocean",
    family: "system",
    scale: "balanced",
    weight: "regular",
    width: "md",
    spacing: "md",
    gap: "md",
    radius: "md",
    shadow: "sm",
    background: "rgb(11, 28, 34)",
    color: "rgb(244, 247, 248)",
    fontFamily: "Inter",
    fontSize: "16px",
    fontWeight: "400",
    contentWidth: "1152px",
    paddingTop: "80px",
    gridGap: "16px",
    borderRadius: "12px",
    boxShadow: "none",
  };
  assertThemeOutput(defaultOutput, expectedDefaultOutput);
  let defaultOutputRejectedAsAgent = false;
  try {
    assertThemeOutput(defaultOutput, expectedAgentOutput);
  } catch {
    defaultOutputRejectedAsAgent = true;
  }
  expect(defaultOutputRejectedAsAgent).toBe(true);

  const canonicalAfter = await page.request.get("/s/parity/");
  expect(canonicalAfter.status()).toBe(200);
  const canonicalAfterBody = await canonicalAfter.text();
  expect(canonicalRendererFingerprint(canonicalAfterBody)).toEqual(
    canonicalBeforeFingerprint,
  );
  expect(canonicalAfterBody).toContain("renderer-theme-palette--ocean");
  expect(canonicalAfterBody).not.toContain("renderer-theme-palette--meadow");
  const otherSiteCanonical = await page.request.get("/s/demo");
  expect(otherSiteCanonical.status()).toBe(200);
  const otherSiteAfterBody = await otherSiteCanonical.text();
  expect(canonicalRendererFingerprint(otherSiteAfterBody)).toEqual(
    otherSiteBeforeFingerprint,
  );
  expect(otherSiteAfterBody).toContain("renderer-theme-palette--ocean");
  expect(failures(), "unexpected Agent theme browser failures").toEqual([]);

  const revokeResponse = await page.request.post(
    `${workspacePath}${agentWorkspace}/capabilities/${capabilityId}/revoke`,
    { headers: { "X-CSRF-Token": csrf } },
  );
  expect(revokeResponse.status()).toBe(200);
});

const DEFAULT_PARITY_HEADER = {
  variant: "institutional",
  content: {
    nav: [{ label: "parity", target: { kind: "internal", value: "/" } }],
  },
};
const DEFAULT_PARITY_FOOTER = {
  variant: "single-column",
  content: { links: [], note: "" },
};

test("global-regions-render-canonical-defaults-and-editor-save-is-preview-scoped", async ({
  page,
}) => {
  const workspaceId = process.env.SLAIF_E2E_PREVIEW_WORKSPACE_ID;
  if (!workspaceId) throw new Error("missing preview fixture channel");
  const credential = secrets();
  const failures = observe(page);

  await login(page, credential);
  const sitesResponse = await page.request.get("/api/control/v1/me/sites");
  expect(sitesResponse.status()).toBe(200);
  const sites = (await sitesResponse.json()) as Array<{
    site_id: string;
    site_key: string;
  }>;
  const parity = sites.find((site) => site.site_key === "parity");
  expect(parity).toBeDefined();
  const csrf = (await page.context().cookies()).find(
    (cookie) => cookie.name === "slaif_csrf",
  )?.value;
  expect(csrf).toBeTruthy();

  // Public canonical renders the virtual defaults before any write.
  const canonical = await page.goto("/s/parity/");
  expect(canonical?.status()).toBe(200);
  const canonicalHeaderClass = await page
    .locator("header.renderer-region-header")
    .getAttribute("class");
  expect(canonicalHeaderClass).toContain("renderer-region-header--institutional");
  await expect(page.locator("header .renderer-region-brand")).toHaveText("parity");
  await expect(page.locator("header .renderer-region-brand")).toHaveAttribute(
    "href",
    "/s/parity",
  );
  const canonicalNavLinks = page.locator('header nav[aria-label="Site"] a');
  expect(await canonicalNavLinks.count()).toBe(1);
  await expect(canonicalNavLinks.first()).toHaveText("parity");
  await expect(canonicalNavLinks.first()).toHaveAttribute("href", "/s/parity");
  await expect(
    page.locator('header nav[aria-label="Language"] span[aria-current="true"]'),
  ).toHaveText("en");
  // The sl-SI locale is enabled, but no page exists at the tagged root
  // route (the fixture's sl-SI page is /sl-SI/parity), so the switcher
  // renders it fail-closed as an inert tag, never a broken link.
  const languageLinks = page.locator('header nav[aria-label="Language"] a');
  expect(await languageLinks.count()).toBe(0);
  await expect(
    page.locator('header nav[aria-label="Language"] .renderer-region-language-inert'),
  ).toHaveText("sl-SI");
  const canonicalFooterClass = await page
    .locator("footer.renderer-region-footer")
    .getAttribute("class");
  expect(canonicalFooterClass).toContain("renderer-region-footer--single-column");
  expect(await page.locator('footer nav[aria-label="Footer"]').count()).toBe(0);
  expect(await page.locator("footer .renderer-region-note").count()).toBe(0);
  expect(await page.locator('nav[aria-label="Breadcrumb"]').count()).toBe(0);

  // Human Editor saves land in the preview workspace overlay only.
  const listResponse = await page.request.get(
    `/api/editor/v1/sites/${parity!.site_id}/global-regions`,
  );
  expect(listResponse.status()).toBe(200);
  const regions = (await listResponse.json()) as Array<{
    region_key: string;
    id: string;
    variant: string;
    content: Record<string, unknown>;
    row_version: number;
  }>;
  const header = regions.find((region) => region.region_key === "header")!;
  const footer = regions.find((region) => region.region_key === "footer")!;
  expect(header.variant).toBe("institutional");
  expect(header.row_version).toBe(1);
  const editorHeaders = {
    "Content-Type": "application/json",
    "X-CSRF-Token": csrf!,
  } as const;
  const headerSave = await page.request.patch(
    `/api/editor/v1/sites/${parity!.site_id}/global-regions/${header.id}`,
    {
      headers: { ...editorHeaders, "Idempotency-Key": crypto.randomUUID() },
      data: {
        variant: "minimal",
        content: {
          nav: [
            { label: "Parity Home", target: { kind: "internal", value: "/" } },
            {
              label: "Docs",
              target: { kind: "external", value: "https://docs.example.org/" },
            },
          ],
        },
      },
    },
  );
  expect(headerSave.status()).toBe(200);
  expect(((await headerSave.json()) as { row_version: number }).row_version).toBe(2);
  const footerSave = await page.request.patch(
    `/api/editor/v1/sites/${parity!.site_id}/global-regions/${footer.id}`,
    {
      headers: { ...editorHeaders, "Idempotency-Key": crypto.randomUUID() },
      data: { content: { links: [], note: "E2E footer note" } },
    },
  );
  expect(footerSave.status()).toBe(200);

  const preview = await page.goto(`/preview/${workspaceId}/s/parity/`);
  expectPrivateHeaders(preview!);
  expect(preview?.status()).toBe(200);
  const previewHeaderClass = await page
    .locator("header.renderer-region-header")
    .getAttribute("class");
  expect(previewHeaderClass).toContain("renderer-region-header--minimal");
  const previewNav = page.locator('header nav[aria-label="Site"] a');
  expect(await previewNav.count()).toBe(2);
  await expect(previewNav.nth(0)).toHaveText("Parity Home");
  // Relative preview href: no private workspace identifier in the HTML.
  await expect(previewNav.nth(0)).toHaveAttribute("href", "parity");
  await expect(previewNav.nth(1)).toHaveText("Docs");
  await expect(previewNav.nth(1)).toHaveAttribute("href", "https://docs.example.org/");
  await expect(page.locator("footer .renderer-region-note")).toHaveText(
    "E2E footer note",
  );

  // Canonical is untouched by the preview-workspace save.
  const canonicalAfter = await page.goto("/s/parity/");
  expect(canonicalAfter?.status()).toBe(200);
  const canonicalAfterClass = await page
    .locator("header.renderer-region-header")
    .getAttribute("class");
  expect(canonicalAfterClass).toContain("renderer-region-header--institutional");
  expect(await page.locator('header nav[aria-label="Site"] a').count()).toBe(1);
  expect(await page.locator("footer .renderer-region-note").count()).toBe(0);

  // Restore the defaults so later preview evidence starts clean.
  for (const [region, body] of [
    [header, DEFAULT_PARITY_HEADER],
    [footer, DEFAULT_PARITY_FOOTER],
  ] as const) {
    const restore = await page.request.patch(
      `/api/editor/v1/sites/${parity!.site_id}/global-regions/${region.id}`,
      {
        headers: { ...editorHeaders, "Idempotency-Key": crypto.randomUUID() },
        data: {
          variant: body.variant,
          content: body.content,
          expected_row_version: region.row_version + 1,
        },
      },
    );
    expect(restore.status()).toBe(200);
  }
  const restoredPreview = await page.goto(`/preview/${workspaceId}/s/parity/`);
  expectPrivateHeaders(restoredPreview!);
  const restoredClass = await page
    .locator("header.renderer-region-header")
    .getAttribute("class");
  expect(restoredClass).toContain("renderer-region-header--institutional");
  expect(await page.locator("footer .renderer-region-note").count()).toBe(0);
  expect(failures(), "unexpected region browser failures").toEqual([]);
});

test("global-regions-agent-patch-renders-in-the-same-authorized-workspace", async ({
  page,
}) => {
  const credential = secrets();
  const failures = observe(page);
  const tag = crypto.randomUUID();

  await login(page, credential);
  const sitesResponse = await page.request.get("/api/control/v1/me/sites");
  expect(sitesResponse.status()).toBe(200);
  const sites = (await sitesResponse.json()) as Array<{
    site_id: string;
    site_key: string;
  }>;
  const parity = sites.find((site) => site.site_key === "parity");
  expect(parity).toBeDefined();
  const csrf =
    (await page.context().cookies()).find((cookie) => cookie.name === "slaif_csrf")
      ?.value ?? "";
  expect(csrf).toBeTruthy();

  const workspacePath = `/api/control/v1/sites/${parity!.site_id}/workspaces/`;
  const createWorkspace = async (title: string, key: string) => {
    const response = await page.request.post(workspacePath, {
      headers: { "X-CSRF-Token": csrf, "Idempotency-Key": key },
      data: {
        title,
        task_description: "Bounded Agent global-region proof",
        delegation_preset: "L4_SITE_ARCHITECT",
        duration_hours: 1,
        request_quota: 1000,
        mutation_quota: 200,
        delete_quota: 50,
        upload_quota: 0,
        browser_quota: 1,
        resource_constraints: { delete_enabled: true, max_deletes: 50 },
      },
    });
    expect(response.status()).toBe(201);
    const document = (await response.json()) as { workspace_id?: unknown };
    expect(typeof document.workspace_id).toBe("string");
    return document.workspace_id as string;
  };
  const agentWorkspace = await createWorkspace(
    `OAP 078-5-a Agent regions ${tag}`,
    `oap-0785a-agent-workspace-${tag}`,
  );
  const defaultWorkspace = await createWorkspace(
    `OAP 078-5-a default control ${tag}`,
    `oap-0785a-default-workspace-${tag}`,
  );
  const capabilityResponse = await page.request.post(
    `${workspacePath}${agentWorkspace}/capabilities/`,
    {
      headers: {
        "X-CSRF-Token": csrf,
        "Idempotency-Key": `oap-0785a-agent-capability-${tag}`,
      },
    },
  );
  expect(capabilityResponse.status()).toBe(201);
  const capability = (await capabilityResponse.json()) as {
    capability_id?: unknown;
    token?: unknown;
  };
  expect(typeof capability.capability_id).toBe("string");
  expect(typeof capability.token).toBe("string");
  const agentToken = capability.token as string;
  const agentHeaders = { Authorization: `Bearer ${agentToken}` } as const;

  const initial = await page.request.get("/api/agent/v1/global-regions", {
    headers: agentHeaders,
  });
  expect(initial.status()).toBe(200);
  const initialRegions = (await initial.json()) as Array<{
    region_key: string;
    id: string;
    variant: string;
    content: Record<string, unknown>;
    row_version: number;
  }>;
  const initialHeader = initialRegions.find(
    (region) => region.region_key === "header",
  )!;
  expect(initialHeader.variant).toBe("institutional");
  expect(initialHeader.row_version).toBe(1);

  // Hostile documents are rejected before any state change.
  const hostile = [
    { expected_row_version: 1, variant: "bogus" },
    {
      expected_row_version: 1,
      content: { nav: [] },
    },
    {
      expected_row_version: 1,
      content: {
        nav: Array.from({ length: 13 }, () => ({
          label: "X",
          target: { kind: "internal", value: "/x" },
        })),
      },
    },
    {
      expected_row_version: 1,
      content: {
        nav: [
          {
            label: "Bad",
            target: { kind: "external", value: "javascript:alert(1)" },
          },
        ],
      },
    },
    { variant: "minimal" },
  ];
  for (const [index, body] of hostile.entries()) {
    const rejected = await page.request.patch(
      `/api/agent/v1/global-regions/${initialHeader.id}`,
      {
        headers: { ...agentHeaders, "Idempotency-Key": `${tag}-hostile-${index}` },
        data: body,
      },
    );
    expect(rejected.status()).toBe(422);
  }

  const updated = await page.request.patch(
    `/api/agent/v1/global-regions/${initialHeader.id}`,
    {
      headers: { ...agentHeaders, "Idempotency-Key": `${tag}-header-update` },
      data: {
        expected_row_version: 1,
        variant: "minimal",
        content: {
          nav: [
            { label: "OAP Home", target: { kind: "internal", value: "/" } },
            {
              label: "Docs",
              target: { kind: "external", value: "https://docs.example.org/" },
            },
          ],
        },
      },
    },
  );
  expect(updated.status()).toBe(200);
  const updateRecord = (await updated.json()) as {
    record?: { row_version?: unknown; variant?: unknown };
  };
  expect(updateRecord.record).toMatchObject({
    row_version: 2,
    variant: "minimal",
  });

  // Page targets resolve to same-site static pages in the rendered href.
  const parentCreate = await page.request.post("/api/agent/v1/pages/", {
    headers: { ...agentHeaders, "Idempotency-Key": `${tag}-region-parent` },
    data: {
      slug: "region-parent",
      title: "Region parent",
      status: "PUBLISHED",
      locale: "en",
    },
  });
  expect(parentCreate.status()).toBe(201);
  const parentRecord = (await parentCreate.json()) as {
    record?: { id?: unknown };
  };
  expect(typeof parentRecord.record?.id).toBe("string");
  const childCreate = await page.request.post("/api/agent/v1/pages/", {
    headers: { ...agentHeaders, "Idempotency-Key": `${tag}-region-child` },
    data: {
      slug: "region-child",
      title: "Region child",
      status: "PUBLISHED",
      locale: "en",
      parent_id: parentRecord.record!.id as string,
    },
  });
  expect(childCreate.status()).toBe(201);
  const childRecord = (await childCreate.json()) as {
    record?: { id?: unknown };
  };
  expect(typeof childRecord.record?.id).toBe("string");
  const pageTargetUpdate = await page.request.patch(
    `/api/agent/v1/global-regions/${initialHeader.id}`,
    {
      headers: { ...agentHeaders, "Idempotency-Key": `${tag}-page-target` },
      data: {
        expected_row_version: 2,
        content: {
          nav: [
            { label: "OAP Home", target: { kind: "internal", value: "/" } },
            {
              label: "Child",
              target: { kind: "page", value: childRecord.record!.id as string },
            },
          ],
        },
      },
    },
  );
  expect(pageTargetUpdate.status()).toBe(200);

  const previewBase = `/preview/${agentWorkspace}/s/parity`;
  const preview = await page.goto(`${previewBase}/`);
  expectPrivateHeaders(preview!);
  expect(preview?.status()).toBe(200);
  const previewHeaderClass = await page
    .locator("header.renderer-region-header")
    .getAttribute("class");
  expect(previewHeaderClass).toContain("renderer-region-header--minimal");
  const previewNav = page.locator('header nav[aria-label="Site"] a');
  expect(await previewNav.count()).toBe(2);
  await expect(previewNav.nth(1)).toHaveText("Child");
  // Preview region links are relative so the private workspace identifier
  // never appears in the page HTML; clicking resolves inside the preview.
  await expect(previewNav.nth(1)).toHaveAttribute(
    "href",
    "parity/region-parent/region-child",
  );
  await previewNav.nth(1).click();
  expect(new URL(page.url()).pathname).toBe(
    `${previewBase}/region-parent/region-child`,
  );

  // Breadcrumbs render the ancestor chain on the child preview page.
  const childPreview = await page.goto(`${previewBase}/region-parent/region-child`);
  expectPrivateHeaders(childPreview!);
  expect(childPreview?.status()).toBe(200);
  const breadcrumbs = page.locator('nav[aria-label="Breadcrumb"] a');
  expect(await breadcrumbs.count()).toBe(1);
  await expect(breadcrumbs.first()).toHaveText("Region parent");
  await expect(breadcrumbs.first()).toHaveAttribute("href", "../region-parent");
  await breadcrumbs.first().click();
  expect(new URL(page.url()).pathname).toBe(`${previewBase}/region-parent`);
  // The parent has no ancestors, so no breadcrumb nav is rendered there.
  expect(await page.locator('nav[aria-label="Breadcrumb"]').count()).toBe(0);

  // Language switcher: the sl-SI mirror page makes the tagged route
  // resolvable, so the switcher renders a real link in the preview.
  const siParentCreate = await page.request.post("/api/agent/v1/pages/", {
    headers: { ...agentHeaders, "Idempotency-Key": `${tag}-region-parent-si` },
    data: {
      slug: "region-parent",
      title: "Region parent sl",
      status: "PUBLISHED",
      locale: "sl-SI",
    },
  });
  expect(siParentCreate.status()).toBe(201);
  const parentPreview = await page.goto(`${previewBase}/region-parent`);
  expectPrivateHeaders(parentPreview!);
  expect(parentPreview?.status()).toBe(200);
  const languageHref = page.locator(
    'header nav[aria-label="Language"] a[href="sl-SI/region-parent"]',
  );
  await expect(languageHref).toHaveText("sl-SI");
  await languageHref.click();
  expect(new URL(page.url()).pathname).toBe(`${previewBase}/sl-SI/region-parent`);
  await expect(
    page.locator('header nav[aria-label="Language"] span[aria-current="true"]'),
  ).toHaveText("sl-SI");
  const backHref = page.locator(
    'header nav[aria-label="Language"] a[href="../region-parent"]',
  );
  await expect(backHref).toHaveText("en");
  await backHref.click();
  expect(new URL(page.url()).pathname).toBe(`${previewBase}/region-parent`);

  // Canonical and the other workspace are untouched.
  const canonical = await page.goto("/s/parity/");
  expect(canonical?.status()).toBe(200);
  const canonicalClass = await page
    .locator("header.renderer-region-header")
    .getAttribute("class");
  expect(canonicalClass).toContain("renderer-region-header--institutional");
  const defaultPreview = await page.goto(`/preview/${defaultWorkspace}/s/parity/`);
  expectPrivateHeaders(defaultPreview!);
  const defaultClass = await page
    .locator("header.renderer-region-header")
    .getAttribute("class");
  expect(defaultClass).toContain("renderer-region-header--institutional");

  // Reload persistence: the overlay state survives a page reload.
  const reloaded = await page.goto(`${previewBase}/`);
  expectPrivateHeaders(reloaded!);
  const reloadedClass = await page
    .locator("header.renderer-region-header")
    .getAttribute("class");
  expect(reloadedClass).toContain("renderer-region-header--minimal");
  expect(failures(), "unexpected agent region browser failures").toEqual([]);
});
