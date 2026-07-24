# arvis/host_api/llm.py

"""The LLM adapter contract.

The response type a host-provided language model adapter produces
for the governed runtime.

Re-export layer only: every symbol is defined where it lives; this
module pins the import path (see VERSIONING.md, host integration
surface).
"""

from arvis.adapters.llm.contracts import LLMResponse

__all__ = [
    "LLMResponse",
]
