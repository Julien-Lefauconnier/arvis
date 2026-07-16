# tests/contracts/test_context_facade_ratchet.py
"""Ratchet: the CognitivePipelineContext compatibility facade only shrinks.

The context is already decomposed into sub-contexts (the
arvis/kernel/pipeline/context/ package); the property layer on
CognitivePipelineContext is a DELIBERATE compatibility facade. The
projection alias family (arvis-projection-v2) was migrated and removed
in Lot 4b. This test freezes the exact set of facade properties:

  - adding a new facade property fails this test (new code must use the
    sub-context directly, e.g. ctx.projection.certificate);
  - removing one (after migrating its callsites) requires updating the
    frozen list below, a deliberate, reviewed act.

The frozen list was measured after the A2.1 dead-alias purge (five
aliases with zero attribute access and zero string/getattr access were
removed: control_runtime, quadratic_lyap_snapshot, runtime_projection,
structured_projection, use_paper_slow_dynamics).
"""

from __future__ import annotations

from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)

FROZEN_FACADE_PROPERTIES = frozenset(
    {
        "_force_execution",
        "_last_tool_spec",
        "_tool_failure",
        "_tool_success",
        "action_decision",
        "adaptive_snapshot",
        "bundle",
        "can_execute",
        "cognitive_state",
        "collapse_risk",
        "cur_lyap",
        "decision_result",
        "delta_w",
        "delta_w_history",
        "drift_score",
        "errors",
        "executable_intent",
        "execution_state",
        "execution_status",
        "fast_dynamics",
        "force_tool",
        "global_forecast",
        "global_stability",
        "global_stability_metrics",
        "ir_decision",
        "ir_state",
        "multi_horizon",
        "perturbation",
        "predictive_snapshot",
        "prev_lyap",
        "quadratic_comparability",
        "regime",
        "requires_confirmation",
        "retry_tool",
        "scientific_snapshot",
        "slow_state",
        "slow_state_prev",
        "stability_projection",
        "stability_statistics",
        "stability_stats",
        "stable",
        "switching_metrics",
        "switching_params",
        "switching_runtime",
        "switching_safe",
        "symbolic_drift",
        "symbolic_features",
        "symbolic_state",
        "symbolic_state_prev",
        "system_tension",
        "theoretical_regime",
        "tool_retry_count",
        "uncertainty",
        "validity_envelope",
        "w_current",
        "w_prev",
    }
)


def test_context_facade_only_shrinks() -> None:
    actual = {
        name
        for name, value in vars(CognitivePipelineContext).items()
        if isinstance(value, property)
    }

    added = actual - FROZEN_FACADE_PROPERTIES
    removed = FROZEN_FACADE_PROPERTIES - actual

    assert not added, (
        "New compatibility properties on CognitivePipelineContext: "
        f"{sorted(added)}. New code must use the sub-contexts directly "
        "(ctx.projection.*, ctx.scientific.*, ...)."
    )
    assert not removed, (
        "Facade properties removed without updating the frozen list: "
        f"{sorted(removed)}. If their callsites were migrated "
        "(arvis-projection-v2), update FROZEN_FACADE_PROPERTIES."
    )
