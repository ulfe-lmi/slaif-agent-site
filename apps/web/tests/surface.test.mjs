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
    /Membership UI/,
    /invitations/,
    /custom roles/,
    /content models and\s+site\s+content/,
    /workspaces and agent capabilities/,
    /editing\/Puck/,
    /review,\s+and\s+publication\s+execution/,
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

test("admin workflows are URL-owned, server-filtered, and accessible", async () => {
  const api = await read("../src/admin/api.ts");
  const shell = await read("../src/admin/shell.tsx");
  const sitePage = await read("../app/admin/sites/[siteId]/page.tsx");
  const settingsPage = await read("../app/admin/sites/[siteId]/settings/page.tsx");
  const membershipsPage = await read(
    "../app/admin/sites/[siteId]/memberships/page.tsx",
  );
  const primitives = await read("../src/components/ui/primitives.tsx");
  const modal = await read("../src/admin/csp-modal.tsx");
  const workflows = await read("../src/admin/site-workflows.tsx");
  const memberships = await read("../src/admin/membership-workflows.tsx");
  for (const path of ["/me/sites", "/my-authority"])
    assert.match(api, new RegExp(path));
  assert.match(api, /credentials: "same-origin"/);
  for (const page of [settingsPage, membershipsPage]) {
    assert.match(page, /<AdminShell selectedSiteId=\{siteId\}>/);
  }
  assert.match(shell, /<nav className="mobile-nav" aria-label="Administration">/);
  assert.match(api, /cache: "no-store"/);
  assert.match(api, /encodeURIComponent\(siteId\)/);
  assert.doesNotMatch(`${api}${shell}`, /localStorage|sessionStorage|serviceWorker/);
  assert.match(shell, /Skip to main content/);
  assert.match(modal, /@radix-ui\/react-dialog/);
  assert.match(modal, /<Dialog\.Root modal=\{false\}/);
  assert.match(modal, /aria-modal="true"/);
  assert.match(modal, /background\.inert = true/);
  assert.match(modal, /priorInertAttribute/);
  assert.match(modal, /document\.addEventListener\("focusin"/);
  assert.match(modal, /event\.shiftKey/);
  assert.match(modal, /onPointerDown=\{\(event\) => event\.preventDefault\(\)\}/);
  assert.doesNotMatch(modal, /\.style\.|setAttribute\(["']style|innerHTML/);
  assert.match(shell, /Platform governance/);
  assert.match(shell, /No authorized sites/);
  assert.match(shell, /Authenticated session active\./);
  assert.match(shell, /Local administrator/);
  assert.match(shell, /This site is unavailable or you do not have access/);
  assert.match(
    shell,
    /value\.sites\.some\(\(site\) => site\.site_id === selectedSiteId\)/,
  );
  assert.match(shell, /"Content"[\s\S]*\{item\} · planned/);
  assert.match(shell, /Users &amp; Permissions/);
  assert.match(sitePage, /selectedSiteId=\{siteId\}/);
  assert.match(primitives, /role="status"/);
  for (const operation of [
    "createSite",
    "updateSite",
    "putDomain",
    "removeDomain",
    "archiveSite",
  ])
    assert.match(workflows, new RegExp(operation));
  assert.match(workflows, /pending\.current/);
  assert.match(workflows, /site-policy:manage/);
  assert.match(workflows, /site-domain:manage/);
  assert.match(workflows, /do not automate DNS/);
  assert.match(workflows, /does not delete|does not\s+delete/);
  assert.equal(`${shell}${workflows}${memberships}`.match(/<CspModal/g)?.length, 4);
  assert.doesNotMatch(`${shell}${workflows}${memberships}`, /<Dialog\./);
  assert.match(workflows, /disabled=\{!recent\}/);
  assert.doesNotMatch(`${api}${shell}${workflows}`, /localStorage|sessionStorage/);
});

test("Puck editor remains trusted, same-origin, and normalized", async () => {
  const editor = await read("../src/admin/composition-editor.tsx");
  const api = await read("../src/admin/api.ts");
  const route = await read("../app/admin/sites/[siteId]/pages/[pageId]/edit/page.tsx");
  const manifest = JSON.parse(await read("../package.json"));
  const adapter = await read(
    "../../../packages/composition-schema/src/puck-adapter.ts",
  );
  assert.equal(manifest.dependencies["@measured/puck"], "0.20.2");
  assert.match(route, /CompositionEditor/);
  assert.match(editor, /from "@measured\/puck"/);
  assert.match(editor, /COMPONENT_CATALOG/);
  assert.match(editor, /data-puck-component/);
  assert.match(editor, /puckToComposition/);
  assert.match(editor, /pending.current/);
  assert.ok(api.includes("/api/editor/v1"));
  assert.match(api, /X-CSRF-Token/);
  assert.match(api, /cache: "no-store"/);
  assert.match(adapter, /schemaVersion/);
  assert.match(adapter, /parentId/);
  assert.match(adapter, /slotKey/);
  assert.match(adapter, /orderKey/);
  assert.match(adapter, /forbidden-component-prop/);
  assert.doesNotMatch(`${editor}${api}`, /localStorage|sessionStorage|Bearer|sas2_/);
});

test("membership administration preserves exact server contracts and UX boundaries", async () => {
  const api = await read("../src/admin/api.ts");
  const workflow = await read("../src/admin/membership-workflows.tsx");
  const page = await read("../app/admin/sites/[siteId]/memberships/page.tsx");
  const shell = await read("../src/admin/shell.tsx");
  const css = await read("../app/styles.css");
  for (const path of [
    'json("/roles")',
    'json("/permissions")',
    "/memberships`",
    "?expected_version=",
  ])
    assert.ok(api.includes(path), path);
  for (const method of ['mutation("POST"', 'mutation("PATCH"', 'mutation("DELETE"'])
    assert.ok(api.includes(method), method);
  for (const field of [
    "target_user_id",
    "expected_version",
    "delegation_ceiling",
    "allow_permissions",
    "deny_permissions",
  ])
    assert.match(api, new RegExp(field));
  for (const validator of [
    "default_permissions",
    "site_assignable",
    "effective_permissions",
    "platform_administrator",
    "user_account_id",
  ])
    assert.match(api, new RegExp(validator));
  assert.match(api, /delegationLevel >= 0/);
  assert.match(workflow, /membership:manage/);
  assert.match(workflow, /role:manage/);
  assert.match(workflow, /site:publish/);
  assert.match(workflow, /Architect ceiling 4 does not\s+publish by default/);
  assert.match(workflow, /completely replaces explicit overrides/);
  assert.match(workflow, /Nonassignable installation and system scopes/);
  assert.match(workflow, /expected version \$\{item\.version\}/);
  assert.match(workflow, /preserves the membership row, history, role, and overrides/);
  assert.match(workflow, /self-mutation controls are not presented/);
  assert.match(workflow, /sequence\.current/);
  assert.match(workflow, /if \(pending\.current\) return/);
  assert.match(workflow, /errorRef\.current\?\.focus/);
  for (const state of [
    "unauthenticated",
    "denied",
    "not-found",
    "conflict",
    "invalid",
    "unavailable",
    "invalid-response",
  ])
    assert.match(workflow, new RegExp(state));
  assert.match(workflow, /CspModal/);
  assert.doesNotMatch(workflow, /<Dialog\./);
  assert.match(page, /MembershipWorkflow siteId=\{siteId\}/);
  assert.match(shell, /Manage memberships/);
  assert.match(css, /membership-card[\s\S]*overflow-wrap: anywhere/);
  assert.match(css, /@media \(max-width: 760px\)[\s\S]*permission-group/);
  assert.doesNotMatch(
    `${api}${workflow}${page}`,
    /localStorage|sessionStorage|dangerouslySetInnerHTML|https?:\/\//,
  );
  assert.doesNotMatch(`${api}${workflow}`, /public_id|email_address/);
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
  const postcss = await read("../postcss.config.mjs");
  const tailwind = await read("../tailwind.config.mjs");
  const manifest = await read("../package.json");
  assert.match(
    css,
    /@tailwind base;[\s\S]*@tailwind components;[\s\S]*@tailwind utilities;/,
  );
  assert.match(postcss, /tailwindcss: \{\}[\s\S]*autoprefixer: \{\}/);
  assert.match(tailwind, /\.\/app\/\*\*\/[\s\S]*\.\/src\/\*\*\//);
  assert.match(manifest, /"tailwindcss": "3\.4\.19"/);
  assert.match(manifest, /"autoprefixer": "10\.5\.4"/);
  assert.doesNotMatch(
    `${css}${postcss}${tailwind}${manifest}`,
    /lightningcss|@tailwindcss\/postcss|tailwindcss": "4\./,
  );
  assert.doesNotMatch(`${css}${postcss}${tailwind}`, /https?:\/\/|@import\s+url/);
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
