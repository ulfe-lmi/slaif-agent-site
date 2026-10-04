"""Bounded document-class PDF policy (079/3): size, signature, page count.

Pure stdlib policy for the document class: no HTTP, no DB, no dependency.
The immutable store applies :func:`enforce_pdf_upload` at its single shared
upload enforcement point (before any staging publish) for every declared
``application/pdf`` upload, so the human edge route and the Agent upload
share one policy with no per-route logic.

Page counting is deliberately conservative and fail-closed: it counts
word-boundary ``/Type /Page`` occurrences (never ``/Type /Pages``) in the
raw bytes and in every FlateDecode ``stream ... endstream`` segment
(zlib-decompressed under a hard decompressed-length cap).  A document whose
page count cannot be determined is undetermined and is rejected by the
store, never guessed.
"""

from __future__ import annotations

import re
import zlib

#: Bounded maximum page count for one document-class asset (079/3 R1).
PDF_MAX_PAGES = 200

#: Bounded maximum byte size for one document-class asset (079/3 R1).
#: Independent of the generic ``max_upload_bytes`` store limit.
PDF_MAX_BYTES = 20 * 1024 * 1024

#: Content signature every declared PDF upload must begin with.
PDF_SIGNATURE = b"%PDF-"

#: Hard decompressed-length cap for one FlateDecode stream (079/3 R1):
#: decompressing beyond this is a decompression bomb and fails closed.
PDF_DECOMPRESS_LIMIT_BYTES = 50 * 1024 * 1024

#: Counting sentinel: counting stops once this many page objects matched,
#: so hostile multi-page documents cannot force unbounded scanning.
_PAGE_COUNT_SENTINEL = PDF_MAX_PAGES + 1

_PAGE_OBJECT = re.compile(rb"/Type\s*/Page\b")
_STREAM_SEGMENT = re.compile(rb"stream\r?\n", re.DOTALL)
_END_STREAM = re.compile(rb"\r?\nendstream")


def _flate_stream_offsets(data: bytes) -> list[tuple[int, int]]:
    """Yield ``(start, end)`` offsets of FlateDecode ``stream`` segments.

    A segment is a ``stream ... endstream`` span whose preceding object
    dictionary (the text between the last ``<<`` and the ``stream``
    keyword) names ``FlateDecode``.  Segments without a readable
    ``endstream`` or with an unreadable dictionary are structural failures
    and are reported by the caller.
    """
    segments: list[tuple[int, int]] = []
    position = 0
    while True:
        opening = _STREAM_SEGMENT.search(data, position)
        if opening is None:
            break
        closing = _END_STREAM.search(data, opening.end())
        if closing is None:
            raise ValueError("structural failure")
        dictionary_start = data.rfind(b"<<", 0, opening.start())
        dictionary = (
            data[dictionary_start : opening.start()] if dictionary_start >= 0 else b""
        )
        if b"FlateDecode" in dictionary:
            segments.append((opening.end(), closing.start()))
        position = closing.end()
    return segments


_FEED_CHUNK_BYTES = 64 * 1024


def _count_in_decompressed(data: bytes, start: int, end: int) -> int | None:
    """Zlib-decompress one segment under the hard cap; count page objects.

    The compressed payload is fed in bounded chunks and the decompressed
    output is drained incrementally, so a decompression bomb cannot
    allocate more than one chunk plus the bounded cap before the check
    trips.  Returns ``None`` on any structural failure (truncated stream,
    bad zlib data, or decompressed length above the bomb cap).
    """
    decompressor = zlib.decompressobj()
    total = 0
    count = 0
    try:
        for offset in range(start, end, _FEED_CHUNK_BYTES):
            output = decompressor.decompress(data[offset : offset + _FEED_CHUNK_BYTES])
            total += len(output)
            if total > PDF_DECOMPRESS_LIMIT_BYTES:
                return None
            count += len(_PAGE_OBJECT.findall(output))
            if count >= _PAGE_COUNT_SENTINEL:
                return _PAGE_COUNT_SENTINEL
        output = decompressor.flush()
    except zlib.error:
        return None
    total += len(output)
    if total > PDF_DECOMPRESS_LIMIT_BYTES:
        return None
    count += len(_PAGE_OBJECT.findall(output))
    return count if count < _PAGE_COUNT_SENTINEL else _PAGE_COUNT_SENTINEL


def pdf_page_count(data: bytes) -> int | None:
    """Bounded page count for one PDF document (079/3 R1).

    Counts word-boundary ``/Type /Page`` occurrences (never matching
    ``/Type /Pages``) in the raw bytes, then in every FlateDecode stream
    segment's decompressed content (under the 50 MiB hard cap).  Stops
    after :data:`PDF_MAX_PAGES` + 1 total matches and returns the 201
    sentinel.  Returns ``None`` (undetermined) when no page objects are
    found in raw or decompressed content, or on any structural failure.
    """
    total = len(_PAGE_OBJECT.findall(data))
    if total >= _PAGE_COUNT_SENTINEL:
        return _PAGE_COUNT_SENTINEL
    try:
        segments = _flate_stream_offsets(data)
    except ValueError:
        return None
    for start, end in segments:
        segment_count = _count_in_decompressed(data, start, end)
        if segment_count is None:
            return None
        total += segment_count
        if total >= _PAGE_COUNT_SENTINEL:
            return _PAGE_COUNT_SENTINEL
    return total if total > 0 else None


def enforce_pdf_upload(data: bytes, size_bytes: int) -> str | None:
    """Apply the bounded PDF policy; return the exact rejection key or None.

    Order of decisions (079/3 R1): size above :data:`PDF_MAX_BYTES` is
    ``media-pdf-too-large``; an undetermined page count is
    ``media-pdf-structure-invalid`` (fail-closed); a count above
    :data:`PDF_MAX_PAGES` is ``media-pdf-too-many-pages``.  ``None`` means
    the document passes the bounded policy.
    """
    if size_bytes > PDF_MAX_BYTES:
        return "media-pdf-too-large"
    count = pdf_page_count(data)
    if count is None:
        return "media-pdf-structure-invalid"
    if count > PDF_MAX_PAGES:
        return "media-pdf-too-many-pages"
    return None


__all__ = [
    "PDF_DECOMPRESS_LIMIT_BYTES",
    "PDF_MAX_BYTES",
    "PDF_MAX_PAGES",
    "PDF_SIGNATURE",
    "enforce_pdf_upload",
    "pdf_page_count",
]
