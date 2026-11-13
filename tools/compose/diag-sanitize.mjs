#!/usr/bin/env node
// Bounded sanitizer for the review worker's diagnostic log lines.
//
// Reads raw service-log lines (container stdout+stderr merged) from
// stdin and re-emits ONLY the fixed bounded fields of lines whose
// JSON `message` field STARTS with the exact diagnostic prefix.
// Everything else is dropped: non-JSON lines, malformed JSON, markers
// embedded in other JSON fields or inside unrelated messages, unknown
// field keys, duplicate keys, and out-of-shape values. Never emits a
// raw log line, traceback, SQL text, DSN, cookie, token or payload.
// Stdin-only; no dependencies, no files, no network.

const PREFIX = "slaif-diag: review-job ";
const PHASES = new Set([
  "fetch",
  "open_verified",
  "publish_public",
  "finalization",
  "retry",
  "media-db-start",
  "media-config",
  "reviewer-tx",
  "pipeline-read",
  "status-promoting",
  "verify-snapshot",
  "media-finalize",
  "worker-crash",
]);
const OUTCOMES = new Set(["failed", "requeue", "budget"]);
const REASONS = new Set([
  "storage_corrupt",
  "media_missing",
  "storage_unavailable",
  "media_signature_mismatch",
  "unsupported_media",
  "media-pdf-too-large",
  "store_error",
  "repository_unavailable",
  "store_unavailable",
  "media_config_invalid",
  "postgres_transient",
  "io_transient",
  "configuration_invalid",
  "connection_unavailable",
  "identity_mismatch",
  "timeout",
  "shutdown",
]);
const CLASS_SHAPE = /^[A-Za-z_][A-Za-z0-9_]{0,63}$/;
const IDENT_SHAPE = /^[A-Za-z_][A-Za-z0-9_$]{0,62}$/;
const SQLSTATE_SHAPE = /^[0-9A-Z]{5}$/;
const JOB_SHAPE = /^[0-9a-f-]{36}$/;
const DIGITS_SHAPE = /^[0-9]{1,12}$/;

function normalizeField(token, seen) {
  const eq = token.indexOf("=");
  if (eq <= 0) return null;
  const key = token.slice(0, eq);
  const value = token.slice(eq + 1);
  if (seen.has(key)) return null;
  let ok = false;
  switch (key) {
    case "phase":
      ok = PHASES.has(value);
      break;
    case "outcome":
      ok = OUTCOMES.has(value);
      break;
    case "class":
      ok = CLASS_SHAPE.test(value);
      break;
    case "sqlstate":
      ok = value === "-" || SQLSTATE_SHAPE.test(value);
      break;
    case "constraint":
      ok = value === "-" || IDENT_SHAPE.test(value);
      break;
    case "reason":
      ok = REASONS.has(value);
      break;
    case "attempt":
    case "max_attempts":
      ok = DIGITS_SHAPE.test(value);
      break;
    case "job":
      ok = JOB_SHAPE.test(value);
      break;
    default:
      return null;
  }
  if (!ok) return null;
  seen.add(key);
  return `${key}=${value}`;
}

let buffer = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => {
  buffer += chunk;
});
process.stdin.on("end", () => {
  const emitted = [];
  for (const line of buffer.split("\n")) {
    if (!line) continue;
    let doc;
    try {
      doc = JSON.parse(line);
    } catch {
      continue;
    }
    if (typeof doc !== "object" || doc === null || Array.isArray(doc)) continue;
    const message = doc.message;
    if (typeof message !== "string" || !message.startsWith(PREFIX)) continue;
    const fields = message.slice(PREFIX.length).trim();
    if (!fields) continue;
    const seen = new Set();
    const normalized = [];
    let valid = true;
    for (const token of fields.split(/\s+/)) {
      const field = normalizeField(token, seen);
      if (field === null) {
        valid = false;
        break;
      }
      normalized.push(field);
    }
    if (!valid) continue;
    // A diagnostic is accepted only when it carries both a phase and an
    // outcome; class-only or prefix-only fragments are dropped.
    if (!seen.has("phase") || !seen.has("outcome")) continue;
    emitted.push(PREFIX + normalized.join(" "));
    if (emitted.length >= 60) break;
  }
  for (const out of emitted) process.stdout.write(out + "\n");
});
