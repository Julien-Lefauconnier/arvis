# tests/math/decision/test_multiaxial_fusion.py
"""The assessment-phase fusion is observation-only.

The former composite and global-policy axes were pruned (audit G3,
decision D1, 2026-08): production never wired their knobs, the branches
existed only for these unit tests, and one of them relaxed
REQUIRE_CONFIRMATION to ALLOW against the verdict-strictness order.
What remains is a passthrough that records observations; these tests
pin exactly that, so any reintroduction of a decision in the fusion
shows up as a failure here.
"""

import itertools

from arvis.math.decision.multiaxial_fusion import (
    MultiaxialInputs,
    multiaxial_fusion,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def test_fusion_passes_every_verdict_through_unchanged():
    for verdict, switching_safe in itertools.product(
        list(LyapunovVerdict), [True, False]
    ):
        result = multiaxial_fusion(
            MultiaxialInputs(fast_verdict=verdict, switching_safe=switching_safe)
        )
        assert result.verdict is verdict, (
            "the fusion is observation-only; enforcement belongs to the "
            f"policy layer (got {result.verdict} for {verdict})"
        )


def test_fusion_records_no_reason_when_nothing_observed():
    result = multiaxial_fusion(
        MultiaxialInputs(fast_verdict=LyapunovVerdict.ALLOW, switching_safe=True)
    )
    assert result.reasons == []


def test_multiaxial_switching_is_monitoring_only():
    result = multiaxial_fusion(
        MultiaxialInputs(fast_verdict=LyapunovVerdict.ALLOW, switching_safe=False)
    )
    assert result.verdict == LyapunovVerdict.ALLOW
    assert "switching_unsafe_monitoring" in result.reasons


def test_dead_decision_knobs_stay_pruned():
    """The pruned knobs must not quietly return: a decision axis in the
    fusion needs a production caller and a policy-layer justification
    first (see multiaxial_fusion's docstring)."""
    fields = set(MultiaxialInputs.__dataclass_fields__)
    assert "use_composite" not in fields
    assert "global_action" not in fields
    assert "delta_w" not in fields
