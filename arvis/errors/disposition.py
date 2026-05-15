# arvis/errors/disposition.py

from __future__ import annotations

from enum import StrEnum

from arvis.errors.base import ErrorPolicy


class ErrorDisposition(StrEnum):
    CONTINUE = "continue"
    ABSTAIN = "abstain"
    DEGRADE = "degrade"
    RETRY = "retry"
    HALT_STAGE = "halt_stage"
    HALT_PIPELINE = "halt_pipeline"
    HALT_PROCESS = "halt_process"
    FAIL_CLOSED = "fail_closed"
    ESCALATE = "escalate"


def disposition_from_policy(policy: ErrorPolicy) -> ErrorDisposition:
    match policy:
        case ErrorPolicy.IGNORE:
            return ErrorDisposition.CONTINUE
        case ErrorPolicy.RETRY:
            return ErrorDisposition.RETRY
        case ErrorPolicy.DEGRADE:
            return ErrorDisposition.DEGRADE
        case ErrorPolicy.HALT_PROCESS:
            return ErrorDisposition.HALT_PROCESS
        case ErrorPolicy.HALT_PIPELINE:
            return ErrorDisposition.HALT_PIPELINE
        case ErrorPolicy.FAIL_CLOSED:
            return ErrorDisposition.FAIL_CLOSED
        case ErrorPolicy.ESCALATE:
            return ErrorDisposition.ESCALATE

    raise ValueError(f"Unhandled ErrorPolicy: {policy!r}")
