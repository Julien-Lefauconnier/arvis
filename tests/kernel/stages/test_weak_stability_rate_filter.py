# tests/kernel/stages/test_weak_stability_rate_filter.py
"""Campaign SEUIL, RED-first: the local soft filter resolves its
threshold through the registered rate policy.

The filter itself is three lines (floor ALLOW when
``threshold < delta_w < 0``); what carries the campaign is WHERE the
threshold comes from. These pins hold the resolution seam: the rate
policy fed by the turn's composite energy by default, and the
explicit context attribute kept as a host escape hatch, exactly as
the old ``getattr(ctx, "delta_w_soft_threshold", -0.05)`` behaved
when a host set it.

The end-to-end effect is measured, not fixtured: the campaign runs
published with M10 section 14 show the feedback family reaching
ALLOW (8 turns) under the rate rule, which the absolute -0.05 kept
at zero.
"""

from __future__ import annotations

from pytest import approx

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.kernel.pipeline.stages.gate.decision_stack import (
    resolve_weak_stability_threshold,
)


def _ctx(w_current: float | None) -> CognitivePipelineContext:
    ctx = CognitivePipelineContext(user_id="test", cognitive_input={})
    ctx.scientific.composite.w_current = w_current
    return ctx


def test_the_default_threshold_is_the_rate_policy_on_the_turn_energy() -> None:
    assert resolve_weak_stability_threshold(_ctx(w_current=1.0)) == approx(-0.05)
    assert resolve_weak_stability_threshold(_ctx(w_current=0.4)) == approx(-0.02)


def test_the_absolute_floor_applies_when_the_energy_is_tiny_or_absent() -> None:
    assert resolve_weak_stability_threshold(_ctx(w_current=0.01)) == -0.005
    assert resolve_weak_stability_threshold(_ctx(w_current=None)) == -0.005


def test_an_explicit_host_override_is_still_honored() -> None:
    """The context attribute stays an escape hatch: setting it gives
    an absolute threshold, bypassing the rate rule."""
    ctx = _ctx(w_current=0.1)
    ctx.delta_w_soft_threshold = -0.02

    assert resolve_weak_stability_threshold(ctx) == approx(-0.02)


def test_a_garbage_override_falls_back_to_the_policy() -> None:
    """Fail-safe toward the registered policy, never toward a free
    pass or an exception inside the gate."""
    ctx = _ctx(w_current=0.4)
    ctx.delta_w_soft_threshold = "not a number"

    assert resolve_weak_stability_threshold(ctx) == approx(-0.02)
