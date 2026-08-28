import assert from "node:assert/strict";
import { Buffer } from "node:buffer";
import { createHash } from "node:crypto";
import {
  chmod,
  link,
  lstat,
  mkdir,
  mkdtemp,
  readdir,
  rename,
  symlink,
  unlink,
  writeFile,
} from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { test } from "node:test";

import { BrowserArtifactStore } from "../dist/artifact-store.js";
import {
  parseWorkerArtifactRetrievalRequest,
  parseWorkerSubmitRequest,
} from "../dist/contracts.js";

const now = 1_800_000_000;
const route = "/s/demo/";
const binding = {
  version: "browser-worker/v1",
  deployment: "slaif-agent-site",
  requestId: "00000000-0000-4000-8000-000000000001",
  runId: "00000000-0000-4000-8000-000000000002",
  siteId: "00000000-0000-4000-8000-000000000003",
  workspaceId: "00000000-0000-4000-8000-000000000004",
  capabilityId: "00000000-0000-4000-8000-000000000005",
  operationId: "00000000-0000-4000-8000-000000000006",
  leaseId: "00000000-0000-4000-8000-000000000007",
  attempt: 1,
  route,
  routeDigest: createHash("sha256").update(route).digest("hex"),
  target: "desktop-chromium",
  evidence: ["heading-summary"],
  artifactBytesLimit: 1_048_576,
  durationSeconds: 30,
  issuedAt: now,
  expiresAt: now + 30,
  previewCredential: "sbp1.a.b.c",
};

function retrieval(metadata, update = {}) {
  return parseWorkerArtifactRetrievalRequest({
    version: "browser-worker/v1",
    deployment: "slaif-agent-site",
    requestId: binding.requestId,
    runId: metadata.runId,
    siteId: metadata.siteId,
    workspaceId: metadata.workspaceId,
    artifactId: metadata.artifactId,
    kind: metadata.kind,
    target: metadata.target,
    routeDigest: metadata.routeDigest,
    sha256: metadata.sha256,
    sizeBytes: metadata.sizeBytes,
    ...update,
  });
}

test("artifact store publishes/reuses/reads immutably across restart and root replacement", async () => {
  const parent = await mkdtemp(join(tmpdir(), "slaif-artifacts-"));
  const root = join(parent, "root");
  await mkdir(root, { mode: 0o700 });
  await chmod(root, 0o700);
  const request = parseWorkerSubmitRequest(binding, now + 1);
  const content = {
    kind: "heading-summary",
    mimeType: "application/json",
    bytes: Buffer.from('{"headings":["Overlay"]}', "utf8"),
  };
  const store = await BrowserArtifactStore.open(root);
  const [first, second] = await Promise.all([
    store.publish(request, content, now + 1),
    store.publish(request, content, now + 1),
  ]);
  assert.deepEqual(first, second);
  assert.equal((await readdir(root)).length, 2);
  assert.equal(
    (await readdir(root)).some((name) => name.startsWith(".stage-")),
    false,
  );
  for (const name of await readdir(root)) {
    const info = await lstat(join(root, name));
    assert.equal(info.mode & 0o777, 0o600);
    assert.equal(info.nlink, 1);
  }
  const exact = await store.retrieve(retrieval(first), now + 2);
  assert.deepEqual(exact.bytes, content.bytes);

  const anchored = `${root}.anchored`;
  await rename(root, anchored);
  await mkdir(root, { mode: 0o700 });
  const another = await store.publish(
    request,
    { ...content, kind: "structure-summary", bytes: Buffer.from('{"main":1}') },
    now + 1,
  );
  assert.equal((await readdir(root)).length, 0);
  assert.equal((await readdir(anchored)).length, 4);
  await store.close();

  await rename(root, `${root}.replacement`);
  await rename(anchored, root);
  const restarted = await BrowserArtifactStore.open(root);
  assert.deepEqual(
    (await restarted.retrieve(retrieval(first), now + 3)).bytes,
    content.bytes,
  );
  assert.deepEqual(
    (await restarted.retrieve(retrieval(another), now + 3)).bytes,
    Buffer.from('{"main":1}'),
  );
  await assert.rejects(
    restarted.retrieve(retrieval(first, { runId: binding.siteId }), now + 3),
  );
  await assert.rejects(restarted.retrieve(retrieval(first), first.expiresAt));
  await restarted.close();
});

test("artifact store rejects traversal, symlink, hardlink, corruption, and quota without partials", async () => {
  const parent = await mkdtemp(join(tmpdir(), "slaif-artifact-negative-"));
  const root = join(parent, "root");
  await mkdir(root, { mode: 0o700 });
  await chmod(root, 0o700);
  const linkRoot = join(parent, "link-root");
  await symlink(root, linkRoot);
  await assert.rejects(BrowserArtifactStore.open(linkRoot));
  const store = await BrowserArtifactStore.open(root);
  const request = parseWorkerSubmitRequest(binding, now + 1);
  await assert.rejects(
    store.publish(
      request,
      {
        kind: "heading-summary",
        mimeType: "application/json",
        bytes: Buffer.alloc(8_388_609),
      },
      now + 1,
    ),
  );
  assert.deepEqual(await readdir(root), []);
  const metadata = await store.publish(
    request,
    {
      kind: "heading-summary",
      mimeType: "application/json",
      bytes: Buffer.from('{"headings":["Safe"]}'),
    },
    now + 1,
  );
  const dataName = (await readdir(root)).find((name) => name.endsWith(".bin"));
  assert.ok(dataName);
  const hardlink = join(root, "extra-hardlink");
  await link(join(root, dataName), hardlink);
  await assert.rejects(store.retrieve(retrieval(metadata), now + 2));
  await unlink(hardlink);
  await writeFile(join(root, dataName), Buffer.alloc(metadata.sizeBytes, 65));
  await assert.rejects(store.retrieve(retrieval(metadata), now + 2));
  assert.throws(() => retrieval(metadata, { artifactId: "../../private" }));
  assert.equal(
    (await readdir(root)).some((name) => name.startsWith(".stage-")),
    false,
  );
  await store.close();
});
