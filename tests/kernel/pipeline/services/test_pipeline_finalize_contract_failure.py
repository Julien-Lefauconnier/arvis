# tests/kernel/pipeline/services/test_pipeline_finalize_contract_failure.py

from __future__ import annotations

from unittest.mock import patch

import pytest

from arvis.kernel.pipeline.cognitive_pipeline import (
    CognitivePipeline,
)
from arvis.kernel.pipeline.services.pipeline_finalize_service import (
    PipelineFinalizeService,
)
from tests.fixtures.builders.context_builder import (
    build_finalize_compatible_context,
)


def test_pipeline_finalize_fail_closed_on_contract_violation() -> None:
    pipeline = CognitivePipeline()

    ctx = build_finalize_compatible_context()

    # Force finalize validation path
    ctx.observability.state.cognitive_state = object()

    with patch(
        "arvis.contracts.cognitive_state_contract.CognitiveStateContract.validate",
        side_effect=ValueError("invalid cognitive state"),
    ):
        with pytest.raises(ValueError):
            PipelineFinalizeService.run(
                pipeline,
                ctx,
            )

    attached_errors = ctx.extra.get("errors", [])

    assert attached_errors

    contract_errors = [
        err
        for err in attached_errors
        if err["code"] == "pipeline_execution_contract_violation"
    ]

    assert contract_errors

    error = contract_errors[0]

    assert error["code"] == "pipeline_execution_contract_violation"

    assert error["details"]["contract_violation"] is True

    assert error["details"]["component"] in {
        "CognitiveIRValidator",
        "CognitiveStateContract",
    }

    assert error["policy"] == "fail_closed"

    assert error["replay_safe"] is False


# ---------------------------------------------------------------
# Campaign RELEASE (LOT R2): the two lifecycle contract guards.
# Finalize is a runtime-authority boundary: a context reaching it
# without an execution_state, or with an execution_state that never
# received a status, is a permanent contract violation, captured and
# raised (fail closed), never silently defaulted.
# ---------------------------------------------------------------

from arvis.errors.base import ArvisRuntimeError  # noqa: E402
from arvis.errors.codes import ErrorCode  # noqa: E402


def test_finalize_without_execution_state_fails_closed() -> None:
    pipeline = CognitivePipeline()
    ctx = build_finalize_compatible_context()
    ctx.execution.execution_state = None

    with pytest.raises(ArvisRuntimeError) as exc_info:
        PipelineFinalizeService.run(pipeline, ctx)

    assert exc_info.value.code == ErrorCode.PIPELINE_FINALIZE_CONTRACT_VIOLATION
    assert exc_info.value.details["missing"] == "execution_state"
    assert exc_info.value.details["retry_class"] == "permanent"


def test_finalize_without_execution_status_fails_closed() -> None:
    pipeline = CognitivePipeline()
    ctx = build_finalize_compatible_context()
    assert ctx.execution.execution_state is not None
    ctx.execution.execution_state.execution_status = None

    with pytest.raises(ArvisRuntimeError) as exc_info:
        PipelineFinalizeService.run(pipeline, ctx)

    assert exc_info.value.code == ErrorCode.PIPELINE_FINALIZE_CONTRACT_VIOLATION
    assert exc_info.value.details["missing"] == "runtime.execution_status"
