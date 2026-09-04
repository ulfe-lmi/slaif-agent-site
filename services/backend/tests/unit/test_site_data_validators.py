from uuid import uuid4

import pytest
from slaif_agent_site.content_model.site_data_models import (
    AgentCreateRedirectRequest,
    AgentUpdateRedirectRequest,
    CreateLocaleRequest,
    CreateNavigationItemRequest,
    CreateProposedSideEffectRequest,
    CreateRedirectRequest,
)
from slaif_agent_site.content_model.site_data_validators import (
    validate_internal_route,
    validate_redirect,
    validate_side_effect,
)


def test_locale_and_route_models_normalize_once() -> None:
    assert CreateLocaleRequest(tag="sl-si").tag == "sl-SI"
    assert validate_internal_route("/News") == "/news"
    assert (
        CreateRedirectRequest(source_route="/Old", target="/new").source_route == "/old"
    )


@pytest.mark.parametrize(
    "value", ["/api/private", "/a//b", "/a/../b", "/a%2Fb", "/a\\b"]
)
def test_routes_reject_reserved_or_ambiguous_forms(value: str) -> None:
    with pytest.raises(ValueError):
        validate_internal_route(value)


def test_redirects_reject_unsafe_targets_and_self_loops() -> None:
    with pytest.raises(ValueError):
        validate_redirect("/old", "javascript:alert(1)")
    with pytest.raises(ValueError):
        validate_redirect("/old", "/old")
    with pytest.raises(ValueError):
        CreateNavigationItemRequest(
            navigation_id=uuid4(),
            target_kind="EXTERNAL",
            target_value="https://user:password@example.test",
            labels={"en": "Unsafe"},
        )


def test_agent_redirect_models_normalize_and_require_meaningful_patch() -> None:
    created = AgentCreateRedirectRequest(
        source_route="/Old",
        target="/Destination",
    )
    assert created.source_route == "/old"
    assert created.target == "/destination"
    with pytest.raises(ValueError):
        AgentUpdateRedirectRequest(expected_row_version=1)
    with pytest.raises(ValueError):
        AgentUpdateRedirectRequest(target=None, expected_row_version=1)
    with pytest.raises(ValueError):
        AgentCreateRedirectRequest(
            source_route="/download.php", target="https://example.test/download"
        )


def test_proposed_side_effect_is_inert_and_bounded() -> None:
    request = CreateProposedSideEffectRequest(
        workspace_id=uuid4(), kind="analytics_event", payload={"name": "view"}
    )
    validate_side_effect(request.kind, request.payload)
    with pytest.raises(ValueError):
        validate_side_effect("webhook", {})
    with pytest.raises(ValueError):
        validate_side_effect("cache_purge", {"value": "; drop"})
