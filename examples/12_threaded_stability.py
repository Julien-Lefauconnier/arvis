# examples/12_threaded_stability.py
"""Threaded scientific state: the trajectory across governed turns.

The engine is one-turn by design: parallelism and cross-turn memory
belong to the host. The contraction monitor (the default core model)
therefore measures each turn, and hands the host a compact, replayable
``scientific_state`` to thread into the next turn. From the second
threaded turn on, the trajectory quantities become live: delta-V
(contraction signal), the drift score, the PAC risk ceiling tightening
over the window, and the empirical regime leaving ``warmup``.

The wire contract (campaign MATH-A, M2):

- pass the previous state:  ``run(..., extra={"scientific_state": s})``
- read the next state back: ``extra["scientific_state_next"]``

The state is a plain JSON-safe dict; the host stores and threads it as
an opaque blob (per user, per session, wherever its own model of
continuity lives) and never needs to import its type.
"""

from arvis import CognitiveOS


def governed_turn(payload: dict, state: dict | None) -> tuple[str, dict | None]:
    """One engine per governed turn (the documented lifecycle), with
    the scientific state threaded through the extra channel."""
    extra: dict = {}
    if state is not None:
        extra["scientific_state"] = state
    result = CognitiveOS().run(user_id="ops", cognitive_input=payload, extra=extra)
    view = result.stability_view
    line = (
        f"regime={view.regime:<8} "
        f"stability={view.stability_score:.2f} "
        f"risk_rate={view.risk_level:.2f}"
        if view is not None
        else "no stability assessment"
    )
    return line, extra.get("scientific_state_next")


def main() -> None:
    print("=== Threaded stability across governed turns ===\n")
    state: dict | None = None
    turns = [
        {"query": "summarize the quarterly report"},
        {"query": "list the accounts mentioned in it"},
        {"query": "draft the follow-up note"},
        {"query": "schedule the review meeting"},
    ]
    for index, payload in enumerate(turns):
        line, state = governed_turn(payload, state)
        threaded = "threaded" if index else "first turn (unthreaded)"
        print(f"turn {index}  [{threaded:<22}] {line}")
        assert state is not None, "a measured run must emit its next state"
        assert state["turn_index"] == index

    print("\nThe host owns this thread: store the state per conversation,")
    print("pass it to the next governed turn, and the delta-V trajectory")
    print("branch of the gate is live; drop it and every turn is a")
    print("conservative first turn again.")


if __name__ == "__main__":
    main()
