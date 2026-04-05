# arvis/api/ir.py

from __future__ import annotations

from typing import Any, Dict
from arvis.api.ir_canonical import hash_ir

IR_VERSION = "arvis-ir.v1"
IR_FINGERPRINT = "stable"

def build_ir_view(result: Any) -> Dict[str, Any]:
    if result is None:
        raise ValueError("Pipeline returned None result (invalid state)")
    """
    Canonical IR view (stable public contract).

    This is the future-proof API surface.
    """

    ir = {
        "version": IR_VERSION,
        "fingerprint": IR_FINGERPRINT,
        "input": _serialize_ir(result.ir_input),
        "context": _serialize_ir(result.ir_context),
        "decision": _serialize_ir(result.ir_decision),
        "state": _serialize_ir(result.ir_state),
        "gate": _serialize_ir(result.ir_gate),

        # extension zone 
        "meta": {},
    }

    ir["meta"]["canonical_hash"] = hash_ir(ir)

    return ir


def _serialize_ir(obj: Any) -> Any:
    """
    Strict IR serialization (fully JSON-safe).
    """

    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, dict):
        return {k: _serialize_ir(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [_serialize_ir(v) for v in obj]

    # dataclass / object
    if hasattr(obj, "__dict__"):
        return {
            k: _serialize_ir(v)
            for k, v in obj.__dict__.items()
            if not k.startswith("_")
        }

    # fallback safe
    return str(obj)