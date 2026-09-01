# tests/math/m10/test_m10_d2_feedback.py
"""Gate smoke of the D-2.0 state-feedback extension (MATH-C LOT C3).

D-1.0's failed 5.1 criterion measured an exogenous walk; D-2.0
encodes the contraction regime in the input dynamics. These pins fix
the corpus identity, the feedback law's effect (the consumed energy
contracts along the transient) and its determinism.
"""

from __future__ import annotations

from validation.m10.corpus import (
    FAMILIES_D2,
    build_corpus_d2,
    build_smoke_corpus_d2,
)
from validation.m10.runner import run_trajectory


def test_d2_families_are_the_seven_plus_feedback() -> None:
    expected = (
        "nominal",
        "boundary",
        "adversarial",
        "switching_stress",
        "long_horizon",
        "conflicting",
        "declared_risk",
        "nominal_feedback",
    )
    assert FAMILIES_D2 == expected
    corpus = build_smoke_corpus_d2()
    assert tuple(t.family for t in corpus.trajectories) == expected


def test_d2_corpus_is_bit_for_bit_reproducible() -> None:
    first = build_corpus_d2()
    second = build_corpus_d2()

    assert first.corpus_version == "D-2.0"
    assert first.manifest() == second.manifest()
    assert first.trajectories == second.trajectories


def test_feedback_family_contracts_along_the_transient() -> None:
    """The point of D-2.0: with contracting input dynamics the energy
    the gate consumes contracts; the feedback run is deterministic."""
    corpus = build_smoke_corpus_d2()
    spec = next(t for t in corpus.trajectories if t.family == "nominal_feedback")

    first = run_trajectory(spec)
    second = run_trajectory(spec)

    assert [m.to_dict() for m in first] == [m.to_dict() for m in second]
    deltas = [m.delta_w for m in first[1:] if m.delta_w is not None]
    assert deltas and all(d < 0 for d in deltas), deltas
    energies = [m.energy_v for m in first if m.energy_v is not None]
    assert energies[0] > energies[-1]


def test_feedback_law_reacts_to_tightened_verdicts() -> None:
    """The state-feedback semantic itself: after a tightened verdict
    the channels relax faster (rho_tightened) than after none; both
    match the published law exactly."""
    from validation.m10.corpus import FEEDBACK_LAW
    from validation.m10.runner import _feedback_turn

    corpus = build_smoke_corpus_d2()
    spec = next(t for t in corpus.trajectories if t.family == "nominal_feedback")
    turn = spec.turns[1]
    state = {"retrieval_confidence": 0.50, "memory_pressure": 0.50}

    free, _ = _feedback_turn(turn, dict(state), None)
    tight, _ = _feedback_turn(turn, dict(state), "REQUIRE_CONFIRMATION")

    targets = FEEDBACK_LAW["targets"]
    jitter = FEEDBACK_LAW["jitter_scale"]

    def expected(rho: float, name: str, spec_value: float) -> float:
        target = targets[name]
        value = (
            target + rho * (state[name] - target) + jitter * (spec_value - state[name])
        )
        return round(min(1.0, max(0.0, value)), 6)

    assert free.retrieval_confidence == expected(
        FEEDBACK_LAW["rho_free"], "retrieval_confidence", turn.retrieval_confidence
    )
    assert tight.retrieval_confidence == expected(
        FEEDBACK_LAW["rho_tightened"],
        "retrieval_confidence",
        turn.retrieval_confidence,
    )
    # tightened relaxes strictly harder toward the calm target
    assert tight.retrieval_confidence > free.retrieval_confidence
    assert tight.memory_pressure < free.memory_pressure


def test_campaign2_criteria_differ_from_d1_only_on_5_1() -> None:
    """DM-C2 pin: PROPOSED_D2 is the registered D-1.0 set with exactly
    one change, the 5.1 subject family."""
    from validation.m10.thresholds import PROPOSED, PROPOSED_D2

    assert PROPOSED_D2["lyapunov_evolution"]["nominal_contraction_dominates"] == (
        "families.nominal_feedback.lyapunov_evolution.p_contraction",
        ">=",
        0.60,
    )
    for family, criteria in PROPOSED.items():
        for name, spec in criteria.items():
            if (family, name) == (
                "lyapunov_evolution",
                "nominal_contraction_dominates",
            ):
                continue
            assert PROPOSED_D2[family][name] == spec


def test_the_published_feedback_law_constants() -> None:
    """The law is part of D-2.0's published identity: its constants
    are pinned as literals (MATH-C mutation replay, survivor M4: a
    mechanism pin that reads FEEDBACK_LAW mutates in lockstep with
    it and cannot catch a drifted constant)."""
    from validation.m10.corpus import FEEDBACK_LAW

    assert FEEDBACK_LAW == {
        "targets": {"retrieval_confidence": 0.97, "memory_pressure": 0.02},
        "rho_free": 0.92,
        "rho_tightened": 0.85,
        "tightened_verdicts": ("REQUIRE_CONFIRMATION", "ABSTAIN"),
        "jitter_scale": 0.02,
    }


def test_published_artifacts_absorb_last_ulp_platform_noise() -> None:
    """Third-party reproduction (macOS arm64, FMA reductions) drifted
    one double by one ulp in a family sup_w_max against the Linux
    x86-64 reference, breaking byte-identity of a published artifact.
    Published floats are rounded to 12 decimals at serialization so
    both platforms write the same text; 12 decimals sits far above
    the 1e-16 relative ulp noise and far below any scientific
    meaning in these metrics."""
    from validation.m10.__main__ import _round_floats

    linux = 0.9532080249999999
    darwin = 0.953208025

    assert _round_floats(linux) == _round_floats(darwin)
    tree = {
        "x": [linux, 3, "keep"],
        "t": (darwin,),
        "flag": True,
        "none": None,
    }
    out = _round_floats(tree)
    assert out["x"][0] == round(darwin, 12)
    assert out["x"][1] == 3 and out["x"][2] == "keep"
    assert out["t"][0] == round(darwin, 12)
    assert out["flag"] is True and out["none"] is None
