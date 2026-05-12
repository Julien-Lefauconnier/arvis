# arvis/errors/provenance.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.errors.types import ErrorDetails
from arvis.types.identifiers import deterministic_id


@dataclass(frozen=True, slots=True)
class ErrorOrigin:
    component: str | None = None
    subsystem: str | None = None
    stage: str | None = None
    syscall: str | None = None
    provider: str | None = None
    process_id: str | None = None

    def to_dict(self) -> ErrorDetails:
        out: ErrorDetails = {}

        if self.component is not None:
            out["component"] = self.component
        if self.subsystem is not None:
            out["subsystem"] = self.subsystem
        if self.stage is not None:
            out["stage"] = self.stage
        if self.syscall is not None:
            out["syscall"] = self.syscall
        if self.provider is not None:
            out["provider"] = self.provider
        if self.process_id is not None:
            out["process_id"] = self.process_id

        return out


@dataclass(frozen=True, slots=True)
class ErrorCause:
    code: str
    error_type: str
    fingerprint: str | None = None

    def to_dict(self) -> ErrorDetails:
        out: ErrorDetails = {
            "code": self.code,
            "error_type": self.error_type,
        }

        if self.fingerprint is not None:
            out["fingerprint"] = self.fingerprint

        return out


def build_error_fingerprint(
    *,
    code: str,
    domain: str,
    category: str,
    severity: str,
    policy: str,
    semantics: tuple[str, ...],
    deterministic: bool,
    replay_safe: bool,
    degraded: bool,
) -> str:
    return deterministic_id(
        "err",
        code,
        domain,
        category,
        severity,
        policy,
        *sorted(semantics),
        deterministic,
        replay_safe,
        degraded,
        length=24,
    )


def cause_from_exception(exc: BaseException) -> ErrorCause:
    code = getattr(exc, "code", type(exc).__name__)
    fingerprint = getattr(exc, "fingerprint", None)

    return ErrorCause(
        code=str(code),
        error_type=type(exc).__name__,
        fingerprint=str(fingerprint) if fingerprint is not None else None,
    )
