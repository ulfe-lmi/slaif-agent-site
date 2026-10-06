import { defineConfig, devices } from "@playwright/test";

const baseURL = "http://localhost:8080";

export default defineConfig({
  testDir: "tests/e2e",
  timeout: 30_000,
  expect: { timeout: 8_000 },
  fullyParallel: false,
  workers: 1,
  retries: 0,
  reporter: [["./tests/e2e/reporter.mjs"]],
  outputDir: process.env.SLAIF_E2E_OUTPUT_DIR ?? "/tmp/slaif-playwright-output",
  use: {
    baseURL,
    screenshot: "off",
    trace: "off",
    video: "off",
    serviceWorkers: "block",
  },
  projects: [
    {
      name: "setup",
      testMatch: /setup\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "governance",
      dependencies: ["setup"],
      testMatch: /governance\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "preview",
      testMatch: /preview\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "preview-filtering",
      testMatch: /collection-filtering\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "desktop-chromium",
      dependencies: ["governance"],
      testMatch: /auth\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "desktop-firefox",
      dependencies: ["governance"],
      testMatch: /auth\.spec\.ts/,
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "desktop-webkit",
      dependencies: ["governance"],
      testMatch: /auth\.spec\.ts/,
      use: { ...devices["Desktop Safari"] },
    },
    {
      name: "tablet",
      dependencies: ["governance"],
      testMatch: /auth\.spec\.ts/,
      use: { ...devices["iPad (gen 7)"] },
    },
    {
      name: "mobile-chromium",
      dependencies: ["governance"],
      testMatch: /auth\.spec\.ts/,
      use: { ...devices["Pixel 5"] },
    },
    {
      name: "mobile-webkit",
      dependencies: ["governance"],
      testMatch: /auth\.spec\.ts/,
      use: { ...devices["iPhone 13"] },
    },
    {
      name: "agent-desktop-chromium",
      dependencies: ["governance"],
      testMatch: /agent-sessions\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "agent-mobile-chromium",
      dependencies: ["governance"],
      testMatch: /agent-sessions\.spec\.ts/,
      use: { ...devices["Pixel 5"] },
    },
    {
      name: "media-publication",
      dependencies: ["setup"],
      testMatch: /media-publication\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "agent-workspace-puck-desktop",
      dependencies: ["governance"],
      testMatch: /agent-workspace-puck\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "agent-workspace-puck-tablet",
      dependencies: ["governance"],
      testMatch: /agent-workspace-puck\.spec\.ts/,
      use: { ...devices["iPad (gen 7)"] },
    },
    {
      name: "freeze-review-snapshot",
      dependencies: ["governance"],
      testMatch: /freeze-review-snapshot\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "review-surface",
      dependencies: ["governance"],
      testMatch: /review-surface\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "accept-lifecycle",
      dependencies: ["governance"],
      testMatch: /accept-lifecycle\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "discard-lifecycle",
      dependencies: ["governance"],
      testMatch: /discard-lifecycle\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
