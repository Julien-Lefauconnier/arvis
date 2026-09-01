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
