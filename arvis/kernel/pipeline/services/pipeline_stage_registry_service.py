# arvis/kernel/pipeline/services/pipeline_stage_registry_service.py

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import (
        CognitivePipeline,
        PipelineStage,
    )


class PipelineStageRegistryService:
    @staticmethod
    def iter_stages(
        pipeline: "CognitivePipeline",
    ) -> Iterable["PipelineStage"]:
        return [
            pipeline.tool_feedback_stage,
            pipeline.tool_retry_stage,
            pipeline.decision_stage,
            pipeline.passive_stage,
            pipeline.bundle_stage,
            pipeline.conflict_stage,
            pipeline.core_stage,
            pipeline.regime_stage,
            pipeline.temporal_stage,
            pipeline.conflict_modulation_stage,
            pipeline.control_stage,
            pipeline.projection_stage,
            pipeline.gate_stage,
            pipeline.control_feedback_stage,
            pipeline.structural_risk_stage,
            pipeline.confirmation_stage,
            pipeline.execution_stage,
            pipeline.action_stage,
            pipeline.intent_stage,
            pipeline.runtime_stage,
        ]