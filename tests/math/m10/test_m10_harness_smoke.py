# tests/math/m10/test_m10_harness_smoke.py
"""Gate smoke of the M10 harness: deterministic, complete, faithful.

The full campaign runs out of band (python -m validation.m10 run);
the gate pins the instrument itself on the tiny smoke corpus: the
corpus is bit-for-bit reproducible from its seeds, every turn yields
a complete measurement, the closed-loop threading produces live
trajectory quantities, and the metrics are stable across reruns.
"""

from __future__ import annotations

from validation.m10.corpus import FAMILIES, build_smoke_corpus
from validation.m10.metrics import compute_all
from validation.m10.runner import run_corpus, run_trajectory


def test_corpus_is_bit_for_bit_reproducible() -> None:
    first = build_smoke_corpus()
    second = build_smoke_corpus()

    assert first.manifest() == second.manifest()
    assert first.trajectories == second.trajectories


def test_every_family_is_present_once() -> None:
    """Pinned as a literal: comparing against FAMILIES would mutate in
    lockstep with the corpus and can never catch a dropped family
    (MATH-B mutation replay, survivor M7)."""
    corpus = build_smoke_corpus()

    expected = (
        "nominal",
        "boundary",
        "adversarial",
        "switching_stress",
        "long_horizon",
        "conflicting",
        "declared_risk",
    )
    assert FAMILIES == expected
    assert tuple(t.family for t in corpus.trajectories) == expected


def test_measurements_are_complete_and_deterministic() -> None:
    corpus = build_smoke_corpus()
    spec = corpus.trajectories[0]

    first = run_trajectory(spec)
    second = run_trajectory(spec)

    assert [m.to_dict() for m in first] == [m.to_dict() for m in second]
    assert len(first) == len(spec.turns)
    for m in first:
        assert m.final_verdict in {"ALLOW", "REQUIRE_CONFIRMATION", "ABSTAIN"}
        assert m.energy_v is not None
        assert m.projection_certification is not None


def test_threading_produces_live_trajectory_quantities() -> None:
    """From the second turn on, the composite delta the gate consumes
    must move (the harness threads fast, slow and switching state; a
    frozen 0.0 delta would mean the closed loop is not closed)."""
    corpus = build_smoke_corpus()
    nominal = next(t for t in corpus.trajectories if t.family == "nominal")

    ms = run_trajectory(nominal)
    deltas = [m.delta_w for m in ms[1:] if m.delta_w is not None]

    assert any(abs(d) > 1e-9 for d in deltas), deltas
    # and the switching clock accumulates across turns
    taus = [m.switching_metrics.get("tau_d") for m in ms if m.switching_metrics]
    assert taus and max(t for t in taus if t is not None) >= 4.0


def test_the_adaptive_layer_is_live_on_threaded_turns() -> None:
    """DM-B0 (RED-first): with the observer reading the estimator's
    smoothed factor, threaded turns (fast state, switching runtime
    and adaptive observer carried across turns) must yield available
    adaptive snapshots; the layer's availability on live paths is
    exactly what the bug suppressed."""
    corpus = build_smoke_corpus()
    nominal = next(t for t in corpus.trajectories if t.family == "nominal")

    ms = run_trajectory(nominal)

    assert any(m.adaptive_available for m in ms[1:]), [
        (m.turn_index, m.adaptive_available) for m in ms
    ]


def test_metrics_cover_the_nine_families_of_m10() -> None:
    corpus = build_smoke_corpus()
    observed = compute_all(run_corpus(corpus))

    assert set(observed) == {
        "lyapunov_evolution",
        "iss_residual",
        "adaptive_estimation",
        "kappa_violations",
        "gate_distribution",
        "projection_overrides",
        "closed_loop_feedback",
        "perturbation_decomposition",
        "envelope_compliance",
    }
    assert observed["lyapunov_evolution"]["samples"] > 0
    assert observed["gate_distribution"]["by_family"].keys() == set(FAMILIES)


def test_verdict_shares_are_always_fully_encoded() -> None:
    """Disclosed instrument correction of campaign run 1: a zero
    verdict share is an explicit 0.0, never a missing key, so the
    fail-closed judge can resolve zero-observation criteria."""
    corpus = build_smoke_corpus()
    observed = compute_all(run_corpus(corpus))

    dist = observed["gate_distribution"]
    subs = [dist["overall"], dist["given_expansion"], dist["given_contraction"]]
    subs.extend(dist["by_family"].values())
    for sub in subs:
        assert {"ALLOW", "REQUIRE_CONFIRMATION", "ABSTAIN"} <= set(sub)


def test_the_monotone_invariant_holds_on_the_smoke_corpus() -> None:
    """M10 5.4's hard invariant, checked directly on measurements: no
    transition ever relaxes an ABSTAIN past REQUIRE_CONFIRMATION."""
    corpus = build_smoke_corpus()
    order = {"ALLOW": 0, "REQUIRE_CONFIRMATION": 1, "ABSTAIN": 2}

    for m in run_corpus(corpus):
        for t in m.verdict_transitions:
            before = order.get(str(t.get("before")))
            after = order.get(str(t.get("after")))
            if before == 2:
                assert after is not None and after >= 1, t
