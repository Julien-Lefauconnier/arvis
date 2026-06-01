# tests/kernel/test_engine_actionable_blocked.py
"""
Non-regression: an ACTIONABLE turn must keep the full execution-safety stack.

The answer regime must not leak into actionable turns. An action request on a
degenerate cognitive state must still NOT be freely allowed: this proves the
action/answer boundary holds on the action side as well.
"""

from __future__ import annotations

from typing import Any

from arvis import ArvisEngine, CognitiveOSConfig

try:  # contract module path may vary across versions
    from arvis.adapters.llm.contracts.response import LLMResponse
except Exception:  # pragma: no cover
    from arvis.adapters.llm.contracts.request import LLMResponse


class _StubLLM:
    def generate(self, request: Any) -> LLMResponse:
        return LLMResponse(content="stub answer")


def test_actionable_turn_is_not_allowed_on_degenerate_state() -> None:
    engine = ArvisEngine(config=CognitiveOSConfig(adapter_registry={"llm": _StubLLM()}))

    result = engine.run(
        user_id="demo",
        cognitive_input={
            "query": "transfer 1000 euros to account 12345 now",
            "surface_kind": "linguistic",
            "intent_type": "action",
        },
    )

    ir = result.to_ir()
    decision = ir["decision"]
    gate = ir["gate"]
    gate_reasons = gate.get("reason_codes") or []

    print("\n[DIAG] decision_kind :", decision.get("decision_kind"))
    print("[DIAG] reason_codes  :", decision.get("reason_codes"))
    print("[DIAG] gate verdict  :", gate.get("verdict"))
    print("[DIAG] gate reasons  :", gate_reasons)

    # Action regime kept the execution-safety stack: not freely allowed.
    assert gate.get("verdict") != "allow", gate_reasons
