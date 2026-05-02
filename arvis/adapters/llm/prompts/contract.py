# arvis/adapters/llm/prompts/contract.py

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class PromptPurpose(StrEnum):
    INTENT_ENRICHMENT = "intent_enrichment"


class PromptContract(BaseModel):
    purpose: PromptPurpose
    system: str
    user: str
    constraints: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    def render_user_content(self) -> str:
        if not self.constraints:
            return self.user

        constraints = "\n".join(f"- {item}" for item in self.constraints)
        return f"{self.user}\n\nConstraints:\n{constraints}"
