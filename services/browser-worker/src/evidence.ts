import {
  BROWSER_WORKER_BOUNDS,
  canonicalJson,
  type BrowserEvidence,
  type BrowserWorkerSubmitRequest,
} from "@slaif-agent-site/browser-tool-contracts";
import type { ConsoleMessage, Page, Request } from "playwright-core";

import { pngDimensions, type ArtifactContent } from "./artifact-store.js";

const credentialPattern =
  /(?:sbp1(?:\.[A-Za-z0-9_-]+){3}|sbws1:[A-Za-z0-9:_-]+|sas2_[A-Za-z0-9_-]+)/gu;

export function sanitizeOutput(value: string): string {
  return value
    .replaceAll(credentialPattern, "[REDACTED]")
    .replaceAll(/./gu, (character) => {
      const codePoint = character.codePointAt(0) ?? 0;
      return codePoint <= 0x1f || codePoint === 0x7f ? " " : character;
    })
    .replaceAll(/\s+/gu, " ")
    .trim()
    .slice(0, BROWSER_WORKER_BOUNDS.outputStringCharacters);
}

function jsonArtifact(kind: BrowserEvidence, value: unknown): ArtifactContent {
  const bytes = Buffer.from(canonicalJson(value), "utf8");
  if (bytes.length > BROWSER_WORKER_BOUNDS.summaryBytes) {
    throw new Error("browser evidence is unavailable");
  }
  return Object.freeze({ kind, mimeType: "application/json", bytes });
}

export interface EvidenceEvents {
  readonly console: readonly { readonly type: string; readonly text: string }[];
  readonly failedRequests: readonly {
    readonly method: string;
    readonly resourceType: string;
    readonly failure: string;
  }[];
  readonly blockedRequests: number;
}

export function observeEvidenceEvents(
  page: Page,
  blockedRequests: () => number,
): { readonly events: EvidenceEvents } {
  const consoleEntries: { type: string; text: string }[] = [];
  const failedRequests: { method: string; resourceType: string; failure: string }[] =
    [];
  page.on("console", (message: ConsoleMessage) => {
    if (consoleEntries.length < BROWSER_WORKER_BOUNDS.outputItems) {
      consoleEntries.push({
        type: message.type(),
        text: sanitizeOutput(message.text()),
      });
    }
  });
  page.on("requestfailed", (request: Request) => {
    if (failedRequests.length < BROWSER_WORKER_BOUNDS.outputItems) {
      failedRequests.push({
        method: request.method(),
        resourceType: request.resourceType(),
        failure: sanitizeOutput(request.failure()?.errorText ?? "failed"),
      });
    }
  });
  return Object.freeze({
    events: {
      get console() {
        return Object.freeze([...consoleEntries]);
      },
      get failedRequests() {
        return Object.freeze([...failedRequests]);
      },
      get blockedRequests() {
        return blockedRequests();
      },
    },
  });
}

async function boundedTexts(page: Page, selector: string): Promise<readonly string[]> {
  const values = await page.locator(selector).allTextContents();
  return Object.freeze(
    values
      .slice(0, BROWSER_WORKER_BOUNDS.outputItems)
      .map((value) => sanitizeOutput(value))
      .filter(Boolean),
  );
}

async function collectSummary(
  page: Page,
  kind: Exclude<BrowserEvidence, "screenshot">,
  events: EvidenceEvents,
): Promise<ArtifactContent> {
  if (kind === "accessibility-summary") {
    return jsonArtifact(kind, {
      buttons: await page.getByRole("button").count(),
      headings: await page.getByRole("heading").count(),
      images: await page.getByRole("img").count(),
      links: await page.getByRole("link").count(),
      main: await page.getByRole("main").count(),
    });
  }
  if (kind === "structure-summary") {
    return jsonArtifact(kind, {
      articles: await page.locator("article").count(),
      components: await page.locator("[data-component-type]").count(),
      main: await page.locator("main").count(),
      navigation: await page.locator("nav").count(),
      sections: await page.locator("section").count(),
    });
  }
  if (kind === "heading-summary") {
    return jsonArtifact(kind, {
      headings: await boundedTexts(page, "h1,h2,h3,h4,h5,h6"),
    });
  }
  if (kind === "link-summary") {
    return jsonArtifact(kind, {
      count: await page.locator("a").count(),
      labels: await boundedTexts(page, "a"),
    });
  }
  if (kind === "media-summary") {
    return jsonArtifact(kind, {
      audio: await page.locator("audio").count(),
      imageAlt: await page
        .locator("img")
        .evaluateAll((elements) =>
          elements.slice(0, 64).map((element) => element.getAttribute("alt") ?? ""),
        ),
      images: await page.locator("img").count(),
      video: await page.locator("video").count(),
    });
  }
  if (kind === "overflow-summary") {
    return jsonArtifact(
      kind,
      await page.locator("body").evaluate((body) => ({
        clientWidth: body.ownerDocument.documentElement.clientWidth,
        scrollWidth: body.ownerDocument.documentElement.scrollWidth,
        overflows:
          body.ownerDocument.documentElement.scrollWidth >
          body.ownerDocument.documentElement.clientWidth,
      })),
    );
  }
  if (kind === "console-summary") {
    return jsonArtifact(kind, { entries: events.console });
  }
  return jsonArtifact(kind, {
    blocked: events.blockedRequests,
    entries: events.failedRequests,
  });
}

export async function collectEvidence(
  page: Page,
  request: BrowserWorkerSubmitRequest,
  events: EvidenceEvents,
): Promise<readonly ArtifactContent[]> {
  const artifacts: ArtifactContent[] = [];
  for (const kind of request.evidence) {
    if (kind === "screenshot") {
      const bytes = await page.screenshot({
        type: "png",
        fullPage: false,
        animations: "disabled",
      });
      const dimensions = pngDimensions(bytes);
      const viewport = page.viewportSize();
      if (
        viewport === null ||
        dimensions.width !== viewport.width ||
        dimensions.height !== viewport.height
      )
        throw new Error("browser evidence is unavailable");
      artifacts.push(Object.freeze({ kind, mimeType: "image/png", bytes }));
    } else {
      artifacts.push(await collectSummary(page, kind, events));
    }
  }
  const total = artifacts.reduce((sum, item) => sum + item.bytes.length, 0);
  if (
    total > request.artifactBytesLimit ||
    total > BROWSER_WORKER_BOUNDS.totalArtifactBytes
  )
    throw new Error("browser evidence is unavailable");
  return Object.freeze(artifacts);
}
