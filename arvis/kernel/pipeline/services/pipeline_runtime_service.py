# arvis/kernel/pipeline/services/pipeline_runtime_service.py

from __future__ import annotations

from typing import TYPE_CHECKING

from arvis.cognition.control.cognitive_control_runtime import (
    CognitiveControlRuntime,
)

if TYPE_CHECKING:
    from arvis.kernel.pipeline.cognitive_pipeline import (
        CognitivePipeline,
    )


class PipelineRuntimeService:
    @staticmethod
    def get_control_runtime(
        pipeline: CognitivePipeline,
        user_id: str,
    ) -> CognitiveControlRuntime:
        runtime = pipeline.control_runtimes.get(user_id)
        if runtime is None:
            runtime = CognitiveControlRuntime()
            pipeline.control_runtimes[user_id] = runtime
        return runtime
