# tests/errors/test_api_errors.py

from __future__ import annotations

from arvis.errors.api import (
    ArvisAPIError,
    CognitiveStateRequiredError,
    InvalidIRPayloadError,
)
from arvis.errors.base import (
    ArvisErrorCategory,
)


def test_api_error():
    error = ArvisAPIError("api")

    assert error.category == ArvisErrorCategory.RUNTIME
    assert error.replay_safe is True


def test_cognitive_state_required_error():
    error = CognitiveStateRequiredError("missing state")

    assert error.default_code == ("cognitive_state_required")


def test_invalid_ir_payload_error():
    error = InvalidIRPayloadError("invalid ir")

    assert error.default_code == ("invalid_ir_payload")
