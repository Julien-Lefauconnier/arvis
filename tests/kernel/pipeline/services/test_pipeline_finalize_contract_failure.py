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
    ctx.cognitive_state = object()

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
