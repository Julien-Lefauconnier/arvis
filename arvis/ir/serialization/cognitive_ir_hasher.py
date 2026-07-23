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
    def hash_canonical_text(canonical_text: str) -> str:
        """Hash an already produced canonical serialization.

        The witness dict, the hash and the envelope must all derive from
        the same canonical bytes (audit a13, P1-04): the producer
        serializes once and derives every artifact from that text, so a
        mutation of the live IR between steps can no longer desynchronize
        them. This is the single place the hash formula lives.
        """
        return hashlib.sha256(canonical_text.encode("utf-8")).hexdigest()

    @staticmethod
    def hash(ir: object) -> str:
        """
        Compute SHA-256 hash of canonical IR.
        """

        serialized = CognitiveIRSerializer.serialize(ir)

        return CognitiveIRHasher.hash_canonical_text(serialized)
