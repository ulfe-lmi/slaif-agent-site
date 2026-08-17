import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { URL } from "node:url";

test("landing page is explicit about implemented and deferred behavior", async () => {
  const page = await readFile(new URL("../app/page.tsx", import.meta.url), "utf8");
  assert.match(page, /Pre-alpha deployment skeleton/);
  assert.match(page, /Deliberately deferred/);
  assert.match(page, /It is not a website editor yet/);
});

test("health routes make only web-process claims", async () => {
  for (const name of ["live", "ready"]) {
    const route = await readFile(
      new URL(`../app/health/${name}/route.ts`, import.meta.url),
      "utf8",
    );
    assert.match(route, /service: "web"/);
    assert.doesNotMatch(route, /database|product|published/i);
  }
});
