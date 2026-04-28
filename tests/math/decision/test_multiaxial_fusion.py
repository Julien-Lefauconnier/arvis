# tests/math/decision/test_multiaxial_fusion.py

from arvis.math.decision.multiaxial_fusion import (
    MultiaxialInputs,
    multiaxial_fusion,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def test_multiaxial_keeps_fast_verdict_when_no_constraints():
    result = multiaxial_fusion(
        MultiaxialInputs(
            fast_verdict=LyapunovVerdict.ALLOW,
            delta_w=0.0,
            switching_safe=True,
            global_safe=True,
            use_composite=False,
            global_action="ignore",
        )
    )

    assert result.verdict == LyapunovVerdict.ALLOW
    assert result.reasons == []


def test_multiaxial_composite_positive_requires_confirmation():
    result = multiaxial_fusion(
        MultiaxialInputs(
            fast_verdict=LyapunovVerdict.ALLOW,
            delta_w=0.5,
            switching_safe=True,
            global_safe=True,
            use_composite=True,
            global_action="ignore",
        )
    )

    assert result.verdict == LyapunovVerdict.REQUIRE_CONFIRMATION
    assert "composite_positive_delta_w" in result.reasons


def test_multiaxial_composite_negative_promotes_allow():
    result = multiaxial_fusion(
        MultiaxialInputs(
            fast_verdict=LyapunovVerdict.REQUIRE_CONFIRMATION,
            delta_w=-0.5,
            switching_safe=True,
            global_safe=True,
            use_composite=True,
            global_action="ignore",
        )
    )

    assert result.verdict == LyapunovVerdict.ALLOW
    assert "composite_negative_delta_w" in result.reasons


def test_multiaxial_global_confirm_overrides():
    result = multiaxial_fusion(
        MultiaxialInputs(
            fast_verdict=LyapunovVerdict.ALLOW,
            delta_w=-0.5,
            switching_safe=True,
            global_safe=False,
            use_composite=True,
            global_action="confirm",
        )
    )

    assert result.verdict == LyapunovVerdict.REQUIRE_CONFIRMATION
    assert "global_instability_confirm" in result.reasons


def test_multiaxial_global_abstain_overrides():
    result = multiaxial_fusion(
        MultiaxialInputs(
            fast_verdict=LyapunovVerdict.ALLOW,
            delta_w=-0.5,
            switching_safe=True,
            global_safe=False,
            use_composite=True,
            global_action="abstain",
        )
    )

    assert result.verdict == LyapunovVerdict.ABSTAIN
    assert "global_instability_abstain" in result.reasons


def test_multiaxial_switching_is_monitoring_only():
    result = multiaxial_fusion(
        MultiaxialInputs(
            fast_verdict=LyapunovVerdict.ALLOW,
            delta_w=None,
            switching_safe=False,
            global_safe=True,
            use_composite=False,
            global_action="ignore",
        )
    )

    assert result.verdict == LyapunovVerdict.ALLOW
    assert "switching_unsafe_monitoring" in result.reasons
