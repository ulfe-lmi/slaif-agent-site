/**
 * Immutable browser preview-run contracts.
 *
 * These contracts describe data only. They do not provide a route, credential,
 * dispatcher, browser process, filesystem, or publication authority.
 */

export const BROWSER_CONTRACT_VERSION = "browser-preview/v1" as const;

export const BROWSER_TARGETS = Object.freeze([
  "desktop-chromium",
  "tablet",
  "mobile-chromium",
] as const);
export type BrowserTarget = (typeof BROWSER_TARGETS)[number];

export const BROWSER_EVIDENCE = Object.freeze([
  "screenshot",
  "accessibility-summary",
  "structure-summary",
  "heading-summary",
  "link-summary",
  "media-summary",
  "overflow-summary",
  "console-summary",
  "failed-request-summary",
] as const);
export type BrowserEvidence = (typeof BROWSER_EVIDENCE)[number];

export const BROWSER_RUN_STATES = Object.freeze([
  "QUEUED",
  "RUNNING",
  "COMPLETED",
  "FAILED",
  "TIMED_OUT",
  "CANCELLED",
] as const);
export type BrowserRunState = (typeof BROWSER_RUN_STATES)[number];

export const BROWSER_TERMINAL_STATES = Object.freeze([
  "COMPLETED",
  "FAILED",
  "TIMED_OUT",
  "CANCELLED",
] as const);
export type BrowserTerminalState = (typeof BROWSER_TERMINAL_STATES)[number];

export const BROWSER_CONTRACT_BOUNDS = Object.freeze({
  routeBytes: 2048,
  evidenceItems: 9,
  summaryProperties: 32,
  summaryBytes: 16_384,
  errorCodeCharacters: 64,
  errorMessageCharacters: 512,
  artifactItems: 16,
  artifactBytes: 1_073_741_824,
  durationSeconds: 600,
  attempts: 5,
} as const);

export const BROWSER_PREVIEW_CREDENTIAL_FACTS = Object.freeze({
  tokenVersion: "sbp1",
  algorithm: "HS256",
  type: "SLAIF-BROWSER-PREVIEW",
  audience: "slaif-render-browser-preview",
  deployment: "slaif-agent-site",
  browserHeader: "X-SLAIF-Browser-Preview",
  renderHeader: "X-SLAIF-Browser-Run-Token",
  maxTokenBytes: 4096,
  maxTtlSeconds: 60,
  claims: Object.freeze([
    "deployment",
    "audience",
    "contract_version",
    "capability_id",
    "site_id",
    "workspace_id",
    "run_id",
    "route",
    "target",
    "evidence",
    "artifact_bytes_limit",
    "duration_seconds",
    "issued_at",
    "expires_at",
    "nonce",
    "key_id",
  ]),
} as const);

const targetSet = new Set<string>(BROWSER_TARGETS);
const evidenceSet = new Set<string>(BROWSER_EVIDENCE);
const evidenceOrder = new Map<string, number>(
  BROWSER_EVIDENCE.map((item, index) => [item, index]),
);

export interface PreviewRunCreateRequest {
  readonly version: typeof BROWSER_CONTRACT_VERSION;
  readonly route: string;
  readonly target: BrowserTarget;
  readonly evidence: readonly BrowserEvidence[];
}

export interface PreviewRunStatus {
  readonly version: typeof BROWSER_CONTRACT_VERSION;
  readonly runId: string;
  readonly state: BrowserRunState;
  readonly route: string;
  readonly target: BrowserTarget;
  readonly evidence: readonly BrowserEvidence[];
  readonly createdAt: string;
  readonly startedAt: string | null;
  readonly completedAt: string | null;
  readonly expiresAt: string;
}

export interface BrowserRunError {
  readonly code: string;
  readonly message: string;
}

export interface PrivateBrowserArtifactMetadata {
  readonly version: typeof BROWSER_CONTRACT_VERSION;
  readonly artifactId: string;
  readonly runId: string;
  readonly kind: BrowserEvidence;
  readonly mimeType: "image/png" | "application/json" | "text/plain";
  readonly sha256: string;
  readonly sizeBytes: number;
  readonly target: BrowserTarget;
  readonly routeDigest: string;
  readonly createdAt: string;
  readonly expiresAt: string;
  readonly visibility: "PRIVATE";
}

export interface PreviewRunResult {
  readonly version: typeof BROWSER_CONTRACT_VERSION;
  readonly runId: string;
  readonly state: BrowserTerminalState;
  readonly summary: Readonly<Record<string, unknown>>;
  readonly error: BrowserRunError | null;
  readonly artifacts: readonly PrivateBrowserArtifactMetadata[];
  readonly completedAt: string;
}

export interface InternalPreviewRunSpecification {
  readonly version: typeof BROWSER_CONTRACT_VERSION;
  readonly runId: string;
  readonly operationId: string;
  readonly siteId: string;
  readonly workspaceId: string;
  readonly capabilityId: string;
  readonly delegatorId: string;
  readonly route: string;
  readonly routeDigest: string;
  readonly target: BrowserTarget;
  readonly evidence: readonly BrowserEvidence[];
  readonly reservedScreenshots: number;
  readonly reservedArtifactBytes: number;
  readonly maxDurationSeconds: number;
  readonly attempt: number;
}

export interface BrowserRunLease {
  readonly version: typeof BROWSER_CONTRACT_VERSION;
  readonly runId: string;
  readonly leaseId: string;
  readonly attempt: number;
  readonly expiresAt: string;
}

export interface BrowserRunCompletion {
  readonly version: typeof BROWSER_CONTRACT_VERSION;
  readonly runId: string;
  readonly leaseId: string;
  readonly state: BrowserTerminalState;
  readonly summary: Readonly<Record<string, unknown>>;
  readonly error: BrowserRunError | null;
}

export class BrowserContractError extends Error {
  public constructor(message: string) {
    super(message);
    this.name = "BrowserContractError";
  }
}

function hasExactKeys(
  value: Record<string, unknown>,
  expected: readonly string[],
): boolean {
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  return (
    actual.length === wanted.length &&
    actual.every((key, index) => key === wanted[index])
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function validateRoute(route: unknown): string {
  if (typeof route !== "string") {
    throw new BrowserContractError("route must be a string");
  }
  const bytes = new TextEncoder().encode(route).byteLength;
  if (bytes === 0 || bytes > BROWSER_CONTRACT_BOUNDS.routeBytes) {
    throw new BrowserContractError("route is empty or oversized");
  }
  if (!route.startsWith("/") || route.startsWith("//")) {
    throw new BrowserContractError("route must be an origin-relative path");
  }
  if (
    route.includes("#") ||
    [...route].some((character) => {
      const codePoint = character.codePointAt(0) ?? 0;
      return codePoint <= 0x20 || codePoint === 0x7f || character === "\\";
    })
  ) {
    throw new BrowserContractError("route contains a fragment or unsafe character");
  }
  if (/%(?:2f|5c)/iu.test(route)) {
    throw new BrowserContractError("route contains an encoded path separator");
  }
  const rawPath = route.split("?", 1)[0] ?? route;
  let decodedPath: string;
  try {
    decodedPath = decodeURIComponent(rawPath);
  } catch {
    throw new BrowserContractError("route contains malformed escaping");
  }
  if (
    decodedPath.split("/").some((segment) => segment === "." || segment === "..") ||
    decodedPath.includes("//")
  ) {
    throw new BrowserContractError("route contains traversal or duplicate separators");
  }
  let parsed: URL;
  try {
    parsed = new URL(route, "https://bound-preview.invalid");
  } catch {
    throw new BrowserContractError("route is malformed");
  }
  if (parsed.origin !== "https://bound-preview.invalid") {
    throw new BrowserContractError("route contains an origin or authority");
  }
  for (const [key, value] of parsed.searchParams) {
    const normalizedKey = key.toLowerCase().replaceAll(/[^a-z0-9]/gu, "");
    if (
      /(token|secret|credential|password|cookie|authorization|apikey|accesskey|signature)/u.test(
        normalizedKey,
      ) ||
      /sas2_[0-9a-f]+_/iu.test(value)
    ) {
      throw new BrowserContractError("route query contains credential-shaped data");
    }
  }
  const encoded = (value: string) =>
    encodeURIComponent(value)
      .replaceAll(
        /[!'()*]/gu,
        (character) => `%${character.codePointAt(0)?.toString(16).toUpperCase() ?? ""}`,
      )
      .replaceAll("%20", "+");
  const query = [...parsed.searchParams]
    .sort(([leftKey, leftValue], [rightKey, rightValue]) =>
      leftKey === rightKey
        ? leftValue.localeCompare(rightValue)
        : leftKey.localeCompare(rightKey),
    )
    .map(([key, value]) => `${encoded(key)}=${encoded(value)}`)
    .join("&");
  return rawPath + (query ? `?${query}` : "");
}

export function parsePreviewRunCreateRequest(value: unknown): PreviewRunCreateRequest {
  if (
    !isRecord(value) ||
    !hasExactKeys(value, ["version", "route", "target", "evidence"])
  ) {
    throw new BrowserContractError("create request has unknown or missing fields");
  }
  if (value.version !== BROWSER_CONTRACT_VERSION) {
    throw new BrowserContractError("unsupported contract version");
  }
  if (typeof value.target !== "string" || !targetSet.has(value.target)) {
    throw new BrowserContractError("unsupported browser target");
  }
  if (
    !Array.isArray(value.evidence) ||
    value.evidence.length === 0 ||
    value.evidence.length > BROWSER_CONTRACT_BOUNDS.evidenceItems ||
    !value.evidence.every(
      (item) => typeof item === "string" && evidenceSet.has(item),
    ) ||
    new Set(value.evidence).size !== value.evidence.length
  ) {
    throw new BrowserContractError(
      "evidence must be a unique bounded allowlisted list",
    );
  }
  return Object.freeze({
    version: BROWSER_CONTRACT_VERSION,
    route: validateRoute(value.route),
    target: value.target as BrowserTarget,
    evidence: Object.freeze([...(value.evidence as BrowserEvidence[])]),
  });
}

export function canonicalSerializePreviewRunRequest(value: unknown): string {
  const request = parsePreviewRunCreateRequest(value);
  const evidence = [...request.evidence].sort(
    (left, right) => (evidenceOrder.get(left) ?? 0) - (evidenceOrder.get(right) ?? 0),
  );
  return JSON.stringify({
    evidence,
    route: request.route,
    target: request.target,
    version: request.version,
  });
}

export async function previewRunRequestDigest(value: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(canonicalSerializePreviewRunRequest(value));
  const digest = await globalThis.crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

const stringSchema = (maxLength: number) =>
  Object.freeze({ type: "string", minLength: 1, maxLength } as const);
const idSchema = Object.freeze({
  type: "string",
  pattern: "^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
} as const);
const digestSchema = Object.freeze({
  type: "string",
  pattern: "^[0-9a-f]{64}$",
} as const);
const dateTimeSchema = Object.freeze({ type: "string", format: "date-time" } as const);
const nullableDateTimeSchema = Object.freeze({
  type: Object.freeze(["string", "null"]),
  format: "date-time",
} as const);
const routeSchema = stringSchema(BROWSER_CONTRACT_BOUNDS.routeBytes);
const targetSchema = Object.freeze({ enum: BROWSER_TARGETS });
const evidenceSchema = Object.freeze({
  type: "array",
  minItems: 1,
  maxItems: BROWSER_CONTRACT_BOUNDS.evidenceItems,
  uniqueItems: true,
  items: Object.freeze({ enum: BROWSER_EVIDENCE }),
} as const);
const summarySchema = Object.freeze({
  type: "object",
  maxProperties: BROWSER_CONTRACT_BOUNDS.summaryProperties,
  "x-maxSerializedBytes": BROWSER_CONTRACT_BOUNDS.summaryBytes,
} as const);
const errorSchema = Object.freeze({
  type: "object",
  additionalProperties: false,
  required: Object.freeze(["code", "message"]),
  properties: Object.freeze({
    code: Object.freeze({
      type: "string",
      pattern: "^[A-Z][A-Z0-9_]{0,63}$",
      maxLength: BROWSER_CONTRACT_BOUNDS.errorCodeCharacters,
    }),
    message: stringSchema(BROWSER_CONTRACT_BOUNDS.errorMessageCharacters),
  }),
} as const);
const nullableErrorSchema = Object.freeze({
  anyOf: Object.freeze([errorSchema, Object.freeze({ type: "null" })]),
} as const);
const artifactSchema = Object.freeze({
  type: "object",
  additionalProperties: false,
  required: Object.freeze([
    "version",
    "artifactId",
    "runId",
    "kind",
    "mimeType",
    "sha256",
    "sizeBytes",
    "target",
    "routeDigest",
    "createdAt",
    "expiresAt",
    "visibility",
  ]),
  properties: Object.freeze({
    version: Object.freeze({ const: BROWSER_CONTRACT_VERSION }),
    artifactId: idSchema,
    runId: idSchema,
    kind: Object.freeze({ enum: BROWSER_EVIDENCE }),
    mimeType: Object.freeze({
      enum: Object.freeze(["image/png", "application/json", "text/plain"]),
    }),
    sha256: digestSchema,
    sizeBytes: Object.freeze({
      type: "integer",
      minimum: 1,
      maximum: BROWSER_CONTRACT_BOUNDS.artifactBytes,
    }),
    target: targetSchema,
    routeDigest: digestSchema,
    createdAt: dateTimeSchema,
    expiresAt: dateTimeSchema,
    visibility: Object.freeze({ const: "PRIVATE" }),
  }),
} as const);

export const BROWSER_CONTRACT_SCHEMAS = Object.freeze({
  previewRunCreateRequest: Object.freeze({
    type: "object",
    additionalProperties: false,
    required: Object.freeze(["version", "route", "target", "evidence"]),
    properties: Object.freeze({
      version: Object.freeze({ const: BROWSER_CONTRACT_VERSION }),
      route: routeSchema,
      target: targetSchema,
      evidence: evidenceSchema,
    }),
  }),
  previewRunStatus: Object.freeze({
    type: "object",
    additionalProperties: false,
    required: Object.freeze([
      "version",
      "runId",
      "state",
      "route",
      "target",
      "evidence",
      "createdAt",
      "startedAt",
      "completedAt",
      "expiresAt",
    ]),
    properties: Object.freeze({
      version: Object.freeze({ const: BROWSER_CONTRACT_VERSION }),
      runId: idSchema,
      state: Object.freeze({ enum: BROWSER_RUN_STATES }),
      route: routeSchema,
      target: targetSchema,
      evidence: evidenceSchema,
      createdAt: dateTimeSchema,
      startedAt: nullableDateTimeSchema,
      completedAt: nullableDateTimeSchema,
      expiresAt: dateTimeSchema,
    }),
  }),
  previewRunResult: Object.freeze({
    type: "object",
    additionalProperties: false,
    required: Object.freeze([
      "version",
      "runId",
      "state",
      "summary",
      "error",
      "artifacts",
      "completedAt",
    ]),
    properties: Object.freeze({
      version: Object.freeze({ const: BROWSER_CONTRACT_VERSION }),
      runId: idSchema,
      state: Object.freeze({ enum: BROWSER_TERMINAL_STATES }),
      summary: summarySchema,
      error: nullableErrorSchema,
      artifacts: Object.freeze({
        type: "array",
        maxItems: BROWSER_CONTRACT_BOUNDS.artifactItems,
        items: artifactSchema,
      }),
      completedAt: dateTimeSchema,
    }),
  }),
  privateArtifactMetadata: artifactSchema,
  internalRunSpecification: Object.freeze({
    type: "object",
    additionalProperties: false,
    required: Object.freeze([
      "version",
      "runId",
      "operationId",
      "siteId",
      "workspaceId",
      "capabilityId",
      "delegatorId",
      "route",
      "routeDigest",
      "target",
      "evidence",
      "reservedScreenshots",
      "reservedArtifactBytes",
      "maxDurationSeconds",
      "attempt",
    ]),
    properties: Object.freeze({
      version: Object.freeze({ const: BROWSER_CONTRACT_VERSION }),
      runId: idSchema,
      operationId: idSchema,
      siteId: idSchema,
      workspaceId: idSchema,
      capabilityId: idSchema,
      delegatorId: idSchema,
      route: routeSchema,
      routeDigest: digestSchema,
      target: targetSchema,
      evidence: evidenceSchema,
      reservedScreenshots: Object.freeze({
        type: "integer",
        minimum: 0,
        maximum: 1,
      }),
      reservedArtifactBytes: Object.freeze({
        type: "integer",
        minimum: 0,
        maximum: BROWSER_CONTRACT_BOUNDS.artifactBytes,
      }),
      maxDurationSeconds: Object.freeze({
        type: "integer",
        minimum: 5,
        maximum: BROWSER_CONTRACT_BOUNDS.durationSeconds,
      }),
      attempt: Object.freeze({
        type: "integer",
        minimum: 1,
        maximum: BROWSER_CONTRACT_BOUNDS.attempts,
      }),
    }),
  }),
  runLease: Object.freeze({
    type: "object",
    additionalProperties: false,
    required: Object.freeze(["version", "runId", "leaseId", "attempt", "expiresAt"]),
    properties: Object.freeze({
      version: Object.freeze({ const: BROWSER_CONTRACT_VERSION }),
      runId: idSchema,
      leaseId: idSchema,
      attempt: Object.freeze({
        type: "integer",
        minimum: 1,
        maximum: BROWSER_CONTRACT_BOUNDS.attempts,
      }),
      expiresAt: dateTimeSchema,
    }),
  }),
  runCompletion: Object.freeze({
    type: "object",
    additionalProperties: false,
    required: Object.freeze([
      "version",
      "runId",
      "leaseId",
      "state",
      "summary",
      "error",
    ]),
    properties: Object.freeze({
      version: Object.freeze({ const: BROWSER_CONTRACT_VERSION }),
      runId: idSchema,
      leaseId: idSchema,
      state: Object.freeze({ enum: BROWSER_TERMINAL_STATES }),
      summary: summarySchema,
      error: nullableErrorSchema,
    }),
  }),
} as const);

export const packageMetadata = Object.freeze({
  name: "@slaif-agent-site/browser-tool-contracts",
  status: "typed-preview-contracts",
  version: BROWSER_CONTRACT_VERSION,
} as const);
