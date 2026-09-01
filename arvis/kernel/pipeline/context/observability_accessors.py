# arvis/kernel/pipeline/context/observability_accessors.py

"""Duck-tolerant canonical readers for the observability domain.

Campaign OBS (LOT O4). The root context facade mirrors over
``ctx.observability.*`` are retired; typed callsites read the canonical
sub-context paths directly. These accessors serve the callsites that
accept partial duck contexts by contract (projection, adapters,
observability composition): canonical first, root-attribute fallback
so legacy mock contexts keep working.
"""

from __future__ import annotations

from typing import Any


def _observability(ctx: Any) -> Any:
    return getattr(ctx, "observability", None)


def predictive_snapshot(ctx: Any) -> Any:
    observability = _observability(ctx)
    if observability is not None:
        return observability.projections.predictive_snapshot
    return getattr(ctx, "predictive_snapshot", None)


def global_stability(ctx: Any) -> Any:
    observability = _observability(ctx)
    if observability is not None:
        return observability.projections.global_stability
    return getattr(ctx, "global_stability", None)


def symbolic_drift(ctx: Any) -> Any:
    observability = _observability(ctx)
    if observability is not None:
        return observability.symbolic.symbolic_drift
    return getattr(ctx, "symbolic_drift", None)


def symbolic_features(ctx: Any) -> Any:
    observability = _observability(ctx)
    if observability is not None:
        return observability.symbolic.symbolic_features
    return getattr(ctx, "symbolic_features", None)


def ir_state(ctx: Any) -> Any:
    observability = _observability(ctx)
    if observability is not None:
        return observability.state.ir_state
    return getattr(ctx, "ir_state", None)


def cognitive_state(ctx: Any) -> Any:
    observability = _observability(ctx)
    if observability is not None:
        return observability.state.cognitive_state
    return getattr(ctx, "cognitive_state", None)


def multi_horizon(ctx: Any) -> Any:
    observability = _observability(ctx)
    if observability is not None:
        return observability.projections.multi_horizon
    return getattr(ctx, "multi_horizon", None)


def global_forecast(ctx: Any) -> Any:
    observability = _observability(ctx)
    if observability is not None:
        return observability.projections.global_forecast
    return getattr(ctx, "global_forecast", None)
