# arvis/adapters/llm/contracts/context.py

from pydantic import BaseModel, ConfigDict, Field


class ARVISContext(BaseModel):
    risk_score: float = Field(ge=0.0, le=1.0)
    uncertainty_score: float = Field(ge=0.0, le=1.0)
    stability_score: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)

    constraints: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)
