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
  outputDir: "/tmp/slaif-playwright-output",
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
      name: "desktop-chromium",
      dependencies: ["setup"],
      testMatch: /auth\.spec\.ts/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "desktop-firefox",
      dependencies: ["setup"],
      testMatch: /auth\.spec\.ts/,
      use: { ...devices["Desktop Firefox"] },
    },
    {
      name: "desktop-webkit",
      dependencies: ["setup"],
      testMatch: /auth\.spec\.ts/,
      use: { ...devices["Desktop Safari"] },
    },
    {
      name: "tablet",
      dependencies: ["setup"],
      testMatch: /auth\.spec\.ts/,
      use: { ...devices["iPad (gen 7)"] },
    },
    {
      name: "mobile-chromium",
      dependencies: ["setup"],
      testMatch: /auth\.spec\.ts/,
      use: { ...devices["Pixel 5"] },
    },
    {
      name: "mobile-webkit",
      dependencies: ["setup"],
      testMatch: /auth\.spec\.ts/,
      use: { ...devices["iPhone 13"] },
    },
  ],
});
