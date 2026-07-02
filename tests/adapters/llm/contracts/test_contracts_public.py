# tests/adapters/llm/contracts/test_contracts_public.py
"""The LLM contract types must be importable from the package root.

This pins the canonical public import path so the re-export cannot silently
disappear (veramem depends on it via a single import rather than reaching into
submodules).
"""


def test_canonical_llm_contract_import() -> None:
    from arvis.adapters.llm.contracts import LLMRequest, LLMResponse

    assert LLMRequest is not None
    assert LLMResponse is not None


def test_contracts_export_list() -> None:
    from arvis.adapters.llm import contracts

    assert "LLMResponse" in contracts.__all__
    assert "LLMRequest" in contracts.__all__
