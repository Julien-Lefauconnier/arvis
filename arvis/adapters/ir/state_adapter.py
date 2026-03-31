# arvis/adapters/ir/state_adapter.py

from __future__ import annotations

from hashlib import sha256
from json import dumps
from typing import Any, Mapping

from arvis.ir.state import CognitiveRiskIR, CognitiveStateIR

_IR_VERSION = "1.0"

def _maybe_get(obj: Any, *names: str) -> Any:
    if obj is None:
        return None

    if isinstance(obj, Mapping):
        for name in names:
            if name in obj:
                return obj[name]

    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)

    return None


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


class StateIRAdapter:
    @staticmethod
    def from_state(state: object) -> CognitiveStateIR:
        stability = getattr(state, "stability", None)
        risk = getattr(state, "risk", None)
        control = getattr(state, "control", None)
        dynamics = getattr(state, "dynamics", None)
        projection = getattr(state, "projection", None)
        fused = _as_float(getattr(risk, "fused_risk", None))
        fused = min(max(fused, 0.0), 1.0)
        smoothed = _as_float(getattr(risk, "smoothed_risk", None))
        smoothed = min(max(smoothed, 0.0), 1.0)

        risk_ir = CognitiveRiskIR(
            mh_risk=_as_float(getattr(risk, "mh_risk", None)),
            world_risk=_as_float(getattr(risk, "world_risk", None)),
            forecast_risk=_as_float(getattr(risk, "forecast_risk", None)),
            fused_risk=fused,
            smoothed_risk=smoothed,
        )

        payload = {
            "bundle_id": str(getattr(state, "bundle_id", "")),
            "dv": _as_float(getattr(stability, "dv", 0.0)),
            "fused_risk": risk_ir.fused_risk,
            "epsilon": _as_float(getattr(control, "epsilon", 0.0)),
            "version": _IR_VERSION,
        }

        state_id = sha256(
            dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()

        return CognitiveStateIR(
            state_id=state_id,
            bundle_id=str(getattr(state, "bundle_id", "")),
            dv=_as_float(getattr(stability, "dv", 0.0)),
            collapse_risk=risk_ir,
            epsilon=min(max(_as_float(getattr(control, "epsilon", 0.0)), 0.0), 1.0),
            early_warning=bool(getattr(risk, "early_warning", False)),
            world_prediction=getattr(state, "world_prediction", None),
            forecast=getattr(state, "forecast", None),
            irg=getattr(state, "irg", None),
            regime=getattr(stability, "regime", None),
            stable=getattr(stability, "stable", None),

            system_tension=getattr(dynamics, "system_tension", None),
            drift=getattr(dynamics, "drift", None),

            projection_valid=getattr(projection, "valid", None) if projection else None,
            projection_margin=getattr(projection, "margin", None) if projection else None,
        )

    @staticmethod
    def from_context(ctx: object) -> CognitiveStateIR:
        bundle = getattr(ctx, "bundle", None)
        bundle_id = str(getattr(bundle, "bundle_id", "bundle"))

        base_risk = _as_float(getattr(ctx, "collapse_risk", 0.0), 0.0)

        mh_risk = _as_float(
            _maybe_get(getattr(ctx, "multi_horizon", None), "risk", "fused_risk"),
            base_risk,
        )
        world_risk = _as_float(
            _maybe_get(getattr(ctx, "global_forecast", None), "world_risk", "risk"),
            base_risk,
        )
        forecast_risk = _as_float(
            _maybe_get(getattr(ctx, "predictive_snapshot", None), "forecast_risk", "risk"),
            world_risk,
        )
        fused_risk = _as_float(
            _maybe_get(getattr(ctx, "global_stability", None), "fused_risk", "risk"),
            max(base_risk, mh_risk, world_risk, forecast_risk),
        )

        control_snapshot = getattr(ctx, "control_snapshot", None)
        epsilon = _as_float(
            _maybe_get(control_snapshot, "epsilon"),
            _as_float(getattr(ctx, "_effective_epsilon", None), _as_float(getattr(ctx, "_epsilon", None), 0.0)),
        )
        fused_risk = min(max(fused_risk, 0.0), 1.0)
        epsilon = min(max(epsilon, 0.0), 1.0)
        smoothed_risk = _as_float(
            _maybe_get(control_snapshot, "smoothed_risk"),
            fused_risk,
        )
        smoothed_risk = min(max(smoothed_risk, 0.0), 1.0)

        dv = _as_float(
            getattr(ctx, "_dv", None),
            _as_float(getattr(ctx, "drift_score", None), _as_float(getattr(ctx, "delta_w", None), 0.0)),
        )

        extra = getattr(ctx, "extra", {}) or {}
        early_warning = bool(
            extra.get("low_confidence_escalation")
            or extra.get("global_instability_warning")
            or extra.get("switching_warning")
            or extra.get("exponential_bound_warning")
            or fused_risk >= 0.75
        )

        risk_ir = CognitiveRiskIR(
            mh_risk=mh_risk,
            world_risk=world_risk,
            forecast_risk=forecast_risk,
            fused_risk=fused_risk,
            smoothed_risk=smoothed_risk,
        )

        payload = {
            "bundle_id": bundle_id,
            "dv": dv,
            "fused_risk": fused_risk,
            "epsilon": epsilon,
            "early_warning": early_warning,
        }

        state_id = sha256(
            dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()

        return CognitiveStateIR(
            state_id=state_id,
            bundle_id=bundle_id,
            dv=dv,
            collapse_risk=risk_ir,
            epsilon=epsilon,
            early_warning=early_warning,
            world_prediction=getattr(ctx, "predictive_snapshot", None),
            forecast=getattr(ctx, "global_forecast", None),
            irg=getattr(ctx, "irg", None) or getattr(ctx, "introspection", None),
            regime=getattr(ctx, "regime", None),
            stable=getattr(ctx, "stable", None),

            system_tension=getattr(ctx, "system_tension", None),
            drift=getattr(ctx, "drift_score", None),

            projection_valid=getattr(ctx, "projection_domain_valid", None),
            projection_margin=getattr(ctx, "projection_margin", None),
        )