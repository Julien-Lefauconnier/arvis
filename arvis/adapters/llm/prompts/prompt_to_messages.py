# # arvis/adapters/llm/prompts/prompt_to_messages.py

from __future__ import annotations

from arvis.adapters.llm.contracts.message import LLMMessage
from arvis.adapters.llm.prompts.contract import PromptContract


class PromptToMessagesMapper:
    @staticmethod
    def to_messages(prompt: PromptContract) -> list[LLMMessage]:
        messages: list[LLMMessage] = []

        # System
        if prompt.system:
            messages.append(LLMMessage(role="system", content=prompt.system))

        # User (with constraints injected)
        user_content = prompt.user

        if prompt.constraints:
            constraints_block = "\n\nConstraints:\n" + "\n".join(
                f"- {c}" for c in prompt.constraints
            )
            user_content += constraints_block

        messages.append(LLMMessage(role="user", content=user_content))

        return messages
