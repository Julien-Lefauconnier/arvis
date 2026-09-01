# validation/m10/corpus.py
"""The deterministic validation corpus D (M10 section 4).

Six trajectory families, one seeded generator per family, every value
drawn from a per-trajectory ``random.Random(seed)``: same seeds, same
corpus, bit for bit. A turn's observation carries the five certified
projection axes (M3_3), the monitor's input channels (retrieval
confidence, intent, ambiguity, memory pressure) and, per family,
deliberate boundary or adversarial excursions.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

FAMILIES = (
    "nominal",
    "boundary",
    "adversarial",
    "switching_stress",
    "long_horizon",
    "conflicting",
    "declared_risk",
)

_INTENTS = ("question", "search", "action", "other")


@dataclass(frozen=True)
class TurnSpec:
    """One observation o_t: everything the harness seeds for a turn."""

    payload: dict[str, Any]
    system_tension: float
    coherence_score: float
    control_signal: float
    adaptive_kappa_eff: float
    retrieval_confidence: float
    memory_pressure: float
    conflict_pressure: float | None = None
    # slow state z_t for the composite-W / adaptive-kappa path (the v0
    # monitor is fast-only by design, so the corpus supplies the slow
    # trajectory; None = fast-only turn)
    slow_state: tuple[float, float, float, float] | None = None
    # boundary/adversarial families may deliberately break an axis
    drop_axes: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrajectorySpec:
    trajectory_id: str
    family: str
    seed: int
    turns: tuple[TurnSpec, ...]


@dataclass(frozen=True)
class CorpusSpec:
    corpus_version: str
    master_seed: int
    trajectories: tuple[TrajectorySpec, ...]

    def manifest(self) -> dict[str, Any]:
        """The published identity of D: versioned seeds per trajectory."""
        return {
            "corpus_version": self.corpus_version,
            "master_seed": self.master_seed,
            "trajectories": [
                {
                    "id": t.trajectory_id,
                    "family": t.family,
                    "seed": t.seed,
                    "turns": len(t.turns),
                }
                for t in self.trajectories
            ],
        }


def _slow_path(
    rng: random.Random, total: int, kind: str
) -> list[tuple[float, float, float, float]]:
    """Deterministic slow trajectories z_0..z_T per family character:
    contracting (nominal, declared_risk unused), alternating
    (switching), growing (adversarial, long_horizon ramp), wandering
    (boundary, conflicting)."""
    z = [rng.uniform(0.3, 0.7) for _ in range(4)]
    path: list[tuple[float, float, float, float]] = []
    for index in range(total):
        if kind == "contracting":
            z = [v * rng.uniform(0.82, 0.95) for v in z]
        elif kind == "alternating":
            scale = 0.9 if index % 2 else 1.35
            z = [min(1.5, v * scale + rng.uniform(-0.02, 0.02)) for v in z]
        elif kind == "growing":
            z = [min(2.0, v * rng.uniform(1.03, 1.12)) for v in z]
        else:  # wandering
            z = [max(0.0, v + rng.uniform(-0.08, 0.08)) for v in z]
        path.append(tuple(round(v, 4) for v in z))
    return path


_SLOW_KIND = {
    "nominal": "contracting",
    "boundary": "wandering",
    "adversarial": "growing",
    "switching_stress": "alternating",
    "long_horizon": "growing",
    "conflicting": "wandering",
    "declared_risk": None,
}


def _payload(rng: random.Random, intent: str) -> dict[str, Any]:
    return {
        "query": f"m10-turn-{rng.randrange(10**6)}",
        "intent_type": intent,
        "referential_ambiguity": round(rng.uniform(0.0, 0.9), 3),
        "context_dependent": round(rng.uniform(0.0, 0.6), 3),
    }


def _nominal_turn(rng: random.Random) -> TurnSpec:
    """Healthy interior of the validated domain: calm axes, confident
    retrieval, mostly informational intents."""
    intent = rng.choices(_INTENTS, weights=(6, 2, 1, 1))[0]
    return TurnSpec(
        payload=_payload(rng, intent),
        system_tension=round(rng.uniform(15.0, 45.0), 3),
        coherence_score=round(rng.uniform(0.55, 0.85), 3),
        control_signal=round(rng.uniform(15.0, 60.0), 3),
        adaptive_kappa_eff=round(rng.uniform(0.2, 0.5), 3),
        retrieval_confidence=round(rng.uniform(0.7, 0.98), 3),
        memory_pressure=round(rng.uniform(0.0, 0.3), 3),
    )


def _boundary_turn(rng: random.Random) -> TurnSpec:
    """Edge of the domain: axes hugging their bounds, occasionally a
    missing axis (the <key>_present=False failure mode of M3_3)."""
    hug = rng.random() < 0.7
    tension = 100.0 - rng.uniform(0.0, 0.5) if hug else rng.uniform(0.0, 0.5)
    drop: tuple[str, ...] = ()
    if rng.random() < 0.25:
        drop = (rng.choice(("coherence_score", "control_signal")),)
    return TurnSpec(
        payload=_payload(rng, rng.choice(_INTENTS)),
        system_tension=round(tension, 3),
        coherence_score=rng.choice((0.0, 1.0)),
        control_signal=round(rng.uniform(95.0, 100.0), 3),
        adaptive_kappa_eff=round(rng.choice((0.0, 1.0)), 3),
        retrieval_confidence=round(rng.uniform(0.3, 0.7), 3),
        memory_pressure=round(rng.uniform(0.5, 0.9), 3),
        drop_axes=drop,
    )


def _adversarial_turn(rng: random.Random) -> TurnSpec:
    """Bounded adversarial pressure: out-of-bounds axes, hostile
    retrieval, action intents, declared-risk needles."""
    payload = _payload(rng, "action")
    if rng.random() < 0.4:
        payload["risk"] = round(rng.uniform(0.75, 1.0), 3)
    out_of_bounds = rng.random() < 0.6
    tension = rng.uniform(100.5, 250.0) if out_of_bounds else rng.uniform(60.0, 100.0)
    return TurnSpec(
        payload=payload,
        system_tension=round(tension, 3),
        coherence_score=round(rng.uniform(-0.5, 0.2), 3),
        control_signal=round(rng.uniform(80.0, 140.0), 3),
        adaptive_kappa_eff=round(rng.uniform(0.0, 0.1), 3),
        retrieval_confidence=round(rng.uniform(0.0, 0.3), 3),
        memory_pressure=round(rng.uniform(0.7, 1.0), 3),
        conflict_pressure=round(rng.uniform(0.5, 1.0), 3),
    )


def _switching_turn(rng: random.Random, index: int) -> TurnSpec:
    """High-frequency alternation between calm and stressed postures:
    the dwell-time stress case of M10 4.1."""
    stressed = index % 2 == 1
    intent = "action" if stressed else "question"
    return TurnSpec(
        payload=_payload(rng, intent),
        system_tension=round(
            rng.uniform(70.0, 95.0) if stressed else rng.uniform(5.0, 20.0), 3
        ),
        coherence_score=round(
            rng.uniform(0.2, 0.4) if stressed else rng.uniform(0.8, 0.95), 3
        ),
        control_signal=round(
            rng.uniform(70.0, 95.0) if stressed else rng.uniform(5.0, 30.0), 3
        ),
        adaptive_kappa_eff=round(rng.uniform(0.02, 0.12), 3),
        retrieval_confidence=round(
            rng.uniform(0.2, 0.5) if stressed else rng.uniform(0.8, 0.95), 3
        ),
        memory_pressure=round(rng.uniform(0.1, 0.6), 3),
        conflict_pressure=round(rng.uniform(0.4, 0.8), 3) if stressed else None,
    )


def _long_horizon_turn(rng: random.Random, index: int, total: int) -> TurnSpec:
    """Slow ramp over a long window: memory pressure and tension climb,
    retrieval confidence decays; the regime estimator and the PAC
    window are the components under load."""
    t = index / max(1, total - 1)
    return TurnSpec(
        payload=_payload(rng, rng.choices(_INTENTS, weights=(4, 3, 2, 1))[0]),
        system_tension=round(10.0 + 70.0 * t + rng.uniform(-3.0, 3.0), 3),
        coherence_score=round(max(0.05, 0.9 - 0.6 * t + rng.uniform(-0.05, 0.05)), 3),
        control_signal=round(20.0 + 60.0 * t, 3),
        adaptive_kappa_eff=round(max(0.01, 0.25 - 0.2 * t), 3),
        retrieval_confidence=round(
            max(0.05, 0.9 - 0.7 * t + rng.uniform(-0.05, 0.05)), 3
        ),
        memory_pressure=round(min(1.0, 0.1 + 0.8 * t), 3),
    )


def _conflicting_turn(rng: random.Random) -> TurnSpec:
    """Inconsistent signals: calm tension with hostile retrieval, high
    coherence with high conflict pressure, ambiguous intents."""
    return TurnSpec(
        payload=_payload(rng, rng.choice(("other", "action"))),
        system_tension=round(rng.uniform(5.0, 25.0), 3),
        coherence_score=round(rng.uniform(0.7, 0.95), 3),
        control_signal=round(rng.uniform(60.0, 90.0), 3),
        adaptive_kappa_eff=round(rng.uniform(0.1, 0.3), 3),
        retrieval_confidence=round(rng.uniform(0.05, 0.35), 3),
        memory_pressure=round(rng.uniform(0.2, 0.5), 3),
        conflict_pressure=round(rng.uniform(0.55, 0.95), 3),
    )


def _declared_risk_turn(rng: random.Random) -> TurnSpec:
    """The graded input-risk path (M10 5.5's ALLOW mass): pure
    ``{"risk": r}`` payloads sweeping the three documented bands, on a
    calm interior observation."""
    band = rng.choice(("allow", "confirm", "block"))
    if band == "allow":
        r = rng.uniform(0.0, 0.39)
    elif band == "confirm":
        r = rng.uniform(0.4, 0.79)
    else:
        r = rng.uniform(0.8, 1.0)
    return TurnSpec(
        payload={"risk": round(r, 3)},
        system_tension=round(rng.uniform(15.0, 40.0), 3),
        coherence_score=round(rng.uniform(0.55, 0.85), 3),
        control_signal=round(rng.uniform(15.0, 55.0), 3),
        adaptive_kappa_eff=round(rng.uniform(0.2, 0.5), 3),
        retrieval_confidence=round(rng.uniform(0.75, 0.98), 3),
        memory_pressure=round(rng.uniform(0.0, 0.25), 3),
    )


_LENGTHS = {
    "nominal": 24,
    "boundary": 16,
    "adversarial": 16,
    "switching_stress": 24,
    "long_horizon": 60,
    "conflicting": 16,
    "declared_risk": 24,
}


def _trajectory(family: str, seed: int, trajectory_id: str) -> TrajectorySpec:
    rng = random.Random(seed)
    total = _LENGTHS[family]
    slow_kind = _SLOW_KIND[family]
    slow_path = (
        _slow_path(random.Random(seed ^ 0x5A5A5A5A), total, slow_kind)
        if slow_kind is not None
        else None
    )
    turns: list[TurnSpec] = []
    for index in range(total):
        if family == "nominal":
            turns.append(_nominal_turn(rng))
        elif family == "boundary":
            turns.append(_boundary_turn(rng))
        elif family == "adversarial":
            turns.append(_adversarial_turn(rng))
        elif family == "switching_stress":
            turns.append(_switching_turn(rng, index))
        elif family == "long_horizon":
            turns.append(_long_horizon_turn(rng, index, total))
        elif family == "declared_risk":
            turns.append(_declared_risk_turn(rng))
        else:
            turns.append(_conflicting_turn(rng))
    if slow_path is not None:
        turns = [
            TurnSpec(
                payload=t.payload,
                system_tension=t.system_tension,
                coherence_score=t.coherence_score,
                control_signal=t.control_signal,
                adaptive_kappa_eff=t.adaptive_kappa_eff,
                retrieval_confidence=t.retrieval_confidence,
                memory_pressure=t.memory_pressure,
                conflict_pressure=t.conflict_pressure,
                slow_state=slow_path[i],
                drop_axes=t.drop_axes,
            )
            for i, t in enumerate(turns)
        ]
    return TrajectorySpec(
        trajectory_id=trajectory_id,
        family=family,
        seed=seed,
        turns=tuple(turns),
    )


def build_corpus(
    master_seed: int = 20260901,
    trajectories_per_family: int = 8,
    corpus_version: str = "D-1.0",
) -> CorpusSpec:
    """Deterministic corpus: per-trajectory seeds derive from the
    master seed, so the manifest alone identifies D."""
    seeder = random.Random(master_seed)
    trajectories: list[TrajectorySpec] = []
    for family in FAMILIES:
        for i in range(trajectories_per_family):
            seed = seeder.randrange(2**32)
            trajectories.append(_trajectory(family, seed, f"{family}-{i:02d}"))
    return CorpusSpec(
        corpus_version=corpus_version,
        master_seed=master_seed,
        trajectories=tuple(trajectories),
    )


def build_smoke_corpus(master_seed: int = 42) -> CorpusSpec:
    """Tiny corpus for the gate: one short trajectory per family."""
    seeder = random.Random(master_seed)
    trajectories = []
    for family in FAMILIES:
        seed = seeder.randrange(2**32)
        full = _trajectory(family, seed, f"smoke-{family}")
        trajectories.append(
            TrajectorySpec(
                trajectory_id=full.trajectory_id,
                family=family,
                seed=seed,
                turns=full.turns[:6],
            )
        )
    return CorpusSpec(
        corpus_version="D-smoke",
        master_seed=master_seed,
        trajectories=tuple(trajectories),
    )


# ---------------------------------------------------------------------------
# D-2.0: the state-feedback extension (campaign MATH-C, LOT C3)
# ---------------------------------------------------------------------------

FAMILIES_D2 = FAMILIES + ("nominal_feedback",)

# The published feedback law, executed by the harness (runner.py): the
# monitor's fast input channels start far from calm and relax toward
# the targets at a geometric rate each turn, faster when the previous
# final verdict tightened; a small jitter derived from the published
# per-turn specs keeps the equilibrium alive. D-1.0's failed 5.1
# criterion measured an exogenous walk; D-2.0 encodes the contraction
# regime A12 speaks about in the input dynamics themselves.
FEEDBACK_LAW: dict[str, Any] = {
    "targets": {"retrieval_confidence": 0.97, "memory_pressure": 0.02},
    "rho_free": 0.92,
    "rho_tightened": 0.85,
    "tightened_verdicts": ("REQUIRE_CONFIRMATION", "ABSTAIN"),
    "jitter_scale": 0.02,
}


def _nominal_feedback_turn(rng: random.Random) -> TurnSpec:
    """Base spec of a feedback turn: calm interior projection axes, a
    deliberately stressed start on the fast input channels (the law
    relaxes them toward the targets), plain low-ambiguity payloads."""
    return TurnSpec(
        payload={
            "query": f"m10-fb-{rng.randrange(10**6)}",
            "intent_type": "question",
            "referential_ambiguity": round(rng.uniform(0.0, 0.15), 3),
            "context_dependent": round(rng.uniform(0.0, 0.10), 3),
        },
        system_tension=round(rng.uniform(20.0, 40.0), 3),
        coherence_score=round(rng.uniform(0.60, 0.80), 3),
        control_signal=round(rng.uniform(20.0, 50.0), 3),
        adaptive_kappa_eff=round(rng.uniform(0.25, 0.45), 3),
        retrieval_confidence=round(rng.uniform(0.40, 0.55), 3),
        memory_pressure=round(rng.uniform(0.45, 0.60), 3),
    )


def _trajectory_d2(family: str, seed: int, trajectory_id: str) -> TrajectorySpec:
    if family != "nominal_feedback":
        return _trajectory(family, seed, trajectory_id)
    rng = random.Random(seed)
    total = 24
    slow_path = _slow_path(random.Random(seed ^ 0x5A5A5A5A), total, "contracting")
    turns = [_nominal_feedback_turn(rng) for _ in range(total)]
    turns = [
        TurnSpec(
            payload=t.payload,
            system_tension=t.system_tension,
            coherence_score=t.coherence_score,
            control_signal=t.control_signal,
            adaptive_kappa_eff=t.adaptive_kappa_eff,
            retrieval_confidence=t.retrieval_confidence,
            memory_pressure=t.memory_pressure,
            conflict_pressure=t.conflict_pressure,
            slow_state=slow_path[i],
            drop_axes=t.drop_axes,
        )
        for i, t in enumerate(turns)
    ]
    return TrajectorySpec(
        trajectory_id=trajectory_id,
        family=family,
        seed=seed,
        turns=tuple(turns),
    )


def build_corpus_d2(
    master_seed: int = 20260902,
    trajectories_per_family: int = 8,
    corpus_version: str = "D-2.0",
) -> CorpusSpec:
    """D-2.0: every D-1.0 family regenerated under its own master seed
    plus the state-feedback nominal family. The manifest identifies
    the corpus; the feedback law's constants are FEEDBACK_LAW."""
    seeder = random.Random(master_seed)
    trajectories: list[TrajectorySpec] = []
    for family in FAMILIES_D2:
        for i in range(trajectories_per_family):
            seed = seeder.randrange(2**32)
            trajectories.append(_trajectory_d2(family, seed, f"{family}-{i:02d}"))
    return CorpusSpec(
        corpus_version=corpus_version,
        master_seed=master_seed,
        trajectories=tuple(trajectories),
    )


def build_smoke_corpus_d2(master_seed: int = 43) -> CorpusSpec:
    """Tiny D-2.0 for the gate: one short trajectory per family, the
    feedback family kept longer so its transient is visible."""
    seeder = random.Random(master_seed)
    trajectories = []
    for family in FAMILIES_D2:
        seed = seeder.randrange(2**32)
        full = _trajectory_d2(family, seed, f"smoke2-{family}")
        keep = 8 if family == "nominal_feedback" else 6
        trajectories.append(
            TrajectorySpec(
                trajectory_id=full.trajectory_id,
                family=family,
                seed=seed,
                turns=full.turns[:keep],
            )
        )
    return CorpusSpec(
        corpus_version="D-2.0-smoke",
        master_seed=master_seed,
        trajectories=tuple(trajectories),
    )
