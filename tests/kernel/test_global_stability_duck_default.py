# tests/kernel/test_global_stability_duck_default.py
"""DM-F1 (campaign FIX): the duck default of the global stability
policy is fail-closed and identical in both layers.

The math layer read the knob with default "ignore" and the kernel
layer with default "confirm": three truths for one knob (the typed
field, plus two divergent duck defaults), so a partial context
without the field got opposite policies depending on the layer.
Profiles are untouched: local posture stays "ignore", production
stays "confirm" (F-002/A4 pins); only a context that DECLARES
nothing falls back to confirm in both layers.
"""

from __future__ import annotations

from types import SimpleNamespace

from arvis.kernel.pipeline.stages.gate.stability import (
    apply_global_stability_policy,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict


def _duck_ctx() -> SimpleNamespace:
    """A partial host context that never declared the knob."""
    return SimpleNamespace(extra={})


def test_kernel_layer_duck_default_is_confirm() -> None:
    out = apply_global_stability_policy(
        _duck_ctx(), LyapunovVerdict.ALLOW, global_safe=False
    )

    assert out == LyapunovVerdict.REQUIRE_CONFIRMATION


def test_math_layer_duck_default_matches() -> None:
    """The math layer's read must resolve to the same fail-closed
    default; the two layers must never diverge again on a duck."""
    import inspect

    from arvis.math.gate import gate_policy

    src = inspect.getsource(gate_policy)
    # Campaign SURFACE typed the postures: the duck default is the
    # same fail-closed member, spelled as the enum.
    assert (
        'getattr(ctx, "global_stability_action", GlobalStabilityAction.CONFIRM)' in src
    )
    assert '"global_stability_action", "ignore"' not in src
    assert '"global_stability_action", GlobalStabilityAction.IGNORE' not in src
