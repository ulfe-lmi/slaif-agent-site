import { Buffer } from "node:buffer";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve, sep } from "node:path";
import process from "node:process";
import { inflateRawSync } from "node:zlib";

const [archivePath, destination] = process.argv.slice(2);
if (!archivePath || !destination)
  throw new Error("exact archive and destination required");

const archive = readFileSync(archivePath);
const endSignature = 0x06054b50;
const centralSignature = 0x02014b50;
const localSignature = 0x04034b50;
let end = -1;
for (
  let offset = archive.length - 22;
  offset >= Math.max(0, archive.length - 65_557);
  offset -= 1
) {
  if (archive.readUInt32LE(offset) === endSignature) {
    end = offset;
    break;
  }
}
if (end < 0 || archive.readUInt16LE(end + 20) !== archive.length - end - 22) {
  throw new Error("archive end record is invalid");
}
const entries = archive.readUInt16LE(end + 10);
const centralSize = archive.readUInt32LE(end + 12);
const centralOffset = archive.readUInt32LE(end + 16);
if (entries === 0 || entries > 4096 || centralOffset + centralSize !== end) {
  throw new Error("archive central directory is invalid");
}

const crcTable = new Uint32Array(256);
for (let index = 0; index < 256; index += 1) {
  let value = index;
  for (let bit = 0; bit < 8; bit += 1) {
    value = (value & 1) === 1 ? 0xedb88320 ^ (value >>> 1) : value >>> 1;
  }
  crcTable[index] = value >>> 0;
}
function crc32(value) {
  let crc = 0xffffffff;
  for (const byte of value) crc = (crcTable[(crc ^ byte) & 0xff] ?? 0) ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

const root = resolve(destination);
mkdirSync(root, { recursive: true, mode: 0o755 });
const seen = new Set();
let cursor = centralOffset;
for (let index = 0; index < entries; index += 1) {
  if (archive.readUInt32LE(cursor) !== centralSignature) {
    throw new Error("archive entry is invalid");
  }
  const flags = archive.readUInt16LE(cursor + 8);
  const method = archive.readUInt16LE(cursor + 10);
  const expectedCrc = archive.readUInt32LE(cursor + 16);
  const compressedSize = archive.readUInt32LE(cursor + 20);
  const expectedSize = archive.readUInt32LE(cursor + 24);
  const nameLength = archive.readUInt16LE(cursor + 28);
  const extraLength = archive.readUInt16LE(cursor + 30);
  const commentLength = archive.readUInt16LE(cursor + 32);
  const attributes = archive.readUInt32LE(cursor + 38) >>> 16;
  const localOffset = archive.readUInt32LE(cursor + 42);
  const name = archive.subarray(cursor + 46, cursor + 46 + nameLength).toString("utf8");
  cursor += 46 + nameLength + extraLength + commentLength;
  if (
    (flags & ~4) !== 0 ||
    ![0, 8].includes(method) ||
    !name.startsWith("chrome-linux64/") ||
    name.includes("\\") ||
    name.split("/").some((part) => part === ".." || part === ".") ||
    seen.has(name) ||
    Buffer.byteLength(name, "utf8") !== nameLength
  ) {
    throw new Error("archive name or encoding is invalid");
  }
  seen.add(name);
  const output = resolve(root, name);
  if (!output.startsWith(root + sep)) throw new Error("archive escaped destination");
  if (name.endsWith("/")) {
    mkdirSync(output, { recursive: true, mode: 0o755 });
    continue;
  }
  if (archive.readUInt32LE(localOffset) !== localSignature) {
    throw new Error("archive local entry is invalid");
  }
  const localNameLength = archive.readUInt16LE(localOffset + 26);
  const localExtraLength = archive.readUInt16LE(localOffset + 28);
  const localName = archive
    .subarray(localOffset + 30, localOffset + 30 + localNameLength)
    .toString("utf8");
  if (localName !== name) throw new Error("archive entry names disagree");
  const dataOffset = localOffset + 30 + localNameLength + localExtraLength;
  const compressed = archive.subarray(dataOffset, dataOffset + compressedSize);
  if (compressed.length !== compressedSize)
    throw new Error("archive data is truncated");
  const value = method === 0 ? Buffer.from(compressed) : inflateRawSync(compressed);
  if (value.length !== expectedSize || crc32(value) !== expectedCrc) {
    throw new Error("archive data integrity failed");
  }
  mkdirSync(dirname(output), { recursive: true, mode: 0o755 });
  writeFileSync(output, value, {
    flag: "wx",
    mode: attributes & 0o777 ? attributes & 0o777 : 0o644,
  });
}
if (cursor !== end || !seen.has("chrome-linux64/chrome")) {
  throw new Error("archive inventory is incomplete");
}
