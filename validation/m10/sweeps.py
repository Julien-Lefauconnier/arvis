# validation/m10/sweeps.py
"""LOT B4: threshold sensitivity around the registered campaign run.

Sweeps never move a registered criterion. Two instruments:

- flip-distance analyses on the campaign measurements: how much of
  the observed mass sits within delta of each decision edge (the
  adaptive hard-veto edge at margin 0, the kappa bands at -0.02 and
  -0.05, the collapse-abstain threshold at 0.8), so the report can
  say how brittle each verdict boundary is on D;
- config re-runs of the declared_risk family with a WARM risk
  estimator (the trajectory's scientific state threaded, nothing
  else), isolating the cold-start effect run 1 exposed (an
  unthreaded turn faces the fail-closed UCB of an evidence-free
  ceiling and lands CRITICAL whatever the declared risk), then
  sweeping the risk-verdict ceilings on the warm variant.

Exploratory by design, published beside the campaign artifacts.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import (
    CognitivePipelineContext,
)
from arvis.math.core.contraction_monitor_core import (
    ContractionMonitorCore,
    MonitorConfig,
)
from validation.m10.corpus import CorpusSpec, TrajectorySpec
from validation.m10.runner import (
    TurnMeasurement,
    _CorpusCoreModel,
    _measure,
    _seed_context,
)

_COLLAPSE_ABSTAIN_THRESHOLD = 0.8


def _share(count: int, total: int) -> float:
    return count / total if total else 0.0


def margin_edge_sensitivity(
    ms: list[TurnMeasurement],
    edges: tuple[float, ...] = (0.0, -0.02, -0.05),
    deltas: tuple[float, ...] = (0.005, 0.01, 0.02, 0.05),
) -> dict[str, Any]:
    """Mass of adaptive margins within delta of each band edge; the
    edge at 0.0 is the hard-veto boundary (margin >= 0 vetoes to
    ABSTAIN), -0.02 the critical band, -0.05 the warning band."""
    margins = [m.kappa_margin for m in ms if m.kappa_margin is not None]
    total = len(margins)
    out: dict[str, Any] = {"samples": total}
    for edge in edges:
        row: dict[str, float] = {
            "mass_above_edge": _share(sum(1 for v in margins if v >= edge), total),
        }
        for delta in deltas:
            near = sum(1 for v in margins if abs(v - edge) <= delta)
            row[f"mass_within_{delta}"] = _share(near, total)
        out[f"edge_{edge}"] = row
    return out


def collapse_threshold_sensitivity(
    ms: list[TurnMeasurement],
    threshold: float = _COLLAPSE_ABSTAIN_THRESHOLD,
    alternates: tuple[float, ...] = (0.7, 0.75, 0.85, 0.9),
) -> dict[str, Any]:
    """Mass of collapse risk above the abstain threshold and each
    alternate; the flip mass is the share of turns whose abstain
    decision would change if the threshold moved there."""
    values = [m.collapse_risk for m in ms if m.collapse_risk is not None]
    total = len(values)
    above = sum(1 for v in values if v >= threshold)
    out: dict[str, Any] = {
        "samples": total,
        "threshold": threshold,
        "mass_above_threshold": _share(above, total),
    }
    for alt in alternates:
        above_alt = sum(1 for v in values if v >= alt)
        out[f"mass_above_{alt}"] = _share(above_alt, total)
        out[f"flip_mass_to_{alt}"] = _share(abs(above_alt - above), total)
    return out


def run_trajectory_warm_risk(
    spec: TrajectorySpec,
    monitor_config: MonitorConfig | None = None,
) -> list[TurnMeasurement]:
    """The warm-risk variant: thread ONLY the scientific state (the
    violation history the PAC risk ceiling accumulates evidence
    from), so the risk estimator warms across the trajectory while
    the fast state, the switching runtime and the adaptive observer
    stay per-turn (no live W pair, no dwell clock, no veto). One
    variable moves relative to the registered runner: evidence."""
    measurements: list[TurnMeasurement] = []
    scientific_state: dict[str, Any] | None = None
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
        if scientific_state is not None:
            ctx.extra["scientific_state"] = scientific_state
        pipeline.run(ctx)
        measurements.append(_measure(spec, index, ctx))
        scientific_state = ctx.extra.get("scientific_state_next")
    return measurements


def _verdict_shares(ms: list[TurnMeasurement]) -> dict[str, Any]:
    final = Counter(m.final_verdict or "UNKNOWN" for m in ms)
    risk = Counter(m.risk_verdict or "UNKNOWN" for m in ms)
    total = len(ms)
    return {
        "turns": total,
        "final": {k: _share(v, total) for k, v in sorted(final.items())},
        "risk_verdict": {k: _share(v, total) for k, v in sorted(risk.items())},
    }


def declared_risk_warmup_sweep(
    corpus: CorpusSpec,
    cold: list[TurnMeasurement],
) -> dict[str, Any]:
    """Cold (registered run) versus warm risk estimator on the
    declared_risk family, same turns, same seeds."""
    warm: list[TurnMeasurement] = []
    for spec in corpus.trajectories:
        if spec.family == "declared_risk":
            warm.extend(run_trajectory_warm_risk(spec))
    cold_dr = [m for m in cold if m.family == "declared_risk"]
    return {
        "cold": _verdict_shares(cold_dr),
        "warm": _verdict_shares(warm),
    }


def risk_ceiling_sweep(
    corpus: CorpusSpec,
    ok_ceilings: tuple[float, ...] = (0.10, 0.15, 0.20),
    critical_ceilings: tuple[float, ...] = (0.30, 0.40, 0.50),
) -> dict[str, Any]:
    """Risk-verdict band sensitivity on the WARM declared_risk
    variant: sweep the calibratable verdict ceilings of
    MonitorConfig around their defaults (0.15 / 0.40)."""
    specs = [s for s in corpus.trajectories if s.family == "declared_risk"]
    out: dict[str, Any] = {}
    for ok in ok_ceilings:
        for critical in critical_ceilings:
            config = MonitorConfig(
                verdict_ok_ceiling=ok,
                verdict_critical_ceiling=critical,
            )
            ms: list[TurnMeasurement] = []
            for spec in specs:
                ms.extend(run_trajectory_warm_risk(spec, config))
            out[f"ok_{ok}_critical_{critical}"] = _verdict_shares(ms)
    return out


def compute_sweeps(
    corpus: CorpusSpec,
    ms: list[TurnMeasurement],
) -> dict[str, Any]:
    return {
        "margin_edges": margin_edge_sensitivity(ms),
        "collapse_threshold": collapse_threshold_sensitivity(ms),
        "declared_risk_warmup": declared_risk_warmup_sweep(corpus, ms),
        "risk_ceilings_warm": risk_ceiling_sweep(corpus),
    }
