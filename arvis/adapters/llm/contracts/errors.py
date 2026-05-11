# arvis/adapters/llm/contracts/errors.py

from arvis.errors import ArvisExternalError, ArvisRuntimeError


class LLMError(ArvisRuntimeError):
    """Canonical base error for all LLM-related failures.

    This is the only error type that should be exposed to the rest of the stack.
    """

    pass


class LLMGovernanceError(LLMError):
    pass


class LLMPolicyViolation(LLMGovernanceError):
    pass


class LLMProviderError(ArvisExternalError, LLMError):
    pass
