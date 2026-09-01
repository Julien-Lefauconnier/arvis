# validation/m10/runner.py
"""Closed-loop harness: one governed pipeline turn per observation.

Drives the exact system under test of M10 section 3.1 at the pipeline
level: each turn builds a fresh CognitivePipeline (the documented
one-instance-per-turn lifecycle) and a fresh context, seeds the
observation channels the projection certifies, threads the replayable
scientific state through the extra channel and the slow/symbolic
states across contexts, runs the pipeline, and extracts one
TurnMeasurement from the observability exports (the byte-identical
journal exports are the instrument panel).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from arvis.cognition.retrieval.cognitive_retrieval_snapshot import (
    CognitiveRetrievalSnapshot,
)
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.math.core.contraction_monitor_core import (
    ContractionMonitorCore,
    MonitorConfig,
)
from arvis.math.lyapunov.slow_state import SlowState
from validation.m10.corpus import CorpusSpec, TrajectorySpec, TurnSpec


class _CorpusCoreModel:
    """The monitor plus a corpus-supplied slow component.

    The v0 ContractionMonitorCore is fast-only by design (its own
    docstring defers the composite-W path until the fast loop is
    validated). The slow state is core-model territory (the core
    stage rebuilds ``lyap.slow_state`` from the snapshot's
    ``reflexive_state`` every turn), so the corpus feeds its z_t
    through that exact ownership seam: delegate the fast measurement
    to the monitor, attach the trajectory's slow coordinates as the
    reflexive state.
    """

    def __init__(
        self,
        monitor: ContractionMonitorCore,
        z: tuple[float, float, float, float] | None,
    ) -> None:
        self._monitor = monitor
        self._z = z

    def compute(self, bundle: Any, prior_in: Any = None) -> Any:
        result = self._monitor.compute(bundle, prior_in)
        if self._z is None:
            return result
        snapshot, next_state = result
        fields = {
            name: getattr(snapshot, name)
            for name in (
                "collapse_risk",
                "drift_score",
                "cur_lyap",
                "prev_lyap",
                "energy_v",
                "delta_v",
                "regime",
                "stable",
                "risk_ucb",
                "risk_verdict",
            )
        }
        fields["reflexive_state"] = {
            "stability_memory": self._z[0],
            "structural_risk": self._z[1],
            "regime_persistence": self._z[2],
            "uncertainty_drift": self._z[3],
        }
        from types import SimpleNamespace

        return SimpleNamespace(**fields), next_state


@dataclass(frozen=True)
class TurnMeasurement:
    """Everything M10 section 5 needs, for one governed turn."""

    trajectory_id: str
    family: str
    turn_index: int
    # 5.1 Lyapunov evolution (fast monitor energy)
    energy_v: float | None
    delta_v: float | None
    # composite W as the gate saw it
    w_current: float | None
    delta_w: float | None
    # 5.3 / 5.4 adaptive estimation
    kappa_margin: float | None
    kappa_band: str | None
    adaptive_available: bool
    # risk certification
    collapse_risk: float | None
    risk_ucb: float | None
    risk_verdict: str | None
    regime: str | None
    monitor_stable: bool | None
    drift_score: float | None
    # 5.5 / 5.6 verdicts and overrides
    pre_verdict: str | None
    final_verdict: str | None
    pi_gate_verdict: str | None
    last_verdict_source: str | None
    verdict_transitions: tuple[dict[str, Any], ...]
    fusion_reasons: tuple[str, ...]
    requires_confirmation: bool
    can_execute: bool
    # 5.7 closed-loop feedback
    closed_loop: dict[str, Any]
    # 5.8 perturbation decomposition
    iss_perturbation: dict[str, float]
    # 5.9 validity envelope
    envelope_valid: bool | None
    projection_domain_valid: bool | None
    projection_certification: str | None
    # switching guard state
    switching_safe: bool | None
    switching_metrics: dict[str, Any]
    system_confidence: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _seed_context(ctx: CognitivePipelineContext, turn: TurnSpec) -> None:
    """Install the observation o_t on the channels the projection and
    the monitor actually read."""
    if "system_tension" not in turn.drop_axes:
        ctx.observability.diagnostics.system_tension = turn.system_tension
    # The three host-composed projection axes are dynamic attributes a
    # composing layer sets before the run; the corpus plays that layer.
    if "coherence_score" not in turn.drop_axes:
        ctx.coherence_score = turn.coherence_score  # type: ignore[attr-defined]
    if "control_signal" not in turn.drop_axes:
        ctx.control_signal = turn.control_signal  # type: ignore[attr-defined]
    if "adaptive_kappa_eff" not in turn.drop_axes:
        ctx.adaptive_kappa_eff = (  # type: ignore[attr-defined]
            turn.adaptive_kappa_eff
        )
    ctx.extra["retrieval_snapshot"] = CognitiveRetrievalSnapshot(
        source="m10-corpus",
        confidence=turn.retrieval_confidence,
    )
    ctx.memory_projection = {
        "memory_pressure": turn.memory_pressure,
        "has_constraints": False,
    }
    if turn.conflict_pressure is not None:
        ctx.extra["conflict_pressure"] = turn.conflict_pressure


def _get(extra: dict[str, Any], key: str, sub: str | None = None) -> Any:
    value = extra.get(key)
    if sub is not None and isinstance(value, dict):
        return value.get(sub)
    return value


def _measure(
    spec: TrajectorySpec, index: int, ctx: CognitivePipelineContext
) -> TurnMeasurement:
    extra = ctx.extra
    monitor = extra.get("monitor_snapshot") or {}
    fusion = extra.get("fusion_trace") or {}
    theoretical = extra.get("theoretical_trace") or {}
    lyap_trace = theoretical.get("lyapunov") or {}
    envelope = extra.get("validity_envelope") or {}
    switching = dict(extra.get("switching_metrics") or {})

    return TurnMeasurement(
        trajectory_id=spec.trajectory_id,
        family=spec.family,
        turn_index=index,
        energy_v=monitor.get("energy_v"),
        delta_v=monitor.get("delta_v"),
        w_current=lyap_trace.get("w_current"),
        delta_w=fusion.get("delta_w"),
        kappa_margin=extra.get("kappa_margin"),
        kappa_band=extra.get("kappa_band"),
        adaptive_available=bool((extra.get("adaptive_trace") or {}).get("available")),
        collapse_risk=monitor.get("collapse_risk"),
        risk_ucb=monitor.get("risk_ucb"),
        risk_verdict=monitor.get("risk_verdict"),
        regime=monitor.get("regime"),
        monitor_stable=monitor.get("stable"),
        drift_score=monitor.get("drift_score"),
        pre_verdict=fusion.get("pre_verdict"),
        final_verdict=fusion.get("final_verdict"),
        pi_gate_verdict=extra.get("pi_gate_verdict"),
        last_verdict_source=extra.get("last_verdict_source"),
        verdict_transitions=tuple(
            dict(t) for t in (extra.get("verdict_transition_trace") or [])
        ),
        fusion_reasons=tuple(str(r) for r in (extra.get("fusion_reasons") or [])),
        requires_confirmation=bool(extra.get("requires_confirmation", False)),
        can_execute=bool(extra.get("can_execute", False)),
        closed_loop=dict(extra.get("closed_loop_feedback") or {}),
        iss_perturbation={
            str(k): float(v)
            for k, v in (extra.get("iss_perturbation") or {}).items()
            if isinstance(v, (int, float))
        },
        envelope_valid=envelope.get("valid"),
        projection_domain_valid=extra.get("projection_domain_valid"),
        projection_certification=extra.get("projection_certification_level"),
        switching_safe=switching.get("safe"),
        switching_metrics=switching,
        system_confidence=extra.get("system_confidence"),
    )


def run_trajectory(
    spec: TrajectorySpec,
    monitor_config: MonitorConfig | None = None,
) -> list[TurnMeasurement]:
    """Run one trajectory turn by turn with full state threading."""
    measurements: list[TurnMeasurement] = []
    scientific_state: dict[str, Any] | None = None
    prev_slow: SlowState | None = None
    prev_fast: Any = None
    switching_runtime: Any = None
    adaptive_observer: Any = None
    threaded = spec.family != "declared_risk"

    for index, turn in enumerate(spec.turns):
        pipeline = CognitivePipeline(
            core_model=_CorpusCoreModel(
                ContractionMonitorCore(monitor_config or MonitorConfig()),
                turn.slow_state,
            )
        )
        ctx = CognitivePipelineContext(
            user_id=f"m10-{spec.trajectory_id}",
            cognitive_input=dict(turn.payload),
        )
        _seed_context(ctx, turn)
        if threaded and scientific_state is not None:
            ctx.extra["scientific_state"] = scientific_state
        # Thread the causal previous state: the pipeline owns causal
        # history through the entry values of the lyapunov channels
        # (the core stage captures them as prev before installing the
        # turn's current), so the harness plays the host that keeps
        # the lineage: z_{t-1} on slow_state, x_{t-1} on cur_lyap.
        if threaded and prev_slow is not None:
            ctx.scientific.lyapunov.slow_state = prev_slow
        if threaded and prev_fast is not None:
            ctx.scientific.lyapunov.cur_lyap = prev_fast
        # The switching runtime accumulates dwell time and switch
        # counts across the trajectory; a fresh pipeline per turn must
        # not reset the clock the switching theorem runs on.
        if threaded and switching_runtime is not None:
            ctx.scientific.switching.switching_runtime = switching_runtime
        # The adaptive kappa estimator accumulates W-pair samples on
        # the pipeline object; per-turn pipelines must inherit it or
        # the estimator restarts from zero history every turn.
        if threaded and adaptive_observer is not None:
            pipeline.adaptive_observer = adaptive_observer

        pipeline.run(ctx)

        measurements.append(_measure(spec, index, ctx))
        scientific_state = ctx.extra.get("scientific_state_next")
        if turn.slow_state is not None:
            prev_slow = SlowState(*turn.slow_state)
        prev_fast = ctx.scientific.lyapunov.cur_lyap
        switching_runtime = ctx.scientific.switching.switching_runtime
        adaptive_observer = getattr(pipeline, "adaptive_observer", adaptive_observer)

    return measurements


def run_corpus(
    corpus: CorpusSpec,
    monitor_config: MonitorConfig | None = None,
) -> list[TurnMeasurement]:
    measurements: list[TurnMeasurement] = []
    for spec in corpus.trajectories:
        measurements.extend(run_trajectory(spec, monitor_config))
    return measurements
