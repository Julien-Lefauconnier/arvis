# arvis/kernel/kernel_invariants.py

from typing import Any

from arvis.errors.base import ArvisInvariantViolation, ErrorDomain
from arvis.errors.codes import ErrorCode


def assert_kernel_invariants(bundle: Any) -> None:
    """
    Global ARVIS invariants.
    """

    stability_score = getattr(bundle, "stability_score", None)

    if not isinstance(stability_score, int | float) or isinstance(
        stability_score, bool
    ):
        raise ArvisInvariantViolation(
            "kernel invariant violation: stability_score must be numeric",
            code=ErrorCode.KERNEL_INVARIANT_VIOLATION,
            domain=ErrorDomain.KERNEL,
            details={
                "component": "assert_kernel_invariants",
                "field": "stability_score",
                "retry_class": "permanent",
            },
        )

    if stability_score < 0.0 or stability_score > 1.0:
        raise ArvisInvariantViolation(
            "kernel invariant violation: stability_score must be in [0, 1]",
            code=ErrorCode.KERNEL_INVARIANT_VIOLATION,
            domain=ErrorDomain.KERNEL,
            details={
                "component": "assert_kernel_invariants",
                "field": "stability_score",
                "value": float(stability_score),
                "retry_class": "permanent",
            },
        )

    if bundle.reasoning_gap is not None:
        if bundle.reasoning_intent is None:
            raise ArvisInvariantViolation(
                (
                    "kernel invariant violation: "
                    "reasoning_intent required "
                    "when reasoning_gap exists"
                ),
                code=ErrorCode.KERNEL_INVARIANT_VIOLATION,
                domain=ErrorDomain.KERNEL,
                details={
                    "component": "assert_kernel_invariants",
                    "field": "reasoning_intent",
                    "reason": "missing_reasoning_intent",
                    "retry_class": "permanent",
                },
            )
