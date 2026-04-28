# arvis/cognition/gate/gate_trace_builder.py

from typing import Any

from .gate_decision_trace import GateDecisionTrace, GateDecisionTraceStep
from .reason_code_normalizer import ReasonCodeNormalizer


class GateTraceBuilder:
    # NON NORMATIF (important)
    # This is an extended trace layer

    @staticmethod
    def _parse_reason(reason: str) -> tuple[str, ...]:
        return tuple(part.strip() for part in reason.split("|") if part.strip())

    @staticmethod
    def _score_reason(reason: str) -> float:
        r = reason.lower()
        if "unstable" in r or "instability" in r:
            return 0.9
        if "risk" in r or "danger" in r:
            return 0.8
        if "invalid" in r or "violation" in r:
            return 0.7
        if "confirm" in r:
            return 0.5
        return 0.3

    @classmethod
    def build(cls, raw_steps: tuple[dict[str, Any], ...]) -> GateDecisionTrace:
        steps: list[GateDecisionTraceStep] = []

        for item in raw_steps:
            stage = str(item.get("stage", "")).strip()
            before = str(item.get("before", "")).strip()
            after = str(item.get("after", "")).strip()
            reason = str(item.get("reason", "")).strip()

            raw_reason_codes = cls._parse_reason(reason)

            # -----------------------------------------
            # Normalize reason codes (spec alignment)
            # -----------------------------------------
            reason_codes = ReasonCodeNormalizer.normalize(raw_reason_codes)

            severity = max(
                (cls._score_reason(r) for r in reason_codes),
                default=0.0,
            )

            stability_impact = 1.0 if before != after else 0.0

            steps.append(
                GateDecisionTraceStep(
                    stage=stage,
                    before=before,
                    after=after,
                    reason_codes=reason_codes,
                    severity=severity,
                    stability_impact=stability_impact,
                    input_snapshot=None,
                )
            )

        total_severity = sum(s.severity for s in steps)
        max_severity = max((s.severity for s in steps), default=0.0)

        instability_score = sum(
            s.stability_impact for s in steps if s.before != s.after
        )

        return GateDecisionTrace(
            steps=tuple(steps),
            total_severity=total_severity,
            max_severity=max_severity,
            instability_score=instability_score,
        )
