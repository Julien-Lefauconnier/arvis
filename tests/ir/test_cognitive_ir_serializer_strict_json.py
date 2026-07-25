"""Canonical IR serialization emits strict JSON only."""

import pytest

from arvis.ir.serialization.cognitive_ir_serializer import CognitiveIRSerializer


def test_canonical_ir_rejects_non_finite_float() -> None:
    with pytest.raises(ValueError, match="JSON compliant"):
        CognitiveIRSerializer.to_json({"risk": float("nan")})
