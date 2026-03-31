# arvis/reflexive/core/reflexive_mode.py

from enum import Enum


class ReflexiveMode(Enum):
    """
    Declarative reflexive modes.

    A reflexive mode describes HOW the system presents itself,
    not WHAT it does.

    This enum is:
    - finite
    - explicit
    - non-executable
    """

    OBSERVATION_ONLY = "observation_only"
    EXPLANATORY = "explanatory"
    AUDITABLE = "auditable"
    COMPLIANCE_CHAIN_READY = "compliance_chain_ready"

    @property
    def is_public(self) -> bool:
        """
        Indicates whether this mode can be exposed publicly.
        """
        return self in {
            ReflexiveMode.OBSERVATION_ONLY,
        }
