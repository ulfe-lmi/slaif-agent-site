"""Typed liveness and bounded injected readiness primitives."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .authority import ProcessKind


class ComponentStatus(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"


class ReadinessStatus(StrEnum):
    READY = "ready"
    NOT_READY = "not_ready"


class LivenessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: str = Field(default="ok", pattern=r"^ok$")
    service: ProcessKind


class ProbeResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: ComponentStatus
    reason: str | None = Field(
        default=None,
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9_]*$",
    )

    @model_validator(mode="after")
    def validate_status_reason(self) -> Self:
        if self.status is ComponentStatus.OK and self.reason is not None:
            raise ValueError("ready probes have no failure reason")
        if self.status is ComponentStatus.UNAVAILABLE and self.reason is None:
            raise ValueError("unavailable probes require a reason code")
        return self

    @classmethod
    def ready(cls) -> ProbeResult:
        return cls(status=ComponentStatus.OK)

    @classmethod
    def unavailable(cls, reason: str = "dependency_unavailable") -> ProbeResult:
        return cls(status=ComponentStatus.UNAVAILABLE, reason=reason)


class ReadinessComponent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    component: str = Field(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z][a-z0-9_-]*$",
    )
    status: ComponentStatus
    reason: str | None = Field(
        default=None,
        max_length=64,
        pattern=r"^[a-z][a-z0-9_]*$",
    )


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    status: ReadinessStatus
    service: ProcessKind
    components: tuple[ReadinessComponent, ...]


ProbeCallable = Callable[[], Awaitable[ProbeResult]]


@dataclass(frozen=True, slots=True)
class ReadinessProbe:
    component: str
    check: ProbeCallable

    def __post_init__(self) -> None:
        ReadinessComponent(
            component=self.component,
            status=ComponentStatus.OK,
        )


async def _run_probe(probe: ReadinessProbe, timeout: float) -> ReadinessComponent:
    try:
        result = await asyncio.wait_for(probe.check(), timeout=timeout)
        if not isinstance(result, ProbeResult):
            raise TypeError
        return ReadinessComponent(
            component=probe.component,
            status=result.status,
            reason=result.reason,
        )
    except TimeoutError:
        return ReadinessComponent(
            component=probe.component,
            status=ComponentStatus.UNAVAILABLE,
            reason="timeout",
        )
    except Exception:
        return ReadinessComponent(
            component=probe.component,
            status=ComponentStatus.UNAVAILABLE,
            reason="probe_error",
        )


async def evaluate_readiness(
    process: ProcessKind,
    probes: Sequence[ReadinessProbe],
    *,
    timeout: float,
) -> ReadinessResponse:
    """Evaluate probes concurrently and expose only stable reason codes."""

    components = tuple(
        await asyncio.gather(*(_run_probe(probe, timeout) for probe in probes))
    )
    ready = all(component.status is ComponentStatus.OK for component in components)
    return ReadinessResponse(
        status=ReadinessStatus.READY if ready else ReadinessStatus.NOT_READY,
        service=process,
        components=components,
    )


__all__ = [
    "ComponentStatus",
    "LivenessResponse",
    "ProbeResult",
    "ReadinessComponent",
    "ReadinessProbe",
    "ReadinessResponse",
    "ReadinessStatus",
    "evaluate_readiness",
]
