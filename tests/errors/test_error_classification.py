# tests/errors/test_error_classification.py

from __future__ import annotations

import json

from arvis.errors.base import ErrorDomain, ErrorPolicy
from arvis.errors.classification import (
    ErrorClassificationKind,
    classify_exception,
)


def test_classify_timeout_as_external() -> None:
    classification = classify_exception(TimeoutError("timeout"))

    assert classification.kind == ErrorClassificationKind.EXTERNAL
    assert classification.domain == ErrorDomain.EXTERNAL
    assert classification.policy == ErrorPolicy.RETRY
    assert classification.retryable is True
    assert classification.deterministic is False
    assert classification.replay_safe is False


def test_classify_json_decode_as_invalid_payload() -> None:
    exc = json.JSONDecodeError("bad json", "{", 0)

    classification = classify_exception(exc)

    assert classification.kind == ErrorClassificationKind.INVALID_PAYLOAD
    assert classification.domain == ErrorDomain.API
    assert classification.replay_safe is True


def test_classify_value_error_as_invariant_by_default() -> None:
    classification = classify_exception(ValueError("bad value"))

    assert classification.kind == ErrorClassificationKind.INVARIANT
    assert classification.policy == ErrorPolicy.FAIL_CLOSED
    assert classification.replay_safe is False


def test_boundary_hint_can_force_computation_degradation() -> None:
    classification = classify_exception(
        ValueError("bad numeric value"),
        boundary="computation",
    )

    assert classification.kind == ErrorClassificationKind.COMPUTATION
    assert classification.policy == ErrorPolicy.DEGRADE
    assert classification.degraded is True
    assert classification.replay_safe is True


def test_boundary_hint_can_force_contract_failure() -> None:
    classification = classify_exception(
        TypeError("invalid adapter shape"),
        boundary="contract",
    )

    assert classification.kind == ErrorClassificationKind.CONTRACT
    assert classification.policy == ErrorPolicy.FAIL_CLOSED
    assert classification.replay_safe is False
