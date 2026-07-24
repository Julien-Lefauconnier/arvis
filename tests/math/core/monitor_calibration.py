# tests/math/core/monitor_calibration.py
"""Offline calibration sweep for the v0 ContractionMonitorCore (§3.4).

Replays labelled scenarios through the REAL monitor under a grid of two knob
families and reports which operating point makes the certified risk
(``collapse_risk`` / ``risk_verdict``) DISCRIMINATE well-grounded turns from
weakly-grounded ones: on evidence, not by eye.

Two knob families, because the pipeline splits the work:
  * the *confidence transform* (raw retrieval scores -> a single confidence) is
    owned by the host (veramem ``_confidence_from_scores``); the monitor only
    ever sees ``retrieval_snapshot.confidence``. We model candidate transforms
    here (mean / max / rescale) so the sweep can co-optimise them.
  * the *MonitorConfig* (``tau_risk`` and friends) is owned by arvis.

Deterministic, dependency-free (pure arvis math + stdlib), CI-runnable and also
usable as a script::

    python -m tests.math.core.monitor_calibration
    python -m tests.math.core.monitor_calibration --scenarios captured.jsonl

The default scenarios are anchored to values actually observed on the research
box (grounded Méridien hits ~0.65; an off-corpus query ~0.56) so the sweep is
calibrated against real signal, not invented bands. To sweep on fully-captured
data, pass a JSONL of {"name", "label", "turns": [{"scores": [...], ...}]}.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from arvis.math.core.contraction_monitor_core import (
    ContractionMonitorCore,
    MonitorConfig,
    MonitorSnapshot,
)

# Labels that SHOULD stay certified-safe (low risk) vs. SHOULD be flagged.
GOOD_LABELS = frozenset({"grounded", "nominal"})
BAD_LABELS = frozenset({"weak", "adverse"})

ConfidenceFn = Callable[[Sequence[float]], float]


# ---------------------------------------------------------------------------
# Confidence transforms (host-side knob, modelled here)
# ---------------------------------------------------------------------------
def confidence_mean(scores: Sequence[float]) -> float:
    vals = [float(s) for s in scores]
    return sum(vals) / len(vals) if vals else 0.0


def confidence_max(scores: Sequence[float]) -> float:
    vals = [float(s) for s in scores]
    return max(vals) if vals else 0.0


def confidence_rescale(lo: float, hi: float) -> ConfidenceFn:
    """Linearly stretch mean(scores) from [lo, hi] onto [0, 1] (clamped).

    Counters the way sentence embeddings pack cosine scores into a narrow band:
    it amplifies the useful range at the cost of sensitivity near the hinge.
    """
    span = hi - lo

    def _fn(scores: Sequence[float]) -> float:
        if not scores or span <= 0.0:
            return 0.0
        m = sum(float(s) for s in scores) / len(scores)
        return max(0.0, min(1.0, (m - lo) / span))

    return _fn


TRANSFORMS: dict[str, ConfidenceFn] = {
    "mean": confidence_mean,
    "max": confidence_max,
    "rescale(0.50,0.70)": confidence_rescale(0.50, 0.70),
    "rescale(0.45,0.65)": confidence_rescale(0.45, 0.65),
}

DEFAULT_TAUS: tuple[float, ...] = (0.35, 0.40, 0.45, 0.50)


# ---------------------------------------------------------------------------
# Scenario model
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Turn:
    """One conversational turn. Empty ``scores`` => no retrieval (the risk axis
    is off, as for a greeting)."""

    scores: tuple[float, ...] = ()
    reason: str = "informational_query"
    n_uncertainty: int = 0
    memory_pressure: float = 0.0


@dataclass(frozen=True)
class Scenario:
    name: str
    label: str
    turns: tuple[Turn, ...]


def _frame(n_axes: int) -> Any:
    return type("UncertaintyFrame", (), {"axes": tuple(range(n_axes))})()


def _bundle(turn: Turn, confidence: ConfidenceFn) -> Any:
    if turn.scores:
        retrieval: Any = type(
            "RetrievalSnapshot",
            (),
            {
                "confidence": confidence(turn.scores),
                "scores": list(turn.scores),
                "semantic_roles": [],
            },
        )()
    else:
        retrieval = None  # conversational turn: no grounding, risk axis off
    decision = type(
        "DecisionResult",
        (),
        {
            "uncertainty_frames": [_frame(turn.n_uncertainty)]
            if turn.n_uncertainty
            else [],
            "reason": turn.reason,
        },
    )()
    return type(
        "Bundle",
        (),
        {
            "retrieval_snapshot": retrieval,
            "decision_result": decision,
            "memory_features": {"memory_pressure": turn.memory_pressure},
        },
    )()


def replay(
    scenario: Scenario, *, config: MonitorConfig, confidence: ConfidenceFn
) -> list[MonitorSnapshot]:
    """Run one scenario through the real monitor, carrying its state forward."""
    core = ContractionMonitorCore(config)
    state: dict[str, Any] | None = None
    out: list[MonitorSnapshot] = []
    for turn in scenario.turns:
        snap, state = core.compute(_bundle(turn, confidence), state)
        out.append(snap)
    return out


# ---------------------------------------------------------------------------
# Sweep
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SweepResult:
    transform: str
    tau_risk: float
    good_max_phat: float  # worst (highest) certified risk among GOOD scenarios
    bad_min_phat: float  # best (lowest) certified risk among BAD scenarios
    good_risk_max: float  # highest per-turn risk axis over GOOD turns
    per_scenario: dict[str, float] = field(default_factory=dict)

    @property
    def margin(self) -> float:
        """Strict separation margin: BAD all above GOOD when > 0."""
        return self.bad_min_phat - self.good_max_phat

    @property
    def separates(self) -> bool:
        return self.margin > 0.0

    @property
    def good_headroom(self) -> float:
        """How far tau sits ABOVE the worst grounded turn's risk.

        Robustness of the operating point: a large headroom means a grounded
        turn must degrade a lot before it false-alarms. (Negative => grounded
        turns already cross tau, i.e. false alarms.)
        """
        return self.tau_risk - self.good_risk_max


def evaluate(
    scenarios: Sequence[Scenario], *, transform: str, tau_risk: float
) -> SweepResult:
    cfg = MonitorConfig(tau_risk=tau_risk)
    fn = TRANSFORMS[transform]
    final_phat: dict[str, float] = {}
    good: list[float] = []
    bad: list[float] = []
    good_risk_max = 0.0
    for sc in scenarios:
        snaps = replay(sc, config=cfg, confidence=fn)
        final_phat[sc.name] = snaps[-1].collapse_risk
        if sc.label in GOOD_LABELS:
            good.append(snaps[-1].collapse_risk)
            good_risk_max = max(good_risk_max, max(s.cur_lyap.risk for s in snaps))
        elif sc.label in BAD_LABELS:
            bad.append(snaps[-1].collapse_risk)
    return SweepResult(
        transform=transform,
        tau_risk=tau_risk,
        good_max_phat=max(good) if good else 0.0,
        bad_min_phat=min(bad) if bad else 0.0,
        good_risk_max=good_risk_max,
        per_scenario=final_phat,
    )


def sweep(
    scenarios: Sequence[Scenario],
    *,
    transforms: Iterable[str] = tuple(TRANSFORMS),
    taus: Iterable[float] = DEFAULT_TAUS,
) -> list[SweepResult]:
    """All (transform x tau_risk) combos, ranked best separation first."""
    results = [
        evaluate(scenarios, transform=t, tau_risk=tau)
        for t in transforms
        for tau in taus
    ]
    # Best = widest separation, then most robust (largest grounded headroom),
    # then simpler transform.
    results.sort(key=lambda r: (-r.margin, -r.good_headroom, r.transform))
    return results


def recommend(
    results: Sequence[SweepResult], *, max_false_alarm: float = 0.1
) -> SweepResult | None:
    """Best separating operating point that keeps GOOD scenarios quiet.

    Among combos that strictly separate and stay under the false-alarm cap,
    pick widest separation first (BAD clearly flagged), then largest grounded
    headroom (most robust tau). This is the same order as the printed table, so
    the recommendation is just its top eligible row: never the brittle combo
    that only happens to separate this scenario set with razor-thin headroom.
    """
    eligible = [
        r for r in results if r.separates and r.good_max_phat <= max_false_alarm
    ]
    eligible.sort(key=lambda r: (-r.margin, -r.good_headroom, r.transform))
    return eligible[0] if eligible else None


# ---------------------------------------------------------------------------
# Canonical scenarios (anchored to research-box observations)
# ---------------------------------------------------------------------------
def default_scenarios() -> list[Scenario]:
    grounded = (0.660, 0.655, 0.654, 0.623)  # seeded Méridien verify scores
    weak = (0.600, 0.570, 0.540, 0.520)  # off-corpus nearest-of-4 (~0.557 mean)
    return [
        Scenario(
            "grounded_meridien",
            "grounded",
            tuple(Turn(scores=grounded) for _ in range(6)),
        ),
        Scenario(
            "nominal_greeting",
            "nominal",
            (Turn(reason="informational_query"), Turn(reason="informational_query")),
        ),
        Scenario(
            "weak_offcorpus",
            "weak",
            tuple(Turn(scores=weak) for _ in range(6)),
        ),
        Scenario(
            "adverse_degrading",
            "adverse",
            (
                Turn(scores=(0.66, 0.65, 0.65, 0.62)),
                Turn(scores=(0.62, 0.60, 0.58, 0.56)),
                Turn(scores=(0.55, 0.52, 0.50, 0.48)),
                Turn(scores=(0.47, 0.44, 0.42, 0.40)),
                Turn(scores=(0.40, 0.38, 0.36, 0.34)),
                Turn(scores=(0.35, 0.33, 0.31, 0.30)),
            ),
        ),
    ]


def load_scenarios(path: str | Path) -> list[Scenario]:
    """Load captured scenarios from JSONL (one Scenario per line)."""
    out: list[Scenario] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        raw = json.loads(line)
        turns = tuple(
            Turn(
                scores=tuple(float(s) for s in t.get("scores", ())),
                reason=str(t.get("reason", "informational_query")),
                n_uncertainty=int(t.get("n_uncertainty", 0)),
                memory_pressure=float(t.get("memory_pressure", 0.0)),
            )
            for t in raw.get("turns", ())
        )
        out.append(Scenario(str(raw["name"]), str(raw["label"]), turns))
    return out


# ---------------------------------------------------------------------------
# Script entrypoint
# ---------------------------------------------------------------------------
def _format_table(results: Sequence[SweepResult]) -> str:
    rows = [
        f"{r.transform:<20} tau={r.tau_risk:<4} "
        f"good_max={r.good_max_phat:5.3f} bad_min={r.bad_min_phat:5.3f} "
        f"margin={r.margin:+6.3f} headroom={r.good_headroom:+6.3f} "
        f"{'SEP' if r.separates else '   '}"
        for r in results
    ]
    return "\n".join(rows)


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Monitor calibration sweep (§3.4).")
    parser.add_argument("--scenarios", help="JSONL of captured scenarios", default=None)
    parser.add_argument("--max-false-alarm", type=float, default=0.1)
    args = parser.parse_args(argv)

    scenarios = (
        load_scenarios(args.scenarios) if args.scenarios else default_scenarios()
    )
    results = sweep(scenarios)
    print(_format_table(results))
    print()
    best = recommend(results, max_false_alarm=args.max_false_alarm)
    if best is None:
        print("No operating point separates GOOD from BAD under the false-alarm cap.")
        return 1
    print(
        f"RECOMMENDED: transform={best.transform} tau_risk={best.tau_risk} "
        f"(margin={best.margin:+.3f}, false_alarm={best.good_max_phat:.3f})"
    )
    print(f"  per-scenario final p_hat: {best.per_scenario}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
