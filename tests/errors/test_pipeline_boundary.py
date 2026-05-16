# tests/errors/test_pipeline_boundary.py

from __future__ import annotations

from arvis.errors import ErrorManager
from arvis.errors.base import ErrorPolicy
from arvis.errors.boundaries.pipeline import (
    capture_pipeline_contract_failure,
    capture_pipeline_degraded_failure,
    capture_pipeline_runtime_failure,
)
from arvis.errors.codes import ErrorCode
from arvis.errors.context import DefaultErrorContext


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


def test_capture_pipeline_degraded_failure() -> None:
    ctx = DefaultErrorContext()

    payload = capture_pipeline_degraded_failure(
        ctx,
        RuntimeError("adapter failed"),
        component="TestAdapter",
        message="Pipeline degraded failure",
    )

    assert payload["code"] == ErrorCode.PIPELINE_STAGE_DEGRADED
    assert payload["degraded"] is True
    assert payload["policy"] == ErrorPolicy.DEGRADE
    assert payload["details"]["component"] == "TestAdapter"
    assert payload["details"]["runtime_degraded"] is True
    assert payload["origin"]["subsystem"] == "pipeline"
    assert ErrorManager.runtime_degradation_state(ctx)["active"] is True


def test_capture_pipeline_runtime_failure() -> None:
    ctx = DefaultErrorContext()

    payload = capture_pipeline_runtime_failure(
        ctx,
        RuntimeError("projection failed"),
        component="ProjectionStage",
        message="Pipeline runtime failure",
    )

    assert payload["code"] == ErrorCode.PIPELINE_STAGE_FAILURE
    assert payload["degraded"] is False
    assert payload["policy"] == ErrorPolicy.FAIL_CLOSED
    assert payload["replay_safe"] is False
    assert payload["details"]["component"] == "ProjectionStage"
    assert payload["details"]["runtime_degraded"] is False
    assert payload["origin"]["subsystem"] == "pipeline"


def test_capture_pipeline_contract_failure() -> None:
    ctx = DefaultErrorContext()

    payload = capture_pipeline_contract_failure(
        ctx,
        RuntimeError("missing execution_state"),
        component="PipelineFinalizeService",
        message="Pipeline contract failure",
        details={"missing": "execution_state"},
    )

    assert payload["code"] == ErrorCode.PIPELINE_EXECUTION_CONTRACT_VIOLATION
    assert payload["severity"] == "fatal"
    assert payload["policy"] == ErrorPolicy.FAIL_CLOSED
    assert payload["details"]["component"] == "PipelineFinalizeService"
    assert payload["details"]["contract_violation"] is True
    assert payload["details"]["missing"] == "execution_state"
