# arvis/errors/base.py

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from arvis.errors.types import ErrorDetails, ErrorPayload


class ErrorDomain(StrEnum):
    CORE = "core"
    API = "api"
    KERNEL = "kernel"
    PIPELINE = "pipeline"
    SYSCALL = "syscall"
    REPLAY = "replay"
    MEMORY = "memory"
    VFS = "vfs"
    TOOL = "tool"
    LLM = "llm"
    PROJECTION = "projection"
    GATE = "gate"
    SECURITY = "security"
    EXTERNAL = "external"


class ErrorSemantics(StrEnum):
    FAIL_CLOSED = "fail_closed"
    FAIL_OPEN = "fail_open"
    DEGRADED = "degraded"
    TRANSIENT = "transient"
    DETERMINISTIC = "deterministic"
    NON_DETERMINISTIC = "non_deterministic"
    REPLAY_SAFE = "replay_safe"
    REPLAY_UNSAFE = "replay_unsafe"


class ErrorPolicy(StrEnum):
    IGNORE = "ignore"
    RETRY = "retry"
    DEGRADE = "degrade"
    HALT_PROCESS = "halt_process"
    HALT_PIPELINE = "halt_pipeline"
    FAIL_CLOSED = "fail_closed"
    ESCALATE = "escalate"


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
    domain: ErrorDomain
    category: ArvisErrorCategory
    severity: ArvisErrorSeverity = ArvisErrorSeverity.ERROR
    policy: ErrorPolicy = ErrorPolicy.FAIL_CLOSED
    semantics: tuple[ErrorSemantics, ...] = ()
    retryable: bool = False
    deterministic: bool = True
    replay_safe: bool = True
    degraded: bool = False
    details: ErrorDetails = field(default_factory=dict)

    def to_dict(self) -> ErrorPayload:
        return {
            "code": self.code,
            "domain": self.domain.value,
            "category": self.category.value,
            "severity": self.severity.value,
            "policy": self.policy.value,
            "semantics": [s.value for s in self.semantics],
            "retryable": self.retryable,
            "deterministic": self.deterministic,
            "replay_safe": self.replay_safe,
            "degraded": self.degraded,
            "details": dict(self.details),
        }


class ArvisError(Exception):
    domain = ErrorDomain.CORE
    category = ArvisErrorCategory.RUNTIME
    severity = ArvisErrorSeverity.ERROR
    policy = ErrorPolicy.FAIL_CLOSED
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
        domain: ErrorDomain | None = None,
        category: ArvisErrorCategory | None = None,
        severity: ArvisErrorSeverity | None = None,
        policy: ErrorPolicy | None = None,
        retryable: bool | None = None,
        deterministic: bool | None = None,
        replay_safe: bool | None = None,
        degraded: bool | None = None,
        semantics: tuple[ErrorSemantics, ...] | None = None,
        details: ErrorDetails | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        self.code = code or self.default_code

        self.domain = domain or self.__class__.domain
        self.category = category or self.__class__.category
        self.severity = severity or self.__class__.severity
        self.policy = policy or self.__class__.policy

        self.retryable = (
            retryable if retryable is not None else self.__class__.retryable
        )

        self.deterministic = (
            deterministic if deterministic is not None else self.__class__.deterministic
        )

        self.replay_safe = (
            replay_safe if replay_safe is not None else self.__class__.replay_safe
        )

        self.degraded = degraded if degraded is not None else self.__class__.degraded

        self._custom_semantics = semantics
        self.details = dict(details or {})

    @property
    def metadata(self) -> ArvisErrorMetadata:
        return ArvisErrorMetadata(
            code=self.code,
            domain=self.domain,
            category=self.category,
            severity=self.severity,
            policy=self.policy,
            semantics=self._semantics(),
            retryable=self.retryable,
            deterministic=self.deterministic,
            replay_safe=self.replay_safe,
            degraded=self.degraded,
            details=self.details,
        )

    def _semantics(self) -> tuple[ErrorSemantics, ...]:
        if self._custom_semantics is not None:
            return tuple(self._custom_semantics)

        out: list[ErrorSemantics] = []

        out.append(
            ErrorSemantics.DETERMINISTIC
            if self.deterministic
            else ErrorSemantics.NON_DETERMINISTIC
        )

        out.append(
            ErrorSemantics.REPLAY_SAFE
            if self.replay_safe
            else ErrorSemantics.REPLAY_UNSAFE
        )

        if self.retryable:
            out.append(ErrorSemantics.TRANSIENT)

        if self.degraded:
            out.append(ErrorSemantics.DEGRADED)

        if self.policy == ErrorPolicy.FAIL_CLOSED:
            out.append(ErrorSemantics.FAIL_CLOSED)

        return tuple(out)

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
    policy = ErrorPolicy.HALT_PROCESS


class ArvisDomainError(ArvisError):
    default_code = "DOMAIN_ERROR"
    category = ArvisErrorCategory.DOMAIN
    policy = ErrorPolicy.FAIL_CLOSED
    severity = ArvisErrorSeverity.ERROR
    retryable = False
    deterministic = True
    replay_safe = True


class ArvisExternalError(ArvisRuntimeError):
    default_code = "EXTERNAL_ERROR"
    category = ArvisErrorCategory.EXTERNAL
    domain = ErrorDomain.EXTERNAL
    policy = ErrorPolicy.RETRY
    retryable = True
    deterministic = False
    replay_safe = False


class ArvisReplayError(ArvisInvariantViolation):
    default_code = "REPLAY_ERROR"
    category = ArvisErrorCategory.REPLAY
    domain = ErrorDomain.REPLAY


class ArvisSecurityError(ArvisInvariantViolation):
    default_code = "SECURITY_ERROR"
    category = ArvisErrorCategory.SECURITY
    domain = ErrorDomain.SECURITY


class ArvisKernelError(ArvisRuntimeError):
    default_code = "KERNEL_ERROR"
    category = ArvisErrorCategory.KERNEL
    domain = ErrorDomain.KERNEL
    policy = ErrorPolicy.FAIL_CLOSED


class ArvisDegradedModeError(ArvisRuntimeError):
    default_code = "DEGRADED_MODE"
    category = ArvisErrorCategory.DEGRADED
    severity = ArvisErrorSeverity.WARNING
    policy = ErrorPolicy.DEGRADE
    degraded = True
    retryable = True
