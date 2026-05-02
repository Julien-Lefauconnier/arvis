# arvis/adapters/llm/contracts/result.py

from pydantic import BaseModel, ConfigDict

from arvis.adapters.llm.contracts.errors import (
    LLMGovernanceError,
    LLMPolicyViolation,
    LLMProviderError,
)

from .error_payload import LLMErrorPayload
from .response import LLMResponse


class LLMResult(BaseModel):
    success: bool

    response: LLMResponse | None = None
    error: LLMErrorPayload | None = None
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
    )

    @staticmethod
    def map_exception_to_payload(exc: Exception) -> LLMErrorPayload:
        if isinstance(exc, LLMPolicyViolation):
            return LLMErrorPayload(
                code="policy_violation",
                message=str(exc),
                error_type="LLMPolicyViolation",
                retryable=False,
            )

        if isinstance(exc, LLMProviderError):
            return LLMErrorPayload(
                code="provider_error",
                message=str(exc),
                error_type="LLMProviderError",
                retryable=True,
            )

        if isinstance(exc, LLMGovernanceError):
            return LLMErrorPayload(
                code="governance_error",
                message=str(exc),
                error_type="LLMGovernanceError",
                retryable=False,
            )

        return LLMErrorPayload(
            code="unknown",
            message=str(exc),
            error_type=exc.__class__.__name__,
            retryable=False,
        )
