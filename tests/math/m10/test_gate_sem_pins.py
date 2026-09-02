# tests/math/m10/test_gate_sem_pins.py
"""Campaign GATE-SEM pins: no ALLOW without a live, consulted guard.

The campaign closed the audit's P0-1 and P0-2 (2026-09-02): ALLOW was
issued on the least-guarded turn of a trajectory (empty dwell clock,
adaptive layer silently dead, switching condition violated by six
orders of magnitude), and the gate kernel's acceptance shortcut
pre-empted the worst-axis and mean-energy refusals on every live
contracting turn. Measured on the full corpora: 8 of 13 D-1.0 and 13
of 15 D-2.0 final ALLOW sat on the adaptive hole; after the campaign,
every surviving ALLOW carries a live adaptive layer, a strictly
positive dwell and a negative measured margin, and the full-corpus
verdict movement is monotone (no relaxation anywhere, ABSTAIN
bit-preserved).

These pins run the closed-loop smoke corpora in-process at gate time;
the full corpora are re-judged out of band (python -m validation.m10
run / run2) and their artifacts are tracked.
"""

from __future__ import annotations

from validation.m10.corpus import build_smoke_corpus, build_smoke_corpus_d2
from validation.m10.runner import run_trajectory


def _all_measurements(corpus):  # type: ignore[no-untyped-def]
    for spec in corpus.trajectories:
        yield from run_trajectory(spec)


def _assert_no_unguarded_allow(corpus) -> None:  # type: ignore[no-untyped-def]
    for m in _all_measurements(corpus):
        if m.final_verdict != "ALLOW":
            continue
        switching = dict(m.switching_metrics or {})
        assert m.adaptive_available, (
            f"{m.trajectory_id}#{m.turn_index}: ALLOW with the adaptive "
            "layer unavailable"
        )
        tau_d = switching.get("tau_d")
        assert tau_d is not None and float(tau_d) > 0.0, (
            f"{m.trajectory_id}#{m.turn_index}: ALLOW on an empty dwell "
            f"clock (tau_d={tau_d!r})"
        )
        assert m.kappa_margin is not None and float(m.kappa_margin) < 0.0, (
            f"{m.trajectory_id}#{m.turn_index}: ALLOW without a negative "
            f"measured adaptive margin (margin={m.kappa_margin!r})"
        )


def test_no_unguarded_allow_on_the_smoke_corpus() -> None:
    """RED on the pre-campaign tree: the first threaded turn of the
    nominal smoke trajectory reached ALLOW with metrics=None."""
    _assert_no_unguarded_allow(build_smoke_corpus())


def test_no_unguarded_allow_on_the_d2_smoke_corpus() -> None:
    _assert_no_unguarded_allow(build_smoke_corpus_d2())


def test_adaptive_availability_never_dies_mid_trajectory() -> None:
    """The DM-G1 mechanism observed end to end: once the adaptive
    layer comes alive on a trajectory it stays alive, because the
    margin no longer dies on dwell resets (the ValueError on
    ``tau_d <= 0`` swallowed into ``metrics = None``). On the
    pre-campaign tree the layer was dead on the first threaded turn of
    every trajectory, exactly where the corpus ALLOWs leaked."""
    corpus = build_smoke_corpus()
    for spec in corpus.trajectories:
        seen_alive = False
        first_alive_turn: int | None = None
        for m in run_trajectory(spec):
            if m.adaptive_available:
                if not seen_alive:
                    first_alive_turn = m.turn_index
                seen_alive = True
            else:
                assert not seen_alive, (
                    f"{m.trajectory_id}#{m.turn_index}: adaptive layer "
                    "died mid-trajectory (a dwell reset must veto, not "
                    "silence the layer)"
                )
        if seen_alive:
            assert first_alive_turn is not None and first_alive_turn <= 1, (
                f"{spec.trajectory_id}: adaptive layer only came alive "
                f"at turn {first_alive_turn}; the first threaded turn "
                "must already be guarded"
            )
