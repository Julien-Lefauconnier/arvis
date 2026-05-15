# arvis/errors/llm_runtime.py

from __future__ import annotations

from arvis.errors.base import (
    ArvisExternalError,
    ArvisRuntimeError,
    ErrorDomain,
)
from arvis.errors.codes import ErrorCode


class LLMRuntimeError(ArvisRuntimeError):
    domain = ErrorDomain.LLM
    default_code = ErrorCode.LLM_RUNTIME_ERROR
    replay_safe = False


class LLMExecutionContractViolation(LLMRuntimeError):
    default_code = ErrorCode.LLM_EXECUTION_CONTRACT_VIOLATION
    replay_safe = False


class LLMEmptyResponseError(ArvisExternalError):
    domain = ErrorDomain.LLM
    default_code = ErrorCode.LLM_EMPTY_RESPONSE


class LLMRetryExhaustedError(ArvisExternalError):
    domain = ErrorDomain.LLM
    default_code = ErrorCode.LLM_RETRY_EXHAUSTED


class LLMFallbackExhaustedError(ArvisExternalError):
    domain = ErrorDomain.LLM
    default_code = ErrorCode.LLM_FALLBACK_EXHAUSTED
