"""Local and future federated identity contracts owned by Agent-Site."""

from .models import (
    IdentityInputError,
    InitialLocalAdministratorRequest,
    InitialLocalAdministratorResult,
    normalize_local_username,
)
from .sessions import (
    HumanSessionContext,
    HumanSessionError,
    HumanSessionPolicy,
    HumanSessionService,
    IssuedHumanSession,
    SessionCookiePolicy,
)

__all__ = [
    "IdentityInputError",
    "InitialLocalAdministratorRequest",
    "InitialLocalAdministratorResult",
    "normalize_local_username",
    "HumanSessionContext",
    "HumanSessionError",
    "HumanSessionPolicy",
    "HumanSessionService",
    "IssuedHumanSession",
    "SessionCookiePolicy",
]
from .authentication import (
    LocalAuthenticationError,
    LocalAuthenticationResult,
    LocalAuthenticationService,
    LocalLoginRequest,
)

__all__ = [
    "LocalAuthenticationError",
    "LocalAuthenticationResult",
    "LocalAuthenticationService",
    "LocalLoginRequest",
]
