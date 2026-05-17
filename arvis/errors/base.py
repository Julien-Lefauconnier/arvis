# arvis/errors/base.py

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import cast
from uuid import uuid4

from arvis.errors.codes import ErrorCode
from arvis.errors.provenance import (
    ErrorCause,
    ErrorOrigin,
    build_error_fingerprint,
)
from arvis.errors.types import (
    ErrorDetails,
    ErrorPayload,
    ErrorPayloadValue,
)
from arvis.types.timestamps import utcnow


class ErrorDomain(StrEnum):
    CORE = "core"
    API = "api"
    KERNEL = "kernel"
    PIPELINE = "kernel.pipeline"
    SYSCALL = "kernel.syscall"
    REPLAY = "kernel.replay"
    MEMORY = "memory"
    VFS = "vfs"
    TOOL = "tool"
    LLM = "llm"
    PROJECTION = "kernel.projection"
    GATE = "kernel.gate"
    SECURITY = "kernel.security"
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
    OBSERVABLE = "observable"
    RECOVERABLE = "recoverable"
    DEGRADED_RUNTIME = "degraded_runtime"
    COMPUTATION_FAILURE = "computation_failure"


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
    origin: ErrorOrigin | None = None
    cause: ErrorCause | None = None
    fingerprint: str | None = None
    created_at: str | None = None
    monotonic_ns: int | None = None
    sensitive: bool = False
    error_id: str | None = None
    traceback: str | None = None

    redactable: bool = True

    def to_dict(self) -> ErrorPayload:
        payload: ErrorPayload = {
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
            "fingerprint": self.fingerprint,
            "created_at": self.created_at,
            "monotonic_ns": self.monotonic_ns,
            "sensitive": self.sensitive,
            "redactable": self.redactable,
            "error_id": self.error_id,
            "traceback": self.traceback,
        }

        if self.origin is not None:
            payload["origin"] = cast(
                ErrorPayloadValue,
                self.origin.to_dict(),
            )

        if self.cause is not None:
            payload["cause"] = cast(
                ErrorPayloadValue,
                self.cause.to_dict(),
            )

        return payload


class ArvisError(Exception):
    domain = ErrorDomain.CORE
    category = ArvisErrorCategory.RUNTIME
    severity = ArvisErrorSeverity.ERROR
    policy = ErrorPolicy.FAIL_CLOSED
    retryable = False
    deterministic = True
    replay_safe = True
    degraded = False

    default_code: str = ErrorCode.ARVIS_ERROR

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
        origin: ErrorOrigin | None = None,
        cause: ErrorCause | None = None,
        fingerprint: str | None = None,
        created_at: str | None = None,
        monotonic_ns: int | None = None,
        sensitive: bool = False,
        redactable: bool = True,
        traceback: str | None = None,
        error_id: str | None = None,
    ) -> None:
        super().__init__(message)

        self.message = message
        raw_code = code or self.default_code
        self.code = getattr(raw_code, "value", raw_code)

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
        self.origin = origin
        self.cause = cause
        self.created_at = created_at or utcnow().isoformat()
        self.monotonic_ns = (
            monotonic_ns if monotonic_ns is not None else time.monotonic_ns()
        )
        self.sensitive = sensitive
        self.redactable = redactable
        self.error_id = error_id or uuid4().hex
        self.traceback = traceback
        self.fingerprint = fingerprint

    @property
    def metadata(self) -> ArvisErrorMetadata:
        semantics = self._semantics()
        fingerprint = self.fingerprint or build_error_fingerprint(
            code=self.code,
            domain=self.domain.value,
            category=self.category.value,
            severity=self.severity.value,
            policy=self.policy.value,
            semantics=tuple(s.value for s in semantics),
            deterministic=self.deterministic,
            replay_safe=self.replay_safe,
            degraded=self.degraded,
        )
        return ArvisErrorMetadata(
            code=self.code,
            domain=self.domain,
            category=self.category,
            severity=self.severity,
            policy=self.policy,
            semantics=semantics,
            retryable=self.retryable,
            deterministic=self.deterministic,
            replay_safe=self.replay_safe,
            degraded=self.degraded,
            details=self.details,
            origin=self.origin,
            cause=self.cause,
            fingerprint=fingerprint,
            created_at=self.created_at,
            monotonic_ns=self.monotonic_ns,
            sensitive=self.sensitive,
            redactable=self.redactable,
            error_id=self.error_id,
            traceback=self.traceback,
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
            out.append(ErrorSemantics.RECOVERABLE)

        if self.degraded:
            out.append(ErrorSemantics.DEGRADED)
            out.append(ErrorSemantics.DEGRADED_RUNTIME)

        if self.policy == ErrorPolicy.FAIL_CLOSED:
            out.append(ErrorSemantics.FAIL_CLOSED)

        out.append(ErrorSemantics.OBSERVABLE)

        return tuple(out)

    def to_dict(self) -> ErrorPayload:
        payload = self.metadata.to_dict()
        payload["message"] = self.message
        payload["type"] = self.__class__.__name__
        return payload

    def clone(
        self,
        *,
        message: str | None = None,
        code: str | None = None,
        domain: ErrorDomain | None = None,
        category: ArvisErrorCategory | None = None,
        severity: ArvisErrorSeverity | None = None,
        policy: ErrorPolicy | None = None,
        retryable: bool | None = None,
        deterministic: bool | None = None,
        replay_safe: bool | None = None,
        degraded: bool | None = None,
        details: ErrorDetails | None = None,
        origin: ErrorOrigin | None = None,
        cause: ErrorCause | None = None,
        semantics: tuple[ErrorSemantics, ...] | None = None,
    ) -> ArvisError:
        merged_details = dict(self.details)

        if details:
            merged_details.update(details)

        return self.__class__(
            message or self.message,
            code=code or self.code,
            domain=domain or self.domain,
            category=category or self.category,
            severity=severity or self.severity,
            policy=policy or self.policy,
            retryable=(self.retryable if retryable is None else retryable),
            deterministic=(
                self.deterministic if deterministic is None else deterministic
            ),
            replay_safe=(self.replay_safe if replay_safe is None else replay_safe),
            degraded=(self.degraded if degraded is None else degraded),
            semantics=semantics or tuple(self.metadata.semantics),
            details=merged_details,
            origin=origin or self.origin,
            cause=cause or self.cause,
            fingerprint=self.fingerprint,
            created_at=self.created_at,
            monotonic_ns=self.monotonic_ns,
            sensitive=self.sensitive,
            redactable=self.redactable,
            traceback=self.traceback,
            error_id=self.error_id,
        )

    def to_safe_dict(
        self,
        *,
        include_traceback: bool = False,
        include_error_id: bool = True,
    ) -> ErrorPayload:
        from arvis.errors.redaction import redact_error_payload

        return redact_error_payload(
            self.to_dict(),
            include_traceback=include_traceback,
            include_error_id=include_error_id,
        )


class ArvisInvariantViolation(ArvisError, ValueError):
    default_code = ErrorCode.INVARIANT_VIOLATION
    category = ArvisErrorCategory.INVARIANT
    severity = ArvisErrorSeverity.FATAL
    retryable = False
    deterministic = True
    replay_safe = False


class ArvisRuntimeError(ArvisError, RuntimeError):
    default_code = ErrorCode.RUNTIME_ERROR
    category = ArvisErrorCategory.RUNTIME
    policy = ErrorPolicy.HALT_PROCESS


class ArvisDomainError(ArvisError):
    default_code = ErrorCode.DOMAIN_ERROR
    category = ArvisErrorCategory.DOMAIN
    policy = ErrorPolicy.FAIL_CLOSED
    severity = ArvisErrorSeverity.ERROR
    retryable = False
    deterministic = True
    replay_safe = True


class ArvisExternalError(ArvisRuntimeError):
    default_code = ErrorCode.EXTERNAL_ERROR
    category = ArvisErrorCategory.EXTERNAL
    domain = ErrorDomain.EXTERNAL
    policy = ErrorPolicy.RETRY
    retryable = True
    deterministic = False
    replay_safe = False


class ArvisReplayError(ArvisInvariantViolation):
    default_code = ErrorCode.REPLAY_ERROR
    category = ArvisErrorCategory.REPLAY
    domain = ErrorDomain.REPLAY


class ArvisSecurityError(ArvisInvariantViolation):
    default_code = ErrorCode.SECURITY_ERROR
    category = ArvisErrorCategory.SECURITY
    domain = ErrorDomain.SECURITY


class ArvisKernelError(ArvisRuntimeError):
    default_code = ErrorCode.KERNEL_ERROR
    category = ArvisErrorCategory.KERNEL
    domain = ErrorDomain.KERNEL
    policy = ErrorPolicy.FAIL_CLOSED


class ArvisDegradedModeError(ArvisRuntimeError):
    default_code = ErrorCode.DEGRADED_MODE
    category = ArvisErrorCategory.DEGRADED
    severity = ArvisErrorSeverity.WARNING
    policy = ErrorPolicy.DEGRADE
    degraded = True
    retryable = True
