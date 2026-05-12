# arvis/kernel/pipeline/context/scientific_context.py

from dataclasses import dataclass, field
from typing import Any

from arvis.math.adaptive.adaptive_snapshot import (
    AdaptiveSnapshot,
)
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.math.lyapunov.slow_state import SlowState
from arvis.math.signals import (
    DriftSignal,
    RiskSignal,
    UncertaintySignal,
)
from arvis.math.stability.validity_envelope import (
    ValidityEnvelope,
)
from arvis.math.state.symbolic_state import (
    SymbolicState,
)
from arvis.math.switching.switching_runtime import (
    SwitchingRuntime,
)


@dataclass
class PipelineScientificCoreContext:
    scientific_snapshot: Any | None = None
    collapse_risk: RiskSignal | float = 0.0
    uncertainty: UncertaintySignal | float | None = None
    drift_score: DriftSignal | float = 0.0


@dataclass
class PipelineLyapunovContext:
    prev_lyap: LyapunovState | float | None = None
    cur_lyap: LyapunovState | float | None = None
    prev_quadratic_lyap_state: Any | None = None
    cur_quadratic_lyap_state: Any | None = None
    quadratic_lyap_snapshot: Any | None = None
    quadratic_comparability: Any | None = None
    slow_state: SlowState | None = None
    slow_state_prev: SlowState | None = None
    symbolic_state: SymbolicState | None = None
    symbolic_state_prev: SymbolicState | None = None


@dataclass
class PipelineCompositeContext:
    w_current: float | None = None
    w_prev: float | None = None
    delta_w: float | None = None
    delta_w_history: list[float] = field(default_factory=list)
    recommendation: str | None = None
    # Composite W inputs
    # Ownership target for slow/symbolic components used by
    # composite Lyapunov evaluation.
    prev_slow: SlowState | None = None
    cur_slow: SlowState | None = None

    prev_symbolic: SymbolicState | None = None
    cur_symbolic: SymbolicState | None = None


@dataclass
class PipelineDriftContext:
    """
    Scientific drift runtime state.

    Owns drift histories and warnings previously stored in ctx.extra.
    """

    lyap_history: list[float] = field(default_factory=list)
    lyap_delta_history: list[float] = field(default_factory=list)
    slow_drift_history: list[float] = field(default_factory=list)
    slow_drift_warning: bool = False


@dataclass
class PipelineRegimeContext:
    regime: str | None = None
    stable: bool | None = None
    regime_confidence: float = 0.0
    theoretical_regime: Any | None = None
    fast_dynamics: Any | None = None
    perturbation: Any | None = None


@dataclass
class PipelineSwitchingContext:
    switching_runtime: SwitchingRuntime | None = None
    switching_params: Any | None = None
    switching_safe: bool | None = None
    switching_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineAdaptiveContext:
    adaptive_snapshot: AdaptiveSnapshot | None = None
    validity_envelope: ValidityEnvelope | None = None
    use_paper_slow_dynamics: bool = False
    use_paper_composite_gate: bool = False
    global_stability_metrics: Any | None = None
    enforce_global_stability: bool = False
    global_stability_action: str = "ignore"


@dataclass
class PipelineScientificContext:
    """
    Scientific / stability runtime domain.

    Contains:
    - Lyapunov state
    - adaptive stability
    - switching theorem runtime
    - uncertainty signals
    - drift / regime estimation
    - symbolic stability state

    Pure runtime state container.
    No IO.
    No services.
    """

    core: PipelineScientificCoreContext = field(
        default_factory=PipelineScientificCoreContext,
    )
    lyapunov: PipelineLyapunovContext = field(
        default_factory=PipelineLyapunovContext,
    )
    composite: PipelineCompositeContext = field(
        default_factory=PipelineCompositeContext,
    )
    drift: PipelineDriftContext = field(
        default_factory=PipelineDriftContext,
    )
    regime_state: PipelineRegimeContext = field(
        default_factory=PipelineRegimeContext,
    )
    switching: PipelineSwitchingContext = field(
        default_factory=PipelineSwitchingContext,
    )
    adaptive: PipelineAdaptiveContext = field(
        default_factory=PipelineAdaptiveContext,
    )

    @property
    def scientific_snapshot(self) -> Any | None:
        return self.core.scientific_snapshot

    @scientific_snapshot.setter
    def scientific_snapshot(self, value: Any | None) -> None:
        self.core.scientific_snapshot = value

    @property
    def collapse_risk(self) -> RiskSignal | float:
        return self.core.collapse_risk

    @collapse_risk.setter
    def collapse_risk(self, value: RiskSignal | float) -> None:
        self.core.collapse_risk = value

    @property
    def uncertainty(self) -> UncertaintySignal | float | None:
        return self.core.uncertainty

    @uncertainty.setter
    def uncertainty(self, value: UncertaintySignal | float | None) -> None:
        self.core.uncertainty = value

    @property
    def drift_score(self) -> DriftSignal | float:
        return self.core.drift_score

    @drift_score.setter
    def drift_score(self, value: DriftSignal | float) -> None:
        self.core.drift_score = value

    @property
    def prev_lyap(self) -> LyapunovState | float | None:
        return self.lyapunov.prev_lyap

    @prev_lyap.setter
    def prev_lyap(self, value: LyapunovState | float | None) -> None:
        self.lyapunov.prev_lyap = value

    @property
    def cur_lyap(self) -> LyapunovState | float | None:
        return self.lyapunov.cur_lyap

    @cur_lyap.setter
    def cur_lyap(self, value: LyapunovState | float | None) -> None:
        self.lyapunov.cur_lyap = value

    @property
    def prev_quadratic_lyap_state(self) -> Any | None:
        return self.lyapunov.prev_quadratic_lyap_state

    @prev_quadratic_lyap_state.setter
    def prev_quadratic_lyap_state(self, value: Any | None) -> None:
        self.lyapunov.prev_quadratic_lyap_state = value

    @property
    def cur_quadratic_lyap_state(self) -> Any | None:
        return self.lyapunov.cur_quadratic_lyap_state

    @cur_quadratic_lyap_state.setter
    def cur_quadratic_lyap_state(self, value: Any | None) -> None:
        self.lyapunov.cur_quadratic_lyap_state = value

    @property
    def quadratic_lyap_snapshot(self) -> Any | None:
        return self.lyapunov.quadratic_lyap_snapshot

    @quadratic_lyap_snapshot.setter
    def quadratic_lyap_snapshot(self, value: Any | None) -> None:
        self.lyapunov.quadratic_lyap_snapshot = value

    @property
    def quadratic_comparability(self) -> Any | None:
        return self.lyapunov.quadratic_comparability

    @quadratic_comparability.setter
    def quadratic_comparability(self, value: Any | None) -> None:
        self.lyapunov.quadratic_comparability = value

    @property
    def slow_state(self) -> SlowState | None:
        return self.lyapunov.slow_state

    @slow_state.setter
    def slow_state(self, value: SlowState | None) -> None:
        self.lyapunov.slow_state = value

    @property
    def slow_state_prev(self) -> SlowState | None:
        return self.lyapunov.slow_state_prev

    @slow_state_prev.setter
    def slow_state_prev(self, value: SlowState | None) -> None:
        self.lyapunov.slow_state_prev = value

    @property
    def symbolic_state(self) -> SymbolicState | None:
        return self.lyapunov.symbolic_state

    @symbolic_state.setter
    def symbolic_state(self, value: SymbolicState | None) -> None:
        self.lyapunov.symbolic_state = value

    @property
    def symbolic_state_prev(self) -> SymbolicState | None:
        return self.lyapunov.symbolic_state_prev

    @symbolic_state_prev.setter
    def symbolic_state_prev(self, value: SymbolicState | None) -> None:
        self.lyapunov.symbolic_state_prev = value

    @property
    def w_current(self) -> float | None:
        return self.composite.w_current

    @w_current.setter
    def w_current(self, value: float | None) -> None:
        self.composite.w_current = value

    @property
    def w_prev(self) -> float | None:
        return self.composite.w_prev

    @w_prev.setter
    def w_prev(self, value: float | None) -> None:
        self.composite.w_prev = value

    @property
    def delta_w(self) -> float | None:
        return self.composite.delta_w

    @delta_w.setter
    def delta_w(self, value: float | None) -> None:
        self.composite.delta_w = value

    @property
    def delta_w_history(self) -> list[float]:
        return self.composite.delta_w_history

    @delta_w_history.setter
    def delta_w_history(self, value: list[float]) -> None:
        self.composite.delta_w_history = value

    @property
    def regime(self) -> str | None:
        return self.regime_state.regime

    @regime.setter
    def regime(self, value: str | None) -> None:
        self.regime_state.regime = value

    @property
    def stable(self) -> bool | None:
        return self.regime_state.stable

    @stable.setter
    def stable(self, value: bool | None) -> None:
        self.regime_state.stable = value

    @property
    def regime_confidence(self) -> float:
        return self.regime_state.regime_confidence

    @regime_confidence.setter
    def regime_confidence(self, value: float) -> None:
        self.regime_state.regime_confidence = value

    @property
    def theoretical_regime(self) -> Any | None:
        return self.regime_state.theoretical_regime

    @theoretical_regime.setter
    def theoretical_regime(self, value: Any | None) -> None:
        self.regime_state.theoretical_regime = value

    @property
    def fast_dynamics(self) -> Any | None:
        return self.regime_state.fast_dynamics

    @fast_dynamics.setter
    def fast_dynamics(self, value: Any | None) -> None:
        self.regime_state.fast_dynamics = value

    @property
    def perturbation(self) -> Any | None:
        return self.regime_state.perturbation

    @perturbation.setter
    def perturbation(self, value: Any | None) -> None:
        self.regime_state.perturbation = value

    @property
    def switching_runtime(self) -> SwitchingRuntime | None:
        return self.switching.switching_runtime

    @switching_runtime.setter
    def switching_runtime(self, value: SwitchingRuntime | None) -> None:
        self.switching.switching_runtime = value

    @property
    def switching_params(self) -> Any | None:
        return self.switching.switching_params

    @switching_params.setter
    def switching_params(self, value: Any | None) -> None:
        self.switching.switching_params = value

    @property
    def switching_safe(self) -> bool | None:
        return self.switching.switching_safe

    @switching_safe.setter
    def switching_safe(self, value: bool | None) -> None:
        self.switching.switching_safe = value

    @property
    def switching_metrics(self) -> dict[str, Any]:
        return self.switching.switching_metrics

    @switching_metrics.setter
    def switching_metrics(self, value: dict[str, Any]) -> None:
        self.switching.switching_metrics = value

    @property
    def adaptive_snapshot(self) -> AdaptiveSnapshot | None:
        return self.adaptive.adaptive_snapshot

    @adaptive_snapshot.setter
    def adaptive_snapshot(self, value: AdaptiveSnapshot | None) -> None:
        self.adaptive.adaptive_snapshot = value

    @property
    def validity_envelope(self) -> ValidityEnvelope | None:
        return self.adaptive.validity_envelope

    @validity_envelope.setter
    def validity_envelope(self, value: ValidityEnvelope | None) -> None:
        self.adaptive.validity_envelope = value

    @property
    def use_paper_slow_dynamics(self) -> bool:
        return self.adaptive.use_paper_slow_dynamics

    @use_paper_slow_dynamics.setter
    def use_paper_slow_dynamics(self, value: bool) -> None:
        self.adaptive.use_paper_slow_dynamics = value

    @property
    def use_paper_composite_gate(self) -> bool:
        return self.adaptive.use_paper_composite_gate

    @use_paper_composite_gate.setter
    def use_paper_composite_gate(self, value: bool) -> None:
        self.adaptive.use_paper_composite_gate = value

    @property
    def global_stability_metrics(self) -> Any | None:
        return self.adaptive.global_stability_metrics

    @global_stability_metrics.setter
    def global_stability_metrics(self, value: Any | None) -> None:
        self.adaptive.global_stability_metrics = value

    @property
    def enforce_global_stability(self) -> bool:
        return self.adaptive.enforce_global_stability

    @enforce_global_stability.setter
    def enforce_global_stability(self, value: bool) -> None:
        self.adaptive.enforce_global_stability = value

    @property
    def global_stability_action(self) -> str:
        return self.adaptive.global_stability_action

    @global_stability_action.setter
    def global_stability_action(self, value: str) -> None:
        self.adaptive.global_stability_action = value

    @property
    def recommendation(self) -> str | None:
        return self.composite.recommendation

    @recommendation.setter
    def recommendation(self, value: str | None) -> None:
        self.composite.recommendation = value
