"""Stable database-constrained content readiness states."""

from enum import StrEnum


class ReadinessState(StrEnum):
    """The only truthful states published by database bootstrap."""

    PENDING = "PENDING"
    EMPTY_SAFE = "EMPTY_SAFE"
    HARDENED = "HARDENED"


__all__ = ["ReadinessState"]
