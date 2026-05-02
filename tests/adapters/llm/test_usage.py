# tests/unit/llm/test_usage.py

from arvis.adapters.llm.contracts.usage import LLMUsage


def test_usage_creation():
    usage = LLMUsage(
        prompt_tokens=10,
        completion_tokens=20,
        total_tokens=30,
    )

    assert usage.total_tokens == 30
    assert not usage.is_empty()


def test_usage_addition():
    u1 = LLMUsage(10, 20, 30, cost=0.01, latency_ms=100)
    u2 = LLMUsage(5, 5, 10, cost=0.02, latency_ms=50)

    u3 = u1.add(u2)

    assert u3.total_tokens == 40
    assert u3.prompt_tokens == 15
    assert u3.completion_tokens == 25
    assert u3.cost == 0.03
    assert u3.latency_ms == 150


def test_usage_empty():
    usage = LLMUsage(0, 0, 0)
    assert usage.is_empty()
