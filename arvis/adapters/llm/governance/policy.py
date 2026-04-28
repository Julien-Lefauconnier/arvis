# arvis/adapters/llm/governance/policy.py

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class LLMGovernancePolicy:
    """
    Zero-trust policy for LLM execution.

    If no policy is explicitly provided, execution must be denied.
    """

    allow_llm: bool = False
    max_prompt_chars: int = 16_000
    max_output_tokens: int | None = 1_024
    allowed_models: set[str] = field(default_factory=set)
    blocked_terms: set[str] = field(default_factory=set)
    require_system_prompt: bool = False
    audit_required: bool = True

    @staticmethod
    def permissive_for_dev() -> LLMGovernancePolicy:
        return LLMGovernancePolicy(
            allow_llm=True,
            allowed_models=set(),
        )
