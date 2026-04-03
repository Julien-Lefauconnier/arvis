# arvis/adapters/llm/openai_adapter.py

from __future__ import annotations

from typing import Optional, TYPE_CHECKING, Any

from arvis.adapters.llm.base import BaseLLMAdapter, LLMResponse


if TYPE_CHECKING:
    from openai import OpenAI # type: ignore # noqa: F401

class OpenAIAdapter(BaseLLMAdapter):
    def __init__(
        self,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
    ):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAIAdapter requires `openai` package. Install with `pip install openai`."
            )

        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:

        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        content = response.choices[0].message.content

        return LLMResponse(
            content=content,
            raw=response,
            metadata={
                "model": self.model,
            },
        )