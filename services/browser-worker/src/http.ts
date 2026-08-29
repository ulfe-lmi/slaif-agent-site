import {
  createServer,
  type IncomingMessage,
  type Server,
  type ServerResponse,
} from "node:http";

import {
  BROWSER_WORKER_BOUNDS,
  BROWSER_WORKER_ROUTES,
  canonicalJson,
  type BrowserWorkerInspection,
} from "@slaif-agent-site/browser-tool-contracts";

import { BrowserArtifactStore } from "./artifact-store.js";
import {
  authenticateWorkerRequest,
  signWorkerResult,
  type WorkerCredential,
} from "./auth.js";
import {
  parseWorkerArtifactRetrievalRequest,
  parseWorkerInspectionRequest,
  parseWorkerSubmitRequest,
} from "./contracts.js";
import { BrowserAttemptExecutor } from "./execution.js";
import { healthResponse } from "./responses.js";

export interface BrowserWorkerRuntime {
  readonly credential: WorkerCredential;
  readonly artifactStore: BrowserArtifactStore;
  readonly executor: BrowserAttemptExecutor;
}

interface ActiveAttempt {
  readonly startedAt: number;
  readonly controller: AbortController;
}

const errorBody = Buffer.from(
  '{"error":{"code":"BROWSER_WORKER_REJECTED","message":"browser worker request failed"}}',
  "utf8",
);

function rawHeaderCount(request: IncomingMessage, name: string): number {
  let count = 0;
  for (let index = 0; index < request.rawHeaders.length; index += 2) {
    if ((request.rawHeaders[index] ?? "").toLowerCase() === name) count += 1;
  }
  return count;
}

function sendJson(response: ServerResponse, status: number, body: unknown): void {
  const bytes = Buffer.from(canonicalJson(body), "utf8");
  response.writeHead(status, {
    "Cache-Control": "private, no-store",
    "Content-Length": String(bytes.length),
    "Content-Type": "application/json; charset=utf-8",
    "X-Content-Type-Options": "nosniff",
  });
  response.end(bytes);
}

function reject(response: ServerResponse, status: number): void {
  response.writeHead(status, {
    "Cache-Control": "private, no-store",
    Connection: "close",
    "Content-Length": String(errorBody.length),
    "Content-Type": "application/json; charset=utf-8",
    "X-Content-Type-Options": "nosniff",
  });
  response.end(errorBody);
}

async function readCanonicalJson(request: IncomingMessage): Promise<unknown> {
  if (
    rawHeaderCount(request, "content-length") !== 1 ||
    rawHeaderCount(request, "transfer-encoding") !== 0 ||
    rawHeaderCount(request, "content-type") !== 1 ||
    request.headers["content-type"] !== "application/json"
  )
    throw new Error();
  const rawLength = request.headers["content-length"];
  if (typeof rawLength !== "string" || !/^(?:0|[1-9][0-9]{0,4})$/u.test(rawLength))
    throw new Error();
  const expected = Number(rawLength);
  if (expected < 2 || expected > BROWSER_WORKER_BOUNDS.requestBytes) throw new Error();
  const chunks: Buffer[] = [];
  let total = 0;
  for await (const chunk of request) {
    const value = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk as Uint8Array);
    total += value.length;
    if (total > expected || total > BROWSER_WORKER_BOUNDS.requestBytes) {
      throw new Error();
    }
    chunks.push(value);
  }
  if (total !== expected) throw new Error();
  const text = Buffer.concat(chunks, total).toString("utf8");
  const parsed = JSON.parse(text) as unknown;
  if (canonicalJson(parsed) !== text) throw new Error();
  return parsed;
}

export function createBrowserWorkerServer(runtime: () => BrowserWorkerRuntime | null): {
  readonly server: Server;
  readonly abortAll: () => void;
} {
  const active = new Map<string, ActiveAttempt>();
  const server = createServer((request, response) => {
    void (async () => {
      const path = request.url ?? "";
      const selected = runtime();
      const health =
        request.method === "GET" ? healthResponse(path, selected !== null) : null;
      if (health !== null) {
        sendJson(
          response,
          path === "/health/ready" && selected === null ? 503 : 200,
          health,
        );
        return;
      }
      if (selected === null) {
        reject(response, 503);
        return;
      }
      if (!authenticateWorkerRequest(request.rawHeaders, selected.credential)) {
        reject(response, 401);
        return;
      }
      if (request.method !== "POST") {
        reject(response, 404);
        return;
      }
      let body: unknown;
      try {
        body = await readCanonicalJson(request);
      } catch {
        reject(response, 400);
        return;
      }
      if (path === BROWSER_WORKER_ROUTES.inspect) {
        try {
          const inspectionRequest = parseWorkerInspectionRequest(body);
          const attempt = active.get(inspectionRequest.requestId);
          if (attempt === undefined) {
            reject(response, 404);
            return;
          }
          const inspection: BrowserWorkerInspection = Object.freeze({
            version: "browser-worker/v1",
            requestId: inspectionRequest.requestId,
            state: "RUNNING",
            startedAt: attempt.startedAt,
          });
          sendJson(response, 200, inspection);
        } catch {
          reject(response, 400);
        }
        return;
      }
      if (path === BROWSER_WORKER_ROUTES.retrieve) {
        try {
          const retrieval = parseWorkerArtifactRetrievalRequest(body);
          const artifact = await selected.artifactStore.retrieve(
            retrieval,
            Math.floor(Date.now() / 1000),
          );
          response.writeHead(200, {
            "Cache-Control": "private, no-store",
            "Content-Length": String(artifact.bytes.length),
            "Content-Type": artifact.metadata.mimeType,
            "X-Content-Type-Options": "nosniff",
            "X-SLAIF-Artifact-SHA256": artifact.metadata.sha256,
          });
          response.end(artifact.bytes);
        } catch {
          reject(response, 404);
        }
        return;
      }
      if (path !== BROWSER_WORKER_ROUTES.submit) {
        reject(response, 404);
        return;
      }
      let submit;
      try {
        submit = parseWorkerSubmitRequest(body, Math.floor(Date.now() / 1000));
      } catch {
        reject(response, 422);
        return;
      }
      if (
        active.size >= BROWSER_WORKER_BOUNDS.activeAttempts ||
        active.has(submit.requestId)
      ) {
        reject(response, 429);
        return;
      }
      const controller = new AbortController();
      active.set(submit.requestId, {
        startedAt: Math.floor(Date.now() / 1000),
        controller,
      });
      const abort = (): void => controller.abort(new Error("client disconnected"));
      request.once("aborted", abort);
      response.once("close", () => {
        if (!response.writableEnded) abort();
      });
      try {
        const result = await selected.executor.execute(submit, controller.signal);
        if (controller.signal.aborted || response.destroyed) return;
        const envelope = signWorkerResult(result, selected.credential);
        const encoded = Buffer.byteLength(canonicalJson(envelope), "utf8");
        if (encoded > BROWSER_WORKER_BOUNDS.resultBytes) {
          reject(response, 500);
          return;
        }
        sendJson(response, 200, envelope);
      } finally {
        active.delete(submit.requestId);
      }
    })().catch(() => {
      if (!response.headersSent) reject(response, 500);
      else response.destroy();
    });
  });
  server.on("checkContinue", (_request, response) => reject(response, 417));
  server.on("clientError", (_error, socket) => socket.destroy());
  return Object.freeze({
    server,
    abortAll: () => {
      for (const attempt of active.values()) {
        attempt.controller.abort(new Error("worker shutting down"));
      }
    },
  });
}
