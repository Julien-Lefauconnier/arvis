# arvis/kernel/pipeline/context/runtime_policy_context.py

from dataclasses import dataclass


@dataclass
class PipelineRuntimePolicyContext:
    retry_requested: bool = False
    retry_count: int = 0

    force_execution: bool = False
    force_tool: str | None = None
