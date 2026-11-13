import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { deflateSync } from "node:zlib";

import { expect, test } from "@playwright/test";

import {
  classifyConsoleMessage,
  classifyConsoleMessageFamily,
  classifyConsoleOriginFamily,
  classifyConsoleSource,
  type ConsoleMessageFamily,
  type ConsoleOriginFamily,
} from "./observation";
import { login, observe, secrets } from "./support";

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

// ---------------------------------------------------------------- PNG fixture
// Bounded run-unique valid PNG generator: a 1x1 truecolor PNG (the store's
// signature sniffer classifies it as image/png) whose single pixel is
// derived from the run seed, so each run carries a fresh content hash.  The
// full driver runs accept-lifecycle BEFORE this project, and that cycle
// lawfully publishes the static 1x1 PNG shared by the sibling specs; the
// sessionless public digest route is content-addressed across sites (068),
// so a fixed constant would already hold public authorization by the time
// this project runs and its pending-private 404 would be false.  A
// run-unique valid PNG keeps that oracle honest without any product,
// dependency or fixture-authority change.
const PNG_CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c >>> 0;
  }
  return table;
})();

function pngCrc32(bytes: Buffer): number {
  let crc = 0xffffffff;
  for (const byte of bytes)
    crc = (PNG_CRC_TABLE[(crc ^ byte) & 0xff] ?? 0) ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function pngChunk(type: string, data: Buffer): Buffer {
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, "ascii"), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(pngCrc32(body));
  return Buffer.concat([length, body, crc]);
}

function makeRunUniquePng(seed: Buffer): Buffer {
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(1, 0); // width
  ihdr.writeUInt32BE(1, 4); // height
  ihdr[8] = 8; // bit depth
  ihdr[9] = 2; // color type: truecolor
  ihdr[10] = 0; // compression
  ihdr[11] = 0; // filter
  ihdr[12] = 0; // interlace
  const raw = Buffer.from([
    0,
    (seed[0] ?? 0) & 0xff,
    (seed[1] ?? 0) & 0xff,
    (seed[2] ?? 0) & 0xff,
  ]);
  const idat = deflateSync(raw, { level: 9 });
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    pngChunk("IHDR", ihdr),
    // Bounded ancillary tEXt chunk carrying the FULL run seed (keyword +
    // NUL + UTF-8 text): the run identity is bound into the bytes without
    // truncating it, and the 1x1 geometry stays valid for the renderer.
    pngChunk(
      "tEXt",
      Buffer.concat([Buffer.from("Comment", "ascii"), Buffer.from([0]), seed]),
    ),
    pngChunk("IDAT", idat),
    pngChunk("IEND", Buffer.alloc(0)),
  ]);
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

// --------------------------------------------------------------- real review
// The product publication boundary is the real human freeze -> review ->
// accept cycle through the control API and the real review worker: the
// accept job promotes the frozen snapshot in ONE reviewer transaction and
// publishes exactly the reviewed, referenced media closure (WORKSPACE_
// ACCEPTED outbox media_manifest).  No direct finalizer call and no SQL
// fixture promotion anywhere in this spec.

async function adminCsrf(page: import("@playwright/test").Page): Promise<string> {
  const cookie = (await page.context().cookies()).find(
    (item) => item.name === "slaif_csrf",
  );
  if (!cookie?.value) throw new Error("csrf cookie missing");
  return cookie.value;
}

async function controlFreeze(
  page: import("@playwright/test").Page,
  siteId: string,
  workspaceId: string,
): Promise<{ status: number; job_id: string }> {
  const response = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/freeze/`,
    { headers: { "X-CSRF-Token": await adminCsrf(page) } },
  );
  const body = (await response.json().catch(() => ({}))) as {
    job_id?: unknown;
  };
  return {
    status: response.status(),
    job_id: typeof body.job_id === "string" ? body.job_id : "",
  };
}

/**
 * Positive AGENT-workspace HTTP oracle: the human control detail read
 * (038 `slaif_human_agent_workspace_get`) is explicitly scoped to
 * `actor_type='AGENT'`, so this endpoint is valid for agent workspaces
 * only — a 404 for an AGENT workspace is a genuine failure and must not
 * be swallowed.  HUMAN workspaces have no generic authorized HTTP status
 * read; `waitForReview` observes their status through the test fixture
 * SQL instead.
 */
async function workspaceStatus(
  page: import("@playwright/test").Page,
  siteId: string,
  workspaceId: string,
): Promise<string> {
  const response = await page.request.get(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}`,
  );
  expect(response.status()).toBe(200);
  const body = (await response.json()) as { status: string };
  return body.status;
}

/**
 * The snapshot row and the FREEZING -> REVIEW transition commit in one
 * transaction: poll until no consistent read sees FREEZING+snapshot and the
 * workspace is REVIEW (same contract as accept-lifecycle.spec.ts).
 */
async function waitForReview(
  page: import("@playwright/test").Page,
  project: string,
  siteId: string,
  workspaceId: string,
  actorType: "AGENT" | "HUMAN",
  freezeJobId: string,
): Promise<void> {
  const deadline = Date.now() + 240_000;
  for (;;) {
    expect(
      Number(
        psql(
          project,
          `SELECT count(*) FROM control.review_snapshot
            WHERE workspace_id = '${workspaceId}'
              AND EXISTS (SELECT 1 FROM control.workspace w
                          WHERE w.id = '${workspaceId}'::uuid
                            AND w.status = 'FREEZING')`,
        ),
      ),
    ).toBe(0);
    // A freeze job that terminates FAILED leaves the workspace FREEZING;
    // surface its actual terminal error instead of a bare status timeout.
    const freezeJobStatus = psql(
      project,
      `SELECT status FROM control.review_job
         WHERE id = '${freezeJobId}'::uuid`,
    );
    if (freezeJobStatus === "FAILED") {
      throw new Error(
        "freeze job FAILED: " +
          psql(
            project,
            `SELECT COALESCE(error, '') FROM control.review_job
               WHERE id = '${freezeJobId}'::uuid`,
          ),
      );
    }
    const status =
      actorType === "AGENT"
        ? await workspaceStatus(page, siteId, workspaceId)
        : psql(
            project,
            `SELECT status FROM control.workspace
               WHERE id = '${workspaceId}'::uuid`,
          );
    if (status === "REVIEW") return;
    expect(["ACTIVE", "FREEZING"]).toContain(status);
    if (Date.now() > deadline) throw new Error(`timeout at status ${status}`);
    await page.waitForTimeout(500);
  }
}

async function reviewAcceptBody(
  page: import("@playwright/test").Page,
  siteId: string,
  workspaceId: string,
): Promise<{ snapshot_id: string; digest: string; acknowledge_summary: true }> {
  const response = await page.request.get(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/review/`,
  );
  expect(response.status()).toBe(200);
  const document = (await response.json()) as {
    snapshot: { id: string; digest: string };
  };
  return {
    snapshot_id: document.snapshot.id,
    digest: document.snapshot.digest,
    acknowledge_summary: true,
  };
}

/**
 * One real human freeze/accept cycle: freeze (202) -> REVIEW -> accept
 * (202) -> the actual review worker terminal SUCCEEDED -> workspace
 * ACCEPTED, canonical_revision +1, exactly one WORKSPACE_ACCEPTED outbox
 * row whose media_manifest is the asserted published set (by media_id and
 * digest).  Returns the snapshot id, the accept job id, the outbox payload
 * digest and the new canonical revision.
 */
async function acceptCycle(
  page: import("@playwright/test").Page,
  project: string,
  siteId: string,
  workspaceId: string,
  expectedManifest: Array<{ media_id: string; digest: string }>,
  actorType: "AGENT" | "HUMAN",
): Promise<{
  snapshot_id: string;
  job_id: string;
  digest: string;
  canonical_revision: number;
}> {
  const beforeRevision = Number(
    psql(
      project,
      "SELECT canonical_revision FROM control.site WHERE id = " + `'${siteId}'::uuid`,
    ),
  );
  const freeze = await controlFreeze(page, siteId, workspaceId);
  expect(freeze.status).toBe(202);
  expect(freeze.job_id).toMatch(/^[0-9a-f-]{36}$/);
  await waitForReview(page, project, siteId, workspaceId, actorType, freeze.job_id);
  // The freeze job the control call enqueued must itself have succeeded
  // (the snapshot is what the human review below accepts).
  const freezeDeadline = Date.now() + 240_000;
  for (;;) {
    const freezeJob = psql(
      project,
      `SELECT status FROM control.review_job WHERE id = '${freeze.job_id}'::uuid`,
    );
    if (freezeJob === "SUCCEEDED") break;
    if (freezeJob === "FAILED") {
      throw new Error(
        "freeze job FAILED: " +
          psql(
            project,
            `SELECT COALESCE(error, '') FROM control.review_job
               WHERE id = '${freeze.job_id}'::uuid`,
          ),
      );
    }
    if (Date.now() > freezeDeadline)
      throw new Error(`freeze job stuck at ${freezeJob}`);
    await page.waitForTimeout(500);
  }
  const body = await reviewAcceptBody(page, siteId, workspaceId);
  const acceptResponse = await page.request.post(
    `/api/control/v1/sites/${siteId}/workspaces/${workspaceId}/accept/`,
    { headers: { "X-CSRF-Token": await adminCsrf(page) }, data: body },
  );
  expect(acceptResponse.status()).toBe(202);
  const acceptJson = (await acceptResponse.json()) as { job_id: string };
  const deadline = Date.now() + 300_000;
  for (;;) {
    const jobStatus = psql(
      project,
      `SELECT status FROM control.review_job
         WHERE id = '${acceptJson.job_id}'::uuid`,
    );
    if (jobStatus === "SUCCEEDED") break;
    if (jobStatus === "FAILED") {
      throw new Error(
        "accept job FAILED: " +
          psql(
            project,
            `SELECT COALESCE(error, '') FROM control.review_job
               WHERE id = '${acceptJson.job_id}'::uuid`,
          ),
      );
    }
    if (Date.now() > deadline) throw new Error(`accept job stuck at ${jobStatus}`);
    await page.waitForTimeout(500);
  }
  expect(
    psql(
      project,
      `SELECT status FROM control.workspace WHERE id = '${workspaceId}'::uuid`,
    ),
  ).toBe("ACCEPTED");
  expect(
    psql(
      project,
      "SELECT canonical_revision FROM control.site WHERE id = " + `'${siteId}'::uuid`,
    ),
  ).toBe(String(beforeRevision + 1));
  const manifestRaw = psql(
    project,
    `SELECT COALESCE(payload::text, '') FROM control.cache_outbox
      WHERE workspace_id = '${workspaceId}'::uuid
        AND event_kind = 'WORKSPACE_ACCEPTED'`,
  );
  const outboxPayload = JSON.parse(manifestRaw || "{}") as {
    digest: string;
    base_site_revision: number;
    new_canonical_revision: number;
    media_manifest: Array<{
      media_id: string;
      digest: string;
      public_key: string;
    }>;
  };
  // The outbox digest is the human-reviewed snapshot digest itself.
  expect(outboxPayload.digest).toBe(body.digest);
  expect(outboxPayload.base_site_revision).toBe(beforeRevision);
  expect(outboxPayload.new_canonical_revision).toBe(beforeRevision + 1);
  expect(outboxPayload.media_manifest).toHaveLength(expectedManifest.length);
  for (const expected of expectedManifest) {
    const entry = outboxPayload.media_manifest.find(
      (item) => item.media_id === expected.media_id,
    );
    expect(entry, `manifest entry for ${expected.media_id}`).toBeDefined();
    expect(entry?.digest).toBe(expected.digest);
    expect(entry?.public_key).toBe(
      `public/sha256/${expected.digest.slice(0, 2)}/${expected.digest.slice(
        2,
        4,
      )}/${expected.digest}`,
    );
  }
  return {
    snapshot_id: body.snapshot_id,
    job_id: acceptJson.job_id,
    digest: outboxPayload.digest,
    canonical_revision: beforeRevision + 1,
  };
}

/** Unauthenticated public digest read (the sessionless /media/public route). */
function publicDigestPath(digest: string): string {
  return `/media/public/sha256/${digest.slice(0, 2)}/${digest.slice(2, 4)}/${digest}`;
}

// Bounded failure-only console diagnostics: fixed phase/source/message enums,
// console type, numeric text length, bounded origin-scheme class. Never raw
// message text, literal origins/hosts/paths/queries/URLs, IDs, cookies, tokens.
const CONSOLE_SCHEME_CLASSES = new Set([
  "http",
  "https",
  "data",
  "blob",
  "about",
  "devtools",
  "chrome-extension",
  "chrome",
  "chrome-untrusted",
]);

function originSchemeClass(url: string): string {
  if (url === "") return "empty";
  try {
    const scheme = new URL(url).protocol.replace(/:$/, "");
    return CONSOLE_SCHEME_CLASSES.has(scheme) ? scheme : "other-scheme";
  } catch {
    return "unparseable";
  }
}

type ConsolePhase =
  | "init"
  | "login"
  | "setup"
  | "preview-image"
  | "preview-gallery"
  | "preview-doclist"
  | "final";

type RedactedConsoleRecord = {
  phase: ConsolePhase;
  source: string;
  message: string;
  type: "error";
  len: number;
  scheme: string;
  originFamily: ConsoleOriginFamily;
  messageFamily: ConsoleMessageFamily;
};

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

  let consolePhase: ConsolePhase = "init";
  let consoleEventCount = 0;
  const consoleRecords: RedactedConsoleRecord[] = [];
  page.on("console", (message) => {
    if (message.type() !== "error") return;
    consoleEventCount += 1;
    const sourceUrl = message.location().url;
    if (consoleRecords.length < 16) {
      consoleRecords.push({
        phase: consolePhase,
        source: classifyConsoleSource(sourceUrl, page.url()),
        message: classifyConsoleMessage(message.text()),
        type: "error",
        len: message.text().length,
        scheme: originSchemeClass(sourceUrl),
        originFamily: classifyConsoleOriginFamily(sourceUrl, page.url()),
        messageFamily: classifyConsoleMessageFamily(message.text()),
      });
    }
  });
  const redactedConsoleDetail = () => {
    const seen = new Set<string>();
    const events: RedactedConsoleRecord[] = [];
    for (const record of consoleRecords) {
      const key = JSON.stringify(record);
      if (!seen.has(key) && events.length < 4) {
        seen.add(key);
        events.push(record);
      }
    }
    return (
      "redacted-console:" +
      JSON.stringify({
        observed: consoleEventCount,
        stored: consoleRecords.length,
        events,
      })
    );
  };
  const expectConsoleClean = (label: string) => {
    const current = failures();
    try {
      expect(current).toEqual([]);
    } catch (err) {
      throw new Error(
        `${label} ${redactedConsoleDetail()} failures=${JSON.stringify(current)} ` +
          String(err),
        { cause: err },
      );
    }
  };
  // Hermetic bounded-embed fixture: tools/compose/e2e.sh seeds the shared
  // parity preview workspace before the preview project runs, and the
  // preview project's editor path leaves its two bounded-embed components
  // (youtube-nocookie video, openstreetmap map) in that workspace's COW
  // overlay. This project renders the same workspace again, so intercept
  // exactly those two canonical embed URLs with a controlled static
  // response before any navigation. The edge CSP frame-src allowlist and
  // the emitted iframe markup are still exercised; only the third-party
  // response body is replaced, and the fixture marker keeps the
  // interception observable.
  const embedFixtureBody =
    "<!doctype html><html><body>bounded embed fixture</body></html>";
  const embedFixture = async (route: import("@playwright/test").Route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/html",
      body: embedFixtureBody,
    });
  };
  await page.route(
    /^https:\/\/www\.youtube-nocookie\.com\/embed\/dQw4w9WgXcQ$/u,
    embedFixture,
  );
  await page.route(
    /^https:\/\/www\.openstreetmap\.org\/export\/embed\.html\?bbox=-12\.5,55,-12\.4,55\.1&layer=cyclemap$/u,
    embedFixture,
  );

  // ---------------------------------------------------------------- login
  consolePhase = "login";
  await login(page, credential);
  const csrf = (await page.context().cookies()).find(
    (cookie) => cookie.name === "slaif_csrf",
  )?.value;
  expect(csrf).toBeTruthy();
  expectConsoleClean("login");
  consolePhase = "setup";
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
  // Explicit key: this roster also hosts run-unique fixture sites (the
  // 083/1 accept-lifecycle proof), which sort before "demo" in /me/sites.
  const demo = sites.find((site) => site.site_key === "demo");
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
  // Run-unique valid PNG (see generator): its digest holds no prior public
  // authorization anywhere in this driver, so the pending-private 404 and
  // the post-acceptance 200 are both real oracles.
  const agentPngBytes = makeRunUniquePng(Buffer.from(`${tag}:${Date.now()}`, "utf8"));
  const agentPngDigest = sha256Hex(agentPngBytes);
  const agentUpload = await page.request.post("/api/agent/v1/media/assets", {
    headers: {
      ...agentHeaders,
      "Idempotency-Key": `oap-079a-agent-upload-${tag}`,
    },
    multipart: uploadForm(agentPngBytes, "agent-proof.png", "image/png", {
      alt_text: "E2E agent media proof",
    }),
  });
  expect(agentUpload.status()).toBe(201);
  const agentUploadBody = (await agentUpload.json()) as {
    record?: Record<string, unknown>;
  };
  const agentMediaId = requiredString(agentUploadBody.record?.id, "media id");
  expect(agentMediaId).toMatch(/^[0-9a-f-]{36}$/);
  expect(agentUploadBody.record?.content_hash).toBe(agentPngDigest);

  // Idempotent replay: same key + same bounded digest, same record.
  const agentReplay = await page.request.post("/api/agent/v1/media/assets", {
    headers: {
      ...agentHeaders,
      "Idempotency-Key": `oap-079a-agent-upload-${tag}`,
    },
    multipart: uploadForm(agentPngBytes, "agent-proof.png", "image/png", {
      alt_text: "E2E agent media proof",
    }),
  });
  expect(agentReplay.status()).toBe(201);
  const agentReplayBody = (await agentReplay.json()) as {
    record?: Record<string, unknown>;
  };
  expect(agentReplayBody.record?.id).toBe(agentMediaId);

  // ------------------------------------------------ agent hostile uploads
  // These bounded negative/revocation oracles run BEFORE the agent
  // workspace's real freeze/accept (cycle 1): the freeze itself revokes
  // the capability, so a revoked capability could not afterwards serve as
  // the intended 422/413/400 domain-rejection subject.
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

  // Oversized upload: edge body limit rejects before the service.
  const oversized = Buffer.alloc(101 * 1024 * 1024, 0);
  agentPngBytes.copy(oversized, 0);
  const oversizedUpload = await page.request.post("/api/agent/v1/media/assets", {
    headers: {
      ...agentHeaders,
      "Idempotency-Key": `oap-079a-hostile-oversized-${tag}`,
    },
    multipart: uploadForm(oversized, "large.png", "image/png"),
  });
  expect(oversizedUpload.status()).toBe(413);
  oversized.fill(0);

  // Missing idempotency key: 400 with the exact bounded key.
  const missingKey = await page.request.post("/api/agent/v1/media/assets", {
    headers: agentHeaders,
    multipart: uploadForm(agentPngBytes, "agent-proof.png", "image/png"),
  });
  expect(missingKey.status()).toBe(400);
  expect(((await missingKey.json()) as { error: { code: string } }).error.code).toBe(
    "IDEMPOTENCY_KEY_REQUIRED",
  );

  // Revoked capability: the control-plane revoke is 200 with the bounded
  // key, then the agent upload is refused with 401 (the explicit revoke
  // precedes cycle 1 because the revoke requires an ACTIVE workspace and
  // the freeze revokes the capability itself).
  const revokeResponse = await page.request.post(
    `/api/control/v1/sites/${parity.site_id}/workspaces/${agentWorkspaceId}/capabilities/${agentCapabilityId}/revoke`,
    { headers: { "X-CSRF-Token": csrf! } },
  );
  expect(revokeResponse.status()).toBe(200);
  const revokedUpload = await page.request.post("/api/agent/v1/media/assets", {
    headers: agentHeaders,
    multipart: uploadForm(agentPngBytes, "agent-proof.png", "image/png"),
  });
  expect(revokedUpload.status()).toBe(401);
  expect(((await revokedUpload.json()) as { error: { code: string } }).error.code).toBe(
    "AUTHENTICATION_REQUIRED",
  );

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

  // ------------------------------------------------- embed order normalization
  // The preview project's editor path left its two bounded-embed components
  // in this shared preview workspace's COW overlay without an explicit
  // order_key (CreateCompositionNodeRequest default), so the overlay carries
  // two key-0 top-level nodes.  Cycle 3's real acceptance must leave a valid
  // coherent composition for the later hostile Agent tree validation
  // (contiguous unique 0..n-1 per group), so the two nodes are repositioned
  // through the existing lawful human Editor move endpoint before any
  // preview render is captured.  No owner SQL, no product change.
  const compositionListResponse = await page.request.get(
    `/api/editor/v1/sites/${parity.site_id}/pages/${homePage!.id}/composition/`,
  );
  expect(compositionListResponse.status()).toBe(200);
  const compositionNodes = (await compositionListResponse.json()) as Array<{
    id: string;
    component_type: string;
    parent_id: string | null;
    slot_key: string;
    order_key: number;
  }>;
  const embedNodes = compositionNodes.filter(
    (node) =>
      node.parent_id === null &&
      node.slot_key === "default" &&
      (node.component_type === "VideoEmbed" || node.component_type === "MapBlock"),
  );
  expect(embedNodes).toHaveLength(2);
  const videoEmbed = embedNodes.find((node) => node.component_type === "VideoEmbed");
  const mapEmbed = embedNodes.find((node) => node.component_type === "MapBlock");
  if (!videoEmbed || !mapEmbed) throw new Error("preview workspace embeds missing");
  const moveEmbedTo = async (nodeId: string, key: number): Promise<void> => {
    const response = await page.request.post(`${compositionPath}/${nodeId}/move`, {
      headers: editorHeaders(`oap-079a-embed-move-${key}-${tag}`),
      data: { new_order_key: key },
    });
    expect(response.status()).toBe(200);
    const record = (await response.json()) as { order_key: number };
    expect(record.order_key).toBe(key);
  };
  await moveEmbedTo(videoEmbed.id, 7);
  await moveEmbedTo(mapEmbed.id, 8);

  // The agent-uploaded Image node is placed in the AGENT workspace through
  // the lawful delegator-human Editor envelope with the X-Editor-Workspace
  // selection (the L1 agent capability has no component-structure:create,
  // so the agent surface cannot create the node itself).  Explicit order
  // keys keep the promoted canonical top-level group contiguous for the
  // later hostile Agent composition writes: seeded base 0-5 (Heading,
  // RichText, Section, CollectionList, CollectionGrid, CollectionDetail),
  // agent Image 6 (agent workspace), repositioned preview embeds 7-8,
  // human Image 9, Gallery 10, LogoGrid 11, DocumentList 12; the final
  // canonical top-level group is contiguous 0..12.
  const imageCreate = await page.request.post(compositionPath, {
    headers: {
      ...editorHeaders(`oap-079a-image-agent-${tag}`),
      "X-Editor-Workspace": agentWorkspaceId,
    },
    data: {
      component_type: "Image",
      slot_key: "default",
      order_key: 6,
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
      order_key: 9,
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
  consolePhase = "preview-image";
  // A4 actual NEW-pending private preview through the public edge: the
  // delegator human previews the AGENT workspace while the upload is still
  // pending (not canonical, not public): workspace-scoped 054 preview-chain
  // URL and byte-identical authenticated fetch, with the sessionless public
  // digest route and the canonical base both refusing it.
  const agentPreviewPage = await page.goto(`/preview/${agentWorkspaceId}/s/parity/`);
  expect(agentPreviewPage?.status()).toBe(200);
  const agentPendingImage = page
    .locator('img.sl-image[src^="/media/v1/sites/"]')
    .first();
  await expect(agentPendingImage).toBeVisible();
  expect(await agentPendingImage.getAttribute("src")).toBe(
    `/media/v1/sites/${parity.site_id}/workspaces/${agentWorkspaceId}/preview/assets/${agentMediaId}/content`,
  );
  expect(await agentPendingImage.getAttribute("alt")).toBe("E2E agent media proof");
  const agentPreviewFetch = await page.request.get(
    `/media/v1/sites/${parity.site_id}/workspaces/${agentWorkspaceId}/preview/assets/${agentMediaId}/content`,
  );
  expect(agentPreviewFetch.status()).toBe(200);
  expect(agentPreviewFetch.headers()["cache-control"]).toBe("private, no-store");
  expect((await agentPreviewFetch.body()).equals(agentPngBytes)).toBe(true);
  // Run-unique digest: no prior canonical/public authorization exists for
  // these bytes in this driver, so the pending-private 404 is a real oracle.
  const agentPendingPublic = await page.request.get(publicDigestPath(agentPngDigest));
  expect(agentPendingPublic.status()).toBe(404);
  expect(
    psql(
      project,
      `SELECT count(*) FROM content.media_asset_base
        WHERE id = '${agentMediaId}'::uuid`,
    ),
  ).toBe("0");

  // ------------------------------------- real human acceptance cycle 1 (agent)
  // The product publication boundary: the real freeze/review/accept cycle
  // for the AGENT workspace.  Its single reviewer transaction promotes the
  // pending Image node + pending media row and publishes exactly the
  // reviewed, referenced closure (the agent Image).
  const cycle1 = await acceptCycle(
    page,
    project,
    parity.site_id,
    agentWorkspaceId,
    [{ media_id: agentMediaId, digest: agentPngDigest }],
    "AGENT",
  );
  // Canonical promotion effects: the media row is public with a publish
  // timestamp, and the pending overlay is gone.
  expect(
    psql(
      project,
      `SELECT public_status || '|' ||
                CASE WHEN published_at IS NOT NULL THEN 't' ELSE 'f' END
                     || '|' || content_hash
         FROM content.media_asset_base
        WHERE id = '${agentMediaId}'::uuid`,
    ),
  ).toBe(`public|t|${agentPngDigest}`);
  expect(
    psql(
      project,
      `SELECT count(*) FROM content.media_asset_changes
        WHERE session_id = '${agentWorkspaceId}'::uuid`,
    ),
  ).toBe("0");
  // The immutable frozen snapshot descriptor keeps its freeze-time facts
  // (the media was private when reviewed) after acceptance.
  expect(
    psql(
      project,
      `SELECT ((payload::jsonb)->'media'->'${agentMediaId}'->>'public_status')
           || '|' ||
               ((payload::jsonb)->'media'->'${agentMediaId}'->>'content_hash')
         FROM control.review_snapshot
        WHERE id = '${cycle1.snapshot_id}'::uuid`,
    ),
  ).toBe(`private|${agentPngDigest}`);
  // Frozen retained bytes: the review-snapshot byte route still serves the
  // exact frozen PNG after the workspace is ACCEPTED.
  const frozenAgent = await page.request.get(
    `/media/v1/review/${cycle1.snapshot_id}/assets/${agentMediaId}/content`,
  );
  expect(frozenAgent.status()).toBe(200);
  expect((await frozenAgent.body()).equals(agentPngBytes)).toBe(true);

  // ------------------------------------------- unauthenticated public digest read
  const anonymous = await browser.newContext();
  try {
    const agentPublicFetch = await anonymous.request.get(
      publicDigestPath(agentPngDigest),
    );
    expect(agentPublicFetch.status()).toBe(200);
    const publicHeaders = agentPublicFetch.headers();
    expect(publicHeaders["content-type"]).toBe("image/png");
    expect(publicHeaders["cache-control"]).toBe("public, max-age=31536000, immutable");
    expect(publicHeaders["x-content-type-options"]).toBe("nosniff");
    expect(publicHeaders["content-length"]).toBe(String(agentPngBytes.length));
    expect((await agentPublicFetch.body()).equals(agentPngBytes)).toBe(true);
    // Honesty: the human fixture upload is still pending in the preview
    // workspace, so its digest is NOT public yet.
    const humanPendingPublic = await anonymous.request.get(
      publicDigestPath(fixtureDigest),
    );
    expect(humanPendingPublic.status()).toBe(404);
  } finally {
    await anonymous.close();
  }

  // ------------------------------------------- preview render (preview workspace)
  // The agent image is now canonical (public); the preview renderer still
  // emits the workspace-scoped 054 preview-chain URL for it, while the
  // human fixture image is pending in this workspace.
  const previewPage = await page.goto(`/preview/${previewWorkspaceId}/s/parity/`);
  expect(previewPage?.status()).toBe(200);
  // R6: the preview renderer emits the workspace-scoped 054 preview-chain
  // byte URL (human preview); the legacy site-level read route still exists
  // for the route-level authorization negatives below and stays unchanged.
  const agentImage = page.locator('img.sl-image[src^="/media/v1/sites/"]').first();
  await expect(agentImage).toBeVisible();
  expect(await agentImage.getAttribute("src")).toBe(
    `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${agentMediaId}/content`,
  );
  expect(await agentImage.getAttribute("alt")).toBe("E2E agent media proof");
  expect(await agentImage.getAttribute("loading")).toBe("lazy");
  expect(await agentImage.getAttribute("referrerpolicy")).toBe("no-referrer");
  const humanImage = page.locator('img.sl-image[src^="/media/v1/sites/"]').nth(1);
  expect(await humanImage.getAttribute("src")).toBe(
    `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${humanMediaId}/content`,
  );

  // Byte-identical authenticated preview fetch for the human media.
  const previewFetch = await page.request.get(
    `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${humanMediaId}/content`,
  );
  expect(previewFetch.status()).toBe(200);
  expect(previewFetch.headers()["cache-control"]).toBe("private, no-store");
  expect((await previewFetch.body()).equals(fixtureBytes)).toBe(true);

  expectConsoleClean("preview-image");
  consolePhase = "preview-gallery";

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
      publicDigestPath(agentPngDigest),
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
      publicDigestPath(agentPngDigest),
    );
    const previewAgentMarkup = imageMarkup(
      previewHtml,
      `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${agentMediaId}/content`,
    );
    expect(
      previewAgentMarkup.replace(
        `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${agentMediaId}/content`,
        publicDigestPath(agentPngDigest),
      ),
    ).toBe(canonicalAgentMarkup);
  } finally {
    await anonymousPageContext.close();
  }

  // -------------------------------------------- Gallery + LogoGrid (079/2)
  // Seed a well-formed in-site non-image asset: a reference that resolves
  // within the parity site but fails the image MIME class, so both write
  // paths must reject it with the exact item-not-image key.  Base-row
  // fixture seeding, consistent with this spec's psql fixture pattern.
  const NON_IMAGE_MEDIA_ID = "12000000-0000-4000-8000-000000000401";
  const nonImageDigest = sha256Hex(Buffer.from("oap-079-2-hostile-note"));
  psql(
    project,
    `INSERT INTO content.media_asset_base
       (id, site_id, filename, mime_type, size_bytes, content_hash,
        storage_key, alt_text, metadata, public_status)
     VALUES ('${NON_IMAGE_MEDIA_ID}'::uuid, '${parity.site_id}'::uuid,
             'hostile-note.txt', 'text/plain', 42, '${nonImageDigest}',
             'sha256/${nonImageDigest.slice(0, 2)}/${nonImageDigest.slice(2, 4)}/${nonImageDigest}',
             '', '{}'::jsonb, 'private');`,
  );

  // Editor (human) composition: one Gallery and one LogoGrid of the real
  // uploaded media (agent upload + human fixture upload, both parity site).
  const galleryCreate = await page.request.post(compositionPath, {
    headers: editorHeaders(`oap-0792-gallery-${tag}`),
    data: {
      component_type: "Gallery",
      slot_key: "default",
      order_key: 10,
      props: {
        title: "E2E gallery proof",
        columns: "3",
        items: [
          { mediaId: agentMediaId, alt: "E2E gallery agent item" },
          { mediaId: humanMediaId, alt: "E2E gallery human item" },
        ],
      },
    },
  });
  expect(galleryCreate.status()).toBe(201);
  const galleryCreateBody = (await galleryCreate.json()) as {
    id?: unknown;
    row_version?: unknown;
  };
  expect(galleryCreateBody.row_version).toBe(1);
  expect(typeof galleryCreateBody.id).toBe("string");
  const galleryComponentId = galleryCreateBody.id as string;
  const logoGridCreate = await page.request.post(compositionPath, {
    headers: editorHeaders(`oap-0792-logogrid-${tag}`),
    data: {
      component_type: "LogoGrid",
      slot_key: "default",
      order_key: 11,
      props: {
        title: "E2E logo grid proof",
        items: [
          { mediaId: agentMediaId, name: "E2E agent logo" },
          { mediaId: humanMediaId, name: "E2E human logo" },
        ],
      },
    },
  });
  expect(logoGridCreate.status()).toBe(201);
  const logoGridCreateBody = (await logoGridCreate.json()) as {
    id?: unknown;
    row_version?: unknown;
  };
  expect(logoGridCreateBody.row_version).toBe(1);
  expect(typeof logoGridCreateBody.id).toBe("string");
  const logoGridComponentId = logoGridCreateBody.id as string;

  // Preview render of the list components at desktop and tablet.
  const previewReload = await page.goto(`/preview/${previewWorkspaceId}/s/parity/`);
  expect(previewReload?.status()).toBe(200);
  const gallerySection = page.locator("section.sl-gallery");
  await expect(gallerySection).toBeVisible();
  const galleryAgentImage = page
    .locator('section.sl-gallery img.sl-image[src^="/media/v1/sites/"]')
    .first();
  await expect(galleryAgentImage).toBeVisible();
  expect(await galleryAgentImage.getAttribute("src")).toBe(
    `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${agentMediaId}/content`,
  );
  const galleryHumanImage = page
    .locator('section.sl-gallery img.sl-image[src^="/media/v1/sites/"]')
    .nth(1);
  expect(await galleryHumanImage.getAttribute("src")).toBe(
    `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${humanMediaId}/content`,
  );
  const logoGridSection = page.locator("section.sl-logogrid");
  await expect(logoGridSection).toBeVisible();
  const logoGridAgentImage = page
    .locator('section.sl-logogrid img.sl-logogrid__logo[src^="/media/v1/sites/"]')
    .first();
  await expect(logoGridAgentImage).toBeVisible();
  expect(await logoGridAgentImage.getAttribute("src")).toBe(
    `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${agentMediaId}/content`,
  );
  await page.setViewportSize({ width: 768, height: 1024 });
  await expect(gallerySection).toBeVisible();
  await expect(galleryAgentImage).toBeVisible();
  await expect(logoGridSection).toBeVisible();
  await expect(logoGridAgentImage).toBeVisible();
  await page.setViewportSize({ width: 1280, height: 720 });
  // Capture the PRE-acceptance preview DOM: the list parity assertion
  // compares it against the canonical render AFTER real acceptance
  // cycle 3 promotes these nodes and publishes their media.
  const listPreviewHtml = await page.content();

  // Observable interception: the shared workspace must still carry exactly
  // the two bounded-embed components the preview project left behind.
  // preview.spec.ts pins a positional src contract on its own AGENT
  // workspace; this project renders the separate shared HUMAN workspace, so
  // only exact fixture membership is asserted here (layout order is not the
  // purpose of this media check). Scroll each expected lazy iframe into view
  // so the browser commits it, then require the hermetic fixture marker
  // inside the actual frame. A live third-party body, a failed interception,
  // or missing/unexpected fixture state cannot satisfy this.
  const expectedEmbedSrcs = [
    "https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ",
    "https://www.openstreetmap.org/export/embed.html?bbox=-12.5,55,-12.4,55.1&layer=cyclemap",
  ];
  const embedIframes = page.locator("iframe.sl-embed");
  await expect(embedIframes).toHaveCount(2);
  // Closed diagnostic classes derived only by exact equality to the two
  // fixed canonical URLs; the sorted class pair rejects duplicates, missing,
  // or unexpected iframe values without printing raw iframe URLs.
  const embedClass = (src: string | null): "video" | "map" | "unexpected" =>
    src === expectedEmbedSrcs[0]
      ? "video"
      : src === expectedEmbedSrcs[1]
        ? "map"
        : "unexpected";
  expect(
    [
      await embedIframes.nth(0).getAttribute("src"),
      await embedIframes.nth(1).getAttribute("src"),
    ]
      .map(embedClass)
      .sort(),
  ).toEqual(["map", "video"]);
  for (const embedIndex of expectedEmbedSrcs.keys()) {
    const embedIframe = embedIframes.nth(embedIndex);
    await embedIframe.scrollIntoViewIfNeeded();
    await expect(
      embedIframe.contentFrame().getByText("bounded embed fixture"),
    ).toHaveCount(1);
  }

  expectConsoleClean("preview-gallery");
  consolePhase = "preview-doclist";

  // ---------------------------------- hostile L2 workspace (079/2)
  // L2_SITE_EDITOR is the least-privilege preset adding
  // component-structure:create to L1's component-content-props:write; the
  // L1 capability above cannot create components by design.  The hostile
  // workspace is never frozen or accepted in this spec, so its capability
  // stays lawful and ACTIVE for every Agent oracle below.
  const hostileWorkspaceResponse = await page.request.post(
    `/api/control/v1/sites/${parity.site_id}/workspaces/`,
    {
      headers: editorHeaders(`oap-0792-hostile-workspace-${tag}`),
      data: {
        title: `OAP 079-2 media-reference hostile proof ${tag}`,
        task_description: "Bounded Agent media-reference hostile proof",
        delegation_preset: "L2_SITE_EDITOR",
        duration_hours: 1,
        request_quota: 200,
        mutation_quota: 50,
        delete_quota: 0,
        upload_quota: 0,
        browser_quota: 0,
        resource_constraints: {},
      },
    },
  );
  expect(hostileWorkspaceResponse.status()).toBe(201);
  const hostileWorkspaceBody = (await hostileWorkspaceResponse.json()) as {
    workspace_id?: unknown;
  };
  const hostileWorkspaceId = requiredString(
    hostileWorkspaceBody.workspace_id,
    "hostile workspace id",
  );
  const hostileCapabilityResponse = await page.request.post(
    `/api/control/v1/sites/${parity.site_id}/workspaces/${hostileWorkspaceId}/capabilities/`,
    { headers: editorHeaders(`oap-0792-hostile-capability-${tag}`) },
  );
  expect(hostileCapabilityResponse.status()).toBe(201);
  const hostileCapability = (await hostileCapabilityResponse.json()) as {
    capability_id?: unknown;
    token?: unknown;
  };
  const hostileAgentToken = requiredString(
    hostileCapability.token,
    "hostile capability token",
  );
  expect(hostileAgentToken).toMatch(/^sas2_/);
  const hostileAgentHeaders = {
    Authorization: `Bearer ${hostileAgentToken}`,
  } as const;
  // ------------------------------------------------- hostile data + helpers
  // Bounded hostile payloads and the shared case helpers: the Editor
  // oracles run BEFORE the real acceptances (while the preview workspace
  // is still ACTIVE), the Agent oracles run AFTER them, when the hostile
  // workspace's COW view sees the full canonical site media.

  const rowVersionOf = (
    body: Array<{ id: string; row_version: number }>,
    id: string,
  ): number => {
    const record = body.find((node) => node.id === id);
    if (!record) throw new Error(`component missing from agent list: ${id}`);
    return record.row_version;
  };

  const hostileGalleryItems = (count: number) =>
    Array.from({ length: count }, (_, index) => ({
      mediaId: agentMediaId,
      alt: `hostile item ${index}`,
    }));
  const hostileLogoGridItems = (count: number) =>
    Array.from({ length: count }, (_, index) => ({
      mediaId: agentMediaId,
      name: `hostile logo ${index}`,
    }));
  const unknownMediaId = crypto.randomUUID();
  // Bounded hostile DocumentList items (shared by the Editor and Agent
  // oracles): eleven agent cases, ten of them from the exact R3 key list.
  const doclistHostileItems = (count: number) =>
    Array.from({ length: count }, (_, index) => ({
      mediaId: pdfAgentMediaId,
      label: `hostile pdf ${index}`,
    }));

  const agentPatchCase = async (
    componentId: string,
    key: string,
    props: Record<string, unknown>,
    expectedKey: string,
  ): Promise<void> => {
    const response = await page.request.patch(
      `/api/agent/v1/components/${componentId}`,
      {
        headers: {
          ...hostileAgentHeaders,
          "Idempotency-Key": `oap-0792-agent-${key}-${tag}`,
        },
        data: { props, expected_row_version: 1 },
      },
    );
    expect(response.status()).toBe(422);
    const body = (await response.json()) as {
      error: { code: string; details?: { prop_error?: string } };
    };
    expect(body.error.code).toBe("DOMAIN_VALIDATION_FAILED");
    expect(body.error.details?.prop_error).toBe(expectedKey);
  };

  // Editor path rejects the same hostile media references with the exact
  // keys (POST shape bounds + PATCH wholesale-props validation).
  const editorPostCase = async (
    key: string,
    componentType: string,
    orderKey: number,
    props: Record<string, unknown>,
    expectedKey: string | null,
  ): Promise<void> => {
    const response = await page.request.post(compositionPath, {
      headers: editorHeaders(`oap-0792-editor-post-${key}-${tag}`),
      data: {
        component_type: componentType,
        slot_key: "default",
        order_key: orderKey,
        props,
      },
    });
    expect(response.status()).toBe(422);
    const body = (await response.json()) as {
      error: { code: string; details?: { prop_error?: string } };
    };
    expect(body.error.code).toBe("DOMAIN_VALIDATION_FAILED");
    if (expectedKey === null) {
      // Same guard-level shape-bound surface as the Agent path (bare
      // domain-validation 422, no prop_error, no input echo).
      expect(body.error.details).toBeNull();
    } else {
      expect(body.error.details?.prop_error).toBe(expectedKey);
    }
  };
  const editorPatchCase = async (
    nodeId: string,
    key: string,
    props: Record<string, unknown>,
    expectedKey: string | null,
  ): Promise<void> => {
    const response = await page.request.patch(
      `/api/editor/v1/sites/${parity.site_id}/pages/${homePage!.id}/composition/components/${nodeId}`,
      { headers: editorHeaders(`oap-0792-editor-${key}-${tag}`), data: { props } },
    );
    expect(response.status()).toBe(422);
    const body = (await response.json()) as {
      error: { code: string; details?: { prop_error?: string } };
    };
    expect(body.error.code).toBe("DOMAIN_VALIDATION_FAILED");
    if (expectedKey === null) {
      // Same guard-level shape-bound surface as the Agent path (bare
      // domain-validation 422, no prop_error, no input echo).
      expect(body.error.details).toBeNull();
    } else {
      expect(body.error.details?.prop_error).toBe(expectedKey);
    }
  };
  // Before any real acceptance: the preview workspace's own pending media
  // is visible to its editor session, so every reference rejection below
  // reaches the domain-validation layer.
  await editorPostCase(
    "gallery-out-of-range",
    "Gallery",
    24,
    { title: "hostile gallery", items: hostileGalleryItems(13) },
    "gallery.items-out-of-range",
  );
  await editorPostCase(
    "logogrid-out-of-range",
    "LogoGrid",
    25,
    { items: hostileLogoGridItems(1) },
    "logogrid.items-out-of-range",
  );
  await editorPatchCase(
    galleryComponentId,
    "gallery-out-of-range-empty",
    { items: [] },
    "gallery.items-out-of-range",
  );
  await editorPatchCase(
    galleryComponentId,
    "gallery-missing",
    { items: [{ alt: "no reference" }] },
    "gallery.item-missing",
  );
  await editorPatchCase(
    galleryComponentId,
    "gallery-missing-not-a-uuid",
    { items: [{ mediaId: "not-a-uuid", alt: "bad reference" }] },
    "gallery.item-missing",
  );
  await editorPatchCase(
    galleryComponentId,
    "gallery-foreign-demo",
    { items: [{ mediaId: demoMediaId, alt: "foreign reference" }] },
    "gallery.item-foreign-site",
  );
  await editorPatchCase(
    galleryComponentId,
    "gallery-foreign-unknown",
    { items: [{ mediaId: unknownMediaId, alt: "unknown reference" }] },
    "gallery.item-foreign-site",
  );
  await editorPatchCase(
    galleryComponentId,
    "gallery-not-image",
    { items: [{ mediaId: NON_IMAGE_MEDIA_ID, alt: "not an image" }] },
    "gallery.item-not-image",
  );
  await editorPatchCase(
    logoGridComponentId,
    "logogrid-out-of-range-max",
    { items: hostileLogoGridItems(25) },
    "logogrid.items-out-of-range",
  );
  await editorPatchCase(
    logoGridComponentId,
    "logogrid-missing",
    {
      items: [{ mediaId: agentMediaId, name: "valid logo" }, { name: "no reference" }],
    },
    "logogrid.item-missing",
  );
  await editorPatchCase(
    logoGridComponentId,
    "logogrid-foreign",
    {
      items: [
        { mediaId: agentMediaId, name: "valid logo" },
        { mediaId: demoMediaId, name: "foreign logo" },
      ],
    },
    "logogrid.item-foreign-site",
  );
  await editorPatchCase(
    logoGridComponentId,
    "logogrid-not-image",
    {
      items: [
        { mediaId: agentMediaId, name: "valid logo" },
        { mediaId: NON_IMAGE_MEDIA_ID, name: "not an image" },
      ],
    },
    "logogrid.item-not-image",
  );

  // -------------------------------------------------- DocumentList + PDF (079/3)
  // Node-side bounded PDF fixture builder: one /Type /Pages node plus N raw
  // /Type /Page objects (the /Type /Pages token never matches the
  // word-boundary page count).  `seed` varies page content so distinct
  // fixtures carry distinct digests.
  const makePdf = (pages: number, seed: string): Buffer => {
    const kids = Array.from({ length: pages }, (_, i) => `${3 + i} 0 R`).join(" ");
    const parts: string[] = [];
    parts.push("%PDF-1.4\n");
    parts.push("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n");
    parts.push(`2 0 obj\n<< /Type /Pages /Kids [${kids}] /Count ${pages} >>\nendobj\n`);
    for (let i = 0; i < pages; i++) {
      parts.push(
        `${3 + i} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 200 200] /Contents (${seed}-${i}) >>\nendobj\n`,
      );
    }
    parts.push(`trailer\n<< /Root 1 0 R /Size ${pages + 3} >>\n%%EOF\n`);
    return Buffer.from(parts.join(""), "latin1");
  };
  const pdfHumanBytes = makePdf(2, "oap-079-3-human");
  const pdfHumanDigest = sha256Hex(pdfHumanBytes);
  const pdfAgentBytes = makePdf(2, "oap-079-3-agent");
  const pdfAgentDigest = sha256Hex(pdfAgentBytes);
  const pdf201Bytes = makePdf(201, "oap-079-3-pages");
  const pdfOversizedBytes = Buffer.concat([
    makePdf(2, "oap-079-3-oversized"),
    Buffer.alloc(21 * 1024 * 1024, 0),
  ]);
  const pdfUndeterminedBytes = Buffer.from(
    "%PDF-1.4\n1 0 obj\n<< /Info (no page objects) >>\nendobj\ntrailer\n<< /Size 2 >>\n%%EOF\n",
    "latin1",
  );

  // Human edge route: the real 2-page PDF is accepted ...
  const pdfHumanUpload = await page.request.post(
    `/media/v1/sites/${parity.site_id}/assets`,
    {
      headers: {
        "X-CSRF-Token": csrf!,
        "Idempotency-Key": `oap-0793-human-pdf-${tag}`,
      },
      multipart: uploadForm(pdfHumanBytes, "e2e-human.pdf", "application/pdf"),
    },
  );
  expect(pdfHumanUpload.status()).toBe(201);
  const pdfHumanUploadBody = (await pdfHumanUpload.json()) as {
    record?: Record<string, unknown>;
  };
  const pdfHumanMediaId = requiredString(
    pdfHumanUploadBody.record?.id,
    "pdf human media id",
  );
  expect(pdfHumanUploadBody.record?.content_hash).toBe(pdfHumanDigest);
  // ... and every R1 rejection is a bounded 422 on the same route (the one
  // shared store enforcement point; exact store keys are pinned in the
  // unit matrix, the HTTP surface is bounded by design).
  const humanPdfReject = async (
    key: string,
    file: Buffer,
    filename: string,
  ): Promise<void> => {
    const response = await page.request.post(
      `/media/v1/sites/${parity.site_id}/assets`,
      {
        headers: {
          "X-CSRF-Token": csrf!,
          "Idempotency-Key": `oap-0793-human-${key}-${tag}`,
        },
        multipart: uploadForm(file, filename, "application/pdf"),
      },
    );
    expect(response.status()).toBe(422);
    const body = (await response.json()) as { error: { code: string } };
    expect(body.error.code).toBe("DOMAIN_VALIDATION_FAILED");
  };
  await humanPdfReject("signature", agentPngBytes, "forged.pdf");
  await humanPdfReject("too-large", pdfOversizedBytes, "oversized.pdf");
  await humanPdfReject("too-many-pages", pdf201Bytes, "201-pages.pdf");
  await humanPdfReject("undetermined", pdfUndeterminedBytes, "undetermined.pdf");
  pdfOversizedBytes.fill(0);
  // No partial artifacts: none of the rejected documents was stored.
  const pdfRejectNoRecord = psql(
    project,
    `SELECT count(*) FROM content.media_asset
      WHERE site_id = '${parity.site_id}'::uuid
        AND mime_type = 'application/pdf'
        AND content_hash IN ('${sha256Hex(pdf201Bytes)}', '${sha256Hex(pdfUndeterminedBytes)}');`,
  );
  expect(pdfRejectNoRecord).toBe("0");

  // Agent path: a fresh L2 workspace with one upload slot (the 079/1 L1
  // workspace already spent its upload quota).  The 1 MiB /api/agent/ edge
  // body bound keeps the oversized case on the human route; the
  // small-payload rejections exercise the same store policy on the Agent
  // route.
  const docWorkspaceResponse = await page.request.post(
    `/api/control/v1/sites/${parity.site_id}/workspaces/`,
    {
      headers: editorHeaders(`oap-0793-doc-workspace-${tag}`),
      data: {
        title: `OAP 079-3 document class ${tag}`,
        task_description: "Bounded Agent document-class proof",
        delegation_preset: "L2_SITE_EDITOR",
        duration_hours: 1,
        request_quota: 200,
        mutation_quota: 50,
        delete_quota: 0,
        upload_quota: 1,
        browser_quota: 0,
        resource_constraints: {},
      },
    },
  );
  expect(docWorkspaceResponse.status()).toBe(201);
  const docWorkspaceBody = (await docWorkspaceResponse.json()) as {
    workspace_id?: unknown;
  };
  const docWorkspaceId = requiredString(
    docWorkspaceBody.workspace_id,
    "doc workspace id",
  );
  const docCapabilityResponse = await page.request.post(
    `/api/control/v1/sites/${parity.site_id}/workspaces/${docWorkspaceId}/capabilities/`,
    { headers: editorHeaders(`oap-0793-doc-capability-${tag}`) },
  );
  expect(docCapabilityResponse.status()).toBe(201);
  const docCapability = (await docCapabilityResponse.json()) as { token?: unknown };
  const docAgentHeaders = {
    Authorization: `Bearer ${requiredString(docCapability.token, "doc capability token")}`,
  } as const;
  const pdfAgentUpload = await page.request.post("/api/agent/v1/media/assets", {
    headers: {
      ...docAgentHeaders,
      "Idempotency-Key": `oap-0793-agent-pdf-${tag}`,
    },
    multipart: uploadForm(pdfAgentBytes, "e2e-agent.pdf", "application/pdf"),
  });
  expect(pdfAgentUpload.status()).toBe(201);
  const pdfAgentUploadBody = (await pdfAgentUpload.json()) as {
    record?: Record<string, unknown>;
  };
  const pdfAgentMediaId = requiredString(
    pdfAgentUploadBody.record?.id,
    "pdf agent media id",
  );
  expect(pdfAgentUploadBody.record?.content_hash).toBe(pdfAgentDigest);
  const agentPdfReject = async (
    key: string,
    file: Buffer,
    filename: string,
  ): Promise<void> => {
    const response = await page.request.post("/api/agent/v1/media/assets", {
      headers: {
        ...docAgentHeaders,
        "Idempotency-Key": `oap-0793-agent-${key}-${tag}`,
      },
      multipart: uploadForm(file, filename, "application/pdf"),
    });
    expect(response.status()).toBe(422);
    const body = (await response.json()) as { error: { code: string } };
    expect(body.error.code).toBe("DOMAIN_VALIDATION_FAILED");
  };
  await agentPdfReject("too-many-pages", pdf201Bytes, "201-pages.pdf");
  await agentPdfReject("undetermined", pdfUndeterminedBytes, "undetermined.pdf");
  // -------------------------------- real human acceptance cycle 2 (doc ws)
  // The document workspace holds ONLY the unreferenced agent PDF upload:
  // no pending composition node references it, so this real acceptance
  // publishes NO NEW digest: the PDF is promoted canonical PRIVATE
  // metadata under the 077 referenced-closure contract.  The expected
  // manifest is nonetheless the site's FULL referenced media closure,
  // not the newly uploaded set: cycle 1 already promoted the agent
  // Image that references agentMediaId, so the manifest carries that
  // existing public asset even though nothing new becomes public.  The
  // acceptance also precedes the preview workspace's DocumentList
  // reference to this PDF: under the fixed 077 A2 contract a
  // cross-workspace pending lookup cannot resolve the PDF while it is
  // still pending here, so it must already be canonical for that
  // reference to be valid.
  await acceptCycle(
    page,
    project,
    parity.site_id,
    docWorkspaceId,
    [{ media_id: agentMediaId, digest: agentPngDigest }],
    "AGENT",
  );
  // Canonical promotion effects: private, no publish timestamp, overlay gone.
  expect(
    psql(
      project,
      `SELECT public_status || '|' ||
                CASE WHEN published_at IS NOT NULL THEN 't' ELSE 'f' END
                     || '|' || content_hash
         FROM content.media_asset_base
        WHERE id = '${pdfAgentMediaId}'::uuid`,
    ),
  ).toBe(`private|f|${pdfAgentDigest}`);
  expect(
    psql(
      project,
      `SELECT count(*) FROM content.media_asset_changes
        WHERE session_id = '${docWorkspaceId}'::uuid`,
    ),
  ).toBe("0");
  // The sessionless public route refuses the unreferenced digest.
  const pdfAgentPendingPublic = await page.request.get(
    publicDigestPath(pdfAgentDigest),
  );
  expect(pdfAgentPendingPublic.status()).toBe(404);

  // Editor (human) composition: a DocumentList of the two real PDFs: the
  // agent PDF is canonical (private) after the doc workspace acceptance
  // above, and the human PDF is this workspace's own pending upload - both
  // resolvable for this editor session under the 077 A2 contract.
  const doclistCreate = await page.request.post(compositionPath, {
    headers: editorHeaders(`oap-0793-editor-doclist-${tag}`),
    data: {
      component_type: "DocumentList",
      slot_key: "default",
      order_key: 12,
      props: {
        title: "E2E document proof",
        items: [
          { mediaId: pdfAgentMediaId, label: "E2E agent PDF" },
          { mediaId: pdfHumanMediaId, label: "E2E human PDF" },
        ],
      },
    },
  });
  expect(doclistCreate.status()).toBe(201);
  const doclistCreateBody = (await doclistCreate.json()) as {
    id?: unknown;
    row_version?: unknown;
  };
  expect(doclistCreateBody.row_version).toBe(1);
  expect(typeof doclistCreateBody.id).toBe("string");
  const editorDoclistId = doclistCreateBody.id as string;

  // Preview render of the DocumentList at desktop, tablet, and phone.
  const doclistPreview = await page.goto(`/preview/${previewWorkspaceId}/s/parity/`);
  expect(doclistPreview?.status()).toBe(200);
  const doclistSection = page.locator("section.sl-doclist");
  await expect(doclistSection).toBeVisible();
  const doclistAgentLink = page
    .locator('section.sl-doclist a.sl-doclist__link[href^="/media/v1/sites/"]')
    .first();
  await expect(doclistAgentLink).toBeVisible();
  expect(await doclistAgentLink.getAttribute("href")).toBe(
    `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${pdfAgentMediaId}/content`,
  );
  const doclistHumanLink = page
    .locator('section.sl-doclist a.sl-doclist__link[href^="/media/v1/sites/"]')
    .nth(1);
  expect(await doclistHumanLink.getAttribute("href")).toBe(
    `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${pdfHumanMediaId}/content`,
  );
  await page.setViewportSize({ width: 768, height: 1024 });
  await expect(doclistSection).toBeVisible();
  await expect(doclistAgentLink).toBeVisible();
  await expect(doclistHumanLink).toBeVisible();
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(doclistSection).toBeVisible();
  await expect(doclistAgentLink).toBeVisible();
  await expect(doclistHumanLink).toBeVisible();
  await page.setViewportSize({ width: 1280, height: 720 });
  const doclistPreviewHtml = await page.content();

  // Hostile foreign-mediaId component prop: bounded 422 with the exact
  // prop key.  Runs while the preview workspace is still ACTIVE (before
  // cycle 3 freezes it), so the denial reaches the editor's domain
  // validation, not a terminal-workspace refusal.
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

  // Editor path rejects the same hostile document references with the
  // exact keys, plus the catalog label bound (shape guard).  The agent
  // PDF is canonical (private) after cycle 2, so the valid-PDF items in
  // the mixed cases resolve for the preview workspace's editor session.
  await editorPostCase(
    "doclist-out-of-range",
    "DocumentList",
    27,
    { title: "hostile documents", items: doclistHostileItems(13) },
    "doclist.items-out-of-range",
  );
  await editorPostCase(
    "doclist-empty",
    "DocumentList",
    27,
    { items: [] },
    "doclist.items-out-of-range",
  );
  await editorPostCase(
    "doclist-missing",
    "DocumentList",
    27,
    { items: [{ label: "no reference" }] },
    "doclist.item-missing",
  );
  await editorPostCase(
    "doclist-not-pdf",
    "DocumentList",
    27,
    { items: [{ mediaId: humanMediaId, label: "png" }] },
    "doclist.item-not-pdf",
  );
  await editorPatchCase(
    editorDoclistId,
    "doclist-foreign",
    { items: [{ mediaId: demoMediaId, label: "foreign png" }] },
    "doclist.item-foreign-site",
  );
  await editorPatchCase(
    editorDoclistId,
    "doclist-not-pdf-mixed",
    {
      items: [
        { mediaId: pdfAgentMediaId, label: "valid pdf" },
        { mediaId: agentMediaId, label: "png" },
      ],
    },
    "doclist.item-not-pdf",
  );
  await editorPatchCase(
    editorDoclistId,
    "doclist-label-bound",
    { items: [{ mediaId: pdfAgentMediaId, label: "x".repeat(121) }] },
    null,
  );
  // R3 REQUIRED image-class regression negatives at composition (Editor
  // surface): now that PDFs are uploadable, the image-class components
  // reject PDF references with their exact existing keys (079/1 Image
  // key: COMPONENT_BINDING_INVALID on the Editor surface).

  // COMPONENT_BINDING_INVALID on the Editor surface).
  await editorPostCase(
    "gallery-pdf-item",
    "Gallery",
    28,
    {
      title: "hostile gallery pdf",
      items: [{ mediaId: pdfHumanMediaId, alt: "pdf item" }],
    },
    "gallery.item-not-image",
  );
  await editorPostCase(
    "logogrid-pdf-item",
    "LogoGrid",
    28,
    {
      items: [
        { mediaId: pdfHumanMediaId, name: "pdf one" },
        { mediaId: pdfAgentMediaId, name: "pdf two" },
      ],
    },
    "logogrid.item-not-image",
  );
  await editorPostCase(
    "image-pdf-binding",
    "Image",
    28,
    { mediaId: pdfHumanMediaId, alt: "pdf as image" },
    "COMPONENT_BINDING_INVALID",
  );
  // -------------------------------- real human acceptance cycle 3 (preview)
  // The shared preview workspace: the repositioned embeds, the human Image
  // (pending fixture PNG), the Gallery/LogoGrid and the DocumentList that
  // references the canonical-private agent PDF plus the pending human PDF.
  // ONE reviewer transaction promotes all pending nodes and publishes the
  // reviewed referenced closure.  The manifest is the site's FULL closure:
  // the existing agent PNG (already public since cycle 1, re-listed with no
  // new digest) plus the fixture PNG and both PDFs, of which the agent PDF
  // flips from canonical-private to public via the new reference.
  // The shared parity preview workspace is HUMAN (driver-seeded
  // actor_type='HUMAN'), so its status is observed via the test fixture
  // SQL inside the cycle; the freeze/review/accept HTTP calls below are
  // actor-agnostic and remain the real product boundary.
  const cycle3 = await acceptCycle(
    page,
    project,
    parity.site_id,
    previewWorkspaceId,
    [
      { media_id: agentMediaId, digest: agentPngDigest },
      { media_id: humanMediaId, digest: fixtureDigest },
      { media_id: pdfAgentMediaId, digest: pdfAgentDigest },
      { media_id: pdfHumanMediaId, digest: pdfHumanDigest },
    ],
    "HUMAN",
  );
  // Canonical promotion effects: every referenced asset is public with a
  // publish timestamp, and the preview workspace's pending overlay is gone.
  expect(
    psql(
      project,
      `SELECT public_status || '|' ||
                CASE WHEN published_at IS NOT NULL THEN 't' ELSE 'f' END
                     || '|' || content_hash
         FROM content.media_asset_base
        WHERE id = '${humanMediaId}'::uuid`,
    ),
  ).toBe(`public|t|${fixtureDigest}`);
  expect(
    psql(
      project,
      `SELECT public_status || '|' ||
                CASE WHEN published_at IS NOT NULL THEN 't' ELSE 'f' END
                     || '|' || content_hash
         FROM content.media_asset_base
        WHERE id = '${pdfHumanMediaId}'::uuid`,
    ),
  ).toBe(`public|t|${pdfHumanDigest}`);
  expect(
    psql(
      project,
      `SELECT public_status || '|' ||
                CASE WHEN published_at IS NOT NULL THEN 't' ELSE 'f' END
                     || '|' || content_hash
         FROM content.media_asset_base
        WHERE id = '${pdfAgentMediaId}'::uuid`,
    ),
  ).toBe(`public|t|${pdfAgentDigest}`);
  expect(
    psql(
      project,
      `SELECT count(*) FROM content.media_asset_changes
        WHERE session_id = '${previewWorkspaceId}'::uuid`,
    ),
  ).toBe("0");
  // Frozen retained bytes: the cycle-3 snapshot route still serves the
  // exact frozen bytes for all three assets after the workspace is ACCEPTED.
  const frozenHuman = await page.request.get(
    `/media/v1/review/${cycle3.snapshot_id}/assets/${humanMediaId}/content`,
  );
  expect(frozenHuman.status()).toBe(200);
  expect((await frozenHuman.body()).equals(fixtureBytes)).toBe(true);
  const frozenPdfAgent = await page.request.get(
    `/media/v1/review/${cycle3.snapshot_id}/assets/${pdfAgentMediaId}/content`,
  );
  expect(frozenPdfAgent.status()).toBe(200);
  expect((await frozenPdfAgent.body()).equals(pdfAgentBytes)).toBe(true);
  const frozenPdfHuman = await page.request.get(
    `/media/v1/review/${cycle3.snapshot_id}/assets/${pdfHumanMediaId}/content`,
  );
  expect(frozenPdfHuman.status()).toBe(200);
  expect((await frozenPdfHuman.body()).equals(pdfHumanBytes)).toBe(true);
  // Unauthenticated public digest reads after the full closure published:
  // byte-identical bytes, the record's exact Content-Type and the immutable
  // cache headers.
  expectConsoleClean("preview-doclist");
  consolePhase = "final";
  const pdfAnonymous = await browser.newContext();
  try {
    const publicCases = [
      { digest: fixtureDigest, type: "image/png", bytes: fixtureBytes },
      { digest: pdfAgentDigest, type: "application/pdf", bytes: pdfAgentBytes },
      { digest: pdfHumanDigest, type: "application/pdf", bytes: pdfHumanBytes },
    ] as const;
    for (const entry of publicCases) {
      const publicFetch = await pdfAnonymous.request.get(
        publicDigestPath(entry.digest),
      );
      expect(publicFetch.status()).toBe(200);
      const publicHeaders = publicFetch.headers();
      expect(publicHeaders["content-type"]).toBe(entry.type);
      expect(publicHeaders["cache-control"]).toBe(
        "public, max-age=31536000, immutable",
      );
      expect(publicHeaders["x-content-type-options"]).toBe("nosniff");
      expect(publicHeaders["content-length"]).toBe(String(entry.bytes.length));
      expect((await publicFetch.body()).equals(entry.bytes)).toBe(true);
    }
  } finally {
    await pdfAnonymous.close();
  }
  // Canonical render + preview/public parity for the list components: the
  // preview DOM was captured before the real acceptance (listPreviewHtml);
  // the canonical render must carry the identical markup with the
  // workspace-scoped preview byte URLs replaced by the public digest URLs.
  const listParityContext = await browser.newContext();
  try {
    const listCanonicalPage = await listParityContext.newPage();
    const listCanonicalResponse = await listCanonicalPage.goto("/s/parity/");
    expect(listCanonicalResponse?.status()).toBe(200);
    const canonicalGalleryImage = listCanonicalPage
      .locator('section.sl-gallery img.sl-image[src^="/media/public/sha256/"]')
      .first();
    await expect(canonicalGalleryImage).toBeVisible();
    expect(await canonicalGalleryImage.getAttribute("src")).toBe(
      publicDigestPath(agentPngDigest),
    );
    const canonicalLogoImage = listCanonicalPage
      .locator(
        'section.sl-logogrid img.sl-logogrid__logo[src^="/media/public/sha256/"]',
      )
      .first();
    await expect(canonicalLogoImage).toBeVisible();
    expect(await canonicalLogoImage.getAttribute("src")).toBe(
      publicDigestPath(agentPngDigest),
    );
    const listCanonicalHtml = await listCanonicalPage.content();
    const sectionMarkup = (html: string, section: string): string => {
      const match = html.match(
        new RegExp(`<section class="${section}[^"]*">[\\s\\S]*?</section>`),
      );
      if (!match) throw new Error(`section markup missing: ${section}`);
      return match[0];
    };
    const previewToPublic = (markup: string): string =>
      markup
        .replaceAll(
          `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${agentMediaId}/content`,
          publicDigestPath(agentPngDigest),
        )
        .replaceAll(
          `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${humanMediaId}/content`,
          publicDigestPath(fixtureDigest),
        );
    expect(previewToPublic(sectionMarkup(listPreviewHtml, "sl-gallery"))).toBe(
      sectionMarkup(listCanonicalHtml, "sl-gallery"),
    );
    expect(previewToPublic(sectionMarkup(listPreviewHtml, "sl-logogrid"))).toBe(
      sectionMarkup(listCanonicalHtml, "sl-logogrid"),
    );
  } finally {
    await listParityContext.close();
  }

  // Canonical render + preview/public parity for the DocumentList (the
  // preview DOM was captured before the real acceptance, exactly as the
  // 079/1 / 079/2 parity checks did).
  const doclistCanonicalContext = await browser.newContext();
  try {
    const doclistCanonicalPage = await doclistCanonicalContext.newPage();
    const doclistCanonicalResponse = await doclistCanonicalPage.goto("/s/parity/");
    expect(doclistCanonicalResponse?.status()).toBe(200);
    const canonicalPdfLink = doclistCanonicalPage
      .locator('section.sl-doclist a.sl-doclist__link[href^="/media/public/sha256/"]')
      .first();
    await expect(canonicalPdfLink).toBeVisible();
    expect(await canonicalPdfLink.getAttribute("href")).toBe(
      `/media/public/sha256/${pdfAgentDigest.slice(0, 2)}/${pdfAgentDigest.slice(2, 4)}/${pdfAgentDigest}`,
    );
    const doclistCanonicalHtml = await doclistCanonicalPage.content();
    const doclistSectionMarkup = (html: string): string => {
      const match = html.match(
        new RegExp(`<section class="sl-doclist[^"]*">[\\s\\S]*?</section>`),
      );
      if (!match) throw new Error("sl-doclist section markup missing");
      return match[0];
    };
    const pdfPreviewToPublic = (markup: string): string =>
      markup
        .replaceAll(
          `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${pdfAgentMediaId}/content`,
          `/media/public/sha256/${pdfAgentDigest.slice(0, 2)}/${pdfAgentDigest.slice(2, 4)}/${pdfAgentDigest}`,
        )
        .replaceAll(
          `/media/v1/sites/${parity.site_id}/workspaces/${previewWorkspaceId}/preview/assets/${pdfHumanMediaId}/content`,
          `/media/public/sha256/${pdfHumanDigest.slice(0, 2)}/${pdfHumanDigest.slice(2, 4)}/${pdfHumanDigest}`,
        );
    expect(pdfPreviewToPublic(doclistSectionMarkup(doclistPreviewHtml))).toBe(
      doclistSectionMarkup(doclistCanonicalHtml),
    );
  } finally {
    await doclistCanonicalContext.close();
  }

  // Final canonical top-level group: exactly the contiguous 0..12 keys
  // (seeded 0-5, agent Image 6, repositioned embeds 7-8, human Image 9,
  // Gallery 10, LogoGrid 11, DocumentList 12) - the hostile Agent tree
  // validation below requires exactly this shape.
  expect(
    psql(
      project,
      `SELECT string_agg(order_key::text, ',' ORDER BY order_key)
         FROM content.page_composition_base
        WHERE site_id = '${parity.site_id}'::uuid
          AND page_id = '${homePage!.id}'::uuid
          AND parent_id IS NULL
          AND slot_key = 'default'`,
    ),
  ).toBe("0,1,2,3,4,5,6,7,8,9,10,11,12");

  // ------------------------------------------ agent hostile suite (079/2+3)
  // AFTER the real acceptances: the hostile workspace's Agent COW view sees
  // the full canonical site media (agent upload public, fixture PNG public,
  // both PDFs public, hostile note private), so every reference rejection
  // reaches its intended domain-validation layer under a lawful ACTIVE
  // capability context.  Agent creates append max(order_key)+1, keeping the
  // hostile overlay contiguous on top of the canonical 0..12 group.

  const agentGalleryCreate = await page.request.post(
    `/api/agent/v1/pages/${homePage!.id}/components`,
    {
      headers: {
        ...hostileAgentHeaders,
        "Idempotency-Key": `oap-0792-agent-gallery-${tag}`,
      },
      data: {
        component_type: "Gallery",
        slot_key: "default",
        props: {
          title: "Agent gallery proof",
          columns: "3",
          items: [
            { mediaId: agentMediaId, alt: "agent gallery item" },
            { mediaId: humanMediaId, alt: "human gallery item" },
          ],
        },
      },
    },
  );
  expect(agentGalleryCreate.status()).toBe(201);
  const agentGalleryCreateBody = (await agentGalleryCreate.json()) as {
    record?: { id?: unknown; row_version?: unknown };
  };
  expect(agentGalleryCreateBody.record?.row_version).toBe(1);
  expect(typeof agentGalleryCreateBody.record?.id).toBe("string");
  const agentGalleryId = agentGalleryCreateBody.record?.id as string;
  const agentLogoGridCreate = await page.request.post(
    `/api/agent/v1/pages/${homePage!.id}/components`,
    {
      headers: {
        ...hostileAgentHeaders,
        "Idempotency-Key": `oap-0792-agent-logogrid-${tag}`,
      },
      data: {
        component_type: "LogoGrid",
        slot_key: "default",
        props: {
          items: [
            { mediaId: agentMediaId, name: "agent logo" },
            { mediaId: humanMediaId, name: "human logo" },
          ],
        },
      },
    },
  );
  expect(agentLogoGridCreate.status()).toBe(201);
  const agentLogoGridCreateBody = (await agentLogoGridCreate.json()) as {
    record?: { id?: unknown; row_version?: unknown };
  };
  expect(agentLogoGridCreateBody.record?.row_version).toBe(1);
  const agentLogoGridId = agentLogoGridCreateBody.record?.id as string;

  const agentListBefore = await page.request.get(
    `/api/agent/v1/pages/${homePage!.id}/components`,
    { headers: hostileAgentHeaders },
  );
  expect(agentListBefore.status()).toBe(200);
  const agentListBeforeBody = (await agentListBefore.json()) as Array<{
    id: string;
    row_version: number;
  }>;
  expect(rowVersionOf(agentListBeforeBody, agentGalleryId)).toBe(1);
  expect(rowVersionOf(agentListBeforeBody, agentLogoGridId)).toBe(1);

  await agentPatchCase(
    agentGalleryId,
    "out-of-range-max",
    { items: hostileGalleryItems(13) },
    "gallery.items-out-of-range",
  );
  await agentPatchCase(
    agentGalleryId,
    "out-of-range-empty",
    { items: [] },
    "gallery.items-out-of-range",
  );
  await agentPatchCase(
    agentGalleryId,
    "missing",
    { items: [{ alt: "no reference" }] },
    "gallery.item-missing",
  );
  await agentPatchCase(
    agentGalleryId,
    "missing-not-a-uuid",
    { items: [{ mediaId: "not-a-uuid", alt: "bad reference" }] },
    "gallery.item-missing",
  );
  await agentPatchCase(
    agentGalleryId,
    "foreign-demo",
    { items: [{ mediaId: demoMediaId, alt: "foreign reference" }] },
    "gallery.item-foreign-site",
  );
  await agentPatchCase(
    agentGalleryId,
    "foreign-unknown",
    { items: [{ mediaId: unknownMediaId, alt: "unknown reference" }] },
    "gallery.item-foreign-site",
  );
  await agentPatchCase(
    agentGalleryId,
    "not-image",
    { items: [{ mediaId: NON_IMAGE_MEDIA_ID, alt: "not an image" }] },
    "gallery.item-not-image",
  );
  await agentPatchCase(
    agentLogoGridId,
    "out-of-range-max",
    { items: hostileLogoGridItems(25) },
    "logogrid.items-out-of-range",
  );
  await agentPatchCase(
    agentLogoGridId,
    "out-of-range-min",
    { items: [{ mediaId: agentMediaId, name: "only one" }] },
    "logogrid.items-out-of-range",
  );
  await agentPatchCase(
    agentLogoGridId,
    "missing",
    {
      items: [{ mediaId: agentMediaId, name: "valid logo" }, { name: "no reference" }],
    },
    "logogrid.item-missing",
  );
  await agentPatchCase(
    agentLogoGridId,
    "foreign",
    {
      items: [
        { mediaId: agentMediaId, name: "valid logo" },
        { mediaId: demoMediaId, name: "foreign logo" },
      ],
    },
    "logogrid.item-foreign-site",
  );
  await agentPatchCase(
    agentLogoGridId,
    "not-image",
    {
      items: [
        { mediaId: agentMediaId, name: "valid logo" },
        { mediaId: NON_IMAGE_MEDIA_ID, name: "not an image" },
      ],
    },
    "logogrid.item-not-image",
  );
  // Tree and row versions unchanged after every rejection.
  // Tree and row versions unchanged after every rejection.
  const agentListAfter = await page.request.get(
    `/api/agent/v1/pages/${homePage!.id}/components`,
    { headers: hostileAgentHeaders },
  );
  expect(agentListAfter.status()).toBe(200);
  const agentListAfterBody = (await agentListAfter.json()) as Array<{
    id: string;
    row_version: number;
  }>;
  expect(agentListAfterBody).toHaveLength(agentListBeforeBody.length);
  expect(rowVersionOf(agentListAfterBody, agentGalleryId)).toBe(1);
  expect(rowVersionOf(agentListAfterBody, agentLogoGridId)).toBe(1);

  // Agent composition for the hostile suite (hostile L2 workspace owns this
  // node, mirroring the 079/2 agent Gallery/LogoGrid pattern).
  const agentDoclistCreate = await page.request.post(
    `/api/agent/v1/pages/${homePage!.id}/components`,
    {
      headers: {
        ...hostileAgentHeaders,
        "Idempotency-Key": `oap-0793-agent-doclist-${tag}`,
      },
      data: {
        component_type: "DocumentList",
        slot_key: "default",
        props: {
          title: "Agent document proof",
          items: [
            { mediaId: pdfAgentMediaId, label: "agent pdf" },
            { mediaId: pdfHumanMediaId, label: "human pdf" },
          ],
        },
      },
    },
  );
  expect(agentDoclistCreate.status()).toBe(201);
  const agentDoclistCreateBody = (await agentDoclistCreate.json()) as {
    record?: { id?: unknown; row_version?: unknown };
  };
  expect(agentDoclistCreateBody.record?.row_version).toBe(1);
  expect(typeof agentDoclistCreateBody.record?.id).toBe("string");
  const agentDoclistId = agentDoclistCreateBody.record?.id as string;

  const agentDoclistBefore = await page.request.get(
    `/api/agent/v1/pages/${homePage!.id}/components`,
    { headers: hostileAgentHeaders },
  );
  expect(agentDoclistBefore.status()).toBe(200);
  const agentDoclistBeforeBody = (await agentDoclistBefore.json()) as Array<{
    id: string;
    row_version: number;
  }>;
  const agentDoclistPatchCase = async (
    key: string,
    props: Record<string, unknown>,
    expectedKey: string | null,
  ): Promise<void> => {
    const response = await page.request.patch(
      `/api/agent/v1/components/${agentDoclistId}`,
      {
        headers: {
          ...hostileAgentHeaders,
          "Idempotency-Key": `oap-0793-agent-${key}-${tag}`,
        },
        data: { props, expected_row_version: 1 },
      },
    );
    expect(response.status()).toBe(422);
    const body = (await response.json()) as {
      error: { code: string; details?: { prop_error?: string } };
    };
    expect(body.error.code).toBe("DOMAIN_VALIDATION_FAILED");
    if (expectedKey === null) {
      // Catalog shape bounds (label 1..120) are guard-level rejections:
      // the bounded prop_error vocabulary deliberately excludes generic
      // shape-bound keys (079/2 Gallery/LogoGrid parity), so the exact
      // surface is the bare domain-validation 422 with no details and no
      // user-input echo.
      expect(body.error.details).toBeNull();
    } else {
      expect(body.error.details?.prop_error).toBe(expectedKey);
    }
  };
  await agentDoclistPatchCase(
    "doclist-out-of-range-max",
    { items: doclistHostileItems(13) },
    "doclist.items-out-of-range",
  );
  await agentDoclistPatchCase(
    "doclist-out-of-range-empty",
    { items: [] },
    "doclist.items-out-of-range",
  );
  await agentDoclistPatchCase(
    "doclist-missing",
    { items: [{ label: "no reference" }] },
    "doclist.item-missing",
  );
  await agentDoclistPatchCase(
    "doclist-missing-not-a-uuid",
    { items: [{ mediaId: "not-a-uuid", label: "bad reference" }] },
    "doclist.item-missing",
  );
  await agentDoclistPatchCase(
    "doclist-foreign-unknown",
    { items: [{ mediaId: unknownMediaId, label: "unknown reference" }] },
    "doclist.item-foreign-site",
  );
  await agentDoclistPatchCase(
    "doclist-foreign-demo",
    { items: [{ mediaId: demoMediaId, label: "foreign png" }] },
    "doclist.item-foreign-site",
  );
  await agentDoclistPatchCase(
    "doclist-not-pdf-png-human",
    { items: [{ mediaId: humanMediaId, label: "human png" }] },
    "doclist.item-not-pdf",
  );
  await agentDoclistPatchCase(
    "doclist-not-pdf-png-agent",
    { items: [{ mediaId: agentMediaId, label: "agent png" }] },
    "doclist.item-not-pdf",
  );
  await agentDoclistPatchCase(
    "doclist-not-pdf-text",
    { items: [{ mediaId: NON_IMAGE_MEDIA_ID, label: "note" }] },
    "doclist.item-not-pdf",
  );
  await agentDoclistPatchCase(
    "doclist-not-pdf-mixed",
    {
      items: [
        { mediaId: pdfAgentMediaId, label: "valid pdf" },
        { mediaId: humanMediaId, label: "png" },
      ],
    },
    "doclist.item-not-pdf",
  );
  await agentDoclistPatchCase(
    "doclist-label-bound",
    { items: [{ mediaId: pdfAgentMediaId, label: "x".repeat(121) }] },
    null,
  );
  // Tree and row versions unchanged after every rejection.
  const agentDoclistAfter = await page.request.get(
    `/api/agent/v1/pages/${homePage!.id}/components`,
    { headers: hostileAgentHeaders },
  );
  expect(agentDoclistAfter.status()).toBe(200);
  const agentDoclistAfterBody = (await agentDoclistAfter.json()) as Array<{
    id: string;
    row_version: number;
  }>;
  expect(agentDoclistAfterBody).toHaveLength(agentDoclistBeforeBody.length);
  expect(rowVersionOf(agentDoclistAfterBody, agentDoclistId)).toBe(1);
  expect(rowVersionOf(agentDoclistAfterBody, agentGalleryId)).toBe(1);
  expect(rowVersionOf(agentDoclistAfterBody, agentLogoGridId)).toBe(1);

  await agentPatchCase(
    agentGalleryId,
    "gallery-pdf-item",
    { items: [{ mediaId: pdfHumanMediaId, alt: "pdf item" }] },
    "gallery.item-not-image",
  );
  await agentPatchCase(
    agentLogoGridId,
    "logogrid-pdf-item",
    {
      items: [
        { mediaId: pdfHumanMediaId, name: "pdf one" },
        { mediaId: pdfAgentMediaId, name: "pdf two" },
      ],
    },
    "logogrid.item-not-image",
  );

  const agentImagePdfCreate = await page.request.post(
    `/api/agent/v1/pages/${homePage!.id}/components`,
    {
      headers: {
        ...hostileAgentHeaders,
        "Idempotency-Key": `oap-0793-agent-image-pdf-${tag}`,
      },
      data: {
        component_type: "Image",
        slot_key: "default",
        props: { mediaId: pdfHumanMediaId, alt: "pdf as image" },
      },
    },
  );
  expect(agentImagePdfCreate.status()).toBe(422);
  const agentImagePdfBody = (await agentImagePdfCreate.json()) as {
    error: { code: string; details?: { prop_error?: string } };
  };
  expect(agentImagePdfBody.error.code).toBe("DOMAIN_VALIDATION_FAILED");
  // The Agent surface bounds the exact DB-level binding key to the
  // enumerated prop_error vocabulary (pre-079/3 behavior, unchanged); the
  // exact key is proven on the Editor surface above and in the validator
  // contract.
  expect(agentImagePdfBody.error.details?.prop_error).toBeUndefined();
  // The image-class nodes stayed at row version 1 through the rejections.
  const agentImageClassAfter = await page.request.get(
    `/api/agent/v1/pages/${homePage!.id}/components`,
    { headers: hostileAgentHeaders },
  );
  expect(agentImageClassAfter.status()).toBe(200);
  const agentImageClassAfterBody = (await agentImageClassAfter.json()) as Array<{
    id: string;
    row_version: number;
  }>;
  expect(agentImageClassAfterBody).toHaveLength(agentDoclistBeforeBody.length);
  expect(rowVersionOf(agentImageClassAfterBody, agentGalleryId)).toBe(1);
  expect(rowVersionOf(agentImageClassAfterBody, agentLogoGridId)).toBe(1);

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
  expect(await crossSite.body()).not.toEqual(agentPngBytes);

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

  // 13. Non-member preview denial: the compose local administrator IS the
  // platform administrator (platform-admin preview authority outlives any
  // membership toggle), so the denial is proven with a seeded local user
  // that holds no site membership and no platform-administrator row. The
  // preview boundary serves ACTIVE workspaces only and the pinned preview
  // workspace was ACCEPTED in cycle 3, so the denial and its control are
  // proven against the hostile workspace, which this spec never freezes
  // and therefore stays ACTIVE end to end.
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
      `/preview/${hostileWorkspaceId}/s/parity/`,
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
    `/preview/${hostileWorkspaceId}/s/parity/`,
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
    `/preview/${hostileWorkspaceId}/s/parity/`,
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
  // Each row is bound to the workspace its node was actually created
  // through: the agent Image via the X-Editor-Workspace selection (agent
  // workspace), the human Image via headerless resolution to the pinned
  // ACTIVE HUMAN preview workspace.
  const editorAuditCheck = psql(
    project,
    `SELECT count(*) = 2
       AND count(*) FILTER (WHERE response_status = 201) = 2
       AND count(*) FILTER (
             WHERE resource_id = '${imageComponentId}'::uuid
               AND action = 'POST /api/editor/v1/sites/${parity.site_id}/pages/${homePage!.id}/composition/components'
               AND workspace_id = '${agentWorkspaceId}'::uuid
               AND site_id = '${parity.site_id}'::uuid) = 1
       AND count(*) FILTER (
             WHERE resource_id = '${humanComponentId}'::uuid
               AND action = 'POST /api/editor/v1/sites/${parity.site_id}/pages/${homePage!.id}/composition/components'
               AND workspace_id = '${previewWorkspaceId}'::uuid
               AND site_id = '${parity.site_id}'::uuid) = 1
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
    `SELECT count(*) = 4
       AND count(*) FILTER (WHERE published_at IS NOT NULL) = 4
      FROM content.media_asset
      WHERE id IN (
            '${humanMediaId}'::uuid,
            '${agentMediaId}'::uuid,
            '${pdfHumanMediaId}'::uuid,
            '${pdfAgentMediaId}'::uuid
          )
        AND public_status = 'public';`,
  );
  expect(publicStatusCheck).toBe("t");

  expectConsoleClean("final");
  expect(failures()).toEqual([]);
});
