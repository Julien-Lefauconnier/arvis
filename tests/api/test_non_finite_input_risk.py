"""Non-finite public risk values fail closed and stay strict-JSON safe."""

from __future__ import annotations

import json
import math

import pytest

from arvis import (
    CognitiveOS,
    CognitiveOSConfig,
    DecisionStatus,
    verify_reflexive_attestation,
)

NON_FINITE_RISKS = (
    pytest.param(float("nan"), id="nan"),
    pytest.param(float("inf"), id="positive-infinity"),
    pytest.param(float("-inf"), id="negative-infinity"),
)


@pytest.mark.parametrize("risk", NON_FINITE_RISKS)
def test_local_runtime_blocks_non_finite_risk(risk: float) -> None:
    result = CognitiveOS().run("u1", {"risk": risk})

    assert result.status is DecisionStatus.BLOCKED


@pytest.mark.parametrize("risk", NON_FINITE_RISKS)
def test_production_runtime_blocks_non_finite_risk(risk: float) -> None:
    result = CognitiveOS(CognitiveOSConfig.production()).run(
        "u1",
        {"risk": risk},
    )

    assert result.status is DecisionStatus.BLOCKED


@pytest.mark.parametrize("risk", NON_FINITE_RISKS)
def test_non_finite_risk_outputs_remain_strict_json(risk: float) -> None:
    caller_input = {"risk": risk}
    result = CognitiveOS().run("u1", caller_input)

    exported = result.to_ir()
    assert exported["input"]["metadata"]["risk"] is None
    json.dumps(exported, allow_nan=False)
    json.loads(result.to_json())

    assert result.reflexive is not None
    json.dumps(result.reflexive, allow_nan=False)
    assert verify_reflexive_attestation(result.reflexive) is True

    # The runtime sanitizes only its detached context; host input is untouched.
    assert math.isfinite(caller_input["risk"]) is False
