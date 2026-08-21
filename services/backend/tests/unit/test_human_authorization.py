"""Human RBAC catalog, immutable context, and semantic service contracts."""

from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError
from slaif_agent_site.human_authorization import (
    PERMISSIONS,
    ROLE_CEILINGS,
    ROLE_DEFAULTS,
    HumanSiteContext,
    MembershipChange,
)
from slaif_agent_site.human_authorization.catalog import (
    INSTALLATION_SCOPES,
    SYSTEM_SCOPES,
)


def test_exact_roles_ceilings_and_permission_inventory_are_deterministic() -> None:
    assert dict(ROLE_CEILINGS) == {
        "SITE_OWNER": 4,
        "SITE_ARCHITECT": 4,
        "SITE_DESIGNER": 3,
        "SITE_EDITOR": 2,
        "CONTENT_EDITOR": 1,
        "REVIEWER": 0,
        "VIEWER": 0,
    }
    keys = [permission.key for permission in PERMISSIONS]
    assert keys == sorted(set(keys))
    assert "PLATFORM_ADMINISTRATOR" not in ROLE_DEFAULTS
    assert "site:publish" in ROLE_DEFAULTS["SITE_OWNER"]
    assert "site:publish" not in ROLE_DEFAULTS["SITE_ARCHITECT"]
    assert ROLE_DEFAULTS["VIEWER"] < ROLE_DEFAULTS["CONTENT_EDITOR"]
    assert ROLE_DEFAULTS["CONTENT_EDITOR"] < ROLE_DEFAULTS["SITE_EDITOR"]
    assert ROLE_DEFAULTS["SITE_EDITOR"] < ROLE_DEFAULTS["SITE_DESIGNER"]
    assert ROLE_DEFAULTS["SITE_DESIGNER"] < ROLE_DEFAULTS["SITE_ARCHITECT"]


def test_system_and_installation_permissions_cannot_be_membership_granted() -> None:
    by_key = {permission.key: permission for permission in PERMISSIONS}
    for key in INSTALLATION_SCOPES:
        assert by_key[key].installation_only
        assert not by_key[key].site_assignable
        assert by_key[key].delegation_level is None
    for key in SYSTEM_SCOPES:
        assert by_key[key].system_only
        assert not by_key[key].site_assignable
        assert by_key[key].delegation_level is None
    assert not (INSTALLATION_SCOPES | SYSTEM_SCOPES) & set(ROLE_DEFAULTS["SITE_OWNER"])


def test_membership_change_is_frozen_bounded_and_disjoint() -> None:
    change = MembershipChange(
        role_key="SITE_ARCHITECT",
        delegation_ceiling=4,
        allow_permissions=frozenset({"site:publish"}),
        deny_permissions=frozenset({"site-reset:workspace"}),
    )
    assert change.allow_permissions == frozenset({"site:publish"})
    with pytest.raises(ValidationError):
        MembershipChange(
            role_key="SITE_ARCHITECT",
            delegation_ceiling=5,
            allow_permissions=frozenset({"site:publish"}),
        )
    with pytest.raises(ValidationError):
        MembershipChange(
            role_key="SITE_ARCHITECT",
            delegation_ceiling=4,
            allow_permissions=frozenset({"site:publish"}),
            deny_permissions=frozenset({"site:publish"}),
        )


def test_human_site_context_has_no_public_constructor_or_credentials() -> None:
    with pytest.raises(TypeError):
        HumanSiteContext()
    context = HumanSiteContext._from_database(
        (
            UUID(int=1),
            UUID(int=2),
            "VIEWER",
            3,
            0,
            0,
            ["site:read"],
            False,
        )
    )
    assert context.effective_permissions == frozenset({"site:read"})
    assert not any(
        word in field
        for field in context.__dataclass_fields__
        for word in ("cookie", "token", "secret", "digest", "credential")
    )
