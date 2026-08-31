# arvis/reflexive/introspection/arvis_introspection_service.py

from typing import Any

from arvis.reflexive.introspection.architecture_introspector import (
    ArchitectureIntrospector,
)
from arvis.reflexive.introspection.capability_introspector import CapabilityIntrospector
from arvis.reflexive.introspection.cognition_introspector import CognitionIntrospector
from arvis.reflexive.introspection.counterfactual_introspector import (
    CounterfactualIntrospector,
)
from arvis.reflexive.introspection.decision_introspector import DecisionIntrospector
from arvis.reflexive.introspection.math_introspector import MathIntrospector
from arvis.reflexive.introspection.runtime_introspector import RuntimeIntrospector
from arvis.reflexive.introspection.uncertainty_introspector import (
    UncertaintyIntrospector,
)


class ArvisIntrospectionService:
    def build_system_overview(self) -> dict[str, Any]:
        architecture = ArchitectureIntrospector().describe()
        capabilities = CapabilityIntrospector().describe()
        runtime = RuntimeIntrospector().snapshot()
        cognition = CognitionIntrospector().describe()
        math = MathIntrospector().describe()
        counterfactual = CounterfactualIntrospector().describe()
        decision = DecisionIntrospector().describe()
        uncertainty = UncertaintyIntrospector().describe()
        return {
            # The overview aggregates hand-maintained declarations
            # (each introspector says what it is); it is sealed by the
            # attestation for integrity, not derived from the code.
            "provenance": "static_declaration",
            "identity": {
                "name": "ARVIS",
                "type": "Adaptive Resilient Vigilant Intelligence System",
                "scope": "self-descriptive cognitive system",
            },
            "architecture": architecture,
            "capabilities": capabilities,
            "cognition": cognition,
            "runtime": runtime,
            "math": math,
            "counterfactual": counterfactual,
            "decision": decision,
            "uncertainty": uncertainty,
        }
