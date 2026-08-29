import {
  BROWSER_TARGET_DESCRIPTORS,
  type BrowserTarget,
} from "@slaif-agent-site/browser-tool-contracts";
import type { BrowserContextOptions } from "playwright-core";

export function contextOptionsForTarget(target: BrowserTarget): BrowserContextOptions {
  const descriptor = BROWSER_TARGET_DESCRIPTORS[target];
  return Object.freeze({
    viewport: descriptor.viewport,
    deviceScaleFactor: descriptor.deviceScaleFactor,
    hasTouch: descriptor.hasTouch,
    isMobile: descriptor.isMobile,
    acceptDownloads: false,
    serviceWorkers: "block",
  });
}
