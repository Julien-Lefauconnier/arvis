# arvis/uncertainty/uncertainty_frame_registry.py

from arvis.uncertainty.uncertainty_axis import UncertaintyAxis
from arvis.uncertainty.uncertainty_frame import UncertaintyFrame


class UncertaintyFrameRegistry:
    """
    Registry of canonical uncertainty frames.

    Frames are declarative and stable.
    """

    PERSONAL_CONTEXT = UncertaintyFrame(
        frame_id="PERSONAL_CONTEXT",
        label="Personal context",
        description="Reasoning depends on personal user context",
        axes={
            UncertaintyAxis.CONTEXT_DEPENDENT,
            UncertaintyAxis.USER_SENSITIVE,
        },
    )

    FINANCIAL = UncertaintyFrame(
        frame_id="FINANCIAL",
        label="Financial context",
        description="Financial or monetary impact involved",
        axes={
            UncertaintyAxis.HIGH_IMPACT,
            UncertaintyAxis.IRREVERSIBLE_RISK,
        },
    )

    HEALTH = UncertaintyFrame(
        frame_id="HEALTH",
        label="Health context",
        description="Health-related uncertainty",
        axes={
            UncertaintyAxis.HIGH_IMPACT,
            UncertaintyAxis.USER_SENSITIVE,
            UncertaintyAxis.DOMAIN_SPECIFIC,
        },
    )

    @classmethod
    def all(cls) -> list[UncertaintyFrame]:
        return [
            cls.PERSONAL_CONTEXT,
            cls.FINANCIAL,
            cls.HEALTH,
        ]
