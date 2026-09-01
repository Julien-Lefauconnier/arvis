# tests/contracts/test_context_facade_ratchet.py
"""Ratchet: the CognitivePipelineContext root facade stays retired.

History: the context was decomposed into bounded sub-contexts (the
arvis/kernel/pipeline/context/ package) and the root property layer was
kept as a DELIBERATE compatibility facade, frozen by this test and only
allowed to shrink. It shrank in steps: the A2.1 dead-alias purge, the
projection alias family (arvis-projection-v2, Lot 4b), the
decision/execution/policy family (campaign STRUCT, LOT S4b), and
finally the complete retirement of the remaining 43 mirrors in campaign
OBS (LOT O4): scientific (core, lyapunov, composite, regime, switching,
adaptive), observability (projections, symbolic, state), execution,
error and tooling families. Every callsite reads its bounded
sub-context directly (typed sites) or through the duck-tolerant
accessor modules (scientific_accessors, observability_accessors,
tooling_accessors).

Two properties of the retirement are pinned here:

1. The context defines NO properties at all. A new property is a new
   facade; new code uses the sub-context paths.
2. No retired mirror name reappears as a dynamic instance attribute
   after a full pipeline run. The context is a plain dataclass, so a
   stale writer (``ctx.delta_w = ...``) would not fail loudly; it would
   create a shadow attribute the canonical readers never see. This
   guard makes that failure loud.
"""

from __future__ import annotations

import inspect

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)

RETIRED_FACADE_PROPERTIES = frozenset(
    {
        "_last_tool_spec",
        "_tool_failure",
        "_tool_success",
        "adaptive_snapshot",
        "cognitive_state",
        "collapse_risk",
        "cur_lyap",
        "delta_w",
        "delta_w_history",
        "drift_score",
        "errors",
        "executable_intent",
        "fast_dynamics",
        "global_forecast",
        "global_stability",
        "global_stability_metrics",
        "ir_state",
        "multi_horizon",
        "perturbation",
        "predictive_snapshot",
        "prev_lyap",
        "quadratic_comparability",
        "regime",
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
        "theoretical_regime",
        "uncertainty",
        "validity_envelope",
        "w_current",
        "w_prev",
    }
)


def test_context_defines_no_properties() -> None:
    """Direction 1: the facade stays empty (the ratchet's floor)."""
    actual = {
        name
        for name, member in inspect.getmembers(CognitivePipelineContext)
        if isinstance(member, property)
    }
    assert not actual, (
        f"CognitivePipelineContext grew properties again: {sorted(actual)}. "
        "The root facade was retired in campaign OBS (LOT O4); use the "
        "bounded sub-contexts (ctx.scientific.*, ctx.observability.*, "
        "ctx.execution.*, ctx.tooling.*, ctx.error_state.*) or the "
        "accessor modules."
    )


class _GuardCoreModel:
    def compute(self, bundle):  # type: ignore[no-untyped-def]
        class _Snapshot:
            collapse_risk = 0.2
            drift_score = 0.1
            regime = "stable"
            stable = True
            prev_lyap = 0.5
            cur_lyap = 0.4

        return _Snapshot()


def test_no_retired_name_shadows_the_context_after_a_run() -> None:
    """Direction 2: no stale writer resurrects a retired mirror.

    The context is a plain dataclass: ``ctx.delta_w = x`` would succeed
    silently and fork the state from the canonical
    ``scientific.composite.delta_w``. Running the default pipeline and
    inspecting the instance dict makes any such straggler loud.
    """
    ctx = CognitivePipelineContext(
        cognitive_input={},
        user_id="facade_guard",
        timeline=[],
        introspection=None,
        explanation=None,
    )
    pipeline = CognitivePipeline(core_model=_GuardCoreModel())
    pipeline.run(ctx)

    shadows = RETIRED_FACADE_PROPERTIES & set(vars(ctx))
    assert not shadows, (
        f"Retired mirror name(s) written as dynamic attributes during a "
        f"default run: {sorted(shadows)}. Migrate the writer to the "
        "canonical sub-context path."
    )
