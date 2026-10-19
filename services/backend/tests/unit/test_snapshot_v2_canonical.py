"""R2 numeric/Unicode canonicalization golden vectors (083/5).

The golden expected strings are the ACTUAL canonical outputs of the
verbatim 070 ``control.slaif_canonical_jsonb_text`` function family
executed on a disposable PostgreSQL 18.6 (container
``slaif-integration-pg-0833b``) against the verbatim probe documents
below; provenance and full actual output archived at
``/tmp/oap-083-5-a/numeric-probe.sql`` / ``numeric-probe-actual.txt`` /
``numeric-canonicalization-probe-result.json`` (2026-10-18T11:27:26Z,
PSQL_EXIT:0). The same documents reach the worker through asyncpg jsonb
text, so parsing with ``parse_float=Decimal`` + ``canonical_json`` must
reproduce the SQL canonical bytes exactly (R2 numeric identity).
"""

# ruff: noqa: E501 -- verbatim SQL-probe golden vector contracts

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

import pytest
from slaif_agent_site.review_worker.snapshot import (
    canonical_digest,
    canonical_json,
    parse_snapshot_text,
)

# (document key, verbatim probe JSON text, verbatim SQL canonical output)
PROBE_DOCS: tuple[tuple[str, str, str], ...] = (
    (
        "D1_numbers",
        '{"a":1e-05,"b":1E30,"c":1.50,"d":-0,"e":123456789.123456789123456789,"f":100,"g":-1.25,"h":0.000000001,"i":1.0,"j":1e15,"k":9007199254740993,"l":1e-7,"m":1e400,"n":0,"o":123456789012345678901234567890,"p":1e-300,"q":2.5e-10}',
        '{"a":0.00001,"b":1000000000000000000000000000000,"c":1.50,"d":0,"e":123456789.123456789123456789,"f":100,"g":-1.25,"h":0.000000001,"i":1.0,"j":1000000000000000,"k":9007199254740993,"l":0.0000001,"m":10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000,"n":0,"o":123456789012345678901234567890,"p":0.000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001,"q":0.00000000025}',
    ),
    (
        "D2_keyorder",
        '{"z":1,"A":2,"ä":3,"ü":4,"a":5,"Z":6,"0":7}',
        '{"0":7,"A":2,"Z":6,"a":5,"z":1,"\\u00e4":3,"\\u00fc":4}',
    ),
    (
        "D3_strings",
        '{"q":"quote\\"back\\\\slash","u1":"\\u0001","u7f":"\\u007f","e":"é","nb":"𠀋","cr":"a\\r\\nb","tab":"a\\tb","empty":""}',
        '{"cr":"a\\r\\nb","e":"\\u00e9","empty":"","nb":"\\ud840\\udc0b","q":"quote\\"back\\\\slash","tab":"a\\tb","u1":"\\u0001","u7f":"\\u007f"}',
    ),
    (
        "D4_nesting",
        '{"arr":[1,"two",{"three":3},null,true,false,[[]]],"deep":{"l1":{"l2":{"l3":"x"}}}}',
        '{"arr":[1,"two",{"three":3},null,true,false,[[]]],"deep":{"l1":{"l2":{"l3":"x"}}}}',
    ),
    (
        "D5_realistic",
        '{"values":{"price":12.50,"ratio":1e-05,"count":7,"score":85.05112877,"where":{"latitude":37.7749,"longitude":-122.4194,"label":"SF"}},"bbox":{"west":-122.5,"south":37.7,"east":-122.3,"north":37.9},"note":"üñïçödé 🌍"}',
        '{"bbox":{"east":-122.3,"north":37.9,"south":37.7,"west":-122.5},"note":"\\u00fc\\u00f1\\u00ef\\u00e7\\u00f6d\\u00e9 \\ud83c\\udf0d","values":{"count":7,"price":12.50,"ratio":0.00001,"score":85.05112877,"where":{"label":"SF","latitude":37.7749,"longitude":-122.4194}}}',
    ),
)


def test_canonical_json_matches_sql_probe_byte_for_byte() -> None:
    for name, doc_text, expected in PROBE_DOCS:
        value: Any = parse_snapshot_text(doc_text)
        assert canonical_json(value) == expected, name


def test_canonical_digest_matches_sql_probe_sha256() -> None:
    for name, doc_text, expected in PROBE_DOCS:
        value: Any = parse_snapshot_text(doc_text)
        assert canonical_digest(value) == (
            hashlib.sha256(expected.encode("utf-8")).hexdigest()
        ), name


def test_raw_retention_keeps_exact_digits_and_scale() -> None:
    value = parse_snapshot_text('{"a":1.50,"b":-0,"c":1e15,"d":9007199254740993}')
    assert isinstance(value["a"], Decimal) and value["a"] == Decimal("1.50")
    assert value["b"] == Decimal("-0")
    assert value["c"] == Decimal("1e15")
    assert value["d"] == 9007199254740993 and type(value["d"]) is int
    assert canonical_json(value) == (
        '{"a":1.50,"b":0,"c":1000000000000000,"d":9007199254740993}'
    )


def test_negative_zero_normalization_preserves_scale() -> None:
    assert canonical_json({"a": Decimal("-0"), "b": Decimal("-0.00")}) == (
        '{"a":0,"b":0.00}'
    )
    assert canonical_json({"a": Decimal("-0.50")}) == '{"a":-0.50}'


def test_legacy_scalar_rendering_unchanged() -> None:
    value = {
        "s": "a\u00e9\t\"q'",
        "f": 0.1,
        "t": True,
        "n": None,
        "l": [1, 2.5],
        "i": -7,
    }
    import json

    assert canonical_json(value) == json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    assert canonical_json(()) == "[]"
    assert canonical_json({}) == "{}"


def test_key_order_is_code_point_c_collation() -> None:
    assert canonical_json({"z": 1, "A": 2, "ä": 3, "ü": 4, "a": 5, "Z": 6, "0": 7}) == (
        r'{"0":7,"A":2,"Z":6,"a":5,"z":1,"\u00e4":3,"\u00fc":4}'
    )


def test_unicode_ensure_ascii_and_surrogate_pairs() -> None:
    assert canonical_json({"nb": "𠀋", "e": "é", "u7f": ""}) == (
        r'{"e":"\u00e9","nb":"\ud840\udc0b","u7f":"\u007f"}'
    )


def test_unsupported_type_rejected() -> None:
    with pytest.raises(TypeError):
        canonical_json({"a": object()})


# Float boundary qualification (probe-verified against the same disposable PG
# 18.6): the exact shortest-repr tokens json.dumps writes for these finite
# doubles (incl. exponent forms 1e+16/1e+300/1.7976931348623157e+308,
# subnormal 5e-324, -0.0, and 17-significant-digit values) parse to the same
# PG numerics, so the float branch of canonical_json must reproduce the SQL
# canonical bytes. Provenance: /tmp/oap-083-5-a/float-probe.sql /
# float-probe-actual.txt / float-canonicalization-probe-result.json.
FLOAT_BOUNDARY_DOC_TEXT = '{"f00":0.1,"f01":-1.25,"f02":1.5,"f03":100.0,"f04":123456789.12345678,"f05":1e+16,"f06":1e-05,"f07":5e-324,"f08":1.7976931348623157e+308,"f09":2.2250738585072014e-308,"f10":1.2345678901234568e+17,"f11":85.05112877,"f12":-122.4194,"f13":2.5e-10,"f14":-0.0,"f15":1e+100,"f16":1.2345678901234567e+19,"f17":0.30000000000000004,"f18":16777216.0,"f19":1e+300,"f20":1.2345678901234568e+18,"f21":0.0}'
FLOAT_BOUNDARY_EXPECTED = '{"f00":0.1,"f01":-1.25,"f02":1.5,"f03":100.0,"f04":123456789.12345678,"f05":10000000000000000,"f06":0.00001,"f07":0.000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000005,"f08":179769313486231570000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000,"f09":0.000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000022250738585072014,"f10":123456789012345680,"f11":85.05112877,"f12":-122.4194,"f13":0.00000000025,"f14":0.0,"f15":10000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000,"f16":12345678901234567000,"f17":0.30000000000000004,"f18":16777216.0,"f19":1000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000,"f20":1234567890123456800,"f21":0.0}'


def test_float_branch_matches_sql_probe_byte_for_byte() -> None:
    value: Any = json.loads(FLOAT_BOUNDARY_DOC_TEXT)
    assert canonical_json(value) == FLOAT_BOUNDARY_EXPECTED
    assert (
        canonical_digest(value)
        == hashlib.sha256(FLOAT_BOUNDARY_EXPECTED.encode("utf-8")).hexdigest()
    )


def test_nonfinite_float_rejected() -> None:
    with pytest.raises(ValueError):
        canonical_json({"a": float("inf")})
    with pytest.raises(ValueError):
        canonical_json({"a": float("nan")})


# ---------------------------------------------------------------------------
# canonical_json_bounded: exact preallocation cost and byte budget (R8)
# ---------------------------------------------------------------------------

from slaif_agent_site.content_model.canonical import (  # noqa: E402
    CanonicalBudgetExceeded,
    canonical_json_bounded,
)

BOUNDED_EXACT_BOUNDARY_CASES: tuple[tuple[str, Any, int], ...] = (
    ("empty object", {}, 2),
    ("one-entry object", {"a": 1}, 7),
    ("three-element array", [1, 2, 3], 7),
    ("nested object", {"a": {"b": 1}}, 13),
    ("ascii string list", ["a" * 5], 9),
    ("seven-element array", [1, 2, 3, 4, 5, 6, 7], 15),
    ("seven-entry object", {f"k{i}": i for i in range(1, 8)}, 50),
    ("astral escape (12 bytes)", ["\U00010000"], 16),
    ("bmp escape (6 bytes)", ["é"], 10),
    ("delete-char escape (6 bytes)", ["\x7f"], 10),
    ("control escape (6 bytes)", ["\x01"], 10),
    ("named newline escape (2 bytes)", ["\n"], 6),
    ("one-byte int scalar", 1, 1),
    ("1001-digit integer", 10**1000 + 7, 1001),
    ("decimal 1.50 retained scale", Decimal("1.50"), 4),
    ("fractional negative zero", Decimal("-0.0"), 3),
)


def test_bounded_within_budget_is_byte_identical() -> None:
    value: dict[str, Any] = {
        "z": [1, "two", {"three": 3.50, "four": None, "five": True}],
        "unicode": "üñïçödé \U0001f30d \x7f \x01 \n",
        "big": 9007199254740993,
    }
    assert canonical_json_bounded(value, 8 * 1024 * 1024) == canonical_json(value)


@pytest.mark.parametrize(
    ("label", "value", "exact_bytes"),
    BOUNDED_EXACT_BOUNDARY_CASES,
    ids=[case[0] for case in BOUNDED_EXACT_BOUNDARY_CASES],
)
def test_bounded_exact_byte_boundary(label: str, value: Any, exact_bytes: int) -> None:
    expected = canonical_json(value)
    assert len(expected.encode("utf-8")) == exact_bytes, label
    assert canonical_json_bounded(value, exact_bytes) == expected, label
    with pytest.raises(CanonicalBudgetExceeded):
        canonical_json_bounded(value, exact_bytes - 1)


def test_bounded_zero_budget_refuses_everything() -> None:
    with pytest.raises(CanonicalBudgetExceeded):
        canonical_json_bounded({}, 0)


def test_bounded_nonfinite_float_refused() -> None:
    with pytest.raises(ValueError):
        canonical_json_bounded({"a": float("inf")}, 8 * 1024 * 1024)
    with pytest.raises(ValueError):
        canonical_json_bounded({"a": float("nan")}, 8 * 1024 * 1024)


def test_bounded_unsupported_type_refused() -> None:
    with pytest.raises(TypeError):
        canonical_json_bounded({"a": {1, 2}}, 8 * 1024 * 1024)
    with pytest.raises(TypeError):
        canonical_json_bounded({1: 2}, 8 * 1024 * 1024)
