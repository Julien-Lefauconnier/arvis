# arvis/api/os.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional
from typing import Callable, cast
from arvis.reflexive.snapshot.reflexive_snapshot import ReflexiveSnapshot
from arvis.kernel.pipeline.cognitive_pipeline import CognitivePipeline
from arvis.kernel.pipeline.cognitive_pipeline_context import CognitivePipelineContext
from arvis.api.stability import StabilityView
from arvis.api.trace import DecisionTraceView
from arvis.api.timeline import TimelineView
from arvis.api.version import API_VERSION, API_FINGERPRINT
from arvis.api.ir import build_ir_view


@dataclass
class CognitiveOSConfig:
    enable_trace: bool = True
    strict_mode: bool = False

# -----------------------------------------------------
# Public unified result view 
# -----------------------------------------------------

@dataclass(frozen=True)
class CognitiveResultView:
    """
    Unified public result of the Cognitive OS.

    This is the stable contract exposed to external users.
    """

    decision: Any
    stability: Any
    stability_view: Optional[StabilityView]
    trace: Any
    trace_view: Optional[DecisionTraceView] = None
    timeline: Optional[Any] = None
    timeline_view: Optional[TimelineView] = None
    _ir: Optional[Dict[str, Any]] = None
    reflexive: Optional[Dict[str, Any]] = None

    @staticmethod
    def from_pipeline(result: Any) -> "CognitiveResultView":
        stability = getattr(result, "stability", None)
        trace = getattr(result, "trace", None)
        timeline = getattr(result, "timeline", None)
        # --- reflexive snapshot (safe, optional) ---
        reflexive_payload = None
        try:
            from arvis.api.reflexive import get_reflexive_snapshot

            typed_get_snapshot = cast(
                Callable[[Any], ReflexiveSnapshot],
                get_reflexive_snapshot,
            )

            state = getattr(result, "cognitive_state", None)
            if state is not None:
                snapshot = typed_get_snapshot(state)
                reflexive_payload = snapshot.to_dict()
        except Exception:
            reflexive_payload = None

        return CognitiveResultView(
            decision=getattr(result, "action_decision", None),
            stability=stability,
            stability_view=(
                StabilityView.from_snapshot(stability) if stability else None
            ),
            trace=trace,
            trace_view=DecisionTraceView.from_trace(trace) if trace else None,
            timeline=timeline,
            timeline_view=(
                TimelineView.from_snapshot(timeline)
                if timeline
                else None
            ),
            _ir=build_ir_view(result),
            reflexive=reflexive_payload,
        )
    # -----------------------------------------------------
    # STANDARD SERIALIZATION 
    # -----------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """
        Stable JSON-ready representation.
        """

        return {
            "version": API_VERSION,
            "fingerprint": API_FINGERPRINT,
            "decision": str(self.decision),
            "stability": {
                "score": self.stability_view.stability_score
                if self.stability_view else None,
                "risk": self.stability_view.risk_level
                if self.stability_view else None,
                "regime": self.stability_view.regime
                if self.stability_view else None,
            },
            "has_trace": self.trace is not None,
            "has_timeline": self.timeline is not None,
            "trace": self.trace_view.to_dict() if self.trace_view else None,
            "timeline": self.timeline_view.to_dict() if self.timeline_view else None,
            # IR intentionally NOT exposed by default (non-breaking)
        }
    
    def to_ir(self) -> Optional[Dict[str, Any]]:
        """
        Explicit IR access (versioned contract).

        This is the canonical machine interface.
        """
        return self._ir

    def summary(self) -> str:
        """
        Human-readable short summary.
        """

        if not self.stability_view:
            return "No stability data"

        return (
            f"Decision={self.decision} | "
            f"Stability={self.stability_view.stability_score:.2f} | "
            f"Risk={self.stability_view.risk_level:.2f} | "
            f"Regime={self.stability_view.regime}"
        )
class CognitiveOS:
    """
    Public entrypoint for ARVIS Cognitive OS.

    This is the ONLY class external users should need.
    """

    def __init__(self, config: Optional[CognitiveOSConfig] = None):
        self.pipeline = CognitivePipeline()
        self.config = config or CognitiveOSConfig()

    # -----------------------------------------------------
    # PUBLIC API
    # -----------------------------------------------------
    def run(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Public API v1.

        Contract:
            - input: cognitive_input (required)
            - output: CognitiveResultView

        This contract is stable and versioned.
        
        High-level execution entrypoint.

        This method hides ALL internal complexity.
        """

        ctx = self._build_context(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )

        result = self.pipeline.run(ctx)

        # -----------------------------------------------------
        # Unified result (future-proof)
        # -----------------------------------------------------

        if self.config.enable_trace:
            # Return structured OS result instead of raw pipeline
            return CognitiveResultView.from_pipeline(result)

        # -----------------------------------------------------
        # Minimal backward-compatible output
        # -----------------------------------------------------

        return {
            "action": getattr(result, "action_decision", None),
            "can_execute": getattr(result, "can_execute", None),
        }
    

    def run_ir(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Canonical IR API (machine contract).

        Returns:
            dict compliant with ARVIS IR schema (versioned).
        """

        ctx = self._build_context(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline,
            confirmation_result=confirmation_result,
            extra=extra,
        )

        result = self.pipeline.run(ctx)

        return build_ir_view(result)

    # -----------------------------------------------------
    # INTERNAL
    # -----------------------------------------------------
    def _build_context(
        self,
        user_id: str,
        cognitive_input: Any,
        *,
        conversation_context: Any = None,
        timeline: Any = None,
        confirmation_result: Any = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> CognitivePipelineContext:

        ctx = CognitivePipelineContext(
            user_id=user_id,
            cognitive_input=cognitive_input,
            conversation_context=conversation_context,
            timeline=timeline or [],
            confirmation_result=confirmation_result,
            extra=extra or {},
        )

        return ctx