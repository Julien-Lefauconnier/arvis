# arvis/adapters/llm/contracts/message.py

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LLMMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str = Field(min_length=1)

    name: str | None = None
    tool_call_id: str | None = None

    model_config = ConfigDict(frozen=True)
