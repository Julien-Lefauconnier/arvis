# tests/adapters/llm/test_provider_sdk_contracts.py
"""Contract tests of the three real providers, no network, no SDK.

Campaign FIX (LOT F2): the request-to-SDK mapping and the
response-to-LLMResponse mapping of anthropic, openai and ollama were
never exercised (the SDKs are optional extras and no test faked
them). Each test installs a minimal fake SDK module and pins the
exact call the provider makes and the exact response it builds, plus
the guiding ImportError when the SDK is absent.
"""

from __future__ import annotations

import sys
import types
from types import SimpleNamespace
from typing import Any

import pytest

from arvis.adapters.llm.contracts.message import LLMMessage
from arvis.adapters.llm.contracts.options import LLMOptions
from arvis.adapters.llm.contracts.request import LLMRequest


def _request() -> LLMRequest:
    return LLMRequest(
        messages=[
            LLMMessage(role="system", content="be terse"),
            LLMMessage(role="user", content="ping"),
        ],
        options=LLMOptions(temperature=0.2, max_tokens=64),
    )


# ---------------------------------------------------------------
# anthropic
# ---------------------------------------------------------------


def _install_fake_anthropic(
    monkeypatch: pytest.MonkeyPatch, captured: dict[str, Any]
) -> None:
    class _Messages:
        def create(self, **kwargs: Any) -> Any:
            captured.update(kwargs)
            return SimpleNamespace(
                content=[
                    SimpleNamespace(text="pong "),
                    SimpleNamespace(text="pong"),
                ],
                id="msg_123",
            )

    class _Anthropic:
        def __init__(self, api_key: str | None = None) -> None:
            captured["api_key"] = api_key
            self.messages = _Messages()

    module = types.ModuleType("anthropic")
    module.Anthropic = _Anthropic  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "anthropic", module)


def test_anthropic_request_and_response_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from arvis.adapters.llm.providers.anthropic import AnthropicProvider

    captured: dict[str, Any] = {}
    _install_fake_anthropic(monkeypatch, captured)

    response = AnthropicProvider(model="claude-test", api_key="k").generate(_request())

    assert captured["model"] == "claude-test"
    assert captured["messages"] == [
        {"role": "system", "content": "be terse"},
        {"role": "user", "content": "ping"},
    ]
    assert captured["temperature"] == 0.2
    assert captured["max_tokens"] == 64
    assert response.content == "pong pong"
    assert response.provider == "anthropic"
    assert response.model == "claude-test"
    assert response.metadata["provider_response_id"] == "msg_123"


def test_anthropic_max_tokens_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A plain request carries the LLMOptions default on the wire
    (512; the messages API requires a value)."""
    from arvis.adapters.llm.providers.anthropic import AnthropicProvider

    captured: dict[str, Any] = {}
    _install_fake_anthropic(monkeypatch, captured)

    AnthropicProvider().generate(LLMRequest(prompt="ping"))

    # LLMOptions.max_tokens is a required-positive int with default
    # 512, so the provider's "or 1024" fallback is unreachable
    # through any valid LLMRequest: a plain request always carries
    # 512 on the wire (contract finding of this test).
    assert captured["max_tokens"] == 512


def test_anthropic_missing_sdk_guides_the_install(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "anthropic", None)

    from arvis.adapters.llm.providers.anthropic import AnthropicProvider

    with pytest.raises(ImportError, match="pip install anthropic"):
        AnthropicProvider()


# ---------------------------------------------------------------
# openai
# ---------------------------------------------------------------


def _install_fake_openai(
    monkeypatch: pytest.MonkeyPatch,
    captured: dict[str, Any],
    content: str | None,
) -> None:
    class _Completions:
        def create(self, **kwargs: Any) -> Any:
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
                id="cmpl_1",
            )

    class _OpenAI:
        def __init__(self, api_key: str | None = None) -> None:
            self.chat = SimpleNamespace(completions=_Completions())

    module = types.ModuleType("openai")
    module.OpenAI = _OpenAI  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "openai", module)


def test_openai_request_and_response_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from arvis.adapters.llm.providers.openai import OpenAIAdapter

    captured: dict[str, Any] = {}
    _install_fake_openai(monkeypatch, captured, "pong")

    response = OpenAIAdapter(model="gpt-test").generate(_request())

    assert captured["model"] == "gpt-test"
    assert captured["messages"][1] == {"role": "user", "content": "ping"}
    assert captured["temperature"] == 0.2
    assert response.content == "pong"
    assert response.provider == "openai"


def test_openai_null_content_becomes_empty_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from arvis.adapters.llm.providers.openai import OpenAIAdapter

    captured: dict[str, Any] = {}
    _install_fake_openai(monkeypatch, captured, None)

    response = OpenAIAdapter().generate(LLMRequest(prompt="ping"))

    assert response.content == ""


# ---------------------------------------------------------------
# ollama
# ---------------------------------------------------------------


def _install_fake_ollama(
    monkeypatch: pytest.MonkeyPatch, captured: dict[str, Any]
) -> None:
    class _Client:
        def __init__(self, host: str | None = None) -> None:
            captured["host"] = host

        def chat(self, **kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {"message": {"content": "pong"}, "id": "oll_1"}

    module = types.ModuleType("ollama")
    module.Client = _Client  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ollama", module)


def test_ollama_request_and_response_mapping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from arvis.adapters.llm.providers.ollama import OllamaProvider

    captured: dict[str, Any] = {}
    _install_fake_ollama(monkeypatch, captured)

    response = OllamaProvider(model="llama-test", host="http://box:11434").generate(
        _request()
    )

    assert captured["host"] == "http://box:11434"
    assert captured["model"] == "llama-test"
    assert captured["options"] == {"temperature": 0.2}
    assert response.content == "pong"
    assert response.provider == "ollama"
    assert response.metadata["provider_response_id"] == "oll_1"


def test_ollama_empty_response_defaults_to_empty_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from arvis.adapters.llm.providers.ollama import OllamaProvider

    captured: dict[str, Any] = {}

    class _Client:
        def __init__(self, host: str | None = None) -> None:
            captured["host"] = host

        def chat(self, **kwargs: Any) -> dict[str, Any]:
            return {}

    module = types.ModuleType("ollama")
    module.Client = _Client  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ollama", module)

    response = OllamaProvider().generate(LLMRequest(prompt="ping"))

    assert response.content == ""
    assert captured["host"] is None
