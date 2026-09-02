# tests/math/gate/test_gate_postures.py
"""The gate postures are named, closed sets with unchanged wire values.

Campaign SURFACE (DM-S5, 2026-09-02). The three verdict-affecting
postures of the pipeline context were free strings compared inline;
these tests pin the typed sets and the compatibility contract: wire
values are exactly the strings hosts already assign, a plain string
still compares equal, and the production profile selects the
enforcing member of each posture.
"""

from __future__ import annotations

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    PRODUCTION_PROFILE,
    CognitivePipelineContext,
    apply_runtime_postures,
)
from arvis.math.gate.gate_postures import (
    GlobalStabilityAction,
    InputRiskMode,
    SwitchingEnvelopeMode,
)


def test_wire_values_are_the_historical_strings() -> None:
    assert [m.value for m in GlobalStabilityAction] == [
        "ignore",
        "confirm",
        "abstain",
    ]
    assert [m.value for m in SwitchingEnvelopeMode] == ["soft", "enforce"]
    assert [m.value for m in InputRiskMode] == ["graded", "harden_only"]


def test_plain_strings_still_compare_equal() -> None:
    """A host assigning the historical plain string keeps working."""
    assert GlobalStabilityAction.CONFIRM == "confirm"
    assert SwitchingEnvelopeMode.ENFORCE == "enforce"
    assert InputRiskMode.HARDEN_ONLY == "harden_only"


def test_the_default_context_carries_the_permissive_development_posture() -> None:
    ctx = CognitivePipelineContext(user_id="u", cognitive_input="x")
    assert ctx.global_stability_action is GlobalStabilityAction.IGNORE
    assert ctx.switching_envelope_mode is SwitchingEnvelopeMode.SOFT
    assert ctx.input_risk_mode is InputRiskMode.GRADED


def test_the_production_profile_selects_the_enforcing_members() -> None:
    ctx = CognitivePipelineContext(user_id="u", cognitive_input="x")
    apply_runtime_postures(ctx, PRODUCTION_PROFILE)
    assert ctx.global_stability_action is GlobalStabilityAction.CONFIRM
    assert ctx.switching_envelope_mode is SwitchingEnvelopeMode.ENFORCE
    assert ctx.input_risk_mode is InputRiskMode.HARDEN_ONLY
