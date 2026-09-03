# arvis/adapters/llm/contracts/response.py


from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .usage import LLMUsage


class LLMResponse(BaseModel):
    """A provider-neutral completion: content plus usage and provenance.

    What the LLM runtime hands back to the pipeline whatever the
    provider; hosts see it when they bind a runtime of their own.
    """

    content: str

    provider: str = "unknown"
    model: str = "unknown"
    usage: LLMUsage = LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

    finish_reason: str | None = None

    response_id: str | None = None
    trace_id: str | None = None

    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)

    def is_empty(self) -> bool:
        return not self.content.strip()
