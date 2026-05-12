# arvis/errors/base.py

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from arvis.errors.types import ErrorDetails, ErrorPayload


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
    details: ErrorDetails = field(default_factory=dict)

    def to_dict(self) -> ErrorPayload:
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

    default_code = "ARVIS_ERROR"

    def __init__(
        self,
        message: str = "",
        *,
        code: str | None = None,
        details: ErrorDetails | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
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

    def to_dict(self) -> ErrorPayload:
        payload = self.metadata.to_dict()
        payload["message"] = self.message
        payload["type"] = self.__class__.__name__
        return payload


class ArvisInvariantViolation(ArvisError, ValueError):
    default_code = "INVARIANT_VIOLATION"
    category = ArvisErrorCategory.INVARIANT
    severity = ArvisErrorSeverity.FATAL
    retryable = False
    deterministic = True
    replay_safe = False


class ArvisRuntimeError(ArvisError, RuntimeError):
    default_code = "RUNTIME_ERROR"
    category = ArvisErrorCategory.RUNTIME


class ArvisDomainError(ArvisError):
    default_code = "DOMAIN_ERROR"
    category = ArvisErrorCategory.DOMAIN
    severity = ArvisErrorSeverity.ERROR
    retryable = False
    deterministic = True
    replay_safe = True


class ArvisExternalError(ArvisRuntimeError):
    default_code = "EXTERNAL_ERROR"
    category = ArvisErrorCategory.EXTERNAL
    retryable = True
    deterministic = False
    replay_safe = False


class ArvisReplayError(ArvisInvariantViolation):
    default_code = "REPLAY_ERROR"
    category = ArvisErrorCategory.REPLAY


class ArvisSecurityError(ArvisInvariantViolation):
    default_code = "SECURITY_ERROR"
    category = ArvisErrorCategory.SECURITY


class ArvisKernelError(ArvisRuntimeError):
    default_code = "KERNEL_ERROR"
    category = ArvisErrorCategory.KERNEL


class ArvisDegradedModeError(ArvisRuntimeError):
    default_code = "DEGRADED_MODE"
    category = ArvisErrorCategory.DEGRADED
    severity = ArvisErrorSeverity.WARNING
    degraded = True
    retryable = True
