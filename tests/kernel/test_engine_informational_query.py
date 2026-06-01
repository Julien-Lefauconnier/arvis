# tests/kernel/test_engine_informational_query.py
"""
Integration: a conversational query (intent_type="question") must be
classified as informational AND must reach ALLOW.

Rationale: the projection certificate guards safe *execution*; a non-actionable
informational turn proposes nothing to execute, so projection enforcement does
not apply and must neither block nor downgrade the answer.

Deterministic invariants:
- decision reason_codes == ["informational_query"]
- gate verdict == "allow"  (no projection hard block, no soft downgrade)

The injected stub LLM lets the ALLOW path exercise generation without network.
"""

from __future__ import annotations

from typing import Any

from arvis import ArvisEngine, CognitiveOSConfig

try:  # contract module path may vary across versions
    from arvis.adapters.llm.contracts.response import LLMResponse
except Exception:  # pragma: no cover
    from arvis.adapters.llm.contracts.request import LLMResponse


class _StubLLM:
    """Minimal injected LLM adapter: deterministic, offline."""

    def generate(self, request: Any) -> LLMResponse:
        return LLMResponse(content="stub answer")


def test_informational_query_reaches_allow() -> None:
    engine = ArvisEngine(config=CognitiveOSConfig(adapter_registry={"llm": _StubLLM()}))

    result = engine.run(
        user_id="demo",
        cognitive_input={
            "query": "who are you?",
            "surface_kind": "linguistic",
            "intent_type": "question",
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

    assert decision.get("reason_codes") == ["informational_query"]
    assert "projection_invalid" not in gate_reasons
    assert gate.get("verdict") == "allow", gate_reasons
