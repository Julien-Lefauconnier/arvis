# arvis/errors/disposition.py

from __future__ import annotations

from enum import StrEnum


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
