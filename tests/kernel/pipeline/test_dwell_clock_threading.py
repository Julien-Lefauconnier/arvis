# tests/kernel/pipeline/test_dwell_clock_threading.py
"""Campaign PROJ, RED-first: the dwell clock crosses the public
contract.

The switching condition is ln(J) / tau_d < kappa_eff, and tau_d is
how long the system has stayed in one regime. The dwell clock lived
on a live SwitchingRuntime rebuilt fresh by the preparation service
on every pipeline construction, and the opaque scientific state blob
did not carry it, so a host driving ARVIS through ArvisEngine (one
engine per turn, the documented lifecycle) could never accumulate
dwell time: tau_d restarted at zero on every call and
switching_unsafe_monitoring never went away, however long the
session. PATH_TO_ALLOW documented this as the honest v0 limit.

The blob now carries a "switching" section (the runtime's three
fields), written at finalize after the turn's regime update and
restored by the preparation service on the next turn. The monitor's
own from_dict ignores unknown keys, so blobs produced before this
change load exactly as before (a fresh clock), and a malformed
section degrades to a fresh clock rather than failing the turn.

En route, the clock itself: BOTH regime_stage (before the gate) and
runtime_stage (after it) called switching_runtime.update() on the
same object, so the clock ticked twice per turn and tau_d was
inflated by a factor of two at the moment the guard read it, which
made ln(J)/tau_d half its true value: the switching guard was
declared safe with half the real dwell. One turn now ticks the clock
once, in runtime_stage, after the decision, so the guard reads the
dwell of COMPLETED turns (the conservative end).
"""

from __future__ import annotations

from arvis.api.engine import ArvisEngine
from arvis.math.switching.switching_runtime import SwitchingRuntime


def _turn(state: object) -> tuple[object, dict]:
    bag: dict = {}
    if state is not None:
        bag["scientific_state"] = state
    view = ArvisEngine().ask(
        "Steady topic, same regime.",
        user_id="dwell-probe",
        extra=bag,
    )
    return view.next_scientific_state, bag


def test_the_switching_state_rides_the_opaque_blob() -> None:
    """The blob a host carries forward includes the dwell clock."""
    state, _ = _turn(None)

    assert isinstance(state, dict)
    assert "switching" in state
    section = state["switching"]
    assert set(section) == {"last_regime", "steps_since_switch", "total_switches"}


def test_tau_d_accumulates_across_engine_turns() -> None:
    """The public contract accumulates dwell: after enough threaded
    turns tau_d exceeds what any single fresh turn can produce, and
    the switching guard stops flagging cold monitoring."""
    state = None
    tau_seen = []
    last_bag: dict = {}

    for _ in range(14):
        state, last_bag = _turn(state)
        metrics = dict(last_bag.get("switching_metrics") or {})
        if "tau_d" in metrics:
            tau_seen.append(float(metrics["tau_d"]))

    assert tau_seen, "switching_metrics never exported tau_d"
    assert max(tau_seen) >= 5.0, tau_seen
    assert tau_seen[-1] > tau_seen[0], tau_seen
    assert "switching_unsafe_monitoring" not in list(
        last_bag.get("fusion_reasons") or []
    )


def test_a_blob_without_the_switching_section_still_loads() -> None:
    """Backward compatibility: a blob produced before this change
    (no switching key) starts a fresh clock, the historical
    behavior, and the turn completes normally."""
    state, _ = _turn(None)
    legacy = {k: v for k, v in state.items() if k != "switching"}

    next_state, bag = _turn(legacy)

    assert isinstance(next_state, dict)
    metrics = dict(bag.get("switching_metrics") or {})
    assert float(metrics.get("tau_d", 0.0)) <= 1.0


def test_a_malformed_switching_section_degrades_to_a_fresh_clock() -> None:
    """Fail-safe, not fail-turn: garbage in the section is ignored."""
    state, _ = _turn(None)
    poisoned = {**state, "switching": "garbage"}

    next_state, _ = _turn(poisoned)

    assert isinstance(next_state, dict)
    assert isinstance(next_state.get("switching"), dict)


def test_the_runtime_state_round_trips() -> None:
    runtime = SwitchingRuntime()
    for regime in ("stable", "stable", "stable", "critical", "critical"):
        runtime.update(regime)

    restored = SwitchingRuntime.from_state(runtime.to_state())

    assert restored is not None
    assert restored.last_regime == runtime.last_regime
    assert restored.steps_since_switch == runtime.steps_since_switch
    assert restored.total_switches == runtime.total_switches


def test_from_state_refuses_garbage() -> None:
    assert SwitchingRuntime.from_state(None) is None
    assert SwitchingRuntime.from_state("nope") is None
    assert SwitchingRuntime.from_state({"steps_since_switch": "many"}) is None


def test_one_turn_ticks_the_clock_exactly_once() -> None:
    """The double-tick defect: regime_stage and runtime_stage both
    updated the same runtime, so tau_d counted two per turn and the
    guard read twice the real dwell. Two threaded turns in the same
    regime must leave at most two accumulated steps."""
    state, _ = _turn(None)
    state, _ = _turn(state)

    section = state["switching"]
    assert section["steps_since_switch"] <= 2, section
