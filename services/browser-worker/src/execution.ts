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
import { chromium, type Browser } from "playwright-core";

import { BrowserArtifactStore } from "./artifact-store.js";
import { collectEvidence, observeEvidenceEvents } from "./evidence.js";
import { contextOptionsForTarget } from "./targets.js";
import {
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
