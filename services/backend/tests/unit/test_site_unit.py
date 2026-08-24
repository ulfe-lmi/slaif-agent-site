"""Site normalization, immutable context, and semantic service contracts."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from pydantic import ValidationError
from slaif_agent_site.sites import (
    CreateSiteRequest,
    DomainMappingRequest,
    SiteContext,
    SiteService,
    SiteServiceError,
    SiteServiceReason,
)
from slaif_agent_site.sites.normalization import (
    SiteInputError,
    normalize_authority,
    normalize_hostname,
    normalize_locale,
    normalize_path_prefix,
    normalize_request_path,
    normalize_site_key,
)
from slaif_agent_site.sites.service import (
    CREATE_SITE_SQL,
    RESOLVE_LOCAL_SQL,
    RESOLVE_SITE_SQL,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("Research-Lab", "research-lab"), ("site1", "site1")],
)
def test_site_key_normalization(value: str, expected: str) -> None:
    assert normalize_site_key(value) == expected


@pytest.mark.parametrize(
    "value",
    ["", "-site", "site-", "site--name", "café", "admin", "api", "s" * 64],
)
def test_site_key_rejects_ambiguous_reserved_or_overlong_values(value: str) -> None:
    with pytest.raises(SiteInputError):
        normalize_site_key(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("EXAMPLE.COM", "example.com"),
        ("example.com.", "example.com"),
        ("bücher.example", "xn--bcher-kva.example"),
        ("localhost", "localhost"),
    ],
)
def test_hostname_idna_case_and_trailing_dot_normalization(
    value: str, expected: str
) -> None:
    assert normalize_hostname(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com",
        "user@example.com",
        "example.com/path",
        "example.com?x=1",
        "example.com#part",
        "example.com:8080",
        "127.0.0.1",
        "[::1]",
        "::1",
        "example..com",
        "-bad.example",
        "bad-.example",
        "example.com..",
        f"{'a' * 64}.example",
    ],
)
def test_stored_hostname_rejects_authority_and_ambiguity(value: str) -> None:
    with pytest.raises(SiteInputError):
        normalize_hostname(value)


def test_request_authority_separates_valid_port_from_stored_host() -> None:
    assert normalize_authority("Example.COM:8080").hostname == "example.com"
    assert normalize_authority("Example.COM:8080").port == 8080
    for value in ("example.com:0", "example.com:65536", "example.com:http"):
        with pytest.raises(SiteInputError):
            normalize_authority(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("/", "/"), ("/News", "/news"), ("/research/People", "/research/people")],
)
def test_path_prefix_normalization(value: str, expected: str) -> None:
    assert normalize_path_prefix(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "news",
        "/news/",
        "/news//item",
        "/news/../item",
        "/news/%2e%2e",
        "/news\\item",
        "/news?q=1",
        "/api",
        "/admin/site",
        "/agent",
        "/control/site",
        "/editor",
        "/_next/static",
        "/s/site",
        "/" + "a" * 512,
    ],
)
def test_path_prefix_rejects_reserved_or_ambiguous_values(value: str) -> None:
    with pytest.raises(SiteInputError):
        normalize_path_prefix(value)


def test_request_path_has_canonical_boundary_behavior() -> None:
    assert normalize_request_path("/Site/Page/") == "/site/page"
    assert normalize_request_path("/site-other") != normalize_request_path("/site")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("EN", "en"),
        ("sl-si", "sl-SI"),
        ("zh-hant-tw", "zh-Hant-TW"),
        ("de-CH-1901", "de-CH-1901"),
    ],
)
def test_locale_product_subset_normalization(value: str, expected: str) -> None:
    assert normalize_locale(value) == expected


@pytest.mark.parametrize(
    "value", ["", "e", "english", "en_US", "en-GB-variant-variant", "en-@"]
)
def test_locale_rejects_malformed_values(value: str) -> None:
    with pytest.raises(SiteInputError):
        normalize_locale(value)


def test_requests_forbid_caller_owned_identity_revision_and_status() -> None:
    request = CreateSiteRequest(
        site_key="Research-Lab", display_name=" Research Lab ", default_locale="sl-si"
    )
    assert request.model_dump() == {
        "site_key": "research-lab",
        "display_name": "Research Lab",
        "default_locale": "sl-SI",
    }
    with pytest.raises(ValidationError):
        CreateSiteRequest.model_validate(
            {
                **request.model_dump(),
                "site_id": str(UUID(int=1)),
                "status": "ACTIVE",
                "canonical_revision": 8,
            }
        )


def test_site_context_has_no_public_constructor() -> None:
    with pytest.raises(TypeError):
        SiteContext()


class FakeTransaction:
    async def __aenter__(self) -> None: ...

    async def __aexit__(self, *_arguments: object) -> None: ...


class FakeConnection:
    def __init__(self) -> None:
        self.rows: dict[str, list[tuple[Any, ...]]] = {}
        self.calls: list[tuple[str, tuple[object, ...]]] = []

    def transaction(self) -> FakeTransaction:
        return FakeTransaction()

    async def fetchrow(self, query: str, *arguments: object) -> Any:
        self.calls.append((query, arguments))
        rows = self.rows.get(query, [])
        return rows[0] if rows else None

    async def fetch(self, query: str, *arguments: object) -> list[tuple[Any, ...]]:
        self.calls.append((query, arguments))
        return self.rows.get(query, [])


class FakeAcquire:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    async def __aenter__(self) -> FakeConnection:
        return self.connection

    async def __aexit__(self, *_arguments: object) -> None: ...


class FakePool:
    def __init__(self, connection: FakeConnection) -> None:
        self.connection = connection

    def acquire(self, *, timeout: float) -> FakeAcquire:
        assert timeout > 0
        return FakeAcquire(self.connection)


def _site_row(key: str = "alpha") -> tuple[Any, ...]:
    now = datetime.now(UTC)
    return (
        UUID(int=1),
        key,
        "Alpha",
        "ACTIVE",
        0,
        "en",
        "catalog-v1",
        0,
        now,
        now,
    )


async def test_service_normalizes_before_create_and_uses_server_identity() -> None:
    connection = FakeConnection()
    connection.rows[CREATE_SITE_SQL] = [_site_row()]
    service = SiteService(FakePool(connection))
    result = await service.create(
        CreateSiteRequest(site_key="ALPHA", display_name="Alpha", default_locale="EN")
    )
    assert result.site_id == UUID(int=1)
    assert connection.calls == [
        (CREATE_SITE_SQL, ("alpha", "Alpha", "en", "catalog-v1"))
    ]


async def test_resolver_uses_longest_boundary_match_and_constant_denial() -> None:
    connection = FakeConnection()
    context = (
        UUID(int=1),
        "alpha",
        "ACTIVE",
        4,
        "en",
        "example.test",
        "/research",
    )
    connection.rows[RESOLVE_SITE_SQL] = [context]
    service = SiteService(FakePool(connection))
    resolved = await service.resolve("EXAMPLE.TEST:8080", "/research/page/")
    assert resolved.matched_path_prefix == "/research"
    assert connection.calls == [(RESOLVE_SITE_SQL, ("example.test", "/research/page"))]
    for authority, path in (("unknown", "/"), ("example.test", "/api")):
        with pytest.raises(SiteServiceError) as error:
            await service.resolve(authority, path)
        assert error.value.reason is SiteServiceReason.NOT_FOUND


async def test_local_resolver_derives_site_key_from_path_not_request_id() -> None:
    connection = FakeConnection()
    connection.rows[RESOLVE_LOCAL_SQL] = [(UUID(int=2), "beta", "ACTIVE", 0, "sl-SI")]
    service = SiteService(FakePool(connection))
    context = await service.resolve("localhost:8080", "/s/BETA/news")
    assert context.site_id == UUID(int=2)
    assert context.matched_path_prefix == "/s/beta"
    assert connection.calls == [(RESOLVE_LOCAL_SQL, ("beta",))]


async def test_local_namespace_never_falls_through_to_domain_resolution() -> None:
    connection = FakeConnection()
    service = SiteService(FakePool(connection))
    for authority, path in (("example.test", "/s/beta"), ("localhost", "/s")):
        with pytest.raises(SiteServiceError) as error:
            await service.resolve(authority, path)
        assert error.value.reason is SiteServiceReason.NOT_FOUND
    assert connection.calls == []


def test_domain_request_normalizes_equivalent_mapping() -> None:
    mapping = DomainMappingRequest(
        hostname="BÜCHER.EXAMPLE.", path_prefix="/Research", is_primary=True
    )
    assert mapping.hostname == "xn--bcher-kva.example"
    assert mapping.path_prefix == "/research"
