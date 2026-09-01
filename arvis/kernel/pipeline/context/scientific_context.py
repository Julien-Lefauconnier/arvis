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
from arvis.reasoning.reasoning_intent import ReasoningIntent


@dataclass
class PipelineScientificCoreContext:
    scientific_snapshot: Any | None = None
    # The opaque cross-turn blob the host feeds back next turn. Typed
    # storage is the source of truth (DM-F3); the extra export stays
    # byte-identical for the documented host contract.
    next_scientific_state: dict[str, Any] | None = None
    collapse_risk: RiskSignal | float = 0.0
    uncertainty: UncertaintySignal | float | None = None
    drift_score: DriftSignal | float = 0.0
    # Declared in campaign STRUCT LOT S2. Always None on the default
    # path today: the intent mapper requires an UncertaintyFrame that
    # no default path constructs (see the control stage note).
    uncertainty_intent: list[ReasoningIntent] | None = None


@dataclass
class PipelineLyapunovContext:
    prev_lyap: LyapunovState | float | None = None
    cur_lyap: LyapunovState | float | None = None
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
    global_stability_metrics: Any | None = None


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
