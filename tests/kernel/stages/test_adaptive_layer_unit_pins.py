# tests/kernel/stages/test_adaptive_layer_unit_pins.py
"""Unit pins of the adaptive verdict layer (campaign MATH-B).

The MATH-B mutation replay showed the integration tests accept the
critical forcing and the final veto disjunctively (other layers also
produce REQUIRE_CONFIRMATION on a cold context), so a dropped forcing
and a dropped veto both survived. These pins call the layer functions
directly and assert the exact transformation each one owns.
"""

from __future__ import annotations

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.stages.gate.adaptive import (
    apply_final_adaptive_veto,
    apply_kappa_margin_layer,
    updated_pre_verdict,
)
from arvis.math.adaptive.adaptive_snapshot import AdaptiveSnapshot
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def _ctx() -> CognitivePipelineContext:
    return CognitivePipelineContext(user_id="test", cognitive_input={})


def test_critical_band_forces_allow_to_confirmation() -> None:
    """A critical margin on an ALLOW pre-verdict must come out as
    REQUIRE_CONFIRMATION from this layer itself, not from whatever
    other layer would also have tightened the turn."""
    ctx = _ctx()
    snap = AdaptiveSnapshot(
        kappa_eff=0.9,
        margin=-0.01,
        regime="critical",
        available=True,
    )

    apply_kappa_margin_layer(ctx, LyapunovVerdict.ALLOW, snap)
    out = updated_pre_verdict(ctx, LyapunovVerdict.ALLOW, snap)

    assert out == LyapunovVerdict.REQUIRE_CONFIRMATION


def test_final_veto_abstains_on_unstable_after_any_relaxation() -> None:
    """The final veto is the defense-in-depth rung: even if a later
    layer relaxed the verdict below ABSTAIN, an available unstable
    snapshot must re-abstain here, with the veto trace set."""
    ctx = _ctx()
    snap = AdaptiveSnapshot(
        kappa_eff=0.2,
        margin=0.15,
        regime="unstable",
        available=True,
    )

    out = apply_final_adaptive_veto(ctx, LyapunovVerdict.REQUIRE_CONFIRMATION, snap)

    assert out == LyapunovVerdict.ABSTAIN
    assert ctx.extra.get("_hard_adaptive_veto") is True
