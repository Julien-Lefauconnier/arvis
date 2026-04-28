# arvis/api/views/cognitive_result_view.py

from __future__ import annotations

import json
from pprint import pformat
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Callable, Dict, Optional, cast

from arvis.adapters.kernel.timeline_from_signals import (
    signal_journal_to_timeline_snapshot,
)
from arvis.api.ir import build_ir_view
from arvis.api.stability import StabilityView
from arvis.api.timeline import TimelineView
from arvis.api.trace import DecisionTraceView
from arvis.api.version import API_FINGERPRINT, API_VERSION
from arvis.cognition.state.cognitive_state import CognitiveState
from arvis.reflexive.snapshot.reflexive_snapshot import ReflexiveSnapshot
from arvis.signals.signal_journal import SignalJournal


@dataclass(frozen=True)
class CognitiveResultView:
    decision: Any
    stability: Any
    stability_view: Optional[StabilityView]
    trace: Any
    trace_view: Optional[DecisionTraceView] = None
    timeline: Optional[Any] = None
    timeline_view: Optional[TimelineView] = None
    timeline_commitment: Optional[str] = None
    global_commitment: Optional[str] = None
    _ir: Optional[Dict[str, Any]] = None
    reflexive: Optional[Dict[str, Any]] = None

    @staticmethod
    def from_state(
        state: CognitiveState,
        result: Any,
    ) -> "CognitiveResultView":
        stability = getattr(result, "stability", None)
        trace = getattr(result, "trace", None)
        timeline_journal = state.timeline

        ir_payload = build_ir_view(state)

        try:
            ir_bytes = json.dumps(
                ir_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")
            ir_hash = sha256(ir_bytes).hexdigest()
        except Exception:
            ir_hash = None

        if not isinstance(timeline_journal, SignalJournal):
            timeline_snapshot = None
            timeline_commitment = None
        else:
            timeline_snapshot = signal_journal_to_timeline_snapshot(timeline_journal)
            try:
                from arvis.timeline.timeline_commitment import (
                    TimelineCommitment,
                )

                commitment = TimelineCommitment.from_snapshot(timeline_snapshot)
                timeline_commitment = commitment.commitment
            except Exception:
                timeline_commitment = None

        if timeline_commitment and ir_hash:
            try:
                global_commitment = sha256(
                    (timeline_commitment + ir_hash).encode("utf-8")
                ).hexdigest()
            except Exception:
                global_commitment = None
        else:
            global_commitment = None

        reflexive_payload = None
        try:
            from arvis.api.reflexive import get_reflexive_snapshot

            typed_get_snapshot = cast(
                Callable[[Any], ReflexiveSnapshot],
                get_reflexive_snapshot,
            )
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
            trace_view=(DecisionTraceView.from_trace(trace) if trace else None),
            timeline=timeline_snapshot,
            timeline_view=(
                TimelineView.from_snapshot(timeline_snapshot)
                if timeline_snapshot is not None
                else None
            ),
            timeline_commitment=timeline_commitment,
            global_commitment=global_commitment,
            _ir=ir_payload,
            reflexive=reflexive_payload,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": API_VERSION,
            "fingerprint": API_FINGERPRINT,
            "decision": str(self.decision),
            "stability": {
                "score": (
                    self.stability_view.stability_score if self.stability_view else None
                ),
                "risk": (
                    self.stability_view.risk_level if self.stability_view else None
                ),
                "regime": (self.stability_view.regime if self.stability_view else None),
            },
            "has_trace": self.trace is not None,
            "has_timeline": self.timeline is not None,
            "timeline_commitment": self.timeline_commitment,
            "global_commitment": self.global_commitment,
            "trace": (self.trace_view.to_dict() if self.trace_view else None),
            "timeline": (self.timeline_view.to_dict() if self.timeline_view else None),
        }

    def to_ir(self) -> Optional[Dict[str, Any]]:
        return self._ir

    def quickstart_payload(self) -> Dict[str, Any]:
        """
        Compact structured payload intended for examples,
        onboarding, demos, and README snippets.
        """
        decision = self.decision

        allowed = bool(getattr(decision, "allowed", False))
        requires_validation = bool(getattr(decision, "requires_user_validation", False))
        denied_reason = getattr(decision, "denied_reason", None)

        return {
            "version": API_VERSION,
            "status": ("ALLOWED" if allowed else "BLOCKED"),
            "approval_required": requires_validation,
            "reason": denied_reason,
            "has_trace": self.trace_view is not None,
            "has_timeline": self.timeline_view is not None,
            "commitment": self.global_commitment,
        }

    def to_json(self, *, indent: int = 2) -> str:
        """
        Stable JSON serialization of public structured output.
        """
        return json.dumps(
            self.to_dict(),
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
        )

    def quickstart_json(self, *, indent: int = 2) -> str:
        """
        Compact JSON payload for quickstarts.
        """
        return json.dumps(
            self.quickstart_payload(),
            indent=indent,
            sort_keys=False,
            ensure_ascii=False,
        )

    def explain(self) -> str:
        """
        Human-friendly executive summary intended for examples,
        demos, CLI usage, and onboarding.
        """
        decision = self.decision

        allowed = bool(getattr(decision, "allowed", False))
        requires_validation = bool(getattr(decision, "requires_user_validation", False))
        denied_reason = getattr(decision, "denied_reason", None) or "-"

        status = "ALLOWED" if allowed else "BLOCKED"
        approval = "YES" if requires_validation else "NO"
        commitment = (
            f"{self.global_commitment[:16]}..." if self.global_commitment else "-"
        )
        trace = "Available" if self.trace_view else "None"

        lines = [
            f"Status         : {status}",
            f"Approval Need  : {approval}",
            f"Reason         : {denied_reason}",
            f"Commitment     : {commitment}",
            f"Trace          : {trace}",
        ]

        return "\n".join(lines)

    def pretty(self) -> str:
        """
        Pretty printed structured payload for terminal use.
        """
        return pformat(self.to_dict(), sort_dicts=False)

    def summary(self) -> str:
        if not self.stability_view:
            return "No stability data"

        return (
            f"Decision={self.decision} | "
            f"Stability={self.stability_view.stability_score:.2f} | "
            f"Risk={self.stability_view.risk_level:.2f} | "
            f"Regime={self.stability_view.regime}"
        )
