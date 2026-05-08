# arvis/kernel/pipeline/result/observability_result.py

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PipelineObservabilityResult:
    scientific: Any | None = None
    control: Any | None = None
