# arvis/api/ir.py

from __future__ import annotations

import copy
from typing import Any, Dict
from arvis.api.ir_canonical import hash_ir

IR_VERSION = "arvis-ir.v1"
IR_FINGERPRINT = "stable"


def build_ir_view(obj: Any) -> Dict[str, Any]:
    if obj is None:
        raise ValueError("IR source is None")

    result = getattr(obj, "last_result", obj)
    if result is None:
        raise ValueError("IR result is None")
    """
    Canonical IR view (stable public contract).

    This is the future-proof API surface.
    """

    ir = {
        "version": IR_VERSION,
        "fingerprint": IR_FINGERPRINT,
        "input": _serialize_ir(getattr(result, "ir_input", None)),
        "context": _serialize_ir(getattr(result, "ir_context", None)),
        "decision": _serialize_ir(getattr(result, "ir_decision", None)),
        "state": _serialize_ir(getattr(result, "ir_state", None)),
        "gate": _serialize_ir(getattr(result, "ir_gate", None)),
        # extension zone
        "meta": {},
    }

    # -----------------------------------------
    # Compute hash on IR WITHOUT canonical_hash
    # -----------------------------------------
    ir_for_hash = copy.deepcopy(ir)
    ir_for_hash["meta"].pop("canonical_hash", None)

    ir["meta"]["canonical_hash"] = hash_ir(ir_for_hash)

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
