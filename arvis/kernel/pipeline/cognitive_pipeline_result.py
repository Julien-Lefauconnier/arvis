# arvis/kernel/pipeline/cognitive_pipeline_result.py

from dataclasses import dataclass
from typing import Any, Optional


@dataclass(frozen=True)
class CognitivePipelineResult:
    """
    Final kernel output.

    No execution.
    No LLM.
    No side effects.
    """

    bundle: Optional[Any]
    decision: Optional[Any]
    scientific: Optional[Any]
    control: Optional[Any]
    gate_result: Optional[Any]
    executable_intent: Optional[Any] = None