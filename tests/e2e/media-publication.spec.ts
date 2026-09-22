import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

import { expect, test } from "@playwright/test";

import { login, observe, secrets } from "./support";

// One 1x1 PNG: the store's signature sniffer classifies it as image/png.
const TINY_PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJ" +
    "AAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "base64",
);
const MEDIA_ROOT_IN_CONTAINER = "/var/lib/slaif/media";

function composeProject(): string {
  const project = process.env.SLAIF_E2E_COMPOSE_PROJECT;
  if (!project) throw new Error("missing SLAIF_E2E_COMPOSE_PROJECT");
  return project;
}

function docker(project: string, args: readonly string[]): string {
  return execFileSync("docker", args, { encoding: "utf8" });
}

function psql(project: string, sql: string): string {
  return docker(project, [
    "exec",
    `${project}-postgres-1`,
    "psql",
    "-U",
    "postgres",
    "-d",
    "slaif",
    "-Atc",
    sql,
  ]).trim();
}

function sha256Hex(bytes: Buffer): string {
  return createHash("sha256").update(bytes).digest("hex");
}

function uploadForm(
  file: Buffer,
  filename: string,
  mimeType: string,
  fields: Record<string, string> = {},
): FormData {
  const form = new FormData();
  form.append("file", new Blob([new Uint8Array(file)], { type: mimeType }), filename);
  for (const [key, value] of Object.entries(fields)) {
    form.append(key, value);
  }
  return form;
}

function requiredString(value: unknown, label: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`unexpected ${label} in response`);
  }
  return value;
}

function digestSegments(digest: string): { p1: string; p2: string } {
  return { p1: digest.slice(0, 2), p2: digest.slice(2, 4) };
}

function objectPath(digest: string, publicNamespace: boolean): string {
  const { p1, p2 } = digestSegments(digest);
  const root = publicNamespace
    ? `${MEDIA_ROOT_IN_CONTAINER}/public`
    : MEDIA_ROOT_IN_CONTAINER;
  return `${root}/sha256/${p1}/${p2}/${digest}`;
}

test("media-publication-core-human-agent-preview-finalize-public-hostile", async ({
  page,
  browser,
}) => {
  test.setTimeout(300_000);
  const credential = secrets();
  const project = composeProject();
  const tag = crypto.randomUUID();
  const previewWorkspaceId = process.env.SLAIF_E2E_PREVIEW_WORKSPACE_ID;
  if (!previewWorkspaceId) throw new Error("missing parity preview workspace");
  const failures = observe(page);

  // ---------------------------------------------------------------- login
  await login(page, credential);
  const csrf = (await page.context().cookies()).find(
    (cookie) => cookie.name === "slaif_csrf",
  )?.value;
  expect(csrf).toBeTruthy();
  const editorHeaders = (key = crypto.randomUUID()) =>
    ({
      "Content-Type": "application/json",
      "X-CSRF-Token": csrf!,
      "Idempotency-Key": key,
    }) as const;

  const sitesResponse = await page.request.get("/api/control/v1/me/sites");
  expect(sitesResponse.status()).toBe(200);
  const sites = (await sitesResponse.json()) as Array<{
    site_id: string;
    site_key: string;
  }>;
  const parity = sites.find((site) => site.site_key === "parity");
  const demo = sites.find((site) => site.site_key !== "parity");
  if (!parity || !demo) throw new Error("parity or demo site missing");

  // ------------------------------------------------------- human uploads
  const fixturePath = new URL(
    "../../docs/screenshots/01-landing-page.png",
    import.meta.url,
  ).pathname;
  const fixtureBytes = readFileSync(fixturePath);
  const fixtureDigest = sha256Hex(fixtureBytes);

  const humanUpload = await page.request.post(
    `/media/v1/sites/${parity.site_id}/assets`,
    {
      headers: {
        "X-CSRF-Token": csrf!,
        "Idempotency-Key": `oap-079a-human-upload-${tag}`,
      },
      multipart: uploadForm(fixtureBytes, "01-landing-page.png", "image/png", {
        alt_text: "Compose fixture image",
        metadata: '{"source":"e2e"}',
      }),
    },
  );
  expect(humanUpload.status()).toBe(201);
  const humanUploadBody = (await humanUpload.json()) as {
    record?: Record<string, unknown>;
  };
  const humanMediaId = requiredString(humanUploadBody.record?.id, "media id");
  expect(humanMediaId).toMatch(/^[0-9a-f-]{36}$/);
  expect(humanUploadBody.record?.content_hash).toBe(fixtureDigest);

  // Cross-site hostile reference target: the same fixture on the demo site.
  const demoUpload = await page.request.post(`/media/v1/sites/${demo.site_id}/assets`, {
    headers: {
      "X-CSRF-Token": csrf!,
      "Idempotency-Key": `oap-079a-demo-upload-${tag}`,
    },
    multipart: uploadForm(fixtureBytes, "01-landing-page.png", "image/png"),
  });
  expect(demoUpload.status()).toBe(201);
  const demoUploadBody = (await demoUpload.json()) as {
    record?: Record<string, unknown>;
  };
  const demoMediaId = requiredString(demoUploadBody.record?.id, "media id");
  expect(demoMediaId).toMatch(/^[0-9a-f-]{36}$/);

  // -------------------------------------------------- agent workspace + capability
  const workspaceResponse = await page.request.post(
    `/api/control/v1/sites/${parity.site_id}/workspaces/`,
    {
      headers: editorHeaders(`oap-079a-agent-workspace-${tag}`),
      data: {
        title: `OAP 079-a media publication ${tag}`,
        task_description: "Bounded Agent media publication proof",
        delegation_preset: "L1_CONTENT_EDITOR",
        duration_hours: 1,
        request_quota: 200,
        mutation_quota: 50,
        delete_quota: 0,
        upload_quota: 2,
        browser_quota: 0,
        resource_constraints: {},
      },
    },
  );
  expect(workspaceResponse.status()).toBe(201);
  const workspaceBody = (await workspaceResponse.json()) as {
    workspace_id?: unknown;
  };
  const agentWorkspaceId = requiredString(workspaceBody.workspace_id, "workspace id");
  expect(agentWorkspaceId).toMatch(/^[0-9a-f-]{36}$/);
  const capabilityResponse = await page.request.post(
    `/api/control/v1/sites/${parity.site_id}/workspaces/${agentWorkspaceId}/capabilities/`,
    { headers: editorHeaders(`oap-079a-agent-capability-${tag}`) },
  );
  expect(capabilityResponse.status()).toBe(201);
  const capability = (await capabilityResponse.json()) as {
    capability_id?: unknown;
    token?: unknown;
  };
  const agentToken = requiredString(capability.token, "capability token");
  expect(agentToken).toMatch(/^sas2_/);
  const agentCapabilityId = requiredString(capability.capability_id, "capability id");
  const agentHeaders = { Authorization: `Bearer ${agentToken}` } as const;

  // ------------------------------------------------------------- agent upload
  const tinyDigest = sha256Hex(TINY_PNG);
  const agentUpload = await page.request.post("/api/agent/v1/media/assets", {
    headers: {
      ...agentHeaders,
      "Idempotency-Key": `oap-079a-agent-upload-${tag}`,
    },
    multipart: uploadForm(TINY_PNG, "agent-proof.png", "image/png", {
      alt_text: "E2E agent media proof",
    }),
  });
  expect(agentUpload.status()).toBe(201);
  const agentUploadBody = (await agentUpload.json()) as {
    record?: Record<string, unknown>;
  };
  const agentMediaId = requiredString(agentUploadBody.record?.id, "media id");
  expect(agentMediaId).toMatch(/^[0-9a-f-]{36}$/);
  expect(agentUploadBody.record?.content_hash).toBe(tinyDigest);

  // Idempotent replay: same key + same bounded digest, same record.
  const agentReplay = await page.request.post("/api/agent/v1/media/assets", {
    headers: {
      ...agentHeaders,
      "Idempotency-Key": `oap-079a-agent-upload-${tag}`,
    },
    multipart: uploadForm(TINY_PNG, "agent-proof.png", "image/png", {
      alt_text: "E2E agent media proof",
    }),
  });
  expect(agentReplay.status()).toBe(201);
  const agentReplayBody = (await agentReplay.json()) as {
    record?: Record<string, unknown>;
  };
  expect(agentReplayBody.record?.id).toBe(agentMediaId);

  // Deterministic editor workspace resolution: the human editor resolves to
  // the latest ACTIVE HUMAN workspace of the user on the site. Control-API
  // workspaces are actor_type=AGENT and never candidates; the only HUMAN
  // workspace on the parity fixture site is the pinned preview workspace,
  // whose 1-hour fixture TTL is refreshed here so slow suite runs cannot
  // make the resolution fall through to a server-created workspace.
  psql(
    project,
    `UPDATE control.workspace
       SET status = 'ACTIVE',
           expires_at = CURRENT_TIMESTAMP + interval '2 hours'
     WHERE id = '${previewWorkspaceId}'::uuid
       AND site_id = '${parity.site_id}'::uuid
       AND actor_type = 'HUMAN'
       AND status IN ('ACTIVE', 'EXPIRED');`,
  );
  expect(
    psql(
      project,
      `SELECT status FROM control.workspace
        WHERE id = '${previewWorkspaceId}'::uuid
          AND site_id = '${parity.site_id}'::uuid
          AND actor_type = 'HUMAN';`,
    ),
  ).toBe("ACTIVE");

  // ------------------------------------------------ Image composition nodes
  const pagesResponse = await page.request.get(
    `/api/editor/v1/sites/${parity.site_id}/pages/`,
  );
  expect(pagesResponse.status()).toBe(200);
  const pages = (await pagesResponse.json()) as Array<{
    id: string;
    slug: string;
    locale: string;
  }>;
  const homePage = pages.find((pg) => pg.slug === "home" && pg.locale === "en");
  expect(homePage).toBeDefined();
  const compositionPath = `/api/editor/v1/sites/${parity.site_id}/pages/${homePage!.id}/composition/components`;

  const imageCreate = await page.request.post(compositionPath, {
    headers: editorHeaders(`oap-079a-image-agent-${tag}`),
    data: {
      component_type: "Image",
      slot_key: "default",
      order_key: 20,
      props: { mediaId: agentMediaId, alt: "E2E agent media proof" },
    },
  });
  expect(imageCreate.status()).toBe(201);
  const imageCreateBody = (await imageCreate.json()) as {
    id?: unknown;
    row_version?: unknown;
  };
  expect(imageCreateBody.row_version).toBe(1);
  expect(typeof imageCreateBody.id).toBe("string");
  const imageComponentId = imageCreateBody.id as string;
  const humanImageCreate = await page.request.post(compositionPath, {
    headers: editorHeaders(`oap-079a-image-human-${tag}`),
    data: {
      component_type: "Image",
      slot_key: "default",
      order_key: 21,
      props: { mediaId: humanMediaId, alt: "Compose fixture image" },
    },
  });
  expect(humanImageCreate.status()).toBe(201);
  const humanImageCreateBody = (await humanImageCreate.json()) as {
    id?: unknown;
    row_version?: unknown;
  };
  expect(humanImageCreateBody.row_version).toBe(1);
  expect(typeof humanImageCreateBody.id).toBe("string");
  const humanComponentId = humanImageCreateBody.id as string;

  // -------------------------------------------------------- preview render
  const previewPage = await page.goto(`/preview/${previewWorkspaceId}/s/parity/`);
  expect(previewPage?.status()).toBe(200);
  const agentImage = page.locator('img.sl-image[src^="/media/v1/sites/"]').first();
  await expect(agentImage).toBeVisible();
  expect(await agentImage.getAttribute("src")).toBe(
    `/media/v1/sites/${parity.site_id}/assets/${agentMediaId}/content`,
  );
  expect(await agentImage.getAttribute("alt")).toBe("E2E agent media proof");
  expect(await agentImage.getAttribute("loading")).toBe("lazy");
  expect(await agentImage.getAttribute("referrerpolicy")).toBe("no-referrer");
  const humanImage = page.locator('img.sl-image[src^="/media/v1/sites/"]').nth(1);
  expect(await humanImage.getAttribute("src")).toBe(
    `/media/v1/sites/${parity.site_id}/assets/${humanMediaId}/content`,
  );

  // Byte-identical authenticated preview fetch for the human media.
  const previewFetch = await page.request.get(
    `/media/v1/sites/${parity.site_id}/assets/${humanMediaId}/content`,
  );
  expect(previewFetch.status()).toBe(200);
  expect(previewFetch.headers()["cache-control"]).toBe("private, no-store");
  expect((await previewFetch.body()).equals(fixtureBytes)).toBe(true);

  // --------------------------------------- direct finalization (083 boundary call)
  const finalizationScript = `
import asyncio, json
from uuid import UUID
from slaif_agent_site.media_service.config import MediaSettings
from slaif_agent_site.media_service.database import MediaDatabase
from slaif_agent_site.media_service.finalize import (
    MediaFinalizationRepository,
    finalize_media_for_promotion,
)
from slaif_agent_site.media_service.store import MediaStore

async def main():
    settings = MediaSettings.load()
    database = MediaDatabase(settings)
    await database.start()
    try:
        manifest = await finalize_media_for_promotion(
            UUID(${JSON.stringify(parity.site_id)}),
            UUID(${JSON.stringify(previewWorkspaceId)}),
            [UUID(${JSON.stringify(humanMediaId)}), UUID(${JSON.stringify(agentMediaId)})],
            store=MediaStore(settings.media_root),
            repository=MediaFinalizationRepository(database),
        )
        print(json.dumps({"manifest": manifest.to_list()}))
    finally:
        await database.stop()

asyncio.run(main())
`;
  const finalizationOutput = docker(project, [
    "exec",
    `${project}-media-service-1`,
    "python",
    "-c",
    finalizationScript,
  ]);
  const manifest = (
    JSON.parse(finalizationOutput.trim()) as {
      manifest: Array<{ media_id: string; digest: string; public_key: string }>;
    }
  ).manifest;
  const digestOf: Record<string, string> = {
    [humanMediaId]: fixtureDigest,
    [agentMediaId]: tinyDigest,
  };
  const publicKeyOf = (mediaId: string): string => {
    const digest = digestOf[mediaId];
    if (digest === undefined) throw new Error(`unknown media id: ${mediaId}`);
    return `public/sha256/${digest.slice(0, 2)}/${digest.slice(2, 4)}/${digest}`;
  };
  expect(manifest).toEqual(
    [humanMediaId, agentMediaId].sort().map((mediaId) => ({
      media_id: mediaId,
      digest: digestOf[mediaId],
      public_key: publicKeyOf(mediaId),
    })),
  );

  // ------------------------------------------- unauthenticated public digest read
  const anonymous = await browser.newContext();
  try {
    const publicFetch = await anonymous.request.get(
      `/media/public/sha256/${fixtureDigest.slice(0, 2)}/${fixtureDigest.slice(2, 4)}/${fixtureDigest}`,
    );
    expect(publicFetch.status()).toBe(200);
    const publicHeaders = publicFetch.headers();
    expect(publicHeaders["content-type"]).toBe("image/png");
    expect(publicHeaders["cache-control"]).toBe("public, max-age=31536000, immutable");
    expect(publicHeaders["x-content-type-options"]).toBe("nosniff");
    expect(publicHeaders["content-length"]).toBe(String(fixtureBytes.length));
    expect((await publicFetch.body()).equals(fixtureBytes)).toBe(true);
    const tinyFetch = await anonymous.request.get(
      `/media/public/sha256/${tinyDigest.slice(0, 2)}/${tinyDigest.slice(2, 4)}/${tinyDigest}`,
    );
    expect(tinyFetch.status()).toBe(200);
    expect((await tinyFetch.body()).equals(TINY_PNG)).toBe(true);
  } finally {
    await anonymous.close();
  }

  // Fixture-level publication of the preview composition: the two Image
  // nodes exist in the preview workspace overlay; move them into the base
  // composition so the canonical (public) render carries the same
  // composition. The product promotion boundary itself is the direct
  // finalization call above (the exact call 083 makes); this is fixture
  // state management, consistent with the psql seeding/audit/membership
  // driving used elsewhere in this spec.
  psql(
    project,
    `BEGIN;
      INSERT INTO content.page_composition_base
        (id, site_id, page_id, component_type, schema_version, parent_id,
         slot_key, order_key, props)
      SELECT c.id, c.site_id, c.page_id, c.component_type, c.schema_version,
             c.parent_id, c.slot_key, c.order_key, c.props
      FROM content.page_composition_changes c
      WHERE c.session_id = '${previewWorkspaceId}'::uuid
        AND c.component_type = 'Image' AND NOT c._cow_deleted;
      DELETE FROM content.page_composition_changes
      WHERE session_id = '${previewWorkspaceId}'::uuid
        AND component_type = 'Image';
      COMMIT;`,
  );

  // ------------------------------------------------- canonical render + parity
  const anonymousPageContext = await browser.newContext();
  try {
    const canonicalPage = await anonymousPageContext.newPage();
    const canonicalResponse = await canonicalPage.goto("/s/parity/");
    expect(canonicalResponse?.status()).toBe(200);
    const canonicalImage = canonicalPage
      .locator('img.sl-image[src^="/media/public/sha256/"]')
      .first();
    await expect(canonicalImage).toBeVisible();
    expect(await canonicalImage.getAttribute("src")).toBe(
      `/media/public/sha256/${tinyDigest.slice(0, 2)}/${tinyDigest.slice(2, 4)}/${tinyDigest}`,
    );
    const canonicalHtml = await canonicalPage.content();
    const previewHtml = await page.content();
    // Browser DOM serialization differs from the SSR string: void elements
    // lose their self-closing slash and referrerPolicy is emitted
    // lowercase, so the img terminator is an optional slash before >.
    const imageMarkup = (html: string, src: string): string => {
      const match = html.match(
        new RegExp(
          `<div aria-label="[^"]*" class="renderer-image-placeholder[^"]*" role="img"><img [^>]*src="${src.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\$&")}"[^>]*/?></div>`,
        ),
      );
      if (!match) throw new Error(`image markup missing for ${src}`);
      return match[0];
    };
    const canonicalAgentMarkup = imageMarkup(
      canonicalHtml,
      `/media/public/sha256/${tinyDigest.slice(0, 2)}/${tinyDigest.slice(2, 4)}/${tinyDigest}`,
    );
    const previewAgentMarkup = imageMarkup(
      previewHtml,
      `/media/v1/sites/${parity.site_id}/assets/${agentMediaId}/content`,
    );
    expect(
      previewAgentMarkup.replace(
        `/media/v1/sites/${parity.site_id}/assets/${agentMediaId}/content`,
        `/media/public/sha256/${tinyDigest.slice(0, 2)}/${tinyDigest.slice(2, 4)}/${tinyDigest}`,
      ),
    ).toBe(canonicalAgentMarkup);
  } finally {
    await anonymousPageContext.close();
  }

  // ---------------------------------------------------------------- hostile suite
  // 1. Cross-site private byte read: 404, never 403, never bytes. The
  // 404 carries the standard bounded error envelope (never empty), and
  // the body must never be the foreign media's bytes.
  const crossSite = await page.request.get(
    `/media/v1/sites/${demo.site_id}/assets/${agentMediaId}/content`,
  );
  expect(crossSite.status()).toBe(404);
  const crossSiteBody = (await crossSite.json()) as { error: { code: string } };
  expect(crossSiteBody.error.code).toBe("RESOURCE_NOT_FOUND");
  expect(await crossSite.body()).not.toEqual(TINY_PNG);

  // 2-3. Forged and unknown digests: 404 (not 403) end to end.
  const forgedDigest = "0".repeat(64);
  const forged = await page.request.get(`/media/public/sha256/00/00/${forgedDigest}`);
  expect(forged.status()).toBe(404);
  expect(((await forged.json()) as { error: { code: string } }).error.code).toBe(
    "RESOURCE_NOT_FOUND",
  );
  const unknownDigest =
    crypto.randomUUID().replace(/-/g, "") + crypto.randomUUID().replace(/-/g, "");
  const unknown = await page.request.get(
    `/media/public/sha256/${unknownDigest.slice(0, 2)}/${unknownDigest.slice(2, 4)}/${unknownDigest}`,
  );
  expect(unknown.status()).toBe(404);
  expect(((await unknown.json()) as { error: { code: string } }).error.code).toBe(
    "RESOURCE_NOT_FOUND",
  );

  // 4-5. Staging and private object namespaces are unrouteable under /media/
  // (404, never the object bytes).
  const stagingProbe = await page.request.get("/media/.staging/probe");
  expect(stagingProbe.status()).toBe(404);
  expect(await stagingProbe.body()).not.toEqual(fixtureBytes);
  const privateNamespaceProbe = await page.request.get(
    `/media/sha256/${fixtureDigest.slice(0, 2)}/${fixtureDigest.slice(2, 4)}/${fixtureDigest}`,
  );
  expect(privateNamespaceProbe.status()).toBe(404);
  expect(await privateNamespaceProbe.body()).not.toEqual(fixtureBytes);

  // 6. Path traversal through the public digest location.
  const traversal = await page.request.get(
    "/media/public/sha256/..%2F..%2F..%2F.staging%2Fprobe",
  );
  expect([404, 422]).toContain(traversal.status());
  expect(await traversal.body()).not.toEqual(fixtureBytes);

  // 7. SVG upload: rejected by MIME policy, never sanitized or stored.
  const svgUpload = await page.request.post("/api/agent/v1/media/assets", {
    headers: {
      ...agentHeaders,
      "Idempotency-Key": `oap-079a-hostile-svg-${tag}`,
    },
    multipart: uploadForm(Buffer.from("<svg></svg>"), "x.svg", "image/svg+xml"),
  });
  expect(svgUpload.status()).toBe(422);
  expect(((await svgUpload.json()) as { error: { code: string } }).error.code).toBe(
    "DOMAIN_VALIDATION_FAILED",
  );

  // 8. Oversized upload: edge body limit rejects before the service.
  const oversized = Buffer.alloc(101 * 1024 * 1024, 0);
  TINY_PNG.copy(oversized, 0);
  const oversizedUpload = await page.request.post("/api/agent/v1/media/assets", {
    headers: {
      ...agentHeaders,
      "Idempotency-Key": `oap-079a-hostile-oversized-${tag}`,
    },
    multipart: uploadForm(oversized, "large.png", "image/png"),
  });
  expect(oversizedUpload.status()).toBe(413);
  oversized.fill(0);

  // 9. Missing idempotency key: 400 with the exact bounded key.
  const missingKey = await page.request.post("/api/agent/v1/media/assets", {
    headers: agentHeaders,
    multipart: uploadForm(TINY_PNG, "agent-proof.png", "image/png"),
  });
  expect(missingKey.status()).toBe(400);
  expect(((await missingKey.json()) as { error: { code: string } }).error.code).toBe(
    "IDEMPOTENCY_KEY_REQUIRED",
  );

  // 10. Foreign-mediaId component prop: bounded 422 with the exact prop key.
  const foreignImage = await page.request.post(compositionPath, {
    headers: editorHeaders(`oap-079a-hostile-foreign-media-${tag}`),
    data: {
      component_type: "Image",
      slot_key: "default",
      order_key: 22,
      props: { mediaId: demoMediaId, alt: "foreign reference" },
    },
  });
  expect(foreignImage.status()).toBe(422);
  const foreignImageBody = (await foreignImage.json()) as {
    error: { code: string; details?: { prop_error?: string } };
  };
  expect(foreignImageBody.error.code).toBe("DOMAIN_VALIDATION_FAILED");
  expect(foreignImageBody.error.details?.prop_error).toBe("COMPONENT_BINDING_INVALID");

  // 11. Corrupt public digest read: 503 while corrupted, 200 after restore.
  const publicObjectPath = objectPath(fixtureDigest, true);
  const privateObjectPath = objectPath(fixtureDigest, false);
  docker(project, [
    "exec",
    `${project}-media-service-1`,
    "sh",
    "-c",
    `printf x >> '${publicObjectPath}'`,
  ]);
  try {
    const corruptContext = await browser.newContext();
    try {
      const corruptFetch = await corruptContext.request.get(
        `/media/public/sha256/${fixtureDigest.slice(0, 2)}/${fixtureDigest.slice(2, 4)}/${fixtureDigest}`,
      );
      expect(corruptFetch.status()).toBe(503);
    } finally {
      await corruptContext.close();
    }
  } finally {
    docker(project, [
      "exec",
      `${project}-media-service-1`,
      "sh",
      "-c",
      `cp '${privateObjectPath}' '${publicObjectPath}' && chmod 600 '${publicObjectPath}'`,
    ]);
  }
  const restoredContext = await browser.newContext();
  try {
    const restoredFetch = await restoredContext.request.get(
      `/media/public/sha256/${fixtureDigest.slice(0, 2)}/${fixtureDigest.slice(2, 4)}/${fixtureDigest}`,
    );
    expect(restoredFetch.status()).toBe(200);
    expect((await restoredFetch.body()).equals(fixtureBytes)).toBe(true);
  } finally {
    await restoredContext.close();
  }

  // 12. Revoked capability: 401 with the bounded key.
  const revokeResponse = await page.request.post(
    `/api/control/v1/sites/${parity.site_id}/workspaces/${agentWorkspaceId}/capabilities/${agentCapabilityId}/revoke`,
    { headers: { "X-CSRF-Token": csrf! } },
  );
  expect(revokeResponse.status()).toBe(200);
  const revokedUpload = await page.request.post("/api/agent/v1/media/assets", {
    headers: agentHeaders,
    multipart: uploadForm(TINY_PNG, "agent-proof.png", "image/png"),
  });
  expect(revokedUpload.status()).toBe(401);
  expect(((await revokedUpload.json()) as { error: { code: string } }).error.code).toBe(
    "AUTHENTICATION_REQUIRED",
  );

  // 13. Non-member preview denial: the compose local administrator IS the
  // platform administrator (platform-admin preview authority outlives any
  // membership toggle), so the denial is proven with a seeded local user
  // that holds no site membership and no platform-administrator row.
  // Fixture credential: fake placeholder, compose stack is disposable.
  const DENIED_USERNAME = "oap079a.denied";
  const DENIED_PASSWORD = "oap-079a-denied-fixture-password";
  psql(
    project,
    `INSERT INTO control.user_account
       (id, identity_kind, local_username, local_username_normalized,
        password_hash, display_name, status)
     VALUES ('12000000-0000-4000-8000-000000000309'::uuid, 'LOCAL',
             'oap079a.denied', 'oap079a.denied',
             '$argon2id$v=19$m=65536,t=3,p=4$aYJmlGOPIzBrYqxaW8KfsA$fa7FxchamufkpmRuLliHvqjt5cUOc4hyNd88X1SRbC4',
             'OAP 079 denied fixture', 'ACTIVE');`,
  );
  const deniedUserId = psql(
    project,
    `SELECT id::text FROM control.user_account
      WHERE id = '12000000-0000-4000-8000-000000000309'::uuid;`,
  );
  expect(deniedUserId).toMatch(/^[0-9a-f-]{36}$/);
  const adminUserId = psql(
    project,
    `SELECT id FROM control.user_account WHERE local_username_normalized = 'compose.admin';`,
  );
  expect(
    psql(
      project,
      `SELECT count(*) FROM control.platform_administrator
        WHERE user_account_id = '${adminUserId}'::uuid;`,
    ),
  ).toBe("1");
  expect(
    psql(
      project,
      `SELECT count(*) FROM control.platform_administrator
        WHERE user_account_id = '${deniedUserId}'::uuid;`,
    ),
  ).toBe("0");
  const deniedContext = await browser.newContext();
  try {
    const deniedLogin = await deniedContext.request.post("/api/control/v1/login", {
      data: { username: DENIED_USERNAME, password: DENIED_PASSWORD },
    });
    expect(deniedLogin.status()).toBe(200);
    const nonMemberPreview = await deniedContext.request.get(
      `/preview/${previewWorkspaceId}/s/parity/`,
    );
    expect(nonMemberPreview.status()).toBe(404);
    const nonMemberMedia = await deniedContext.request.get(
      `/media/v1/sites/${parity.site_id}/assets/${humanMediaId}/content`,
    );
    expect(nonMemberMedia.status()).toBe(404);
  } finally {
    await deniedContext.close();
  }
  // Control: the administrator (platform-administrator branch) keeps
  // preview authority, so the denial above is membership-based.
  const restoredPreview = await page.request.get(
    `/preview/${previewWorkspaceId}/s/parity/`,
  );
  expect(restoredPreview.status()).toBe(200);

  // 14. Revoked human session: a stale session cookie that the server has
  // revoked must fail closed — preview 404 (the render boundary maps every
  // authorization failure to not-found) and private media read 404 (the
  // media boundary maps a present-but-unauthorized token to not-found;
  // only a missing token is 401). Logout also clears the client cookie,
  // so the stale token is captured first and re-added: the denial must
  // come from server-side revocation, not client-side cookie absence.
  const staleSession = (await page.context().cookies()).find(
    (cookie) =>
      cookie.name === "slaif_session" || cookie.name === "__Host-slaif_session",
  );
  if (!staleSession) throw new Error("session cookie missing");
  const logoutResponse = await page.request.post("/api/control/v1/logout", {
    headers: { "X-CSRF-Token": csrf! },
  });
  expect(logoutResponse.status()).toBe(204);
  await page.context().addCookies([
    {
      name: staleSession.name,
      value: staleSession.value,
      url: "http://localhost:8080",
    },
  ]);
  const revokedSessionPreview = await page.request.get(
    `/preview/${previewWorkspaceId}/s/parity/`,
  );
  expect(revokedSessionPreview.status()).toBe(404);
  const revokedSessionMedia = await page.request.get(
    `/media/v1/sites/${parity.site_id}/assets/${humanMediaId}/content`,
  );
  expect(revokedSessionMedia.status()).toBe(404);

  // ------------------------------------------------------------- COW audit rows
  const agentAuditCheck = psql(
    project,
    `SELECT count(*) = 1
       AND count(*) FILTER (
             WHERE resource_type = 'media_asset'
               AND http_method = 'POST' AND response_status = 201
               AND quota_kind = 'upload' AND workspace_id = '${agentWorkspaceId}'::uuid
               AND site_id = '${parity.site_id}'::uuid) = 1
      FROM audit.agent_mutation
      WHERE action = 'MEDIA_UPLOADED' AND resource_id = '${agentMediaId}'::uuid;`,
  );
  expect(agentAuditCheck).toBe("t");
  const agentIdempotencyCheck = psql(
    project,
    `SELECT count(*) = 1 AND count(*) FILTER (
         WHERE status_code = 201 AND resource_type = 'media_asset'
           AND resource_id = '${agentMediaId}'::uuid) = 1
      FROM control.agent_idempotency
      WHERE idempotency_key = 'oap-079a-agent-upload-${tag}';`,
  );
  expect(agentIdempotencyCheck).toBe("t");
  // Scoped to this spec's two created components: the full driver's
  // preview project also legitimately creates editor components on this
  // shared parity fixture page (its own audit rows), while the order
  // requires exact COW audit rows for this spec's reference mutation.
  const editorAuditCheck = psql(
    project,
    `SELECT count(*) = 2
       AND count(*) FILTER (WHERE response_status = 201) = 2
       AND count(*) FILTER (
             WHERE action = 'POST /api/editor/v1/sites/${parity.site_id}/pages/${homePage!.id}/composition/components'
               AND workspace_id = '${previewWorkspaceId}'::uuid) = 2
      FROM audit.human_editor_mutation
      WHERE action LIKE 'POST /api/editor/v1/sites/${parity.site_id}/pages/${homePage!.id}/composition/components%'
        AND resource_id IN ('${imageComponentId}'::uuid, '${humanComponentId}'::uuid);`,
  );
  expect(editorAuditCheck).toBe("t");

  // ------------------------------------------------- restart survival (no re-finalize)
  docker(project, [
    "compose",
    "-f",
    "compose.yaml",
    "-p",
    project,
    "restart",
    "media-service",
  ]);
  const restartedContext = await browser.newContext();
  try {
    const restartedPublicPath = `/media/public/sha256/${fixtureDigest.slice(0, 2)}/${fixtureDigest.slice(2, 4)}/${fixtureDigest}`;
    // The container is "started" before the app accepts; wait for bounded
    // readiness (at most 30s) — the restart itself is the fixture action.
    let restartedFetch = await restartedContext.request.get(restartedPublicPath);
    const deadline = Date.now() + 30_000;
    while (restartedFetch.status() >= 500 && Date.now() < deadline) {
      await new Promise((resolve) => setTimeout(resolve, 500));
      restartedFetch = await restartedContext.request.get(restartedPublicPath);
    }
    expect(restartedFetch.status()).toBe(200);
    expect((await restartedFetch.body()).equals(fixtureBytes)).toBe(true);
    expect(restartedFetch.headers()["cache-control"]).toBe(
      "public, max-age=31536000, immutable",
    );
  } finally {
    await restartedContext.close();
  }
  const publicStatusCheck = psql(
    project,
    `SELECT count(*) = 2
       AND count(*) FILTER (WHERE published_at IS NOT NULL) = 2
      FROM content.media_asset
      WHERE id IN ('${humanMediaId}'::uuid, '${agentMediaId}'::uuid)
        AND public_status = 'public';`,
  );
  expect(publicStatusCheck).toBe("t");

  expect(failures()).toEqual([]);
});
