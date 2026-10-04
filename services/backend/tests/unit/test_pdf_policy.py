"""Unit tests for the bounded document-class PDF policy (079/3 R1)."""

from __future__ import annotations

import zlib

from slaif_agent_site.media_service.pdf_policy import (
    PDF_DECOMPRESS_LIMIT_BYTES,
    PDF_MAX_BYTES,
    PDF_MAX_PAGES,
    PDF_SIGNATURE,
    enforce_pdf_upload,
    pdf_page_count,
)


def make_pdf(pages: int, compress: bool = False) -> bytes:
    """Deterministic minimal PDF fixture with exactly ``pages`` page objects."""
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        (
            b"<< /Type /Pages /Kids ["
            + b" ".join(f"{i} 0 R".encode() for i in range(3, 3 + pages))
            + b"] /Count "
            + str(pages).encode()
            + b" >>"
        ),
    ]
    for _ in range(pages):
        if compress:
            stream = zlib.compress(
                b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>"
            )
            objects.append(
                b"<< /Filter /FlateDecode /Length "
                + str(len(stream)).encode()
                + b" >> stream\n"
                + stream
                + b"\nendstream"
            )
        else:
            objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>")
    out = bytearray(b"%PDF-1.4\n")
    for number, body in enumerate(objects, start=1):
        out += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    out += b"%%EOF"
    return bytes(out)


def make_flate_pdf(pages: int) -> bytes:
    """PDF whose page objects live inside FlateDecode streams.

    The page-object tokens are emitted only inside one ``stream ...
    endstream`` segment whose object dictionary carries the ``FlateDecode``
    filter, so the raw byte scan finds no page objects and the count must
    come entirely from the decompressed stream content.
    """
    payload = b" ".join(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>" for _ in range(pages)
    )
    stream = zlib.compress(payload)
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [] /Count "
        + str(pages).encode()
        + b" >>\nendobj\n"
        b"3 0 obj\n<< /Filter /FlateDecode /Length "
        + str(len(stream)).encode()
        + b" >>\nstream\n"
        + stream
        + b"\nendstream\nendobj\n"
        b"%%EOF"
    )


def test_constants_are_bounded() -> None:
    assert PDF_MAX_PAGES == 200
    assert PDF_MAX_BYTES == 20 * 1024 * 1024
    assert PDF_SIGNATURE == b"%PDF-"
    assert PDF_DECOMPRESS_LIMIT_BYTES == 50 * 1024 * 1024


def test_page_count_raw_one_page() -> None:
    assert pdf_page_count(make_pdf(1)) == 1


def test_page_count_raw_200_page_boundary_accepts() -> None:
    assert pdf_page_count(make_pdf(200)) == 200
    assert enforce_pdf_upload(make_pdf(200), len(make_pdf(200))) is None


def test_page_count_201_pages_returns_sentinel_and_rejects() -> None:
    document = make_pdf(201)
    assert pdf_page_count(document) == 201
    assert enforce_pdf_upload(document, len(document)) == "media-pdf-too-many-pages"


def test_page_count_stops_at_201_sentinel_for_larger_documents() -> None:
    assert pdf_page_count(make_pdf(300)) == 201


def test_page_count_flate_compressed_page_objects() -> None:
    assert pdf_page_count(make_flate_pdf(5)) == 5
    assert pdf_page_count(make_pdf(7, compress=True)) == 7


def test_page_count_mixed_raw_and_compressed_objects() -> None:
    raw = make_pdf(3)
    compressed = make_pdf(2, compress=True)
    mixed = raw[: -len(b"%%EOF")] + b"\n" + compressed[len(b"%PDF-1.4\n") :]
    assert pdf_page_count(mixed) == 5


def test_page_count_never_matches_pages_type() -> None:
    document = b"%PDF-1.4\n<< /Type /Pages /Count 9 >>\n%%EOF"
    assert pdf_page_count(document) is None
    with_page = b"%PDF-1.4\n<< /Type /Pages >>\n<< /Type /Page >>\n%%EOF"
    assert pdf_page_count(with_page) == 1


def test_page_count_undetermined_without_page_objects() -> None:
    assert pdf_page_count(b"%PDF-1.4\nno page objects here\n%%EOF") is None
    assert pdf_page_count(b"%PDF-1.4") is None
    assert pdf_page_count(b"") is None


def test_page_count_undetermined_on_structural_failure() -> None:
    truncated = (
        b"%PDF-1.4\n1 0 obj\n<< /Filter /FlateDecode >> stream\n"
        + zlib.compress(b"payload")[:6]
        + b"\nendstream\n%%EOF"
    )
    assert pdf_page_count(truncated) is None
    missing_endstream = b"%PDF-1.4\n<< /Filter /FlateDecode >> stream\nxx"
    assert pdf_page_count(missing_endstream) is None


def test_enforce_rejects_201_pages() -> None:
    document = make_pdf(201)
    assert enforce_pdf_upload(document, len(document)) == "media-pdf-too-many-pages"


def test_enforce_rejects_above_20_mib() -> None:
    document = make_pdf(1) + b"%0" * (PDF_MAX_BYTES)  # padding after EOF marker
    assert len(document) > PDF_MAX_BYTES
    assert enforce_pdf_upload(document, len(document)) == "media-pdf-too-large"


def test_enforce_accepts_exactly_20_mib() -> None:
    document = make_pdf(1)
    pad = PDF_MAX_BYTES - len(document)
    padded = document[: -len(b"%%EOF")] + b"%" + b"0" * (pad - 1) + b"%%EOF"
    assert len(padded) == PDF_MAX_BYTES
    assert enforce_pdf_upload(padded, len(padded)) is None


def test_enforce_rejects_undetermined_structure() -> None:
    document = b"%PDF-1.4\nundetermined\n%%EOF"
    assert enforce_pdf_upload(document, len(document)) == (
        "media-pdf-structure-invalid"
    )


def test_enforce_rejects_decompression_bomb() -> None:
    bomb_stream = zlib.compress(b" " * (PDF_DECOMPRESS_LIMIT_BYTES + 1))
    document = (
        b"%PDF-1.4\n1 0 obj\n<< /Filter /FlateDecode /Length "
        + str(len(bomb_stream)).encode()
        + b" >> stream\n"
        + bomb_stream
        + b"\nendstream\n%%EOF"
    )
    assert len(document) < PDF_MAX_BYTES
    assert pdf_page_count(document) is None
    assert enforce_pdf_upload(document, len(document)) == (
        "media-pdf-structure-invalid"
    )
