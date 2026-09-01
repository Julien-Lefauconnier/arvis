# examples/07_session_threading.py
"""Session threading: how a host carries a trajectory across turns.

Every other example runs a single governed turn. That is the honest
default, and it is also why they all end in REQUIRES_CONFIRMATION: a
turn with no history has no measured trajectory, so the monitor sits
in its warmup regime and the gate has nothing to certify.

This example shows the documented host contract instead: feed the
opaque state blob back on the next call, and the monitor accumulates
a trajectory. Note that each turn builds a FRESH engine, as the
lifecycle requires: continuity comes from the threaded state, never
from reusing an engine object. Run it and watch the regime leave
warmup.

    python examples/07_session_threading.py

What it does NOT claim: that threading alone yields ALLOW. See
docs/PATH_TO_ALLOW.md for the full set of conditions, and for the
ones a v0 host cannot reach yet.
"""

from arvis import ArvisEngine


def main() -> None:
    # One engine per turn: that is the documented lifecycle (see
    # 09_multi_engine_hosting.py). Continuity does NOT come from
    # reusing an engine object, it comes from the state blob below.
    state = None
    print("=== Session threading ===")
    print()
    print(f"{'turn':>4}  {'regime':<12}  {'status':<24}  threaded")
    print("-" * 60)

    for turn in range(12):
        extra = {"scientific_state": state} if state is not None else None
        view = ArvisEngine().ask(
            f"What should I know about topic {turn}?",
            user_id="session-demo",
            extra=extra,
        )

        payload = view.to_dict()
        regime = payload["stability"]["regime"]
        status = payload["decision"]["status"]

        print(
            f"{turn:>4}  {regime:<12}  {status:<24}  "
            f"{'yes' if state is not None else 'no (first turn)'}"
        )

        # The contract: carry the opaque blob to the next turn.
        state = view.next_scientific_state

    print()
    print("The regime leaves warmup once the monitor has enough samples.")
    print("Without threading it would stay in warmup forever, however")
    print("many calls the host makes.")


if __name__ == "__main__":
    main()
