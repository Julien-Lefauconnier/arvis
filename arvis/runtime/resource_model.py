# arvis/runtime/resource_model.py

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ResourcePressure:
    reasoning_pressure: float = 0.0
    attention_pressure: float = 0.0
    uncertainty_pressure: float = 0.0
    temporal_pressure: float = 0.0
    memory_pressure: float = 0.0

    def validate(self) -> None:
        for name, value in (
            ("reasoning_pressure", self.reasoning_pressure),
            ("attention_pressure", self.attention_pressure),
            ("uncertainty_pressure", self.uncertainty_pressure),
            ("temporal_pressure", self.temporal_pressure),
            ("memory_pressure", self.memory_pressure),
        ):
            if value < 0.0:
                raise ValueError(f"{name} must be >= 0")

    def total(self) -> float:
        self.validate()
        return (
            self.reasoning_pressure
            + self.attention_pressure
            + self.uncertainty_pressure
            + self.temporal_pressure
            + self.memory_pressure
        ) / 5.0


@dataclass
class ResourceState:
    pressure: ResourcePressure = ResourcePressure()
    active_budget_grants: int = 0
    total_ticks: int = 0
    total_processes_seen: int = 0

    def note_tick(self) -> None:
        self.total_ticks += 1

    def note_process_seen(self) -> None:
        self.total_processes_seen += 1
