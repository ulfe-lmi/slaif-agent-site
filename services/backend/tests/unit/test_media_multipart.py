"""Bounded multipart and cancellation proof for the Media parser."""

from __future__ import annotations

import asyncio
from pathlib import Path
from uuid import uuid4

import pytest
from slaif_agent_site.media_service.multipart import MultipartUploadError, parse_upload
from slaif_agent_site.media_service.store import MediaStore
from starlette.requests import Request

PNG = b"\x89PNG\r\n\x1a\nfixture"


def _body(
    boundary: str,
    *,
    part_name: str = "file",
    filename: str = "fixture.png",
    file_bytes: bytes = PNG,
    declared: str = "image/png",
    extra_headers: str = "",
) -> bytes:
    return (
        (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="alt_text"\r\n\r\n'
            "Alt\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="metadata"\r\n\r\n'
            '{"caption":"fixture"}\r\n'
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{part_name}"; '
            f'filename="{filename}"\r\n'
            f"Content-Type: {declared}\r\n"
            f"{extra_headers}"
            "\r\n"
        ).encode()
        + file_bytes
        + f"\r\n--{boundary}--\r\n".encode()
    )


def _request(
    body: bytes,
    boundary: str,
    *,
    chunks: list[bytes] | None = None,
    content_length: str | None = None,
    extra_headers: list[tuple[bytes, bytes]] | None = None,
) -> Request:
    pieces = chunks or [body]
    headers = [
        (b"content-type", f"multipart/form-data; boundary={boundary}".encode()),
        (b"content-length", str(len(body)).encode())
        if content_length is None
        else (b"content-length", content_length.encode()),
        *(extra_headers or []),
    ]
    index = 0

    async def receive() -> dict[str, object]:
        nonlocal index
        if index >= len(pieces):
            return {"type": "http.request", "body": b"", "more_body": False}
        chunk = pieces[index]
        index += 1
        return {
            "type": "http.request",
            "body": chunk,
            "more_body": index < len(pieces),
        }

    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": f"/v1/sites/{uuid4()}/assets",
            "headers": headers,
        },
        receive,
    )


@pytest.mark.asyncio
async def test_parser_accepts_adversarial_chunk_boundaries(tmp_path: Path) -> None:
    boundary = "media-boundary-070b"
    body = _body(boundary)
    for width in range(1, min(len(body), 24) + 1):
        store = MediaStore(tmp_path / f"media-{width}")
        parsed = await parse_upload(
            _request(
                body,
                boundary,
                chunks=[body[i : i + width] for i in range(0, len(body), width)],
            ),
            store,
        )
        assert parsed.filename == "fixture.png"
        assert parsed.staged.size_bytes == len(PNG)
        assert parsed.metadata == {"caption": "fixture"}
        store.discard_staged(parsed.staged)


@pytest.mark.asyncio
async def test_parser_rejects_bounds_duplicates_and_truncation(tmp_path: Path) -> None:
    boundary = "media-boundary-070b"
    cases = [
        (_body(boundary)[:-4], None),
        (_body(boundary, extra_headers="Content-Type: image/png\r\n"), None),
        (_body(boundary, file_bytes=PNG + b"too-large"), 8),
    ]
    for index, (body, limit) in enumerate(cases):
        store = MediaStore(tmp_path / f"media-{index}", max_upload_bytes=limit or 100)
        with pytest.raises(MultipartUploadError):
            await parse_upload(_request(body, boundary), store)
        assert list(store.staging_root.iterdir()) == []

    store = MediaStore(tmp_path / "negative")
    with pytest.raises(MultipartUploadError, match="malformed_multipart"):
        await parse_upload(
            _request(body, boundary, content_length="-1"),
            store,
        )


@pytest.mark.asyncio
async def test_parser_rejects_ambiguous_length_and_cleans_on_cancellation(
    tmp_path: Path,
) -> None:
    boundary = "media-boundary-070b"
    body = _body(boundary)
    store = MediaStore(tmp_path / "headers")
    with pytest.raises(MultipartUploadError, match="malformed_multipart"):
        await parse_upload(
            _request(
                body,
                boundary,
                extra_headers=[(b"content-length", str(len(body)).encode())],
            ),
            store,
        )
    assert not store.staging_root.exists() or list(store.staging_root.iterdir()) == []


@pytest.mark.asyncio
async def test_parser_requires_exact_filename_bearing_file_part(tmp_path: Path) -> None:
    boundary = "media-boundary-070c"
    valid = _body(boundary)
    final = f"--{boundary}--\r\n".encode()
    duplicate = (
        valid[: -len(final)]
        + valid[
            valid.index(
                f'--{boundary}\r\nContent-Disposition: form-data; name="file"'.encode()
            ) : -len(final)
        ]
        + final
    )
    filename_less = valid.replace(
        b'Content-Disposition: form-data; name="file"; filename="fixture.png"',
        b'Content-Disposition: form-data; name="file"',
    )
    for index, body in enumerate(
        (
            _body(boundary, part_name="wrong"),
            duplicate,
            filename_less,
        )
    ):
        store = MediaStore(tmp_path / f"reject-{index}")
        with pytest.raises(MultipartUploadError):
            await parse_upload(_request(body, boundary), store)
        assert (
            not store.staging_root.exists() or list(store.staging_root.iterdir()) == []
        )

    cancellation_store = MediaStore(tmp_path / "cancel")
    first = body[: body.index(PNG) + 2]

    class CancelRequest(Request):
        async def stream(self):  # type: ignore[no-untyped-def]
            yield first
            raise asyncio.CancelledError

    request = CancelRequest(
        {
            "type": "http",
            "method": "POST",
            "path": "/v1/assets",
            "headers": [
                (b"content-type", f"multipart/form-data; boundary={boundary}".encode()),
                (b"content-length", str(len(body)).encode()),
            ],
        }
    )
    with pytest.raises(asyncio.CancelledError):
        await parse_upload(request, cancellation_store)
    assert list(cancellation_store.staging_root.iterdir()) == []
