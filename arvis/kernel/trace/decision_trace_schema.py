# arvis/kernel/trace/decision_trace_schema.py

from typing import Any

TRACE_VERSION = "1.0"


def serialize_trace(trace: Any) -> dict[str, Any]:
    return {
        "version": TRACE_VERSION,
        "timestamp": trace.timestamp.isoformat(),
        "user_id": trace.user_id,
        "gate_result": str(trace.gate_result),
        "action_allowed": trace.action_decision.allowed
        if trace.action_decision
        else None,
        "has_intent": trace.executable_intent is not None,
    }
