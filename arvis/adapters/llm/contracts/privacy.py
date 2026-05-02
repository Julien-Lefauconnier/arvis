# arvis/adapters/llm/contracts/privacy.py

from enum import StrEnum


class LLMPrivacyLevel(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    CRITICAL = "critical"
