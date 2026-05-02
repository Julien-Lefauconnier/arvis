# arvis/adapters/llm/contracts/structured_output.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LLMStructuredOutputSpec:
    schema_name: str
    schema: type[Any]
    strict: bool = True
    retry_on_invalid: bool = True
