# arvis/cognition/policy/cognitive_policy_result.py

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass(frozen=True)
class CognitivePolicyResult:
    """
    Declarative result produced by a cognitive policy.

    Kernel invariants:
    - immutable
    - serializable
    - no execution
    - no automatic effect
    """

    policy_name: str
    dimension: str
    suggestion_type: str
    rationale: str

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)