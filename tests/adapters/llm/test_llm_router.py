# tests/adapters/llm/test_llm_router.py

from arvis.adapters.llm.contracts.request import LLMRequest
from arvis.adapters.llm.runtime.router import LLMRouter, LLMRoutingRequest


def test_router_uses_default_provider() -> None:
    router = LLMRouter()

    provider = router.route()

    assert provider is not None


def test_router_prefers_explicit_provider() -> None:
    router = LLMRouter()

    provider = router.route(LLMRoutingRequest(preferred_provider="mock"))

    response = provider.generate(LLMRequest(prompt="hello"))

    assert response.content == "mock:hello"


def test_router_offline_uses_ollama() -> None:
    router = LLMRouter()

    selected = router._select_provider_name(LLMRoutingRequest(offline_required=True))

    assert selected == "ollama"


def test_router_cost_sensitive_uses_ollama() -> None:
    router = LLMRouter()

    selected = router._select_provider_name(LLMRoutingRequest(cost_sensitive=True))

    assert selected == "ollama"


def test_router_latency_sensitive_uses_openai() -> None:
    router = LLMRouter()

    selected = router._select_provider_name(LLMRoutingRequest(latency_sensitive=True))

    assert selected == "openai"


def test_router_explicit_provider_has_priority() -> None:
    router = LLMRouter()

    selected = router._select_provider_name(
        LLMRoutingRequest(
            preferred_provider="mock",
            offline_required=True,
            cost_sensitive=True,
            latency_sensitive=True,
        )
    )

    assert selected == "mock"
