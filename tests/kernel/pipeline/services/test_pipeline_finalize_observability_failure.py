# tests/kernel/pipeline/services/test_pipeline_finalize_observability_failure.py

from __future__ import annotations

from unittest.mock import patch

from arvis.kernel.execution.execution_gate_status import (
    ExecutionGateStatus,
)
from arvis.kernel.pipeline.cognitive_pipeline import (
    CognitivePipeline,
)
from arvis.kernel.pipeline.services.pipeline_finalize_service import (
    PipelineFinalizeService,
)
from arvis.math.lyapunov.lyapunov_gate import (
    LyapunovVerdict,
)
from tests.fixtures.builders.context_builder import (
    build_finalize_compatible_context,
)


def test_pipeline_finalize_observability_failure_is_degraded() -> None:
    pipeline = CognitivePipeline()

    ctx = build_finalize_compatible_context()

    # ---------------------------------------------------------
    # Minimal finalize compatibility
    # ---------------------------------------------------------
    ctx.gate_result = LyapunovVerdict.ALLOW

    runtime = ctx.execution.execution_state

    assert runtime is not None

    runtime.can_execute = True
    runtime.requires_confirmation = False
    runtime.execution_status = ExecutionGateStatus.READY

    # ---------------------------------------------------------
    # Observability crash
    # ---------------------------------------------------------
    with patch(
        "arvis.kernel.pipeline.services.pipeline_finalize_service."
        "PipelineObservabilityService.run",
        side_effect=RuntimeError("observability boom"),
    ):
        result = PipelineFinalizeService.run(
            pipeline,
            ctx,
        )

    # ---------------------------------------------------------
    # Finalize must continue
    # ---------------------------------------------------------
    assert result is not None

    # ---------------------------------------------------------
    # Error must be attached as degraded
    # ---------------------------------------------------------
    errors = ctx.extra.get("errors", [])

    assert any(
        err.get("details", {}).get("component") == "PipelineObservabilityService"
        for err in errors
        if isinstance(err, dict)
    )

    # ---------------------------------------------------------
    # Runtime authority still finalized
    # ---------------------------------------------------------
    runtime = ctx.execution.execution_state

    assert runtime is not None
    assert runtime.execution_status == ExecutionGateStatus.READY
    assert runtime.can_execute is True
