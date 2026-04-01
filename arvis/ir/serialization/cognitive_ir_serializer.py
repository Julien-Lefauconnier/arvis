# arvis/ir/serialization/cognitive_ir_serializer.py

from __future__ import annotations

import json
from dataclasses import is_dataclass, asdict
from typing import Any, Dict


class CognitiveIRSerializer:
    """
    Canonical serializer for CognitiveIR.

    Guarantees:
    - deterministic ordering
    - canonical dict representation
    - stable hashing input
    """

    # -----------------------------------------
    # INTERNAL: object → dict
    # -----------------------------------------
    @staticmethod
    def to_dict(obj: Any) -> Any:
        if obj is None:
            return None

        if isinstance(obj, (str, int, bool)):
            return obj

        if isinstance(obj, float):
            return round(obj, 12)

        if isinstance(obj, (list, tuple)):
            return [CognitiveIRSerializer.to_dict(x) for x in obj]

        if isinstance(obj, dict):
            return {
                str(k): CognitiveIRSerializer.to_dict(v)
                for k, v in obj.items()
            }

        if is_dataclass(obj) and not isinstance(obj, type):
            return CognitiveIRSerializer.to_dict(asdict(obj))

        return str(obj)

    # -----------------------------------------
    # INTERNAL: canonical ordering
    # -----------------------------------------
    @staticmethod
    def canonicalize(data: Any) -> Any:
        if isinstance(data, dict):
            return {
                k: CognitiveIRSerializer.canonicalize(data[k])
                for k in sorted(data.keys())
            }

        if isinstance(data, list):
            return [CognitiveIRSerializer.canonicalize(x) for x in data]

        return data

    # -----------------------------------------
    # PUBLIC: canonical dict (IMPORTANT)
    # -----------------------------------------
    @classmethod
    def to_canonical_dict(cls, ir: Any) -> Dict[str, Any]:
        raw = cls.to_dict(ir)
        canonical = cls.canonicalize(raw)

        if not isinstance(canonical, dict):
            raise TypeError("Canonical IR must be a dict")

        return canonical

    # -----------------------------------------
    # PUBLIC: JSON serialization (OPTIONAL)
    # -----------------------------------------
    @classmethod
    def to_json(cls, ir: Any) -> str:
        canonical = cls.to_canonical_dict(ir)

        return json.dumps(
            canonical,
            separators=(",", ":"),
            ensure_ascii=False,
        )
    

    @classmethod
    def serialize(cls, ir: Any) -> str:
        """
        Backward-compatible canonical JSON serialization.
        """
        return cls.to_json(ir)