import { createHash } from "node:crypto";
import { constants } from "node:fs";
import { open } from "node:fs/promises";

import {
  BROWSER_WORKER_BOUNDS,
  BROWSER_WORKER_CONTRACT_VERSION,
  BROWSER_WORKER_DEPLOYMENT,
  type BrowserRunError,
  type BrowserWorkerResult,
  type BrowserWorkerSubmitRequest,
} from "@slaif-agent-site/browser-tool-contracts";
import { chromium, type Browser, type Page } from "playwright-core";

import { BrowserArtifactStore } from "./artifact-store.js";
import { collectEvidence, observeEvidenceEvents } from "./evidence.js";
import { contextOptionsForTarget } from "./targets.js";
import {
  boundMediaUrl,
  CONFINEMENT_SELF_CHECK_URLS,
  installRequestConfinement,
  previewDocumentUrl,
  requestIsAllowed,
  validatePreviewOrigin,
} from "./url-policy.js";
import { workerRequestDigest } from "./contracts.js";

export interface BrowserExecutorConfiguration {
  readonly previewOrigin: URL;
  readonly executablePath: string;
  readonly expectedBrowserVersion: string;
}

export class BrowserExecutionError extends Error {
  public constructor() {
    super("browser execution is unavailable");
    this.name = "BrowserExecutionError";
  }
}

function terminalError(code: string): BrowserRunError {
  return Object.freeze({ code, message: "browser attempt failed" });
}

// Bounded document-media resource read: only document media the rendered
// preview actually references (exact bound asset anchors), fetched as
// same-origin requests through the same confinement handler.  Anchor
// traversal is bounded (no full NodeList materialization), each body is
// streamed with a hard byte ceiling that cancels the read before an
// oversized allocation, and the summary reports exactly how much of the
// referenced set was inspected so completion is never presented as full
// byte verification when a bound was hit.  Bytes are digested in the
// worker process and never stored as artifacts.
const boundDocumentMediaLimits = Object.freeze({
  maxAnchorsSeen: 64,
  maxDocuments: 8,
  maxBytesPerDocument: 262_144,
  maxNodesVisited: 20_000,
  maxChildrenPerLevel: 1024,
});

const boundDocumentMediaIdPattern =
  /^\/media\/v1\/browser-preview\/assets\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/content$/u;

interface BoundDocumentMediaRead {
  readonly mediaId: string;
  readonly sha256: string;
  readonly sizeBytes: number;
  readonly contentType: string;
}

interface BoundDocumentMediaFailure {
  readonly mediaId: string;
  readonly status: string;
}

interface BoundDocumentMediaResult {
  readonly anchorsSeen: number;
  readonly nodesVisited: number;
  readonly walkLimitReached: boolean;
  readonly candidates: number;
  readonly omittedOverLimit: number;
  readonly reads: readonly BoundDocumentMediaRead[];
  readonly failures: readonly BoundDocumentMediaFailure[];
}

async function readBoundDocumentMedia(
  page: Page,
  document: URL,
): Promise<BoundDocumentMediaResult> {
  // True bounded DOM walk: explicit visited-node budget and per-level
  // child bound, indexed child access (no NodeList/array materialization
  // and no selector collection of every anchor).  When a bound is hit
  // the scan reports walkLimitReached; the referenced set may then be
  // incomplete and the summary says so.
  const scan = await page.evaluate(
    (limits: { anchorLimit: number; nodeLimit: number; childLimit: number }) => {
      const hrefs: string[] = [];
      let visited = 0;
      let limitReached = false;
      const visit = (element: Element): void => {
        if (limitReached) return;
        if (visited >= limits.nodeLimit) {
          limitReached = true;
          return;
        }
        visited += 1;
        if (element.tagName === "A") {
          const href = element.getAttribute("href");
          if (href !== null) {
            if (hrefs.length < limits.anchorLimit) {
              hrefs.push(href);
            } else {
              // First omitted anchor: the bounded set is
              // incomplete; stop the walk and report it.
              limitReached = true;
              return;
            }
          }
        }
        const childCount = Math.min(element.children.length, limits.childLimit);
        for (let i = 0; i < childCount; i += 1) {
          visit(element.children.item(i) as Element);
          if (limitReached) return;
        }
        if (element.children.length > childCount) limitReached = true;
      };
      visit(window.document.documentElement);
      return { hrefs, visited, limitReached };
    },
    {
      anchorLimit: boundDocumentMediaLimits.maxAnchorsSeen,
      nodeLimit: boundDocumentMediaLimits.maxNodesVisited,
      childLimit: boundDocumentMediaLimits.maxChildrenPerLevel,
    },
  );
  const candidates: string[] = [];
  for (const href of scan.hrefs) {
    let value: URL;
    try {
      value = new URL(href, document.href);
    } catch {
      continue;
    }
    if (value.search !== "" || value.hash !== "") continue;
    const match = boundDocumentMediaIdPattern.exec(value.pathname);
    // The shared policy helper is the single trusted bound-URL
    // constructor: the anchor must reproduce exactly what
    // boundMediaUrl derives for its media id (same origin, exact
    // path shape), so no rendered input can widen the subresource.
    if (match === null || match[1] === undefined) continue;
    const bound = boundMediaUrl(document, match[1]);
    if (bound === null || bound.href !== value.href) continue;
    if (!candidates.includes(value.href)) candidates.push(value.href);
  }
  const omittedOverLimit = Math.max(
    0,
    candidates.length - boundDocumentMediaLimits.maxDocuments,
  );
  const targets = candidates
    .slice(0, boundDocumentMediaLimits.maxDocuments)
    .map((url) => ({
      url,
      maxBytes: boundDocumentMediaLimits.maxBytesPerDocument,
    }));
  const empty: BoundDocumentMediaResult = {
    anchorsSeen: scan.hrefs.length,
    nodesVisited: scan.visited,
    walkLimitReached: scan.limitReached,
    candidates: candidates.length,
    omittedOverLimit,
    reads: Object.freeze([]),
    failures: Object.freeze([]),
  };
  if (targets.length === 0) return empty;
  const results = await page.evaluate(
    async (targets: readonly { url: string; maxBytes: number }[]) => {
      const out: {
        url: string;
        ok: boolean;
        status: string;
        bytes?: Uint8Array;
        contentType?: string;
      }[] = [];
      for (const target of targets) {
        try {
          const response = await fetch(target.url, { method: "GET" });
          if (!response.ok) {
            out.push({
              url: target.url,
              ok: false,
              status: String(response.status),
            });
            continue;
          }
          const reader = response.body?.getReader();
          if (reader === undefined) {
            out.push({ url: target.url, ok: false, status: "unstreamable" });
            continue;
          }
          let received = 0;
          let oversize = false;
          const chunks: Uint8Array[] = [];
          for (;;) {
            const chunk = await reader.read();
            if (chunk.done) break;
            received += chunk.value.byteLength;
            if (received > target.maxBytes) {
              oversize = true;
              // Cancel before the oversized allocation grows further.
              try {
                await reader.cancel();
              } catch {
                // bounded cancel: the read is already refused
              }
              break;
            }
            chunks.push(chunk.value);
          }
          if (oversize) {
            out.push({ url: target.url, ok: false, status: "oversize" });
            continue;
          }
          if (received === 0) {
            out.push({ url: target.url, ok: false, status: "empty" });
            continue;
          }
          const bytes = new Uint8Array(received);
          let offset = 0;
          for (const piece of chunks) {
            bytes.set(piece, offset);
            offset += piece.byteLength;
          }
          out.push({
            url: target.url,
            ok: true,
            status: "ok",
            bytes,
            contentType: response.headers.get("content-type") ?? "",
          });
        } catch {
          out.push({ url: target.url, ok: false, status: "failed" });
        }
      }
      return out;
    },
    targets,
  );
  const reads: BoundDocumentMediaRead[] = [];
  const failures: BoundDocumentMediaFailure[] = [];
  for (const result of results) {
    let url: URL;
    try {
      url = new URL(result.url, document.href);
    } catch {
      continue;
    }
    const match = boundDocumentMediaIdPattern.exec(url.pathname);
    const mediaId = match?.[1] ?? "";
    const bytes = result.bytes;
    if (!result.ok || mediaId === "" || bytes === undefined) {
      if (mediaId !== "") failures.push({ mediaId, status: result.status });
      continue;
    }
    reads.push({
      mediaId,
      sha256: createHash("sha256").update(Buffer.from(bytes)).digest("hex"),
      sizeBytes: bytes.byteLength,
      contentType: result.contentType ?? "",
    });
  }
  return Object.freeze({
    anchorsSeen: empty.anchorsSeen,
    nodesVisited: empty.nodesVisited,
    walkLimitReached: empty.walkLimitReached,
    candidates: empty.candidates,
    omittedOverLimit,
    reads: Object.freeze(reads),
    failures: Object.freeze(failures),
  });
}

async function launchSandboxed(
  configuration: BrowserExecutorConfiguration,
): Promise<Browser> {
  return chromium.launch({
    headless: true,
    chromiumSandbox: true,
    executablePath: configuration.executablePath,
  });
}

export class BrowserAttemptExecutor {
  readonly #configuration: BrowserExecutorConfiguration;
  readonly #store: BrowserArtifactStore;

  public constructor(
    configuration: BrowserExecutorConfiguration,
    store: BrowserArtifactStore,
  ) {
    this.#configuration = configuration;
    this.#store = store;
  }

  public static configurationFromEnvironment(): BrowserExecutorConfiguration {
    const previewOrigin = validatePreviewOrigin(
      process.env.BROWSER_WORKER_PREVIEW_ORIGIN ?? "",
    );
    const executablePath = process.env.BROWSER_WORKER_CHROMIUM_EXECUTABLE ?? "";
    const expectedBrowserVersion =
      process.env.BROWSER_WORKER_EXPECTED_CHROMIUM_VERSION ?? "";
    if (
      !executablePath.startsWith("/") ||
      !/^\d+\.\d+\.\d+\.\d+$/u.test(expectedBrowserVersion)
    )
      throw new BrowserExecutionError();
    return Object.freeze({
      previewOrigin,
      executablePath,
      expectedBrowserVersion,
    });
  }

  public async readiness(): Promise<void> {
    let executable = null;
    try {
      executable = await open(
        this.#configuration.executablePath,
        constants.O_RDONLY | constants.O_NOFOLLOW,
      );
      const info = await executable.stat();
      if (!info.isFile() || (info.mode & 0o111) === 0)
        throw new BrowserExecutionError();
    } catch {
      throw new BrowserExecutionError();
    } finally {
      await executable?.close().catch(() => undefined);
    }
    const browser = await launchSandboxed(this.#configuration).catch(() => {
      throw new BrowserExecutionError();
    });
    try {
      if (browser.version() !== this.#configuration.expectedBrowserVersion) {
        throw new BrowserExecutionError();
      }
      const request = {
        workspaceId: "00000000-0000-4000-8000-000000000001",
        route: "/",
      } as BrowserWorkerSubmitRequest;
      const expectedDocument = previewDocumentUrl(
        this.#configuration.previewOrigin,
        request,
      );
      for (const value of [
        ...CONFINEMENT_SELF_CHECK_URLS,
        `${this.#configuration.previewOrigin.origin}/not-the-bound-preview`,
        "file:///etc/passwd",
        "data:text/plain,blocked",
        "javascript:alert(1)",
      ]) {
        if (requestIsAllowed(value, "GET", "document", expectedDocument) !== null) {
          throw new BrowserExecutionError();
        }
      }
      const context = await browser.newContext(
        contextOptionsForTarget("desktop-chromium"),
      );
      try {
        let blocked = 0;
        await installRequestConfinement(context, expectedDocument, "probe", () => {
          blocked += 1;
        });
        const page = await context.newPage();
        for (const value of CONFINEMENT_SELF_CHECK_URLS) {
          await page.goto(value, { timeout: 1000 }).catch(() => null);
        }
        if (blocked !== CONFINEMENT_SELF_CHECK_URLS.length) {
          throw new BrowserExecutionError();
        }
      } finally {
        await context.close();
      }
    } finally {
      await browser.close();
    }
  }

  public async execute(
    request: BrowserWorkerSubmitRequest,
    externalSignal: AbortSignal,
  ): Promise<BrowserWorkerResult> {
    const startedAt = Math.floor(Date.now() / 1000);
    const timeoutController = new AbortController();
    const timeout = setTimeout(
      () => timeoutController.abort(new Error("timeout")),
      request.durationSeconds * 1000,
    );
    const signal = AbortSignal.any([externalSignal, timeoutController.signal]);
    let browser: Browser | null = null;
    let state: BrowserWorkerResult["state"] = "FAILED";
    let error: BrowserRunError | null;
    let artifacts: BrowserWorkerResult["artifacts"] = Object.freeze([]);
    let summary: Readonly<Record<string, unknown>> = Object.freeze({});
    let failureCode = "BROWSER_LAUNCH_FAILED";
    try {
      if (signal.aborted) throw new BrowserExecutionError();
      browser = await launchSandboxed(this.#configuration);
      if (browser.version() !== this.#configuration.expectedBrowserVersion) {
        throw new BrowserExecutionError();
      }
      signal.addEventListener("abort", () => void browser?.close(), { once: true });
      failureCode = "BROWSER_CONTEXT_FAILED";
      const context = await browser.newContext(contextOptionsForTarget(request.target));
      try {
        await context.clearCookies();
        await context.clearPermissions();
        const expectedDocument = previewDocumentUrl(
          this.#configuration.previewOrigin,
          request,
        );
        let blockedRequests = 0;
        await installRequestConfinement(
          context,
          expectedDocument,
          request.previewCredential,
          () => {
            blockedRequests += 1;
          },
        );
        const page = await context.newPage();
        const observation = observeEvidenceEvents(page, () => blockedRequests);
        page.setDefaultNavigationTimeout(
          Math.min(request.durationSeconds * 500, 30_000),
        );
        page.setDefaultTimeout(Math.min(request.durationSeconds * 500, 15_000));
        page.on("dialog", (dialog) => void dialog.dismiss());
        page.on("download", (download) => void download.cancel());
        failureCode = "BROWSER_NAVIGATION_FAILED";
        const response = await page.goto(expectedDocument.href, {
          waitUntil: "domcontentloaded",
        });
        if (response === null) {
          failureCode = "BROWSER_NAVIGATION_NO_RESPONSE";
          throw new BrowserExecutionError();
        }
        if (response.status() !== 200) {
          failureCode = `BROWSER_NAVIGATION_HTTP_${response.status()}`;
          throw new BrowserExecutionError();
        }
        failureCode = "BROWSER_STABILITY_FAILED";
        await page
          .locator('main[data-render-mode="preview"]')
          .waitFor({ state: "visible" });
        await page.waitForFunction(() => document.readyState === "complete");
        failureCode = "BROWSER_DOCUMENT_MEDIA_FAILED";
        const documentMedia = await readBoundDocumentMedia(page, expectedDocument);
        failureCode = "BROWSER_EVIDENCE_FAILED";
        const content = await collectEvidence(page, request, observation.events);
        const published = [];
        failureCode = "BROWSER_ARTIFACT_FAILED";
        for (const item of content) {
          published.push(await this.#store.publish(request, item, startedAt));
        }
        artifacts = Object.freeze(published);
        summary = Object.freeze({
          artifactCount: artifacts.length,
          blockedRequestCount: observation.events.blockedRequests,
          documentMedia: {
            anchorsSeen: documentMedia.anchorsSeen,
            nodesVisited: documentMedia.nodesVisited,
            walkLimitReached: documentMedia.walkLimitReached,
            candidates: documentMedia.candidates,
            omittedOverLimit: documentMedia.omittedOverLimit,
            reads: documentMedia.reads,
            failures: documentMedia.failures,
          },
          evidenceCount: request.evidence.length,
        });
        state = "COMPLETED";
        error = null;
      } finally {
        await context.close();
      }
    } catch {
      if (externalSignal.aborted) {
        state = "CANCELLED";
        error = terminalError("BROWSER_CANCELLED");
      } else if (timeoutController.signal.aborted) {
        state = "TIMED_OUT";
        error = terminalError("BROWSER_TIMED_OUT");
      } else {
        error = terminalError(failureCode);
      }
    } finally {
      clearTimeout(timeout);
      await browser?.close().catch(() => undefined);
    }
    const completedAt = Math.floor(Date.now() / 1000);
    return Object.freeze({
      version: BROWSER_WORKER_CONTRACT_VERSION,
      deployment: BROWSER_WORKER_DEPLOYMENT,
      requestId: request.requestId,
      requestDigest: workerRequestDigest(request),
      runId: request.runId,
      siteId: request.siteId,
      workspaceId: request.workspaceId,
      capabilityId: request.capabilityId,
      operationId: request.operationId,
      leaseId: request.leaseId,
      attempt: request.attempt,
      routeDigest: request.routeDigest,
      target: request.target,
      state,
      summary,
      error,
      artifacts,
      startedAt,
      completedAt,
      expiresAt: completedAt + BROWSER_WORKER_BOUNDS.responseTtlSeconds,
    });
  }
}
