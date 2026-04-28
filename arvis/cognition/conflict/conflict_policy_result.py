# arvis/cognition/conflict/conflict_policy_result.py

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ConflictPolicyResult:
    """
    Result of applying conflict policies to a target.
    """

    target_id: str
    metadata: dict[str, Any] = field(default_factory=dict)
