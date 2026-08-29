import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { chmod, mkdtemp, symlink, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import {
  authenticateWorkerRequest,
  loadWorkerCredential,
  signWorkerResult,
  verifyWorkerResultSignature,
} from "../dist/auth.js";
import {
  parseWorkerArtifactRetrievalRequest,
  parseWorkerInspectionRequest,
  parseWorkerSubmitRequest,
  workerRequestDigest,
} from "../dist/contracts.js";
import { sanitizeOutput } from "../dist/evidence.js";
import { contextOptionsForTarget } from "../dist/targets.js";
import {
  CONFINEMENT_SELF_CHECK_URLS,
  installRequestConfinement,
  previewDocumentUrl,
  requestIsAllowed,
  validatePreviewOrigin,
} from "../dist/url-policy.js";

const wire = "sbws1:0123456789abcdef:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8";
const ids = {
  requestId: "00000000-0000-4000-8000-000000000001",
  runId: "00000000-0000-4000-8000-000000000002",
  siteId: "00000000-0000-4000-8000-000000000003",
  workspaceId: "00000000-0000-4000-8000-000000000004",
  capabilityId: "00000000-0000-4000-8000-000000000005",
  operationId: "00000000-0000-4000-8000-000000000006",
  leaseId: "00000000-0000-4000-8000-000000000007",
};

function request(now = 1_800_000_000) {
  const route = "/s/demo/?a=1&b=2";
  return {
    version: "browser-worker/v1",
    deployment: "slaif-agent-site",
    ...ids,
    attempt: 1,
    route,
    routeDigest: createHash("sha256").update("/s/demo?a=1&b=2").digest("hex"),
    target: "desktop-chromium",
    evidence: ["screenshot", "heading-summary"],
    artifactBytesLimit: 8_388_608,
    durationSeconds: 30,
    issuedAt: now,
    expiresAt: now + 30,
    previewCredential: "sbp1.a.b.c",
  };
}

test("worker submit/inspection/retrieval contracts are exact and fully bound", () => {
  const parsed = parseWorkerSubmitRequest(request(), 1_800_000_010);
  assert.equal(parsed.route, "/s/demo?a=1&b=2");
  assert.equal(
    workerRequestDigest(parsed),
    "86ec03e223b2e44355162480d18f87666cf871f10d6e3021860a2bc667d6c8c1",
  );
  assert.throws(() =>
    parseWorkerSubmitRequest({ ...request(), viewport: { width: 1 } }, 1_800_000_010),
  );
  assert.throws(() =>
    parseWorkerSubmitRequest(
      { ...request(), routeDigest: "0".repeat(64) },
      1_800_000_010,
    ),
  );
  assert.throws(() =>
    parseWorkerSubmitRequest({ ...request(), expiresAt: 1_800_000_100 }, 1_800_000_010),
  );
  assert.deepEqual(
    parseWorkerInspectionRequest({
      version: "browser-worker/v1",
      deployment: "slaif-agent-site",
      requestId: ids.requestId,
    }),
    {
      version: "browser-worker/v1",
      deployment: "slaif-agent-site",
      requestId: ids.requestId,
    },
  );
  assert.throws(() => parseWorkerArtifactRetrievalRequest({ path: "../../private" }));
});

test("descriptor-confined worker credential authenticates duplicates and wrong values safely", async () => {
  const root = await mkdtemp(join(tmpdir(), "slaif-worker-auth-"));
  await chmod(root, 0o700);
  const path = join(root, "worker-token");
  await writeFile(path, wire, { encoding: "ascii", mode: 0o400 });
  await chmod(path, 0o400);
  const credential = await loadWorkerCredential(path);
  assert.equal(credential.keyId, "0123456789abcdef");
  assert.equal(
    authenticateWorkerRequest(["X-SLAIF-Browser-Worker-Token", wire], credential),
    true,
  );
  for (const headers of [
    [],
    ["X-SLAIF-Browser-Worker-Token", ""],
    ["X-SLAIF-Browser-Worker-Token", "wrong"],
    ["X-SLAIF-Browser-Worker-Token", wire, "X-SLAIF-Browser-Worker-Token", wire],
  ]) {
    assert.equal(authenticateWorkerRequest(headers, credential), false);
  }
  const linkRoot = await mkdtemp(join(tmpdir(), "slaif-worker-auth-link-"));
  await chmod(linkRoot, 0o700);
  await symlink(path, join(linkRoot, "worker-token"));
  await assert.rejects(loadWorkerCredential(join(linkRoot, "worker-token")));

  const parsed = parseWorkerSubmitRequest(request(), 1_800_000_010);
  const result = {
    version: "browser-worker/v1",
    deployment: "slaif-agent-site",
    ...ids,
    requestDigest: workerRequestDigest(parsed),
    attempt: 1,
    routeDigest: parsed.routeDigest,
    target: parsed.target,
    state: "FAILED",
    summary: {},
    error: { code: "BROWSER_FAILED", message: "browser attempt failed" },
    artifacts: [],
    startedAt: 1_800_000_010,
    completedAt: 1_800_000_011,
    expiresAt: 1_800_000_041,
  };
  const envelope = signWorkerResult(result, credential);
  assert.equal(verifyWorkerResultSignature(envelope, credential), true);
  assert.equal(
    verifyWorkerResultSignature(
      { ...envelope, result: { ...result, runId: ids.siteId } },
      credential,
    ),
    false,
  );
  assert.doesNotMatch(JSON.stringify(envelope), /sbws1:|sbp1\./);
});

test("target, output, origin, and request policy expose no raw automation surface", () => {
  assert.deepEqual(contextOptionsForTarget("mobile-chromium"), {
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    hasTouch: true,
    isMobile: true,
    acceptDownloads: false,
    serviceWorkers: "block",
  });
  const origin = validatePreviewOrigin("http://web:3000");
  const document = previewDocumentUrl(origin, request());
  assert.equal(
    document.href,
    `http://web:3000/preview/${ids.workspaceId}/s/demo/?a=1&b=2`,
  );
  assert.equal(
    requestIsAllowed(document.href, "GET", "document", document),
    "DOCUMENT",
  );
  assert.equal(
    requestIsAllowed("http://web:3000/_next/static/app.js", "GET", "script", document),
    "ASSET",
  );
  for (const value of [
    ...CONFINEMENT_SELF_CHECK_URLS,
    "file:///etc/passwd",
    "data:text/plain,private",
    "javascript:alert(1)",
    "//agent-api:8000/",
    "http://user:pass@web:3000/",
  ]) {
    assert.equal(requestIsAllowed(value, "GET", "document", document), null);
  }
  assert.throws(() => validatePreviewOrigin("http://127.0.0.1:3000"));
  assert.equal(
    sanitizeOutput(` before sbp1.a.b.c and ${wire} and sas2_public_secret after `),
    "before [REDACTED] and [REDACTED] and [REDACTED] after",
  );
});

test("request interception attaches the preview credential only to the first document", async () => {
  let handler;
  const context = {
    async route(pattern, callback) {
      assert.equal(pattern, "**/*");
      handler = callback;
    },
  };
  const document = previewDocumentUrl(
    validatePreviewOrigin("http://web:3000"),
    request(),
  );
  const continued = [];
  const aborted = [];
  const route = {
    async continue(value) {
      continued.push(value.headers);
    },
    async abort(reason) {
      aborted.push(reason);
    },
  };
  const initial = {
    url: () => document.href,
    method: () => "GET",
    resourceType: () => "document",
    redirectedFrom: () => null,
    headers: () => ({
      cookie: "must-strip",
      "x-slaif-browser-worker-token": wire,
      accept: "text/html",
    }),
  };
  await installRequestConfinement(context, document, "sbp1.a.b.c", () => {});
  await handler(route, initial);
  assert.deepEqual(continued[0], {
    accept: "text/html",
    "x-slaif-browser-preview": "sbp1.a.b.c",
  });
  const asset = {
    ...initial,
    url: () => "http://web:3000/_next/static/app.js",
    resourceType: () => "script",
    headers: () => ({
      cookie: "must-strip",
      "x-slaif-browser-preview": "must-strip",
      accept: "*/*",
    }),
  };
  await handler(route, asset);
  assert.deepEqual(continued[1], { accept: "*/*" });
  await handler(route, { ...initial, redirectedFrom: () => initial });
  assert.deepEqual(aborted, ["blockedbyclient"]);
});
