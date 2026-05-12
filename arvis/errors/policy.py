# arvis/errors/policy.py

from __future__ import annotations

from dataclasses import dataclass

from arvis.errors.base import (
    ArvisError,
    ErrorPolicy,
)


@dataclass(frozen=True, slots=True)
class ErrorPolicyDecision:
    policy: ErrorPolicy
    retry: bool
    degrade: bool
    halt_process: bool
    halt_pipeline: bool
    fail_closed: bool
    escalate: bool
    observable: bool
    recoverable: bool


def decide_error_policy(error: ArvisError) -> ErrorPolicyDecision:
    policy = error.metadata.policy

    return ErrorPolicyDecision(
        policy=policy,
        retry=policy == ErrorPolicy.RETRY or error.retryable,
        degrade=policy == ErrorPolicy.DEGRADE or error.degraded,
        halt_process=policy == ErrorPolicy.HALT_PROCESS,
        halt_pipeline=policy == ErrorPolicy.HALT_PIPELINE,
        fail_closed=policy == ErrorPolicy.FAIL_CLOSED,
        escalate=policy == ErrorPolicy.ESCALATE,
        observable=True,
        recoverable=error.retryable or error.degraded,
    )
