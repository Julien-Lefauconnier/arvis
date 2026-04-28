# arvis/kernel_core/contracts/execution_contract.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from arvis.kernel_core.process import BudgetConsumption, CognitiveProcess


@dataclass(frozen=True)
class ProcessExecutionOutcome:
    result: Any
    consumption: BudgetConsumption
    completed: bool
    stage_name: str | None = None


class ProcessExecutor(Protocol):
    def execute_process(self, process: CognitiveProcess) -> ProcessExecutionOutcome: ...
