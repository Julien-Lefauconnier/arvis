# arvis/adapters/llm/context/arvis_context_mapper.py

from __future__ import annotations

from typing import Any

from arvis.adapters.llm.contracts.context import ARVISContext


class ARVISContextMapper:
    @staticmethod
    def from_pipeline_ctx(ctx: Any) -> ARVISContext:
        state = getattr(ctx, "cognitive_state", None)

        if state is None:
            return ARVISContext(
                risk_score=0.0,
                uncertainty_score=0.0,
                stability_score=1.0,
                confidence_score=1.0,
                constraints=[],
                objectives=[],
            )

        regime = getattr(state, "regime", None)
        uncertainty = getattr(state, "uncertainty", None)
        risk = getattr(state, "risk", None)

        # -------------------------
        # Core signals
        # -------------------------
        uncertainty_level = getattr(uncertainty, "level", 0.0) if uncertainty else 0.0
        risk_level = getattr(risk, "level", 0.0) if risk else 0.0

        stability_score = 1.0 if regime == "stability" else 0.0
        confidence_score = max(0.0, 1.0 - uncertainty_level)

        # -------------------------
        # Constraints (safety shaping)
        # -------------------------
        constraints: list[str] = []

        if risk_level > 0.7:
            constraints.append("Avoid speculative or risky reasoning")
            constraints.append("Prefer conservative and safe outputs")

        if uncertainty_level > 0.7:
            constraints.append("Avoid hallucinations")
            constraints.append("Prefer abstention if unsure")

        if regime == "stability":
            constraints.append("Maintain consistent reasoning")
            constraints.append("Avoid unnecessary exploration")

        # -------------------------
        # Objectives (behavior shaping)
        # -------------------------
        objectives: list[str] = []

        if regime == "exploration":
            objectives.append("Explore alternative interpretations")
            objectives.append("Consider multiple hypotheses")

        if regime == "stability":
            objectives.append("Provide clear and deterministic answer")

        if confidence_score < 0.4:
            objectives.append("Clarify assumptions explicitly")

        # -------------------------
        # Final context
        # -------------------------
        return ARVISContext(
            risk_score=risk_level,
            uncertainty_score=uncertainty_level,
            stability_score=stability_score,
            confidence_score=confidence_score,
            constraints=constraints,
            objectives=objectives,
        )
