# arvis/adapters/llm/__init__.py


"""Public LLM adapter API.

Only stable contracts and the production runtime entrypoint are exported here.
Legacy adapters remain importable from their direct modules for backward
compatibility, but must not be exposed as public package-level API.
"""

from __future__ import annotations

from arvis.adapters.llm.contracts.errors import LLMError, LLMPolicyViolation
from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.contracts.response import LLMResponse
from arvis.adapters.llm.contracts.usage import LLMUsage
from arvis.adapters.llm.governance.evaluator import LLMGovernanceEvaluator
from arvis.adapters.llm.governance.policy import LLMGovernancePolicy
from arvis.adapters.llm.runtime.executor import LLMRuntimeExecutor
from arvis.adapters.llm.runtime.guarded_adapter import GuardedLLMAdapter

__all__ = [
    "LLMError",
    "LLMRequest",
    "LLMResponse",
    "LLMRuntimeExecutor",
    "GuardedLLMAdapter",
    "LLMUsage",
    "LLMGovernancePolicy",
    "LLMGovernanceEvaluator",
    "LLMPolicyViolation",
]
