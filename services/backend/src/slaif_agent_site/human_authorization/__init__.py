"""Site-scoped human membership and built-in RBAC."""

from .catalog import PERMISSIONS, ROLE_CEILINGS, ROLE_DEFAULTS
from .models import (
    CurrentHumanAuthority,
    CurrentHumanSite,
    HumanSiteContext,
    MembershipChange,
    MembershipRecord,
    MembershipStatus,
    PermissionCatalogRecord,
    RoleCatalogRecord,
)
from .service import (
    HumanAuthorizationError,
    HumanAuthorizationReason,
    HumanAuthorizationService,
)

__all__ = [
    "PERMISSIONS",
    "ROLE_CEILINGS",
    "ROLE_DEFAULTS",
    "HumanAuthorizationError",
    "HumanAuthorizationReason",
    "HumanAuthorizationService",
    "CurrentHumanAuthority",
    "CurrentHumanSite",
    "HumanSiteContext",
    "MembershipChange",
    "MembershipRecord",
    "MembershipStatus",
    "PermissionCatalogRecord",
    "RoleCatalogRecord",
]
