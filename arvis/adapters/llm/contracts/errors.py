# arvis/adapters/llm/contracts/errors.py


class LLMError(RuntimeError):
    """Canonical base error for all LLM-related failures.

    This is the only error type that should be exposed to the rest of the stack.
    """

    pass


class LLMGovernanceError(LLMError):
    pass


class LLMPolicyViolation(LLMGovernanceError):
    pass


class LLMProviderError(LLMError):
    pass
