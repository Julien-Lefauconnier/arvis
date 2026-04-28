# arvis/cognition/conflict/conflict_policy_result.py

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass(frozen=True)
class ConflictPolicyResult:
    """
    Result of applying conflict policies to a target.
    """

    target_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)
