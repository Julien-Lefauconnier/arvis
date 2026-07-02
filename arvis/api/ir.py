# arvis/api/ir.py

from __future__ import annotations

import copy
from typing import Any

from arvis.api.ir_canonical import hash_ir

IR_VERSION = "arvis-ir.v1"
IR_FINGERPRINT = "stable"


def build_ir_view(obj: Any) -> dict[str, Any]:
    if obj is None:
        raise ValueError("IR source is None")

    result = getattr(obj, "last_result", obj)
    if result is None:
        raise ValueError("IR result is None")

    ir_result = getattr(result, "ir", result)
    """
    Canonical IR view (stable public contract).

    This is the future-proof API surface. The projection / validity /
    stability / adaptive / tools axes are part of the stable shape even when a
    given turn does not populate them (they serialize to null): keeping them
    present lets consumers rely on a fixed schema and see the governance axes
    ARVIS reasons over.
    """

    ir = {
        "version": IR_VERSION,
        "fingerprint": IR_FINGERPRINT,
        "input": _serialize_ir(getattr(ir_result, "ir_input", None)),
        "context": _serialize_ir(getattr(ir_result, "ir_context", None)),
        "decision": _serialize_ir(getattr(ir_result, "ir_decision", None)),
        "state": _serialize_ir(getattr(ir_result, "ir_state", None)),
        "projection": _serialize_ir(getattr(ir_result, "ir_projection", None)),
        "validity": _serialize_ir(getattr(ir_result, "ir_validity", None)),
        "stability": _serialize_ir(getattr(ir_result, "ir_stability", None)),
        "adaptive": _serialize_ir(getattr(ir_result, "ir_adaptive", None)),
        "tools": _serialize_ir(getattr(ir_result, "ir_tools", None)),
        "gate": _serialize_ir(getattr(ir_result, "ir_gate", None)),
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
