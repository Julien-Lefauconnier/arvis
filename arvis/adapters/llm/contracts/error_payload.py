# arvis/adapters/llm/contracts/error_payload.py

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LLMErrorPayload(BaseModel):
    code: str
    message: str

    error_type: str

    provider: str | None = None
    model: str | None = None

    retryable: bool = False

    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )
