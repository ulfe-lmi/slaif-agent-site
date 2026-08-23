# OAP Work Order — 069-a

## Objective

Implement binary media upload with streaming hash validation and
content-addressed immutable storage, replacing metadata-only CRUD.

## GitHub objective state

- Numeric objective: `069`; round: `069-a`
- Mode: `CREATE_NEW_PR`; exactly one new PR

## Verified current state

- Media metadata CRUD routes exist (`media_asset` table).
- No multipart/binary upload endpoint exists.
- No filesystem blob storage; DB stores metadata only.

## Required changes

1. Add `POST /api/editor/v1/media/upload` accepting multipart/form-data
   with size limit (default 100 MB configurable).
2. Stream body to temp file computing SHA-256 incrementally.
3. Validate MIME type by content sniffing (not filename); reject
   disallowed types; SVG disabled or sanitized initially.
4. Atomically move validated file to content-addressed path
   `{MEDIA_ROOT}/{digest[0:2]}/{digest[2:4]}/{digest}`.
5. Create `MediaAsset` record with digest, MIME, byte_size, original filename;
   all within one transaction with audit event.
6. Add authenticated read endpoint serving immutable bytes with
   appropriate Content-Type and cache headers.
7. Integration tests: upload→store→read round-trip; duplicate upload returns
   existing asset (deduplication); oversized rejected; wrong MIME rejected;
   delete removes reference not bytes while referenced.

## Explicit non-goals

- Do NOT implement image resizing/transcoding.
- Do NOT expose staging directories via NGINX directly.
- Do NOT implement shared/distributed MediaStore backend.
- Do NOT allow agents to upload via this endpoint (editor-only).

## Acceptance criteria

- Binary file uploaded, stored at content-addressed path, retrievable.
- Same bytes produce same digest and deduplicated asset.
- Invalid/oversized uploads rejected with structured errors.
- Immutable store: no overwrite of existing digest path.
- All tests pass including negative paths.

## Report

Publish `oap/reports/069-a-media-binary-upload-immutable-store.md` with SELF
report commit parenting implementation SHA.
