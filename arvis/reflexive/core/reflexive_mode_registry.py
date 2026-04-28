# arvis/reflexive/core/reflexive_mode_registry.py

from typing import Any

from arvis.reflexive.core.reflexive_mode import ReflexiveMode


class ReflexiveModeRegistry:
    """
    Declarative registry resolving the current reflexive mode.

    - deterministic
    - stateless
    - snapshot-agnostic
    """

    @classmethod
    def resolve(
        cls,
        *,
        snapshot: Any | None,
        compliance_chain: Any | None = None,
    ) -> ReflexiveMode:
        if compliance_chain is not None:
            return ReflexiveMode.COMPLIANCE_CHAIN_READY

        if snapshot is not None:
            return ReflexiveMode.EXPLANATORY

        return ReflexiveMode.OBSERVATION_ONLY
