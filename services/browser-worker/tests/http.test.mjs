import assert from "node:assert/strict";
import { Buffer } from "node:buffer";
import { createHash } from "node:crypto";
import { createConnection } from "node:net";
import { once } from "node:events";
import { test } from "node:test";

import { canonicalJson } from "@slaif-agent-site/browser-tool-contracts";

import { verifyWorkerResultSignature } from "../dist/auth.js";
import { workerRequestDigest } from "../dist/contracts.js";
import { createBrowserWorkerServer } from "../dist/http.js";

const wire = "sbws1:0123456789abcdef:AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8";
const credential = Object.freeze({
  keyId: "0123456789abcdef",
  secret: Buffer.from([...Array(32).keys()]),
  wireValue: wire,
});

function request(now, requestId = "00000000-0000-4000-8000-000000000001") {
  const route = "/s/demo/";
  return {
    version: "browser-worker/v1",
    deployment: "slaif-agent-site",
    requestId,
    runId: "00000000-0000-4000-8000-000000000002",
    siteId: "00000000-0000-4000-8000-000000000003",
    workspaceId: "00000000-0000-4000-8000-000000000004",
    capabilityId: "00000000-0000-4000-8000-000000000005",
    operationId: "00000000-0000-4000-8000-000000000006",
    leaseId: "00000000-0000-4000-8000-000000000007",
    attempt: 1,
    route,
    routeDigest: createHash("sha256").update(route).digest("hex"),
    target: "desktop-chromium",
    evidence: ["heading-summary"],
    artifactBytesLimit: 1_048_576,
    durationSeconds: 30,
    issuedAt: now,
    expiresAt: now + 30,
    previewCredential: "sbp1.a.b.c",
  };
}

function result(submit, state = "FAILED") {
  const now = Math.floor(Date.now() / 1000);
  return Object.freeze({
    version: "browser-worker/v1",
    deployment: "slaif-agent-site",
    requestId: submit.requestId,
    requestDigest: workerRequestDigest(submit),
    runId: submit.runId,
    siteId: submit.siteId,
    workspaceId: submit.workspaceId,
    capabilityId: submit.capabilityId,
    operationId: submit.operationId,
    leaseId: submit.leaseId,
    attempt: submit.attempt,
    routeDigest: submit.routeDigest,
    target: submit.target,
    state,
    summary: {},
    error: { code: "BROWSER_FAILED", message: "browser attempt failed" },
    artifacts: [],
    startedAt: now,
    completedAt: now,
    expiresAt: now + 60,
  });
}

async function startRuntime(execute) {
  const runtime = {
    credential,
    executor: { execute },
    artifactStore: {
      async retrieve() {
        return {
          metadata: { mimeType: "text/plain", sha256: "a".repeat(64) },
          bytes: Buffer.from("private"),
        };
      },
    },
  };
  const application = createBrowserWorkerServer(() => runtime);
  application.server.listen(0, "127.0.0.1");
  await once(application.server, "listening");
  const address = application.server.address();
  assert.equal(typeof address, "object");
  return {
    ...application,
    url: `http://127.0.0.1:${address.port}`,
    port: address.port,
  };
}

function headers(body) {
  return {
    "Content-Type": "application/json",
    "X-SLAIF-Browser-Worker-Token": wire,
    "Content-Length": String(Buffer.byteLength(body)),
  };
}

test("worker authenticates before body framing and returns signed exact results", async () => {
  const application = await startRuntime(async (submit) => result(submit));
  try {
    const socket = createConnection(application.port, "127.0.0.1");
    socket.write(
      "POST /internal/browser/v1/attempts HTTP/1.1\r\n" +
        "Host: worker\r\nX-SLAIF-Browser-Worker-Token: wrong\r\n" +
        "Content-Type: application/json\r\nContent-Length: 32000\r\n\r\n",
    );
    const [unauthorized] = await once(socket, "data");
    assert.match(unauthorized.toString("ascii"), /^HTTP\/1\.1 401 /u);
    socket.destroy();

    const now = Math.floor(Date.now() / 1000);
    const submit = request(now);
    const body = canonicalJson(submit);
    const response = await globalThis.fetch(
      `${application.url}/internal/browser/v1/attempts`,
      {
        method: "POST",
        headers: headers(body),
        body,
      },
    );
    assert.equal(response.status, 200);
    const envelope = await response.json();
    assert.equal(verifyWorkerResultSignature(envelope, credential), true);
    assert.equal(envelope.result.requestDigest, workerRequestDigest(submit));
    assert.doesNotMatch(JSON.stringify(envelope), /sbp1\.|sbws1:/u);

    const unknown = canonicalJson({ ...submit, javascript: "document.body" });
    assert.equal(
      (
        await globalThis.fetch(`${application.url}/internal/browser/v1/attempts`, {
          method: "POST",
          headers: headers(unknown),
          body: unknown,
        })
      ).status,
      422,
    );
    const noncanonical = JSON.stringify(submit, null, 2);
    assert.equal(
      (
        await globalThis.fetch(`${application.url}/internal/browser/v1/attempts`, {
          method: "POST",
          headers: headers(noncanonical),
          body: noncanonical,
        })
      ).status,
      400,
    );
  } finally {
    application.server.close();
  }
});

test("active inspection, overload, cancellation, and cleanup are bounded", async () => {
  let release;
  const gate = new Promise((resolve) => {
    release = resolve;
  });
  const application = await startRuntime(async (submit, signal) => {
    await Promise.race([gate, once(signal, "abort")]);
    return result(submit, signal.aborted ? "CANCELLED" : "FAILED");
  });
  try {
    const now = Math.floor(Date.now() / 1000);
    const first = request(now);
    const firstBody = canonicalJson(first);
    const pending = globalThis.fetch(
      `${application.url}/internal/browser/v1/attempts`,
      {
        method: "POST",
        headers: headers(firstBody),
        body: firstBody,
      },
    );
    await new Promise((resolve) => globalThis.setTimeout(resolve, 25));

    const inspectionBody = canonicalJson({
      version: "browser-worker/v1",
      deployment: "slaif-agent-site",
      requestId: first.requestId,
    });
    const inspection = await globalThis.fetch(
      `${application.url}/internal/browser/v1/attempts/inspect`,
      { method: "POST", headers: headers(inspectionBody), body: inspectionBody },
    );
    assert.equal(inspection.status, 200);
    assert.equal((await inspection.json()).state, "RUNNING");

    const secondBody = canonicalJson(
      request(now, "00000000-0000-4000-8000-000000000009"),
    );
    assert.equal(
      (
        await globalThis.fetch(`${application.url}/internal/browser/v1/attempts`, {
          method: "POST",
          headers: headers(secondBody),
          body: secondBody,
        })
      ).status,
      429,
    );
    release();
    assert.equal((await pending).status, 200);

    await new Promise((resolve) => globalThis.setTimeout(resolve, 25));
    const absent = await globalThis.fetch(
      `${application.url}/internal/browser/v1/attempts/inspect`,
      { method: "POST", headers: headers(inspectionBody), body: inspectionBody },
    );
    assert.equal(absent.status, 404);
  } finally {
    application.abortAll();
    application.server.close();
  }
});

test("client disconnect aborts the active attempt and releases its slot", async () => {
  let observedAbort = false;
  const application = await startRuntime(async (submit, signal) => {
    await once(signal, "abort");
    observedAbort = true;
    return result(submit, "CANCELLED");
  });
  try {
    const now = Math.floor(Date.now() / 1000);
    const submit = request(now);
    const body = canonicalJson(submit);
    const controller = new globalThis.AbortController();
    const pending = globalThis.fetch(
      `${application.url}/internal/browser/v1/attempts`,
      {
        method: "POST",
        headers: headers(body),
        body,
        signal: controller.signal,
      },
    );
    await new Promise((resolve) => globalThis.setTimeout(resolve, 25));
    controller.abort();
    await assert.rejects(pending);
    for (let attempt = 0; attempt < 20 && !observedAbort; attempt += 1) {
      await new Promise((resolve) => globalThis.setTimeout(resolve, 10));
    }
    assert.equal(observedAbort, true);
    const inspectionBody = canonicalJson({
      version: "browser-worker/v1",
      deployment: "slaif-agent-site",
      requestId: submit.requestId,
    });
    assert.equal(
      (
        await globalThis.fetch(
          `${application.url}/internal/browser/v1/attempts/inspect`,
          {
            method: "POST",
            headers: headers(inspectionBody),
            body: inspectionBody,
          },
        )
      ).status,
      404,
    );
  } finally {
    application.abortAll();
    application.server.close();
  }
});
