# arvis/adapters/llm/contracts/privacy.py

from enum import Enum


class LLMPrivacyLevel(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE = "sensitive"
    CRITICAL = "critical"
