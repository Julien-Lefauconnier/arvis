# tests/adapters/llm/test_evaluation_payload.py
"""LLMEvaluation payload: sparse-by-construction export.

Campaign RELEASE (LOT R2). The evaluation dict carries ONLY the axes
that were measured: absent axes are omitted (not emitted as zeros or
nulls), matching the reported-only-when-measured doctrine of the
stability surfaces.
"""

from __future__ import annotations

from arvis.adapters.llm.observability.evaluation import LLMEvaluation


def test_full_evaluation_exports_every_axis_as_float() -> None:
    payload = LLMEvaluation(
        confidence=0.9, uncertainty=0.2, risk=0.1, variance=0.05
    ).to_dict()

    assert payload == {
        "confidence": 0.9,
        "uncertainty": 0.2,
        "risk": 0.1,
        "variance": 0.05,
    }
    assert all(isinstance(v, float) for v in payload.values())


def test_partial_evaluation_omits_the_unmeasured_axes() -> None:
    payload = LLMEvaluation(confidence=0.7).to_dict()

    assert payload == {"confidence": 0.7}
    assert "risk" not in payload and "uncertainty" not in payload


def test_empty_evaluation_exports_an_empty_dict() -> None:
    assert LLMEvaluation().to_dict() == {}
