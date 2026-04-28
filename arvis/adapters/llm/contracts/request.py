# arvis/adapters/llm/contracts/request.py


from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LLMRequest:
    prompt: str
    system_prompt: str | None = None
    temperature: float = 0.0
    max_tokens: int | None = None
    model: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("LLMRequest.prompt must not be empty")

        if self.temperature < 0.0:
            raise ValueError("LLMRequest.temperature must be >= 0")

        if self.max_tokens is not None and self.max_tokens <= 0:
            raise ValueError("LLMRequest.max_tokens must be > 0")
