"""Deterministic human RBAC permission and built-in role catalog."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class PermissionDefinition:
    key: str
    category: str
    delegation_level: int | None
    site_assignable: bool = True
    installation_only: bool = False
    system_only: bool = False


READ_SCOPES = frozenset(
    """site:read content-model:read content-item:read collection-view:read
    page:read composition:read navigation:read translation:read media:read
    theme:read redirect:read component-catalog:read preview:inspect
    validation:read""".split()
)
L1_SCOPES = frozenset(
    """content-item:create content-item:write content-item:delete
    translation:write media:upload media-metadata:write media-reference:delete
    component-content-props:write seo:write preview:inspect""".split()
)
L2_SCOPES = frozenset(
    """page:create page:write page:delete page:restore page:move route:write
    redirect:create redirect:write redirect:delete navigation:create
    navigation:write navigation:delete collection-view:create
    collection-view:write collection-view:delete component-structure:create
    component-structure:delete component-structure:move
    relationship:write""".split()
)
L3_SCOPES = frozenset(
    """composition:write component-props:write component-variant:write
    layout:write responsive-design:write page-style:write theme-tokens:write
    preview:responsive-sweep""".split()
)
L4_SCOPES = frozenset(
    """content-model:create content-model:write content-model:delete
    field-definition:create field-definition:write field-definition:delete
    content-model:mapping site-structure:write global-region:create
    global-region:write global-region:delete header-footer:write
    theme-global:write locale:configure site-import:validate site-import:apply
    source:inspect site-reset:workspace""".split()
)

SITE_GOVERNANCE_SCOPES = frozenset(
    """site-domain:manage workspace:create workspace:freeze workspace:accept
    workspace:accept-selective workspace:discard capability:create
    capability:revoke site:publish membership:manage role:manage
    workspace:read-all site-policy:manage audit:read audit:export""".split()
)
INSTALLATION_SCOPES = frozenset(
    """site:create site:archive site:delete identity:configure
    installation:manage component-code:install server:configure secret:read
    audit:delete""".split()
)
SYSTEM_SCOPES = frozenset(
    """schema:migrate cow:deploy cow:harden cow:validate job:claim
    browser:internal-preview browser:internal-source media:gc artifact:gc
    backup:run restore:run""".split()
)


def _permission(key: str) -> PermissionDefinition:
    if key in READ_SCOPES:
        return PermissionDefinition(key, "READ", 0)
    for level, scopes in (
        (1, L1_SCOPES),
        (2, L2_SCOPES),
        (3, L3_SCOPES),
        (4, L4_SCOPES),
    ):
        if key in scopes:
            return PermissionDefinition(key, f"L{level}_WRITE", level)
    if key in SITE_GOVERNANCE_SCOPES:
        return PermissionDefinition(key, "HUMAN_ONLY", None)
    if key in INSTALLATION_SCOPES:
        return PermissionDefinition(
            key,
            "INSTALLATION_ONLY",
            None,
            site_assignable=False,
            installation_only=True,
        )
    return PermissionDefinition(
        key, "SYSTEM_ONLY", None, site_assignable=False, system_only=True
    )


PERMISSIONS = tuple(
    _permission(key)
    for key in sorted(
        READ_SCOPES
        | L1_SCOPES
        | L2_SCOPES
        | L3_SCOPES
        | L4_SCOPES
        | SITE_GOVERNANCE_SCOPES
        | INSTALLATION_SCOPES
        | SYSTEM_SCOPES
    )
)
PERMISSION_BY_KEY = MappingProxyType({item.key: item for item in PERMISSIONS})

ROLE_CEILINGS = MappingProxyType(
    {
        "SITE_OWNER": 4,
        "SITE_ARCHITECT": 4,
        "SITE_DESIGNER": 3,
        "SITE_EDITOR": 2,
        "CONTENT_EDITOR": 1,
        "REVIEWER": 0,
        "VIEWER": 0,
    }
)

ROLE_LABELS = MappingProxyType(
    {
        role_key: role_key.removeprefix("SITE_").replace("_", " ").title()
        for role_key in ROLE_CEILINGS
    }
)

_EDITORIAL_BY_LEVEL = {
    0: READ_SCOPES,
    1: READ_SCOPES | L1_SCOPES,
    2: READ_SCOPES | L1_SCOPES | L2_SCOPES,
    3: READ_SCOPES | L1_SCOPES | L2_SCOPES | L3_SCOPES,
    4: READ_SCOPES | L1_SCOPES | L2_SCOPES | L3_SCOPES | L4_SCOPES,
}
ROLE_DEFAULTS = MappingProxyType(
    {
        "SITE_OWNER": frozenset(_EDITORIAL_BY_LEVEL[4] | SITE_GOVERNANCE_SCOPES),
        "SITE_ARCHITECT": frozenset(_EDITORIAL_BY_LEVEL[4]),
        "SITE_DESIGNER": frozenset(_EDITORIAL_BY_LEVEL[3]),
        "SITE_EDITOR": frozenset(_EDITORIAL_BY_LEVEL[2]),
        "CONTENT_EDITOR": frozenset(_EDITORIAL_BY_LEVEL[1]),
        "REVIEWER": frozenset(READ_SCOPES | {"audit:read", "workspace:read-all"}),
        "VIEWER": READ_SCOPES,
    }
)

if set(ROLE_DEFAULTS) != set(ROLE_CEILINGS):
    raise RuntimeError("built-in role catalog drift")
if any(
    not permissions <= set(PERMISSION_BY_KEY) for permissions in ROLE_DEFAULTS.values()
):
    raise RuntimeError("role permission catalog drift")


__all__ = [
    "INSTALLATION_SCOPES",
    "L1_SCOPES",
    "L2_SCOPES",
    "L3_SCOPES",
    "L4_SCOPES",
    "PERMISSIONS",
    "PERMISSION_BY_KEY",
    "READ_SCOPES",
    "ROLE_CEILINGS",
    "ROLE_DEFAULTS",
    "ROLE_LABELS",
    "SITE_GOVERNANCE_SCOPES",
    "SYSTEM_SCOPES",
    "PermissionDefinition",
]
