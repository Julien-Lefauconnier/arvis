# compliance/internal_invariants/core/test_threaded_state_contract.py
"""Normative contract of the threaded scientific state (MATH-A, M2).

The channel names, the state shape and the degradation behavior are
API: hosts thread the state as an opaque blob, so any drift here breaks
them silently. This suite pins:

- the exact channel keys (``scientific_state`` in, ``scientific_state_next``
  out);
- JSON round-trippability of the state (the host may persist it);
- trajectory advancement (turn index, risk window growth) and its
  determinism (same inputs + same thread => same states and same
  commitments);
- safe degradation: a dropped or malformed state behaves as a first
  turn, and never relaxes a verdict.
"""

from __future__ import annotations

import json
from typing import Any

from arvis import CognitiveOS

_PAYLOAD = {"query": "governed turn"}


def _turn(state: dict[str, Any] | None, payload: dict[str, Any]) -> tuple[Any, Any]:
    extra: dict[str, Any] = {}
    if state is not None:
        extra["scientific_state"] = state
    view = CognitiveOS().run(user_id="c", cognitive_input=payload, extra=extra)
    return view, extra.get("scientific_state_next")


def test_channel_keys_are_the_contract() -> None:
    extra: dict[str, Any] = {}
    CognitiveOS().run(user_id="c", cognitive_input=_PAYLOAD, extra=extra)
    assert "scientific_state_next" in extra, (
        "the output channel key is normative: hosts read exactly this"
    )


def test_state_round_trips_as_json() -> None:
    _, state = _turn(None, _PAYLOAD)
    rehydrated = json.loads(json.dumps(state))
    _, state2 = _turn(rehydrated, _PAYLOAD)
    assert state2["turn_index"] == 1


def test_threaded_trajectory_is_deterministic() -> None:
    def thread(n: int) -> list[dict[str, Any]]:
        states: list[dict[str, Any]] = []
        state: dict[str, Any] | None = None
        for _ in range(n):
            _, state = _turn(state, _PAYLOAD)
            assert state is not None
            states.append(state)
        return states

    assert thread(3) == thread(3), (
        "the same inputs threaded the same way must produce the same "
        "trajectory; hosts replay on this"
    )


def test_trajectory_advances_with_the_thread() -> None:
    state: dict[str, Any] | None = None
    for expected_turn in range(3):
        _, state = _turn(state, _PAYLOAD)
        assert state is not None
        assert state["turn_index"] == expected_turn
    assert len(state["risk_window"]) == 3


def test_dropped_thread_degrades_to_a_first_turn() -> None:
    _, state = _turn(None, _PAYLOAD)
    view_threaded, _ = _turn(state, _PAYLOAD)
    view_dropped, next_state = _turn(None, _PAYLOAD)
    assert next_state is not None and next_state["turn_index"] == 0
    assert view_dropped.status is view_threaded.status, (
        "losing the thread must not change the verdict on this nominal "
        "payload; it only resets the trajectory"
    )


def test_malformed_state_never_relaxes() -> None:
    baseline, _ = _turn(None, {"risk": 0.92})
    extra: dict[str, Any] = {"scientific_state": {"turn_index": "not-an-int"}}
    try:
        view = CognitiveOS().run(
            user_id="c", cognitive_input={"risk": 0.92}, extra=extra
        )
    except Exception:
        return  # refusing a malformed state outright is acceptable
    assert view.status is baseline.status, (
        "a malformed thread may reset or refuse, never relax the verdict"
    )
