import assert from "node:assert/strict";
import { test } from "node:test";
import { URL } from "node:url";

import {
  CONFINEMENT_SELF_CHECK_URLS,
  installRequestConfinement,
  previewDocumentUrl,
  requestIsAllowed,
} from "../dist/url-policy.js";

const origin = "http://preview.example";
const document = new URL(`${origin}/preview/00000000-0000-4000-8000-000000000001/`);
const mediaId = "11111111-2222-4333-8444-555555555555";
const mediaUrl = `${origin}/media/v1/browser-preview/assets/${mediaId}/content`;

test("bound media subresource: image and bounded fetch only", () => {
  assert.equal(requestIsAllowed(mediaUrl, "GET", "image", document), "MEDIA");
  assert.equal(requestIsAllowed(mediaUrl, "GET", "fetch", document), "MEDIA");
  // A second top-level navigation to the bound asset (following a
  // DocumentList link, or any other document target on the path) is not a
  // bounded resource read and stays denied.
  assert.equal(requestIsAllowed(mediaUrl, "GET", "document", document), null);
  const otherMediaId = "99999999-8888-4777-8666-555555555555";
  const otherMediaUrl = `${origin}/media/v1/browser-preview/assets/${otherMediaId}/content`;
  assert.equal(requestIsAllowed(otherMediaUrl, "GET", "document", document), null);
  assert.equal(requestIsAllowed(otherMediaUrl, "GET", "image", document), "MEDIA");
  assert.equal(requestIsAllowed(otherMediaUrl, "GET", "fetch", document), "MEDIA");
  // fetch is authorized for the exact bound shape only
  assert.equal(requestIsAllowed(`${mediaUrl}?next=x`, "GET", "fetch", document), null);
  assert.equal(
    requestIsAllowed(
      `https://control-api:8000/media/v1/browser-preview/assets/${mediaId}/content`,
      "GET",
      "fetch",
      document,
    ),
    null,
  );
});

test("bound media subresource: denials", () => {
  const denials = [
    // wrong origin / host / credentials
    `https://preview.example/media/v1/browser-preview/assets/${mediaId}/content`,
    `${origin}/media/v1/browser-preview/assets/${mediaId}/content?next=x`,
    // wrong path shape
    `${origin}/media/v1/browser-preview/assets/${mediaId}`,
    `${origin}/media/v1/browser-preview/assets/${mediaId}/content/`,
    `${origin}/media/v1/browser-preview/assets/${mediaId}/extra/content`,
    `${origin}/media/v1/browser-preview/ASSETS/${mediaId}/content`,
    `${origin}/media/v1/browser-preview/assets/not-a-uuid/content`,
    `${origin}/media/v1/browser-preview/assets/11111111-2222-4333-8444-55555555555g/content`,
    `${origin}/media/v1/sites/00000000-0000-4000-8000-000000000002/assets/${mediaId}/content`,
    `${origin}/not-media/${mediaId}`,
  ];
  for (const value of denials) {
    assert.equal(requestIsAllowed(value, "GET", "image", document), null, value);
  }
  for (const method of ["POST", "PUT", "HEAD", "DELETE"]) {
    assert.equal(requestIsAllowed(mediaUrl, method, "image", document), null, method);
  }
  for (const resourceType of [
    "xhr",
    "script",
    "iframe",
    "font",
    "other",
    "stylesheet",
    "document",
  ]) {
    assert.equal(
      requestIsAllowed(mediaUrl, "GET", resourceType, document),
      null,
      resourceType,
    );
  }
});

test("document and static asset policy unchanged", () => {
  assert.equal(
    requestIsAllowed(document.href, "GET", "document", document),
    "DOCUMENT",
  );
  assert.equal(
    requestIsAllowed(`${origin}/renderer-v1.css`, "GET", "stylesheet", document),
    "ASSET",
  );
  assert.equal(
    requestIsAllowed(`${origin}/_next/static/x.js`, "GET", "script", document),
    "ASSET",
  );
  assert.equal(
    requestIsAllowed(`${origin}/api/anything`, "GET", "xhr", document),
    null,
  );
  for (const value of CONFINEMENT_SELF_CHECK_URLS) {
    assert.equal(requestIsAllowed(value, "GET", "document", document), null);
  }
});

function fakeRequest(
  url,
  { method = "GET", resourceType = "image", headers = {}, redirectedFrom = null } = {},
) {
  return {
    url: () => url,
    method: () => method,
    resourceType: () => resourceType,
    headers: () => headers,
    redirectedFrom: () => redirectedFrom,
  };
}

function fakeRoute() {
  const actions = [];
  return {
    actions,
    continue: async (opts) => {
      actions.push({ kind: "continue", opts });
    },
    abort: async (reason) => {
      actions.push({ kind: "abort", reason });
    },
  };
}

async function installWith(credential) {
  let handler = null;
  const context = {
    route: async (_pattern, h) => {
      handler = h;
    },
  };
  let blocked = 0;
  await installRequestConfinement(context, document, credential, () => {
    blocked += 1;
  });
  const run = async (request) => {
    const route = fakeRoute();
    await handler(route, request);
    return { route, blocked };
  };
  return { run };
}

test("confinement: bound media fetch injects run credential only", async () => {
  const { run } = await installWith("sbp1.probe-token");
  const { route, blocked } = await run(
    fakeRequest(mediaUrl, {
      resourceType: "image",
      headers: {
        cookie: "slaif_session=sas2_stolen",
        authorization: "Bearer stolen",
        "x-slaif-browser-preview": "sbp1.stale",
        accept: "image/*",
      },
    }),
  );
  assert.equal(blocked, 0);
  assert.equal(route.actions.length, 1);
  assert.equal(route.actions[0].kind, "continue");
  const headers = route.actions[0].opts.headers;
  assert.equal(headers["x-slaif-browser-preview"], "sbp1.probe-token");
  assert.equal(headers.cookie, undefined);
  assert.equal(headers.authorization, undefined);
  assert.equal(headers["proxy-authorization"], undefined);
  assert.equal(headers["x-slaif-browser-worker-token"], undefined);
  assert.equal(headers.accept, "image/*");
});

test("confinement: redirected media fetch is denied", async () => {
  const { run } = await installWith("sbp1.probe-token");
  const { route, blocked } = await run(
    fakeRequest(mediaUrl, {
      resourceType: "image",
      redirectedFrom: `${origin}/preview/x/`,
    }),
  );
  assert.equal(blocked, 1);
  assert.equal(route.actions[0].kind, "abort");
});

test("confinement: non-media private path stays denied", async () => {
  const { run } = await installWith("sbp1.probe-token");
  const { route, blocked } = await run(
    fakeRequest(
      `${origin}/media/v1/sites/00000000-0000-4000-8000-000000000002/assets/${mediaId}/content`,
      { resourceType: "image" },
    ),
  );
  assert.equal(blocked, 1);
  assert.equal(route.actions[0].kind, "abort");
});

test("confinement: second navigation to bound media is denied", async () => {
  const { run } = await installWith("sbp1.probe-token");
  const { route, blocked } = await run(
    fakeRequest(mediaUrl, {
      resourceType: "document",
      headers: { cookie: "slaif_session=sas2_stolen" },
    }),
  );
  assert.equal(blocked, 1);
  assert.equal(route.actions.length, 1);
  assert.equal(route.actions[0].kind, "abort");
});

test("confinement: bounded document fetch injects run credential only", async () => {
  const { run } = await installWith("sbp1.probe-token");
  const { route, blocked } = await run(
    fakeRequest(mediaUrl, {
      resourceType: "fetch",
      headers: {
        cookie: "slaif_session=sas2_stolen",
        authorization: "Bearer stolen",
        accept: "application/pdf",
      },
    }),
  );
  assert.equal(blocked, 0);
  assert.equal(route.actions.length, 1);
  assert.equal(route.actions[0].kind, "continue");
  const headers = route.actions[0].opts.headers;
  assert.equal(headers["x-slaif-browser-preview"], "sbp1.probe-token");
  assert.equal(headers.cookie, undefined);
  assert.equal(headers.authorization, undefined);
  assert.equal(headers.accept, "application/pdf");
});

test("confinement: redirected bounded fetch is denied", async () => {
  const { run } = await installWith("sbp1.probe-token");
  const { route, blocked } = await run(
    fakeRequest(mediaUrl, {
      resourceType: "fetch",
      redirectedFrom: `${origin}/preview/x/`,
    }),
  );
  assert.equal(blocked, 1);
  assert.equal(route.actions[0].kind, "abort");
});

const documentWorkspaceId = "00000000-0000-4000-8000-000000000001";
const documentOrigin = new URL(origin);

test("previewDocumentUrl: canonical slashless document form", () => {
  // The framework 308-normalizes trailing slashes before app routing and
  // the confinement handler admits exactly one non-redirected document,
  // so every route - including the root and the root carrying a query -
  // must request the canonical slashless document form.
  const cases = [
    ["/", `${origin}/preview/${documentWorkspaceId}`],
    ["/?q=one", `${origin}/preview/${documentWorkspaceId}?q=one`],
    ["/news", `${origin}/preview/${documentWorkspaceId}/news`],
    ["/news/", `${origin}/preview/${documentWorkspaceId}/news`],
    ["/news?q=one", `${origin}/preview/${documentWorkspaceId}/news?q=one`],
    ["/a/b", `${origin}/preview/${documentWorkspaceId}/a/b`],
    ["/a/b/", `${origin}/preview/${documentWorkspaceId}/a/b`],
  ];
  for (const [route, expected] of cases) {
    const value = previewDocumentUrl(documentOrigin, {
      workspaceId: documentWorkspaceId,
      route,
    });
    assert.equal(value.href, expected, route);
    assert.equal(value.origin, documentOrigin.origin, route);
    // The query is preserved verbatim: the server normalized and digest-
    // bound the route, so the worker must not re-encode it.
    assert.equal(value.search, new URL(expected).search, route);
  }
});

test("previewDocumentUrl: document origin stays pinned to the preview origin", () => {
  // The submit contract binds workspace_id as a UUID and the route to its
  // exact digest, so these malformed shapes cannot reach the worker on the
  // wire; the assertion keeps the origin pin itself honest: whatever the
  // workspace segment carries, the document never leaves the configured
  // preview origin (no authority or origin widening).
  for (const workspaceId of [
    documentWorkspaceId,
    `//evil.example/${documentWorkspaceId}`,
    `@evil.example${documentWorkspaceId}`,
  ]) {
    const value = previewDocumentUrl(documentOrigin, {
      workspaceId,
      route: "/?q=one",
    });
    assert.equal(value.origin, documentOrigin.origin, workspaceId);
  }
});

test("confinement: document policy unchanged after media addition", async () => {
  const { run } = await installWith("sbp1.probe-token");
  const first = await run(
    fakeRequest(document.href, {
      resourceType: "document",
      headers: { cookie: "slaif_session=sas2_stolen" },
    }),
  );
  assert.equal(first.route.actions.length, 1);
  assert.equal(first.route.actions[0].kind, "continue");
  assert.equal(
    first.route.actions[0].opts.headers["x-slaif-browser-preview"],
    "sbp1.probe-token",
  );
  assert.equal(first.route.actions[0].opts.headers.cookie, undefined);
  const second = await run(fakeRequest(document.href, { resourceType: "document" }));
  assert.equal(second.blocked, 1);
  assert.equal(second.route.actions[0].kind, "abort");
});
