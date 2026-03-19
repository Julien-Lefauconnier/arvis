# arvis/cognition/observability/observability_builder.py

from typing import Any, Dict

from arvis.cognition.observability.predictive_snapshot import PredictiveSnapshot
from arvis.cognition.observability.multi_horizon_snapshot import MultiHorizonSnapshot
from arvis.cognition.observability.global_forecast_snapshot import GlobalForecastSnapshot
from arvis.cognition.observability.global_stability_snapshot import GlobalStabilitySnapshot
from arvis.cognition.observability.stability_stats_snapshot import StabilityStatsSnapshot

from arvis.cognition.observability.symbolic.symbolic_state import SymbolicState
from arvis.cognition.observability.symbolic.symbolic_drift_snapshot import SymbolicDriftSnapshot, SymbolicRegime
from arvis.cognition.observability.symbolic.symbolic_feature_snapshot import SymbolicFeatureSnapshot
from arvis.math.signals.system_tension import SystemTensionSignal
from arvis.stability.stability_snapshot import StabilitySnapshot


class ObservabilityBuilder:
    """
    Pure projection layer.
    No side effects.
    """

    def build(self, ctx: Any) -> Dict[str, Any]:

        conflict_pressure = getattr(ctx, "conflict_pressure", None)
        conflict_level = self._signal(conflict_pressure)
        collapse = self._signal(ctx.collapse_risk)
        drift = self._signal(ctx.drift_score)

        tension = SystemTensionSignal(
            collapse=collapse,
            drift=drift,
            conflict=conflict_level,
        )
        # -------------------------
        # Predictive
        # -------------------------
        def _lyap_scalar(x: Any) -> float:
            if x is None:
                return 0.0
            try:
                return float(x)
            except Exception:
                return float(getattr(x, "value", 0.0))

        predictive = PredictiveSnapshot(
            predicted_v=_lyap_scalar(ctx.cur_lyap),
            slope=drift,
            time_to_critical=None,
            verdict=str(ctx.gate_result),
        )

        multi = MultiHorizonSnapshot(
            collapse_risk=collapse,
            stability_confidence=1.0 - self._signal(ctx.collapse_risk),
            early_warning=self._signal(ctx.collapse_risk) > 0.7,
        )

        forecast = GlobalForecastSnapshot(
            predicted_mean_delta=self._signal(ctx.drift_score),
            slope=drift,
            collapse_risk=collapse,
            time_to_critical=None,
            early_warning=self._signal(ctx.collapse_risk) > 0.7,
        )

        internal_stability = GlobalStabilitySnapshot(
            verdict=str(ctx.gate_result),
            score=1.0 - self._signal(ctx.collapse_risk),
            confidence=1.0,
            samples=len(getattr(ctx, "timeline", [])),
            mean_dv=self._signal(ctx.drift_score),
            std_dv=0.0,
            instability_rate=self._signal(ctx.collapse_risk),
            collapse_risk=collapse,
            last_v=_lyap_scalar(ctx.cur_lyap),
            reasons=(
                (
                    ["high_system_tension", tension.dominant_axis()]
                    if tension.is_high()
                    else []
                )
            ),
        )

        stability = StabilitySnapshot.from_global(internal_stability)

        stats = StabilityStatsSnapshot(
            mean_delta=self._signal(ctx.drift_score),
            contraction_rate=1.0 - self._signal(ctx.collapse_risk),
            instability_rate=self._signal(ctx.collapse_risk),
            samples=len(ctx.timeline),
        )

        # -------------------------
        # Symbolic
        # -------------------------
        symbolic_state = SymbolicState(
            intent_type=str(getattr(getattr(ctx, "decision_result", None), "signal", "unknown")),
            intent_confidence=1.0,
            gate_verdict=str(ctx.gate_result),
            conversation_mode="unknown",
            conflict_histogram={},
            conflict_severity=conflict_level,
            override_count=0,
            override_rate=0.0,
        )

        symbolic_drift = SymbolicDriftSnapshot(
            drift_score=self._signal(ctx.drift_score),
            regime=SymbolicRegime.OK if self._signal(ctx.collapse_risk) < 0.5 else SymbolicRegime.WARNING,
            intent_switch=False,
            gate_switch=False,
            confidence_delta=0.0,
            conflict_delta=conflict_level,
            override_rate=0.0,
        )

        symbolic_features = SymbolicFeatureSnapshot(
            conflict_entropy=0.0,
            contradiction_density=0.0,
            gate_switch_rate=0.0,
            policy_disagreement_rate=0.0,
            symbolic_drift_score=self._signal(ctx.drift_score),
            edges_count=0,
            mean_edge_weight=0.0,
            max_edge_weight=0.0,
            spectral_proxy=0.0,
        )

        result: Dict[str, Any] = {
            "predictive": predictive,
            "multi": multi,
            "forecast": forecast,
            "stability": stability,
            "stats": stats,
            "symbolic_state": symbolic_state,
            "symbolic_drift": symbolic_drift,
            "symbolic_features": symbolic_features,
            "system_tension": tension,
        }
        return result
    
    def _signal(self, x: Any, default: float = 0.0) -> float:
        if x is None:
            return default
        if hasattr(x, "level"):
            try:
                return float(x.level())
            except Exception:
                return default
        try:
            return float(x)
        except Exception:
            return default