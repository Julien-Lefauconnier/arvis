# arvis/adapters/llm/prompts/sanitizer.py

from __future__ import annotations


class PromptSanitizer:
    @staticmethod
    def sanitize(text: str) -> str:
        return "\n".join(
            line.strip() for line in text.strip().splitlines() if line.strip()
        )
