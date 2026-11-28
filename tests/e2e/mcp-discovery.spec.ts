import { expect, type APIRequestContext, type Page, test } from "@playwright/test";

import { expectAdminUsable, login, observe, secrets } from "./support";

const PROTOCOL_VERSION = "2026-07-28";
const MCP_ENDPOINT = "/mcp/";

type DiscoveryFacts = {
  site_id: string;
  workspace_id: string;
  scopes: string[];
  request_quota: number;
  component_catalog_version: string;
  composition_schema_version: string;
  content_model_schema_version: string;
  resource_constraints: Record<string, unknown>;
  source_origins: string[];
  mutation_quota: number;
  delete_quota: number;
  upload_quota: number;
};

interface McpErrorPayload {
  jsonrpc: string;
  error: { code: number; message: string };
}

interface McpOptions {
  method: string;
  id?: number | string;
  params?: Record<string, unknown>;
  token?: string;
  omitToken?: boolean;
  malformedToken?: string;
  protocolHeader?: string;
  nameHeader?: string;
  origin?: string;
}

function firstDefined<T>(value: T | undefined, label: string): T {
  if (value === undefined) throw new Error(`${label} is missing`);
  return value;
}

function mcpBody(options: McpOptions) {
  // io.modelcontextprotocol/* keys in options.params override the default
  // _meta values; every other key is a sibling of _meta inside params.
  const extra = options.params ?? {};
  const meta: Record<string, unknown> = {
    "io.modelcontextprotocol/protocolVersion":
      extra["io.modelcontextprotocol/protocolVersion"] ?? PROTOCOL_VERSION,
    "io.modelcontextprotocol/clientInfo": {
      name: "slaif-e2e",
      version: "1.0.0",
    },
    "io.modelcontextprotocol/clientCapabilities":
      extra["io.modelcontextprotocol/clientCapabilities"] ?? {},
  };
  const params: Record<string, unknown> = { _meta: meta };
  for (const [key, value] of Object.entries(extra)) {
    if (!key.startsWith("io.modelcontextprotocol/")) {
      params[key] = value;
    }
  }
  return {
    jsonrpc: "2.0",
    id: options.id ?? 1,
    method: options.method,
    params,
  };
}

async function mcp(
  context: APIRequestContext,
  options: McpOptions,
): Promise<import("@playwright/test").APIResponse> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json, text/event-stream",
    "MCP-Protocol-Version": options.protocolHeader ?? PROTOCOL_VERSION,
    "Mcp-Method": options.method,
  };
  const paramName = options.params?.name;
  if (options.nameHeader !== undefined) {
    headers["Mcp-Name"] = options.nameHeader;
  } else if (
    options.method === "tools/call" &&
    typeof paramName === "string" &&
    paramName
  ) {
    headers["Mcp-Name"] = paramName;
  }
  if (options.origin !== undefined) headers.Origin = options.origin;
  if (options.malformedToken !== undefined) {
    headers.Authorization = options.malformedToken;
  } else if (options.token !== undefined) {
    headers.Authorization = `Bearer ${options.token}`;
  }
  return context.post(MCP_ENDPOINT, { headers, data: mcpBody(options) });
}

async function restSession(
  context: APIRequestContext,
  token?: string,
): Promise<import("@playwright/test").APIResponse> {
  const headers: Record<string, string> = {};
  if (token !== undefined) headers.Authorization = `Bearer ${token}`;
  return context.get("/api/agent/v1/session", { headers });
}

async function createAgentSession(
  page: Page,
  preset: string,
  title: string,
  quota?: string,
): Promise<string> {
  await page.getByLabel("Delegation preset").selectOption(preset);
  await page.getByLabel("Session title").fill(title);
  if (quota !== undefined) {
    await page.locator("#agent-session-quota").fill(quota);
  }
  await page.getByRole("button", { name: "Create Agent session" }).click();
  const secret = page.locator(".one-time-secret code");
  await expect(secret).toHaveText(/^sas2_[^\s]+$/);
  const token = (await secret.textContent()) ?? "";
  expect(token).toMatch(/^sas2_[^\s]+$/);
  await page.getByRole("button", { name: "Dismiss" }).click();
  await expect(page.locator(".one-time-secret")).toHaveCount(0);
  return token;
}

async function revokeSessionByTitle(page: Page, title: string) {
  const row = page
    .locator("li")
    .filter({ has: page.getByText(title, { exact: true }) })
    .first();
  await row.getByRole("button", { name: "Revoke" }).click();
  await expect(row).toContainText("REVOKED");
}

async function gotoDemoSite(page: Page) {
  const siteLink = page.getByRole("link", { name: /SLAIF Demo Site/ }).first();
  const href = await siteLink.getAttribute("href");
  expect(href).toMatch(/^\/admin\/sites\/[0-9a-f-]+$/);
  await page.goto(href!);
  await expectAdminUsable(page);
}

test("mcp-capability-bound-discovery-list-and-call-through-nginx", async ({ page }) => {
  const credential = secrets();
  const failures = observe(page);
  await login(page, credential);
  await gotoDemoSite(page);
  const title = `E2E MCP session ${test.info().project.name}`;
  // Finite budget: the REST comparator plus discover, list, call,
  // and one more REST request; the sixth request must get 429.
  const token = await createAgentSession(page, "L1_CONTENT_EDITOR", title, "5");

  const restA = await restSession(page.request, token);
  expect(restA.status()).toBe(200);
  const factsA = (await restA.json()) as DiscoveryFacts;
  // request_quota is the fixed configured cap, not a remaining count.
  expect(factsA.request_quota).toBe(5);

  const discover = await mcp(page.request, {
    method: "server/discover",
    id: "e2e-discover",
    token,
  });
  expect(discover.status()).toBe(200);
  expect(discover.headers()["cache-control"]).toBe("no-store");
  const discoverPayload = (await discover.json()) as {
    jsonrpc: string;
    id: string;
    result: {
      resultType: string;
      supportedVersions: string[];
      capabilities: Record<string, unknown>;
      _meta: {
        "io.modelcontextprotocol/serverInfo": { name: string; version: string };
      };
      ttlMs: number;
      cacheScope: string;
    };
  };
  expect(discoverPayload.jsonrpc).toBe("2.0");
  expect(discoverPayload.id).toBe("e2e-discover");
  expect(discoverPayload.result.resultType).toBe("complete");
  expect(discoverPayload.result.supportedVersions).toEqual([PROTOCOL_VERSION]);
  expect(discoverPayload.result.capabilities).toEqual({ tools: {} });
  expect(
    discoverPayload.result._meta["io.modelcontextprotocol/serverInfo"].name,
  ).toBeTruthy();
  expect(
    discoverPayload.result._meta["io.modelcontextprotocol/serverInfo"].version,
  ).toBe(PROTOCOL_VERSION);
  expect(discoverPayload.result.ttlMs).toBe(0);
  expect(discoverPayload.result.cacheScope).toBe("private");

  const list = await mcp(page.request, { method: "tools/list", token });
  expect(list.status()).toBe(200);
  const listPayload = (await list.json()) as {
    result: {
      resultType: string;
      ttlMs: number;
      cacheScope: string;
      tools: Array<{
        name: string;
        inputSchema: Record<string, unknown>;
        annotations: Record<string, boolean>;
      }>;
    };
  };
  expect(listPayload.result.resultType).toBe("complete");
  expect(listPayload.result.ttlMs).toBe(0);
  expect(listPayload.result.cacheScope).toBe("private");
  expect(listPayload.result.tools).toHaveLength(1);
  const tool = firstDefined(listPayload.result.tools[0], "declared tool");
  expect(tool.name).toBe("site.describe");
  expect(tool.inputSchema).toEqual({
    type: "object",
    additionalProperties: false,
  });
  expect(tool.annotations.readOnlyHint).toBe(true);

  const call = await mcp(page.request, {
    method: "tools/call",
    params: { name: "site.describe" },
    token,
  });
  expect(call.status()).toBe(200);
  const callPayload = (await call.json()) as {
    result: {
      resultType: string;
      isError: boolean;
      structuredContent: DiscoveryFacts;
      content: Array<{ type: string; text: string }>;
    };
  };
  expect(callPayload.result.resultType).toBe("complete");
  expect(callPayload.result.isError).toBe(false);
  const structured = callPayload.result.structuredContent;
  expect(structured.site_id).toBe(factsA.site_id);
  expect(structured.workspace_id).toBe(factsA.workspace_id);
  expect(structured.scopes).toEqual(factsA.scopes);
  expect(structured.component_catalog_version).toBe(factsA.component_catalog_version);
  expect(structured.composition_schema_version).toBe(factsA.composition_schema_version);
  expect(structured.content_model_schema_version).toBe(
    factsA.content_model_schema_version,
  );
  expect(structured.resource_constraints).toEqual(factsA.resource_constraints);
  expect(structured.source_origins).toEqual(factsA.source_origins);
  expect(structured.request_quota).toBe(factsA.request_quota);
  const contentEntry = firstDefined(
    callPayload.result.content[0],
    "text content entry",
  );
  expect(JSON.parse(contentEntry.text)).toEqual(structured);

  // Each valid request (REST or MCP) consumes the discovery resource
  // exactly once: restA, discover, list, call, restB are the five
  // valid requests of the budget, and the configured cap stays
  // unchanged across them.
  const restB = await restSession(page.request, token);
  expect(restB.status()).toBe(200);
  const factsB = (await restB.json()) as DiscoveryFacts;
  expect(factsB.request_quota).toBe(factsA.request_quota);

  // The sixth valid request is refused: exactly five succeeded.
  const restC = await restSession(page.request, token);
  expect(restC.status()).toBe(429);
  // The REST 429 uses the product error envelope, not JSON-RPC.
  const restCErrors = (await restC.json()) as { error: { code: string } };
  expect(restCErrors.error.code).toBe("QUOTA_EXCEEDED");

  // Pre-dispatch refusals never reach quota or upstream, even after
  // the budget is exhausted.
  const forbiddenArgs = await mcp(page.request, {
    method: "tools/call",
    params: { name: "site.describe", arguments: { site_id: factsA.site_id } },
    token,
  });
  expect(forbiddenArgs.status()).toBe(400);
  expect(((await forbiddenArgs.json()) as McpErrorPayload).error.code).toBe(-32602);
  const unknownTool = await mcp(page.request, {
    method: "tools/call",
    params: { name: "site.list" },
    nameHeader: "site.list",
    token,
  });
  expect(unknownTool.status()).toBe(400);
  const unknownError = (await unknownTool.json()) as McpErrorPayload;
  expect(unknownError.error.code).toBe(-32602);
  expect(unknownError.error.message).toBe("Unknown tool: site.list");

  // Protocol metadata refusals.
  const mismatch = await mcp(page.request, {
    method: "server/discover",
    token,
    params: {
      "io.modelcontextprotocol/protocolVersion": "2025-03-26",
      "io.modelcontextprotocol/clientCapabilities": {},
    },
  });
  expect(mismatch.status()).toBe(400);
  expect(((await mismatch.json()) as McpErrorPayload).error.code).toBe(-32020);
  const unsupported = await mcp(page.request, {
    method: "server/discover",
    token,
    protocolHeader: "2025-03-26",
    params: {
      "io.modelcontextprotocol/protocolVersion": "2025-03-26",
      "io.modelcontextprotocol/clientCapabilities": {},
    },
  });
  expect(unsupported.status()).toBe(400);
  const unsupportedError = (await unsupported.json()) as McpErrorPayload & {
    error: { code: number; data: { supported: string[]; requested: string } };
  };
  expect(unsupportedError.error.code).toBe(-32022);
  expect(unsupportedError.error.data).toEqual({
    supported: [PROTOCOL_VERSION],
    requested: "2025-03-26",
  });

  // Retired routes stay unavailable publicly (edge strips /mcp/ to the
  // adapter root; the legacy /mcp/v1 surface is gone).
  const legacyCall = await page.request.post("/mcp/v1/call", {
    data: { tool: "site.describe" },
  });
  expect(legacyCall.status()).toBe(404);
  const legacyTools = await page.request.get("/mcp/v1/tools");
  expect(legacyTools.status()).toBe(404);
  const legacyHealth = await page.request.get("/mcp/v1/health/live");
  expect(legacyHealth.status()).toBe(404);
  const getEndpoint = await page.request.get(MCP_ENDPOINT);
  expect(getEndpoint.status()).toBe(405);
  const ready = await page.request.get("/mcp/health/ready");
  expect(ready.status()).toBe(200);

  // Real revocation refuses subsequent calls on the same token.
  await revokeSessionByTitle(page, title);
  const revokedCall = await mcp(page.request, {
    method: "tools/call",
    params: { name: "site.describe" },
    token,
  });
  expect(revokedCall.status()).toBe(401);
  expect(((await revokedCall.json()) as McpErrorPayload).error.code).toBe(-32600);
  expect(revokedCall.headers()["www-authenticate"]).toBe("Bearer");
  const revokedBody = await revokedCall.text();
  expect(
    revokedBody.includes(token),
    "revoked response must not echo the credential",
  ).toBe(false);
  const revokedRest = await restSession(page.request, token);
  expect(revokedRest.status()).toBe(401);

  // Absent and malformed credentials.
  const absent = await mcp(page.request, {
    method: "server/discover",
    omitToken: true,
  });
  expect(absent.status()).toBe(401);
  expect(absent.headers()["www-authenticate"]).toBe("Bearer");
  const malformed = await mcp(page.request, {
    method: "server/discover",
    malformedToken: "Bearer",
  });
  expect(malformed.status()).toBe(401);

  expect(failures()).toEqual([]);
});

test("mcp-per-request-authority-follows-its-own-capability", async ({ page }) => {
  const credential = secrets();
  const failures = observe(page);
  await login(page, credential);
  await gotoDemoSite(page);
  const titleOne = `E2E MCP L1 ${test.info().project.name}`;
  const titleTwo = `E2E MCP L4 ${test.info().project.name}`;
  const tokenOne = await createAgentSession(page, "L1_CONTENT_EDITOR", titleOne);
  await page.getByLabel("Delegation preset").selectOption("L4_SITE_ARCHITECT");
  await page.getByLabel("Session title").fill(titleTwo);
  await page.getByText("Advanced source and resource restrictions").click();
  await page.getByLabel("Approved HTTP(S) origin").fill("https://example.com");
  await page
    .getByLabel("Resource constraints (JSON)")
    .fill('{"max_content_types":100}');
  await page.getByRole("button", { name: "Create Agent session" }).click();
  const secret = page.locator(".one-time-secret code");
  await expect(secret).toHaveText(/^sas2_[^\s]+$/);
  const tokenTwo = (await secret.textContent()) ?? "";
  await page.getByRole("button", { name: "Dismiss" }).click();

  const restOne = await restSession(page.request, tokenOne);
  expect(restOne.status()).toBe(200);
  const factsOne = (await restOne.json()) as DiscoveryFacts;
  const restTwo = await restSession(page.request, tokenTwo);
  expect(restTwo.status()).toBe(200);
  const factsTwo = (await restTwo.json()) as DiscoveryFacts;
  expect(factsTwo.workspace_id).not.toBe(factsOne.workspace_id);
  expect(factsTwo.scopes).toContain("content-model:create");

  const callOne = await mcp(page.request, {
    method: "tools/call",
    params: { name: "site.describe" },
    token: tokenOne,
  });
  expect(callOne.status()).toBe(200);
  const one = (
    (await callOne.json()) as {
      result: { structuredContent: DiscoveryFacts };
    }
  ).result.structuredContent;
  expect(one.workspace_id).toBe(factsOne.workspace_id);
  expect(one.scopes).toEqual(factsOne.scopes);

  const callTwo = await mcp(page.request, {
    method: "tools/call",
    params: { name: "site.describe" },
    token: tokenTwo,
  });
  expect(callTwo.status()).toBe(200);
  const two = (
    (await callTwo.json()) as {
      result: { structuredContent: DiscoveryFacts };
    }
  ).result.structuredContent;
  expect(two.workspace_id).toBe(factsTwo.workspace_id);
  expect(two.scopes).toEqual(factsTwo.scopes);
  expect(two.resource_constraints).toEqual({ max_content_types: 100 });

  // Revoking the second capability does not disturb the first.
  await revokeSessionByTitle(page, titleTwo);
  const revokedTwo = await mcp(page.request, {
    method: "tools/call",
    params: { name: "site.describe" },
    token: tokenTwo,
  });
  expect(revokedTwo.status()).toBe(401);
  const stillOne = await mcp(page.request, {
    method: "tools/call",
    params: { name: "site.describe" },
    token: tokenOne,
  });
  expect(stillOne.status()).toBe(200);

  expect(failures()).toEqual([]);
});

test("mcp-bounded-request-quota-exhaustion-preserves-429", async ({ page }) => {
  const credential = secrets();
  const failures = observe(page);
  await login(page, credential);
  await gotoDemoSite(page);
  const title = `E2E MCP quota ${test.info().project.name}`;
  const token = await createAgentSession(page, "L1_CONTENT_EDITOR", title, "1");

  // Quota one, no REST comparator first: the first legitimate MCP
  // call must succeed (it consumes the single request), then both
  // the next MCP call and the REST comparator return 429.
  const first = await mcp(page.request, {
    method: "tools/call",
    params: { name: "site.describe" },
    token,
  });
  expect(first.status()).toBe(200);
  const firstPayload = (await first.json()) as {
    result: { structuredContent: DiscoveryFacts };
  };
  // The configured cap, not a remaining count.
  expect(firstPayload.result.structuredContent.request_quota).toBe(1);

  const second = await mcp(page.request, {
    method: "tools/call",
    params: { name: "site.describe" },
    token,
  });
  expect(second.status()).toBe(429);
  expect(((await second.json()) as McpErrorPayload).error.code).toBe(-32600);

  const restAfter = await restSession(page.request, token);
  expect(restAfter.status()).toBe(429);

  expect(failures()).toEqual([]);
});
