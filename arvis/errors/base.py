# arvis/errors/base.py

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ArvisErrorCategory(StrEnum):
    INVARIANT = "invariant"
    RUNTIME = "runtime"
    DOMAIN = "domain"
    EXTERNAL = "external"
    REPLAY = "replay"
    SECURITY = "security"
    KERNEL = "kernel"
    DEGRADED = "degraded"


class ArvisErrorSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass(slots=True, frozen=True)
class ArvisErrorMetadata:
    code: str
    category: ArvisErrorCategory
    severity: ArvisErrorSeverity = ArvisErrorSeverity.ERROR
    retryable: bool = False
    deterministic: bool = True
    replay_safe: bool = True
    degraded: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "category": self.category.value,
            "severity": self.severity.value,
            "retryable": self.retryable,
            "deterministic": self.deterministic,
            "replay_safe": self.replay_safe,
            "degraded": self.degraded,
            "details": dict(self.details),
        }


class ArvisError(Exception):
    category = ArvisErrorCategory.RUNTIME
    severity = ArvisErrorSeverity.ERROR
    retryable = False
    deterministic = True
    replay_safe = True
    degraded = False

    def __init__(
        self,
        message: str = "",
        *,
        code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = dict(details or {})

    @property
    def metadata(self) -> ArvisErrorMetadata:
        return ArvisErrorMetadata(
            code=self.code,
            category=self.category,
            severity=self.severity,
            retryable=self.retryable,
            deterministic=self.deterministic,
            replay_safe=self.replay_safe,
            degraded=self.degraded,
            details=self.details,
        )

    def to_dict(self) -> dict[str, Any]:
        payload = self.metadata.to_dict()
        payload["message"] = self.message
        payload["type"] = self.__class__.__name__
        return payload


class ArvisInvariantViolation(ArvisError, ValueError):
    category = ArvisErrorCategory.INVARIANT
    severity = ArvisErrorSeverity.FATAL
    retryable = False
    deterministic = True
    replay_safe = False


class ArvisRuntimeError(ArvisError, RuntimeError):
    category = ArvisErrorCategory.RUNTIME


class ArvisDomainError(ArvisError):
    category = ArvisErrorCategory.DOMAIN
    severity = ArvisErrorSeverity.ERROR
    retryable = False
    deterministic = True
    replay_safe = True


class ArvisExternalError(ArvisRuntimeError):
    category = ArvisErrorCategory.EXTERNAL
    retryable = True
    deterministic = False
    replay_safe = False


class ArvisReplayError(ArvisInvariantViolation):
    category = ArvisErrorCategory.REPLAY


class ArvisSecurityError(ArvisInvariantViolation):
    category = ArvisErrorCategory.SECURITY


class ArvisKernelError(ArvisRuntimeError):
    category = ArvisErrorCategory.KERNEL


class ArvisDegradedModeError(ArvisRuntimeError):
    category = ArvisErrorCategory.DEGRADED
    severity = ArvisErrorSeverity.WARNING
    degraded = True
    retryable = True
