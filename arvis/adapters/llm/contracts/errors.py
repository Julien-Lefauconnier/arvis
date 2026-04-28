# arvis/adapters/llm/contracts/errors.py


class LLMGovernanceError(RuntimeError):
    pass


class LLMPolicyViolation(LLMGovernanceError):
    pass


class LLMProviderError(RuntimeError):
    pass
