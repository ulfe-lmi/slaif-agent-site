import { createHash, randomUUID } from "node:crypto";
import { constants } from "node:fs";
import { open, link, unlink, type FileHandle } from "node:fs/promises";

import {
  BROWSER_WORKER_BOUNDS,
  BROWSER_WORKER_CONTRACT_VERSION,
  canonicalJson,
  type BrowserEvidence,
  type BrowserWorkerArtifactMetadata,
  type BrowserWorkerArtifactRetrievalRequest,
  type BrowserWorkerSubmitRequest,
} from "@slaif-agent-site/browser-tool-contracts";

const pngSignature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

export class ArtifactStoreError extends Error {
  public constructor(message = "browser artifact is unavailable") {
    super(message);
    this.name = "ArtifactStoreError";
  }
}

export interface ArtifactContent {
  readonly kind: BrowserEvidence;
  readonly mimeType: "image/png" | "application/json" | "text/plain";
  readonly bytes: Buffer;
}

interface PersistedArtifact extends BrowserWorkerArtifactMetadata {
  readonly requestId: string;
}

function publicMetadata(metadata: PersistedArtifact): BrowserWorkerArtifactMetadata {
  return Object.freeze({
    version: metadata.version,
    artifactId: metadata.artifactId,
    runId: metadata.runId,
    siteId: metadata.siteId,
    workspaceId: metadata.workspaceId,
    kind: metadata.kind,
    mimeType: metadata.mimeType,
    sha256: metadata.sha256,
    sizeBytes: metadata.sizeBytes,
    target: metadata.target,
    routeDigest: metadata.routeDigest,
    createdAt: metadata.createdAt,
    expiresAt: metadata.expiresAt,
    visibility: metadata.visibility,
  });
}

function deterministicArtifactId(
  request: BrowserWorkerSubmitRequest,
  content: ArtifactContent,
  digest: string,
): string {
  const seed = [
    request.siteId,
    request.workspaceId,
    request.runId,
    request.routeDigest,
    request.target,
    content.kind,
    digest,
  ].join(":");
  const value = createHash("sha256").update(seed, "ascii").digest("hex").slice(0, 32);
  return `${value.slice(0, 8)}-${value.slice(8, 12)}-5${value.slice(13, 16)}-8${value.slice(17, 20)}-${value.slice(20)}`;
}

function stem(artifactId: string, digest: string): string {
  return `v1-${artifactId.replaceAll("-", "")}-${digest}`;
}

function anchored(directory: FileHandle, name: string): string {
  if (!/^[a-zA-Z0-9.-]+$/u.test(name) || name.includes("..") || name.includes("/")) {
    throw new ArtifactStoreError();
  }
  return `/proc/self/fd/${directory.fd}/${name}`;
}

async function statRegular(
  handle: FileHandle,
  size: number,
  uid: number,
): Promise<void> {
  const info = await handle.stat();
  if (
    !info.isFile() ||
    (info.mode & 0o777) !== 0o600 ||
    info.uid !== uid ||
    info.nlink !== 1 ||
    info.size !== size
  )
    throw new ArtifactStoreError();
}

async function readExactFile(
  directory: FileHandle,
  name: string,
  size: number,
  uid: number,
): Promise<Buffer> {
  let handle: FileHandle | null = null;
  try {
    handle = await open(
      anchored(directory, name),
      constants.O_RDONLY | constants.O_NOFOLLOW,
    );
    await statRegular(handle, size, uid);
    const value = await handle.readFile();
    if (value.length !== size) throw new ArtifactStoreError();
    return value;
  } catch {
    throw new ArtifactStoreError();
  } finally {
    await handle?.close().catch(() => undefined);
  }
}

async function publishExclusive(
  directory: FileHandle,
  name: string,
  bytes: Buffer,
  uid: number,
): Promise<boolean> {
  const temporary = `.stage-${randomUUID()}`;
  const temporaryPath = anchored(directory, temporary);
  let handle: FileHandle | null = null;
  let linked = false;
  try {
    handle = await open(
      temporaryPath,
      constants.O_WRONLY | constants.O_CREAT | constants.O_EXCL | constants.O_NOFOLLOW,
      0o600,
    );
    await handle.chmod(0o600);
    let offset = 0;
    while (offset < bytes.length) {
      const chunk = bytes.subarray(offset, Math.min(offset + 65_536, bytes.length));
      const result = await handle.write(chunk, 0, chunk.length, offset);
      if (result.bytesWritten !== chunk.length) throw new ArtifactStoreError();
      offset += result.bytesWritten;
    }
    await handle.sync();
    await handle.close();
    handle = null;
    try {
      await link(temporaryPath, anchored(directory, name));
      linked = true;
    } catch (error) {
      if (!(error instanceof Error) || !("code" in error) || error.code !== "EEXIST") {
        throw error;
      }
    }
    await unlink(temporaryPath);
    await directory.sync();
    if (!linked) {
      const existing = await readExactFile(directory, name, bytes.length, uid);
      if (!existing.equals(bytes)) throw new ArtifactStoreError();
    }
    return linked;
  } catch {
    await handle?.close().catch(() => undefined);
    await unlink(temporaryPath).catch(() => undefined);
    throw new ArtifactStoreError();
  }
}

function validateContent(content: ArtifactContent): void {
  if (
    content.bytes.length === 0 ||
    content.bytes.length > BROWSER_WORKER_BOUNDS.artifactBytes
  )
    throw new ArtifactStoreError();
  if (
    content.mimeType === "image/png" &&
    !content.bytes.subarray(0, 8).equals(pngSignature)
  )
    throw new ArtifactStoreError();
  if (
    content.kind === "screenshot"
      ? content.mimeType !== "image/png"
      : content.mimeType === "image/png"
  )
    throw new ArtifactStoreError();
  if (content.mimeType !== "image/png") {
    const text = content.bytes.toString("utf8");
    if (!Buffer.from(text, "utf8").equals(content.bytes))
      throw new ArtifactStoreError();
    if (/sbp1\.|sbws1:|sas2_/u.test(text)) throw new ArtifactStoreError();
  }
}

export class BrowserArtifactStore {
  readonly #directory: FileHandle;
  readonly #uid: number;

  private constructor(directory: FileHandle, uid: number) {
    this.#directory = directory;
    this.#uid = uid;
  }

  public static async open(root: string): Promise<BrowserArtifactStore> {
    if (!root.startsWith("/")) throw new ArtifactStoreError();
    let directory: FileHandle | null = null;
    try {
      directory = await open(
        root,
        constants.O_RDONLY | constants.O_DIRECTORY | constants.O_NOFOLLOW,
      );
      const info = await directory.stat();
      const uid = typeof process.getuid === "function" ? process.getuid() : -1;
      if (!info.isDirectory() || (info.mode & 0o777) !== 0o700 || info.uid !== uid)
        throw new ArtifactStoreError();
      return new BrowserArtifactStore(directory, uid);
    } catch {
      await directory?.close().catch(() => undefined);
      throw new ArtifactStoreError();
    }
  }

  public async close(): Promise<void> {
    await this.#directory.close();
  }

  public async publish(
    request: BrowserWorkerSubmitRequest,
    content: ArtifactContent,
    createdAt: number,
  ): Promise<BrowserWorkerArtifactMetadata> {
    validateContent(content);
    const digest = createHash("sha256").update(content.bytes).digest("hex");
    const artifactId = deterministicArtifactId(request, content, digest);
    const metadata: PersistedArtifact = Object.freeze({
      version: BROWSER_WORKER_CONTRACT_VERSION,
      requestId: request.requestId,
      artifactId,
      runId: request.runId,
      siteId: request.siteId,
      workspaceId: request.workspaceId,
      kind: content.kind,
      mimeType: content.mimeType,
      sha256: digest,
      sizeBytes: content.bytes.length,
      target: request.target,
      routeDigest: request.routeDigest,
      createdAt,
      expiresAt: createdAt + BROWSER_WORKER_BOUNDS.artifactRetentionSeconds,
      visibility: "PRIVATE",
    });
    const base = stem(artifactId, digest);
    const metadataBytes = Buffer.from(canonicalJson(metadata), "utf8");
    const dataCreated = await publishExclusive(
      this.#directory,
      `${base}.bin`,
      content.bytes,
      this.#uid,
    );
    try {
      await publishExclusive(this.#directory, `${base}.json`, metadataBytes, this.#uid);
    } catch {
      if (dataCreated) {
        await unlink(anchored(this.#directory, `${base}.bin`)).catch(() => undefined);
        await this.#directory.sync().catch(() => undefined);
      }
      throw new ArtifactStoreError();
    }
    return publicMetadata(metadata);
  }

  public async retrieve(
    request: BrowserWorkerArtifactRetrievalRequest,
    now: number,
  ): Promise<{
    readonly metadata: BrowserWorkerArtifactMetadata;
    readonly bytes: Buffer;
  }> {
    const base = stem(request.artifactId, request.sha256);
    const metadataPath = `${base}.json`;
    let metadataHandle: FileHandle | null = null;
    let raw: Buffer;
    try {
      metadataHandle = await open(
        anchored(this.#directory, metadataPath),
        constants.O_RDONLY | constants.O_NOFOLLOW,
      );
      const info = await metadataHandle.stat();
      if (
        !info.isFile() ||
        (info.mode & 0o777) !== 0o600 ||
        info.uid !== this.#uid ||
        info.nlink !== 1 ||
        info.size < 2 ||
        info.size > 8192
      )
        throw new ArtifactStoreError();
      raw = await metadataHandle.readFile();
    } catch {
      throw new ArtifactStoreError();
    } finally {
      await metadataHandle?.close().catch(() => undefined);
    }
    let persisted: PersistedArtifact;
    try {
      persisted = JSON.parse(raw.toString("utf8")) as PersistedArtifact;
      const expectedKeys = [
        "artifactId",
        "createdAt",
        "expiresAt",
        "kind",
        "mimeType",
        "requestId",
        "routeDigest",
        "runId",
        "sha256",
        "siteId",
        "sizeBytes",
        "target",
        "version",
        "visibility",
        "workspaceId",
      ];
      if (
        canonicalJson(persisted) !== raw.toString("utf8") ||
        JSON.stringify(Object.keys(persisted).sort()) !==
          JSON.stringify(expectedKeys) ||
        persisted.version !== BROWSER_WORKER_CONTRACT_VERSION ||
        persisted.visibility !== "PRIVATE" ||
        !Number.isInteger(persisted.createdAt) ||
        !Number.isInteger(persisted.expiresAt) ||
        persisted.expiresAt <= persisted.createdAt ||
        (persisted.kind === "screenshot") !== (persisted.mimeType === "image/png")
      )
        throw new Error();
    } catch {
      throw new ArtifactStoreError();
    }
    for (const [expected, actual] of [
      [request.requestId, persisted.requestId],
      [request.runId, persisted.runId],
      [request.siteId, persisted.siteId],
      [request.workspaceId, persisted.workspaceId],
      [request.artifactId, persisted.artifactId],
      [request.kind, persisted.kind],
      [request.target, persisted.target],
      [request.routeDigest, persisted.routeDigest],
      [request.sha256, persisted.sha256],
      [request.sizeBytes, persisted.sizeBytes],
    ] as const) {
      if (expected !== actual) throw new ArtifactStoreError();
    }
    if (persisted.visibility !== "PRIVATE" || persisted.expiresAt <= now) {
      throw new ArtifactStoreError();
    }
    const bytes = await readExactFile(
      this.#directory,
      `${base}.bin`,
      persisted.sizeBytes,
      this.#uid,
    );
    if (createHash("sha256").update(bytes).digest("hex") !== persisted.sha256) {
      throw new ArtifactStoreError();
    }
    return Object.freeze({ metadata: publicMetadata(persisted), bytes });
  }
}

export function pngDimensions(bytes: Buffer): {
  readonly width: number;
  readonly height: number;
} {
  if (bytes.length < 24 || !bytes.subarray(0, 8).equals(pngSignature)) {
    throw new ArtifactStoreError();
  }
  return Object.freeze({
    width: bytes.readUInt32BE(16),
    height: bytes.readUInt32BE(20),
  });
}
