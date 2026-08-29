import { createHash, createHmac, timingSafeEqual } from "node:crypto";
import { constants } from "node:fs";
import { dirname } from "node:path";
import { open, type FileHandle } from "node:fs/promises";

import {
  BROWSER_WORKER_AUTHENTICATION_HEADER,
  BROWSER_WORKER_RESPONSE_ALGORITHM,
  BROWSER_WORKER_RESPONSE_TYPE,
  BROWSER_WORKER_CONTRACT_VERSION,
  canonicalJson,
  type BrowserWorkerResult,
  type SignedBrowserWorkerResult,
} from "@slaif-agent-site/browser-tool-contracts";

const credentialPattern = /^sbws1:([0-9a-f]{16}):([A-Za-z0-9_-]{43})$/u;

export class WorkerCredentialError extends Error {
  public constructor() {
    super("browser worker credential is unavailable");
    this.name = "WorkerCredentialError";
  }
}

export interface WorkerCredential {
  readonly keyId: string;
  readonly secret: Buffer;
  readonly wireValue: string;
}

function decodeCanonicalBase64Url(value: string): Buffer {
  const decoded = Buffer.from(value, "base64url");
  if (decoded.toString("base64url") !== value) throw new WorkerCredentialError();
  return decoded;
}

async function closeQuietly(handle: FileHandle | null): Promise<void> {
  if (handle !== null) await handle.close().catch(() => undefined);
}

export async function loadWorkerCredential(path: string): Promise<WorkerCredential> {
  if (!path.startsWith("/") || !path.endsWith("/worker-token")) {
    throw new WorkerCredentialError();
  }
  let directory: FileHandle | null = null;
  let file: FileHandle | null = null;
  try {
    directory = await open(
      dirname(path),
      constants.O_RDONLY | constants.O_DIRECTORY | constants.O_NOFOLLOW,
    );
    const directoryInfo = await directory.stat();
    const uid = typeof process.getuid === "function" ? process.getuid() : -1;
    if (
      !directoryInfo.isDirectory() ||
      (directoryInfo.mode & 0o777) !== 0o700 ||
      directoryInfo.uid !== uid
    )
      throw new WorkerCredentialError();
    file = await open(
      `/proc/self/fd/${directory.fd}/worker-token`,
      constants.O_RDONLY | constants.O_NOFOLLOW,
    );
    const info = await file.stat();
    if (
      !info.isFile() ||
      (info.mode & 0o777) !== 0o400 ||
      info.uid !== uid ||
      info.nlink !== 1 ||
      info.size !== 66
    )
      throw new WorkerCredentialError();
    const wireValue = await file.readFile({ encoding: "ascii" });
    const match = credentialPattern.exec(wireValue);
    if (match === null) throw new WorkerCredentialError();
    const secret = decodeCanonicalBase64Url(match[2] ?? "");
    if (secret.length !== 32) throw new WorkerCredentialError();
    return Object.freeze({ keyId: match[1] ?? "", secret, wireValue });
  } catch {
    throw new WorkerCredentialError();
  } finally {
    await closeQuietly(file);
    await closeQuietly(directory);
  }
}

export function authenticateWorkerRequest(
  rawHeaders: readonly string[],
  credential: WorkerCredential,
): boolean {
  const values: string[] = [];
  for (let index = 0; index < rawHeaders.length; index += 2) {
    if (
      (rawHeaders[index] ?? "").toLowerCase() ===
      BROWSER_WORKER_AUTHENTICATION_HEADER.toLowerCase()
    )
      values.push(rawHeaders[index + 1] ?? "");
  }
  const candidate = values.length === 1 ? (values[0] ?? "") : "";
  const candidateDigest = createHash("sha256").update(candidate, "utf8").digest();
  const expectedDigest = createHash("sha256")
    .update(credential.wireValue, "ascii")
    .digest();
  const matches = timingSafeEqual(candidateDigest, expectedDigest);
  return (
    matches &&
    values.length === 1 &&
    candidate.length === 66 &&
    credentialPattern.test(candidate)
  );
}

export function signWorkerResult(
  result: BrowserWorkerResult,
  credential: WorkerCredential,
): SignedBrowserWorkerResult {
  const signature = createHmac("sha256", credential.secret)
    .update(canonicalJson(result), "utf8")
    .digest("base64url");
  return Object.freeze({
    version: BROWSER_WORKER_CONTRACT_VERSION,
    algorithm: BROWSER_WORKER_RESPONSE_ALGORITHM,
    type: BROWSER_WORKER_RESPONSE_TYPE,
    keyId: credential.keyId,
    result,
    signature,
  });
}

export function verifyWorkerResultSignature(
  envelope: SignedBrowserWorkerResult,
  credential: WorkerCredential,
): boolean {
  const actual = Buffer.from(envelope.signature, "base64url");
  const expected = createHmac("sha256", credential.secret)
    .update(canonicalJson(envelope.result), "utf8")
    .digest();
  return (
    envelope.version === BROWSER_WORKER_CONTRACT_VERSION &&
    envelope.algorithm === BROWSER_WORKER_RESPONSE_ALGORITHM &&
    envelope.type === BROWSER_WORKER_RESPONSE_TYPE &&
    envelope.keyId === credential.keyId &&
    actual.length === 32 &&
    timingSafeEqual(actual, expected)
  );
}
