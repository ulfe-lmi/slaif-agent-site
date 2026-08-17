import assert from "node:assert/strict";
import { test } from "node:test";

import { healthResponse } from "../src/responses.ts";

test("browser placeholder exposes only bounded health responses", () => {
  assert.deepEqual(healthResponse("/health/live"), {
    service: "browser-worker",
    status: "ok",
  });
  assert.equal(healthResponse("/browse"), null);
  assert.equal(healthResponse("/evaluate"), null);
});
