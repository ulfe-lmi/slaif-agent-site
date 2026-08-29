import assert from "node:assert/strict";
import { test } from "node:test";

import { healthResponse } from "../dist/responses.js";

test("browser worker exposes only bounded readiness-aware health responses", () => {
  assert.deepEqual(healthResponse("/health/live"), {
    service: "browser-worker",
    status: "ok",
  });
  assert.equal(healthResponse("/browse"), null);
  assert.equal(healthResponse("/evaluate"), null);
  assert.deepEqual(healthResponse("/health/ready", false), {
    components: [],
    service: "browser-worker",
    status: "unavailable",
  });
  assert.deepEqual(healthResponse("/health/ready", true), {
    components: [
      "artifact-store",
      "chromium-sandbox",
      "request-confinement",
      "worker-service-auth",
    ],
    service: "browser-worker",
    status: "ready",
  });
});
