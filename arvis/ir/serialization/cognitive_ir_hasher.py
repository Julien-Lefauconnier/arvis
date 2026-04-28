# arvis/ir/serialization/cognitive_ir_hasher.py

from __future__ import annotations

import hashlib

from arvis.ir.serialization.cognitive_ir_serializer import CognitiveIRSerializer


class CognitiveIRHasher:
    """
    Deterministic hasher for CognitiveIR.

    Guarantees:
    - stable hash across runs
    - compatible with replay validation
    """

    @staticmethod
    def hash(ir: object) -> str:
        """
        Compute SHA-256 hash of canonical IR.
        """

        serialized = CognitiveIRSerializer.serialize(ir)

        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()

        return digest
