# tests/adapters/ir/test_decision_kind_search.py
"""A read-only ``search`` turn (querying the user's own corpus to answer) is
answer-only: it proposes no executable action. It must therefore classify as
the ``informational`` decision kind, so the kernel routes it to the ANSWER
gating regime (which allows) rather than the ACTION regime (whose execution
gate blocks a turn that has nothing to execute).
"""

from __future__ import annotations

from arvis.adapters.ir.decision_adapter import DecisionIRAdapter


def test_search_reason_maps_to_informational_kind() -> None:
    assert DecisionIRAdapter._kind(("search",), "none") == "informational"


def test_informational_query_still_maps_to_informational() -> None:
    assert DecisionIRAdapter._kind(("informational_query",), "none") == "informational"


def test_action_request_still_maps_to_action() -> None:
    assert DecisionIRAdapter._kind(("action_request",), "none") == "action"


def test_search_user_files_still_maps_to_action() -> None:
    assert DecisionIRAdapter._kind(("search_user_files",), "none") == "action"
