# tests/errors/test_pipeline_boundary.py

from __future__ import annotations

from arvis.errors.boundaries.pipeline import capture_pipeline_degraded_failure
from arvis.errors.codes import ErrorCode
from arvis.errors.context import DefaultErrorContext
from arvis.errors.manager import ErrorManager


def test_capture_pipeline_degraded_failure_attaches_structured_error() -> None:
    ctx = DefaultErrorContext()

    payload = capture_pipeline_degraded_failure(
        ctx,
        ValueError("boom"),
        component="ProjectionIRAdapter",
        message="Projection IR adapter failure",
        details={
            "adapter": "projection",
        },
    )

    assert payload["type"] == "PipelineStageDegradedError"
    assert payload["code"] == ErrorCode.PIPELINE_STAGE_DEGRADED.value
    assert payload["domain"] == "kernel.pipeline"
    assert payload["severity"] == "warning"
    assert payload["policy"] == "degrade"
    assert payload["degraded"] is True
    assert payload["replay_safe"] is True

    details = payload["details"]
    assert isinstance(details, dict)
    assert details["component"] == "ProjectionIRAdapter"
    assert details["runtime_degraded"] is True
    assert details["adapter"] == "projection"


def test_capture_pipeline_degraded_failure_tracks_runtime_degradation() -> None:
    ctx = DefaultErrorContext()

    capture_pipeline_degraded_failure(
        ctx,
        RuntimeError("failed"),
        component="CognitiveIRBuilder",
        message="Cognitive IR build failure",
    )

    state = ErrorManager.runtime_degradation_state(ctx)

    assert state["active"] is True
    assert state["count"] == 1
    assert state["last_code"] == ErrorCode.PIPELINE_STAGE_DEGRADED.value
    assert state["domains"] == {
        "kernel.pipeline": 1,
    }


def test_capture_pipeline_degraded_failure_preserves_origin_and_cause() -> None:
    ctx = DefaultErrorContext()

    payload = capture_pipeline_degraded_failure(
        ctx,
        TypeError("bad type"),
        component="CognitiveIRValidator",
        message="Cognitive IR validation failure",
    )

    origin = payload["origin"]
    cause = payload["cause"]

    assert isinstance(origin, dict)
    assert origin["component"] == "CognitiveIRValidator"
    assert origin["subsystem"] == "pipeline"

    assert isinstance(cause, dict)
    assert cause["error_type"] == "TypeError"
