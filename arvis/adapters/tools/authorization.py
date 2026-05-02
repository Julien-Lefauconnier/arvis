# arvis/adapters/tools/authorization.py

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolAuthorizationDecision:
    allowed: bool
    reason: str
    requires_confirmation: bool = False
