# tests/kernel/pipeline/services/test_llm_request_builder.py

from types import SimpleNamespace

from arvis.kernel.pipeline.services.llm_request_builder import LLMRequestBuilder


def build_high_risk_context():
    return SimpleNamespace(
        cognitive_state=SimpleNamespace(
            regime="stability",
            uncertainty=SimpleNamespace(level=0.2),
            risk=SimpleNamespace(level=0.9),
        )
    )


def test_llm_request_builder_adapts_stable_context() -> None:
    ctx = SimpleNamespace(
        cognitive_state=SimpleNamespace(
            regime="stability",
            uncertainty=None,
            risk=None,
        )
    )

    req = LLMRequestBuilder.build_intent_enrichment_request(
        ctx,
        "hello",
    )

    assert req.options.temperature == 0.2
    assert req.options.max_tokens == 512
    assert req.messages is not None
    assert req.messages[0].role == "system"
    assert req.messages[1].role == "user"
    assert "LINGUISTIC FRAME" in req.messages[1].content
    assert "Constraints:" in req.messages[1].content


def test_llm_request_builder_constrains_high_uncertainty() -> None:
    ctx = SimpleNamespace(
        cognitive_state=SimpleNamespace(
            regime="exploration",
            uncertainty=SimpleNamespace(level=0.9),
            risk=None,
        )
    )

    req = LLMRequestBuilder.build_intent_enrichment_request(
        ctx,
        "hello",
    )

    assert req.temperature == 0.1
    assert req.max_tokens == 384
    assert req.messages is not None
    assert "Avoid speculation." in req.messages[1].content
    assert (
        "Abstain if the available context is insufficient." in req.messages[1].content
    )


def test_llm_request_builder_abstention_on_high_risk() -> None:
    ctx = SimpleNamespace(
        cognitive_state=SimpleNamespace(
            regime="stability",
            uncertainty=SimpleNamespace(level=0.2),
            risk=SimpleNamespace(level=0.9),
        )
    )

    req = LLMRequestBuilder.build_intent_enrichment_request(
        ctx,
        "hello",
    )

    assert req.temperature == 0.0
    assert req.max_tokens == 256
    assert "linguistic_act:abstention" in req.tags
    assert "Act: abstention" in req.messages[1].content


def test_policy_constraints_propagate_to_prompt():
    ctx = build_high_risk_context()

    req = LLMRequestBuilder.build_intent_enrichment_request(
        ctx,
        "unsafe request",
    )

    content = req.messages[1].content

    assert "Avoid speculation." in content
    assert "Abstain if the available context is insufficient." in content
