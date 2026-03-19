# arvis/cognition/conflict/conflict_pressure_engine.py

from typing import Any, List
from arvis.math.signals.conflict import ConflictSignal



class ConflictPressureEngine:
    """
    Pure, stateless engine computing structured conflict pressure.
    """

    def compute(self, conflicts: List[Any]) -> ConflictSignal:
        score = 0.0
        epistemic = 0.0
        decisional = 0.0
        temporal = 0.0
        ethical = 0.0

        for c in conflicts:
            s = getattr(c, "score", 0.0) or 0.0
            score += s

            ctype = getattr(c, "type", None)

            if ctype == "epistemic":
                epistemic += s
            elif ctype == "decision":
                decisional += s
            elif ctype == "temporal":
                temporal += s
            elif ctype == "ethical":
                ethical += s

        return ConflictSignal(
            global_score=min(1.0, score),
            epistemic=min(1.0, epistemic),
            decisional=min(1.0, decisional),
            temporal=min(1.0, temporal),
            ethical=min(1.0, ethical),
        )
    
    def from_scalar(self, value: float) -> ConflictSignal:
        return ConflictSignal.from_scalar(value)