# arvis/adapters/llm/contracts/contracts/request.py

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .context import ARVISContext
from .message import LLMMessage
from .options import LLMOptions
from .privacy import LLMPrivacyLevel
from .structured_output import LLMStructuredOutputSpec


class LLMRequest(BaseModel):
    # NEW standard
    messages: list[LLMMessage] | None = None

    # LEGACY support
    prompt: str | None = None

    # options
    options: LLMOptions = Field(default_factory=LLMOptions)

    context: ARVISContext | None = None
    privacy: LLMPrivacyLevel = LLMPrivacyLevel.INTERNAL

    request_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    structured_output: LLMStructuredOutputSpec | None = None

    model: str | None = None

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    @model_validator(mode="after")
    def normalize_messages(self) -> "LLMRequest":
        # cas 1: messages déjà fournis
        if self.messages:
            if len(self.messages) == 0:
                raise ValueError("messages cannot be empty")
            return self

        # cas 2: prompt → convertir en message
        if self.prompt:
            object.__setattr__(
                self,
                "messages",
                [LLMMessage(role="user", content=self.prompt)],
            )
            return self

        # cas invalide
        raise ValueError("Either 'messages' or 'prompt' must be provided")

    @property
    def max_tokens(self) -> int | None:
        return self.options.max_tokens if self.options else None

    @property
    def temperature(self) -> float | None:
        return self.options.temperature if self.options else None

    @property
    def effective_model(self) -> str | None:
        return self.model or getattr(self.options, "model", None)

    @property
    def metadata(self) -> dict[str, Any]:
        # compat legacy
        return {}
