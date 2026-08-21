import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { test } from "node:test";
import { URL } from "node:url";

const read = (path) => readFile(new URL(path, import.meta.url), "utf8");

test("auth routes and landing page expose truthful local flows", async () => {
  const home = await read("../app/page.tsx");
  assert.match(home, /href="\/setup"/);
  assert.match(home, /href="\/login"/);
  assert.match(home, /Secure local administrator setup and server-side sessions/);
  assert.match(home, /trusted\s+multi-site identity and routing/);
  assert.match(home, /Platform Administrator site\/domain\s+APIs/);
  assert.match(home, /built-in RBAC and membership APIs/);
  assert.match(home, /route-policy declarations/);
  assert.match(home, /publication authority stays separate/);
  const deferred = home.match(
    /Still deliberately absent<\/h2>\s*<p>([\s\S]*?)<\/p>/,
  )?.[1];
  assert.ok(deferred);
  for (const claim of [
    /Site and membership UI/,
    /invitations/,
    /custom roles/,
    /content models and\s+site\s+content/,
    /workspaces and agent capabilities/,
    /editing\/Puck/,
    /review,\s+and\s+publication execution/,
  ])
    assert.match(deferred, claim);
  assert.doesNotMatch(deferred, /\bsites\b|site routing/i);
  const implemented = home.match(/Implemented now<\/h2>\s*<p>([\s\S]*?)<\/p>/)?.[1];
  assert.ok(implemented);
  assert.doesNotMatch(implemented, /content models|publication execution/i);
  assert.doesNotMatch(deferred, /Membership\/RBAC|membership APIs/i);
  for (const route of ["setup", "login", "admin"]) {
    const expected =
      route === "admin" ? "AdminShell" : route === "setup" ? "SetupForm" : "LoginForm";
    assert.match(await read(`../app/${route}/page.tsx`), new RegExp(expected));
  }
});

test("admin shell is URL-owned, server-filtered, accessible, and read-only", async () => {
  const api = await read("../src/admin/api.ts");
  const shell = await read("../src/admin/shell.tsx");
  const sitePage = await read("../app/admin/sites/[siteId]/page.tsx");
  const primitives = await read("../src/components/ui/primitives.tsx");
  for (const path of ["/me/sites", "/my-authority"])
    assert.match(api, new RegExp(path));
  assert.match(api, /credentials: "same-origin"/);
  assert.match(api, /cache: "no-store"/);
  assert.match(api, /encodeURIComponent\(siteId\)/);
  assert.doesNotMatch(`${api}${shell}`, /localStorage|sessionStorage|serviceWorker/);
  assert.match(shell, /Skip to main content/);
  assert.match(shell, /@radix-ui\/react-dialog/);
  assert.match(shell, /Dialog\.Overlay/);
  assert.match(shell, /Dialog\.Close/);
  assert.match(shell, /Platform governance/);
  assert.match(shell, /No authorized sites/);
  assert.match(shell, /Authenticated session active\./);
  assert.match(shell, /Local administrator/);
  assert.match(shell, /This site is unavailable or you do not have access/);
  assert.match(shell, /"Content"[\s\S]*\{item\} · planned/);
  assert.match(shell, /Users &amp; Permissions/);
  assert.match(sitePage, /selectedSiteId=\{siteId\}/);
  assert.match(primitives, /role="status"/);
  assert.doesNotMatch(shell, /create|update|delete|archive/i);
});

test("forms preserve accessibility, password manager, and pending contracts", async () => {
  const forms = await read("../src/auth/forms.tsx");
  for (const value of ["username", "new-password", "current-password", "name", "email"])
    assert.match(forms, new RegExp(`autoComplete="${value}"`));
  assert.match(forms, /role="status"/);
  assert.match(forms, /aria-live="polite"/);
  assert.match(forms, /submitting\.current/);
  assert.match(forms, /disabled=\{!available \|\| pending\}/);
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

test("site shell uses only the fixed server-side Render resolver", async () => {
  const client = await read("../src/sites/render.ts");
  const shell = await read("../app/[...sitePath]/page.tsx");
  const shellView = await read("../src/sites/shell.tsx");
  const landing = await read("../app/page.tsx");
  assert.match(client, /http:\/\/render-api:8000\/internal\/render\/v1\/site-context/);
  assert.match(client, /credentials: "omit"/);
  assert.match(client, /cache: "no-store"/);
  assert.doesNotMatch(client, /process\.env|cookie|authorization|forwarded/i);
  assert.match(shell, /requestHeaders\.get\("host"\)/);
  assert.match(shellView, /Trusted routing context/);
  assert.match(shellView, /Editorial content and\s+publication are not implemented/);
  assert.match(landing, /isLoopbackAuthority/);
  assert.match(landing, /resolveSiteContext\(authority, "\/"\)/);
  assert.doesNotMatch(shell, /site_id.*params|x-forwarded-host/i);
});
