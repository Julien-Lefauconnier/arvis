# arvis/adapters/llm/contracts/response.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LLMResponse:
    content: str
    raw: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise TypeError("LLMResponse.content must be a string")
