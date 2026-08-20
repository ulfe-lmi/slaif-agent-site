import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { URL } from "node:url";

const read = (path) => readFile(new URL(path, import.meta.url), "utf8");

test("auth routes and landing page expose truthful local flows", async () => {
  const home = await read("../app/page.tsx");
  assert.match(home, /href="\/setup"/);
  assert.match(home, /href="\/login"/);
  assert.match(home, /OIDC, MFA, rate limiting/);
  for (const route of ["setup", "login", "admin"]) {
    const expected =
      route === "admin"
        ? "AdminSession"
        : route === "setup"
          ? "SetupForm"
          : "LoginForm";
    assert.match(await read(`../app/${route}/page.tsx`), new RegExp(expected));
  }
});

test("forms preserve accessibility, password manager, and pending contracts", async () => {
  const forms = await read("../src/auth/forms.tsx");
  for (const value of ["username", "new-password", "current-password", "name", "email"])
    assert.match(forms, new RegExp(`autoComplete="${value}"`));
  assert.match(forms, /role="status"/);
  assert.match(forms, /aria-live="polite"/);
  assert.match(forms, /if \(pending\) return/);
  assert.match(forms, /type="password"/);
  assert.match(forms, /window\.location\.protocol === "https:"/);
  assert.doesNotMatch(forms, /localStorage|sessionStorage|public_id/);
});

test("auth client uses exact same-origin methods and strict CSRF cookies", async () => {
  const client = await read("../src/auth/client.ts");
  assert.match(client, /"\/api\/control\/v1"/);
  assert.match(client, /credentials: "same-origin"/);
  for (const path of ["setup/status", "setup", "login", "session", "logout"])
    assert.match(client, new RegExp(path.replace("/", "\\/")));
  assert.match(client, /X-CSRF-Token/);
  assert.match(client, /__Host-slaif_csrf/);
  assert.match(client, /values\.has\(name\)/);
  assert.doesNotMatch(client, /localStorage|sessionStorage|URLSearchParams/);
});

test("responsive styles cover narrow layout, focus, contrast, and reduced motion", async () => {
  const css = await read("../app/styles.css");
  assert.match(css, /@media \(max-width: 360px\)/);
  assert.match(css, /overflow-wrap: anywhere/);
  assert.match(css, /focus-visible/);
  assert.match(css, /prefers-reduced-motion/);
});

test("health routes make only web-process claims", async () => {
  for (const name of ["live", "ready"]) {
    const route = await read(`../app/health/${name}/route.ts`);
    assert.match(route, /service: "web"/);
    assert.doesNotMatch(route, /database|product|published/i);
  }
});
