# arvis/adapters/llm/contracts/options.py

from pydantic import BaseModel, ConfigDict, Field


class LLMOptions(BaseModel):
    temperature: float = Field(ge=0.0, le=2.0, default=0.7)
    max_tokens: int = Field(gt=0, default=512)

    timeout_ms: int = Field(gt=0, default=10_000)

    top_p: float | None = Field(default=None, ge=0.0, le=1.0)
    frequency_penalty: float | None = None
    presence_penalty: float | None = None

    model_config = ConfigDict(frozen=True)
