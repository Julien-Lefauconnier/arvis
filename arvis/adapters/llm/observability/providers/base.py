# arvis/adapters/llm/observation/providers/base.py

from abc import ABC, abstractmethod
from typing import Any

from arvis.adapters.llm.observability.observation import LLMObservation


class BaseObservationProvider(ABC):
    @abstractmethod
    def observe(self, response: Any) -> LLMObservation: ...
