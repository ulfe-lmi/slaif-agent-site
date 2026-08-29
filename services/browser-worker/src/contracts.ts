import { createHash } from "node:crypto";

import {
  BROWSER_CONTRACT_BOUNDS,
  BROWSER_EVIDENCE,
  BROWSER_TARGETS,
  BROWSER_WORKER_BOUNDS,
  BROWSER_WORKER_CONTRACT_VERSION,
  BROWSER_WORKER_DEPLOYMENT,
  canonicalJson,
  normalizeBrowserPreviewRoute,
  type BrowserEvidence,
  type BrowserTarget,
  type BrowserWorkerArtifactRetrievalRequest,
  type BrowserWorkerInspectionRequest,
  type BrowserWorkerSubmitRequest,
} from "@slaif-agent-site/browser-tool-contracts";

const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/u;
const digestPattern = /^[0-9a-f]{64}$/u;
const previewCredentialPattern = /^sbp1(?:\.[A-Za-z0-9_-]+){3}$/u;
const targetSet = new Set<string>(BROWSER_TARGETS);
const evidenceSet = new Set<string>(BROWSER_EVIDENCE);

export class WorkerContractError extends Error {
  public constructor(message = "browser worker request is invalid") {
    super(message);
    this.name = "WorkerContractError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function exactKeys(value: Record<string, unknown>, expected: readonly string[]): void {
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (
    actual.length !== wanted.length ||
    actual.some((key, index) => key !== wanted[index])
  )
    throw new WorkerContractError();
}

function exactUuid(value: unknown): string {
  if (typeof value !== "string" || !uuidPattern.test(value)) {
    throw new WorkerContractError();
  }
  return value;
}

function exactDigest(value: unknown): string {
  if (typeof value !== "string" || !digestPattern.test(value)) {
    throw new WorkerContractError();
  }
  return value;
}

function exactInteger(value: unknown, minimum: number, maximum: number): number {
  if (
    !Number.isInteger(value) ||
    (value as number) < minimum ||
    (value as number) > maximum
  )
    throw new WorkerContractError();
  return value as number;
}

function exactTarget(value: unknown): BrowserTarget {
  if (typeof value !== "string" || !targetSet.has(value)) {
    throw new WorkerContractError();
  }
  return value as BrowserTarget;
}

function exactEvidence(value: unknown): readonly BrowserEvidence[] {
  if (
    !Array.isArray(value) ||
    value.length === 0 ||
    value.length > BROWSER_CONTRACT_BOUNDS.evidenceItems ||
    !value.every((item) => typeof item === "string" && evidenceSet.has(item)) ||
    new Set(value).size !== value.length
  )
    throw new WorkerContractError();
  return Object.freeze([...(value as BrowserEvidence[])]);
}

function fixedFacts(value: Record<string, unknown>): void {
  if (
    value.version !== BROWSER_WORKER_CONTRACT_VERSION ||
    value.deployment !== BROWSER_WORKER_DEPLOYMENT
  )
    throw new WorkerContractError();
}

export function parseWorkerSubmitRequest(
  value: unknown,
  now: number,
): BrowserWorkerSubmitRequest {
  if (!isRecord(value)) throw new WorkerContractError();
  exactKeys(value, [
    "version",
    "deployment",
    "requestId",
    "runId",
    "siteId",
    "workspaceId",
    "capabilityId",
    "operationId",
    "leaseId",
    "attempt",
    "route",
    "routeDigest",
    "target",
    "evidence",
    "artifactBytesLimit",
    "durationSeconds",
    "issuedAt",
    "expiresAt",
    "previewCredential",
  ]);
  fixedFacts(value);
  const route = normalizeBrowserPreviewRoute(value.route);
  const routeDigest = exactDigest(value.routeDigest);
  if (createHash("sha256").update(route, "utf8").digest("hex") !== routeDigest) {
    throw new WorkerContractError();
  }
  const issuedAt = exactInteger(value.issuedAt, 0, 4_102_444_800);
  const expiresAt = exactInteger(value.expiresAt, 0, 4_102_444_800);
  if (issuedAt > now + 5 || expiresAt <= now || expiresAt - issuedAt > 60) {
    throw new WorkerContractError();
  }
  if (
    typeof value.previewCredential !== "string" ||
    Buffer.byteLength(value.previewCredential, "utf8") >
      BROWSER_WORKER_BOUNDS.previewCredentialBytes ||
    !previewCredentialPattern.test(value.previewCredential)
  )
    throw new WorkerContractError();
  return Object.freeze({
    version: BROWSER_WORKER_CONTRACT_VERSION,
    deployment: BROWSER_WORKER_DEPLOYMENT,
    requestId: exactUuid(value.requestId),
    runId: exactUuid(value.runId),
    siteId: exactUuid(value.siteId),
    workspaceId: exactUuid(value.workspaceId),
    capabilityId: exactUuid(value.capabilityId),
    operationId: exactUuid(value.operationId),
    leaseId: exactUuid(value.leaseId),
    attempt: exactInteger(value.attempt, 1, BROWSER_CONTRACT_BOUNDS.attempts),
    route,
    routeDigest,
    target: exactTarget(value.target),
    evidence: exactEvidence(value.evidence),
    artifactBytesLimit: exactInteger(
      value.artifactBytesLimit,
      1,
      BROWSER_WORKER_BOUNDS.totalArtifactBytes,
    ),
    durationSeconds: exactInteger(
      value.durationSeconds,
      5,
      BROWSER_WORKER_BOUNDS.durationSeconds,
    ),
    issuedAt,
    expiresAt,
    previewCredential: value.previewCredential,
  });
}

export function parseWorkerInspectionRequest(
  value: unknown,
): BrowserWorkerInspectionRequest {
  if (!isRecord(value)) throw new WorkerContractError();
  exactKeys(value, ["version", "deployment", "requestId"]);
  fixedFacts(value);
  return Object.freeze({
    version: BROWSER_WORKER_CONTRACT_VERSION,
    deployment: BROWSER_WORKER_DEPLOYMENT,
    requestId: exactUuid(value.requestId),
  });
}

export function parseWorkerArtifactRetrievalRequest(
  value: unknown,
): BrowserWorkerArtifactRetrievalRequest {
  if (!isRecord(value)) throw new WorkerContractError();
  exactKeys(value, [
    "version",
    "deployment",
    "requestId",
    "runId",
    "siteId",
    "workspaceId",
    "artifactId",
    "kind",
    "target",
    "routeDigest",
    "sha256",
    "sizeBytes",
  ]);
  fixedFacts(value);
  const evidence = exactEvidence([value.kind]);
  return Object.freeze({
    version: BROWSER_WORKER_CONTRACT_VERSION,
    deployment: BROWSER_WORKER_DEPLOYMENT,
    requestId: exactUuid(value.requestId),
    runId: exactUuid(value.runId),
    siteId: exactUuid(value.siteId),
    workspaceId: exactUuid(value.workspaceId),
    artifactId: exactUuid(value.artifactId),
    kind: evidence[0]!,
    target: exactTarget(value.target),
    routeDigest: exactDigest(value.routeDigest),
    sha256: exactDigest(value.sha256),
    sizeBytes: exactInteger(value.sizeBytes, 1, BROWSER_WORKER_BOUNDS.artifactBytes),
  });
}

export function workerRequestDigest(request: BrowserWorkerSubmitRequest): string {
  return createHash("sha256").update(canonicalJson(request), "utf8").digest("hex");
}
