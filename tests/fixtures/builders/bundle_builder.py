# tests/fixtures/builders/bundle_builder.py

from __future__ import annotations

from arvis.cognition.bundle.cognitive_bundle_builder import (
    CognitiveBundleBuilder,
)
from arvis.cognition.decision.decision_result import (
    DecisionResult,
)
from arvis.cognition.explanation.explanation_snapshot import (
    ExplanationSnapshot,
)
from arvis.cognition.introspection.introspection_snapshot import (
    IntrospectionSnapshot,
)


def build_test_bundle(
    *,
    memory_pressure: float = 0.0,
    has_constraints: bool = False,
):
    return CognitiveBundleBuilder.build(
        decision_result=DecisionResult.empty(),
        introspection=IntrospectionSnapshot(),
        explanation=ExplanationSnapshot(),
        timeline=[],
        memory={
            "memory_pressure": memory_pressure,
            "has_constraints": has_constraints,
            "preferences": {},
        },
    )
