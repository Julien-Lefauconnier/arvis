# arvis/reflexive/explanation/timeline/irg_timeline_explanation_builder.py

from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_memory import (
    IRGTimelineTemporalMemory,
)
from arvis.reflexive.timeline.explanation.irg_timeline_explanation import (
    IRGTimelineExplanation,
)


class IRGTimelineExplanationBuilder:
    """
    Builds a reflexive explanation from IRG temporal memory.

    This builder:
    - Is deterministic
    - Does not infer intent
    - Does not emit recommendations
    """

    @staticmethod
    def build(
        memory: IRGTimelineTemporalMemory,
    ) -> IRGTimelineExplanation:
        diffs = list(memory.iter_diffs())

        if not diffs:
            return IRGTimelineExplanation(
                summary="No significant evolution of the timeline was observed.",
                signals=[],
                stability="stable",
            )

        signals = []
        unstable = False

        for diff in diffs:
            if diff.views_added:
                signals.append(
                    f"New timeline views appeared: {', '.join(diff.views_added)}."
                )
            if diff.views_removed:
                signals.append("Some timeline views are no longer observed.")
            if diff.entry_types_added:
                signals.append("New types of timeline entries have been observed.")
            if not diff.is_stable:
                unstable = True

        stability = "evolving" if unstable else "stable"

        summary = (
            "The system observed changes in how timeline information "
            "is structured over time."
            if unstable
            else "The timeline structure remained stable over time."
        )

        return IRGTimelineExplanation(
            summary=summary,
            signals=signals,
            stability=stability,
        )
