# arvis/cognition/policy/cognitive_policy_result.py

from dataclasses import asdict, dataclass


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

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
