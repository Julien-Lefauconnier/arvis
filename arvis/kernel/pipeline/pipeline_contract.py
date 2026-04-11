# arvis/kernel/pipeline/pipeline_contract.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PipelineStageSignal:
    """
    Explicit signal returned by run_stage().

    completed=False here means:
    - the pipeline has advanced one step
    - finalization has NOT happened yet
    - no terminal result should be exposed to the scheduler
    """

    completed: bool = False
    result: Any | None = None


@dataclass(frozen=True)
class PipelineFinalizeSignal:
    """
    Explicit signal returned by finalize_run().

    completed=True is mandatory here.
    result must be non-null for a valid finalized pipeline.
    """

    result: Any
    completed: bool = True