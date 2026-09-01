# tests/api/test_public_state_threading.py
"""DM-F3 (campaign FIX): the documented host threading contract is
reachable from the public surface.

``core_stage`` documents an opaque cross-turn contract: the host
injects ``scientific_state`` and reads ``scientific_state_next``
back. The write existed, but no public result surface exposed it, so
a host could only reach it by passing a mutable ``extra`` dict and
reading the mutation back, an undocumented side effect. Without the
threading the regime estimator never accumulates samples and stays
in ``warmup`` forever, whatever the number of calls.

The blob stays opaque: the view exposes it, the serialized contract
does not carry it.
"""

from __future__ import annotations

from arvis import ArvisEngine


def test_the_view_exposes_the_next_scientific_state() -> None:
    engine = ArvisEngine()

    view = engine.ask("hello", user_id="threading")

    assert view.next_scientific_state is not None


def test_threading_the_state_advances_the_regime() -> None:
    """The contract's purpose: fed back turn after turn, the monitor
    leaves warmup instead of restarting from zero every call."""
    engine = ArvisEngine()
    state = None
    regimes = []

    for index in range(12):
        extra = {"scientific_state": state} if state is not None else None
        view = engine.ask(f"fact {index}", user_id="threading", extra=extra)
        state = view.next_scientific_state
        regimes.append(view.to_dict()["stability"]["regime"])

    assert regimes[0] == "warmup"
    assert regimes[-1] != "warmup", regimes


def test_the_opaque_blob_stays_out_of_the_serialized_contract() -> None:
    engine = ArvisEngine()

    payload = engine.ask("hello", user_id="threading").to_dict()

    assert "next_scientific_state" not in payload
    assert "scientific_state" not in payload
