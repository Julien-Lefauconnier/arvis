# arvis/ir/envelope.py

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from arvis.ir.cognitive_ir import CognitiveIR


@dataclass(frozen=True)
class CognitiveIREnvelope:
    """
    Canonical export envelope for CognitiveIR.

    This is the transport / audit / replay artifact.
    The enclosed IR remains the canonical cognitive representation.
    """

    ir: CognitiveIR
    serialized: dict[str, Any]
    hash: str
    created_at: datetime
    version: str = "arvis.ir.envelope.v1"

    @classmethod
    def build(
        cls,
        ir: CognitiveIR,
        serialized: dict[str, Any],
        hash_value: str,
        *,
        created_at: datetime | None = None,
        version: str = "arvis.ir.envelope.v1",
    ) -> CognitiveIREnvelope:
        return cls(
            ir=ir,
            serialized=serialized,
            hash=hash_value,
            created_at=created_at or datetime.now(UTC),
            version=version,
        )
