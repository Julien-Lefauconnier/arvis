# arvis/api/views/cognitive_result_view.py

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pprint import pformat
from typing import Any, cast

from arvis.adapters.kernel.timeline_from_signals import (
    signal_journal_to_timeline_snapshot,
)
from arvis.api.audit import AuditCommitmentPolicy
from arvis.api.commitment import (
    CommitmentInputs,
    CommitmentInputsValidationError,
    compose_global_commitment,
    validate_commitment_inputs,
)
from arvis.api.execution import ExecutionTraceView
from arvis.api.ir import build_ir_view
from arvis.api.stability import StabilityView
from arvis.api.timeline import TimelineView
from arvis.api.trace import DecisionTraceView
from arvis.api.version import API_FINGERPRINT, API_VERSION
from arvis.cognition.state.cognitive_state import CognitiveState
from arvis.errors.base import ArvisSecurityError
from arvis.reflexive.snapshot.reflexive_snapshot import ReflexiveSnapshot
from arvis.signals.signal_journal import SignalJournal


@dataclass(frozen=True)
class CognitiveResultView:
    decision: Any
    stability: Any
    stability_view: StabilityView | None
    trace: Any
    trace_view: DecisionTraceView | None = None
    timeline: Any | None = None
    timeline_view: TimelineView | None = None
    timeline_commitment: str | None = None
    global_commitment: str | None = None
    _ir: dict[str, Any] | None = None
    reflexive: dict[str, Any] | None = None
    execution_view: ExecutionTraceView | None = None
    # F-015: audit commitment accounting. Absence of a commitment is
    # never silent: applied policy, reason code when missing, and an
    # explicit degradation flag under the DEGRADED policy.
    commitment_policy: str | None = None
    commitment_reason: str | None = None
    commitment_degraded: bool = False

    @staticmethod
    def from_state(
        state: CognitiveState,
        result: Any,
        *,
        commitment_policy: AuditCommitmentPolicy = AuditCommitmentPolicy.DEGRADED,
        commitment_inputs: dict[str, Any] | None = None,
    ) -> CognitiveResultView:
        observability = getattr(result, "observability", None)
        execution = getattr(result, "execution", result)

        stability = (
            getattr(observability, "scientific", None)
            if observability is not None
            else getattr(result, "stability", None)
        )

        trace = getattr(result, "trace", None)
        timeline_journal = state.timeline

        ir_payload = build_ir_view(state)

        execution_state = getattr(execution, "execution_state", None)

        execution_view = (
            ExecutionTraceView.from_execution_state(execution_state)
            if execution_state is not None
            else None
        )

        # F-015: track why an audit commitment could not be produced.
        commitment_reason: str | None = None

        try:
            ir_bytes = json.dumps(
                ir_payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            ).encode("utf-8")
            ir_hash = sha256(ir_bytes).hexdigest()
        except (TypeError, ValueError):
            ir_hash = None
            commitment_reason = "ir_not_serializable"

        if ir_hash is not None:
            # F-013: detach the audit artifact at commitment time.
            # The stored IR is rebuilt from the exact hashed bytes,
            # so no upstream alias can diverge the payload from its
            # hash.
            ir_payload = json.loads(ir_bytes.decode("utf-8"))

        if not isinstance(timeline_journal, SignalJournal):
            timeline_snapshot = None
            timeline_commitment = None
            if commitment_reason is None:
                commitment_reason = "timeline_not_journal"
        else:
            timeline_snapshot = signal_journal_to_timeline_snapshot(timeline_journal)
            try:
                from arvis.timeline.timeline_commitment import (
                    TimelineCommitment,
                )

                commitment = TimelineCommitment.from_snapshot(timeline_snapshot)
                timeline_commitment = commitment.commitment
            except Exception:  # arvis-broad: defensive view enrichment
                timeline_commitment = None
                if commitment_reason is None:
                    commitment_reason = "timeline_commitment_failure"

        # F-007-a5: composed v2 commitment. Binds the cognitive IR, the
        # timeline, the redacted syscall journals, the registry manifest
        # fingerprint, the effective configuration and the active policy
        # tables (explicit named components, version embedded). The
        # non-cognitive components come from the caller: computed from
        # the live environment on a fresh run, reused verbatim from the
        # exported IR on replay (decision D-a).
        # P0-2-a6: the inputs block is strictly validated before any
        # composition, whether it comes from the live environment or
        # from a replayed export. A forged, incomplete or malformed
        # block never composes into a formally valid commitment; it
        # surfaces as an absent commitment with a dedicated reason and
        # the governed absence machinery applies (REQUIRED refuses).
        validated_inputs: CommitmentInputs | None = None
        if commitment_inputs is not None:
            try:
                validated_inputs = validate_commitment_inputs(commitment_inputs)
            except CommitmentInputsValidationError:
                validated_inputs = None
                if commitment_reason is None:
                    commitment_reason = "commitment_inputs_invalid"

        if timeline_commitment and ir_hash and validated_inputs is not None:
            try:
                global_commitment = compose_global_commitment(
                    ir_hash=ir_hash,
                    timeline_commitment=timeline_commitment,
                    commitment_inputs=validated_inputs,
                )
            except Exception:  # arvis-broad: defensive view enrichment
                global_commitment = None
                if commitment_reason is None:
                    commitment_reason = "commitment_hash_failure"
        else:
            global_commitment = None
            if (
                commitment_reason is None
                and timeline_commitment
                and ir_hash
                and validated_inputs is None
            ):
                commitment_reason = "commitment_inputs_unavailable"

        # F-015: the absence of an audit commitment is never silent.
        commitment_degraded = False
        if global_commitment is None:
            if commitment_reason is None:
                commitment_reason = "commitment_unavailable"
            if commitment_policy is AuditCommitmentPolicy.REQUIRED:
                raise ArvisSecurityError(
                    "audit commitment is required but missing "
                    f"(reason={commitment_reason})",
                    details={"reason": commitment_reason},
                )
            commitment_degraded = commitment_policy is AuditCommitmentPolicy.DEGRADED

        reflexive_payload = None
        try:
            from arvis.api.reflexive import get_reflexive_snapshot

            typed_get_snapshot = cast(
                Callable[[Any], ReflexiveSnapshot],
                get_reflexive_snapshot,
            )
            snapshot = typed_get_snapshot(state)
            reflexive_payload = snapshot.to_dict()
        except Exception:  # arvis-broad: optional reflexive enrichment
            reflexive_payload = None

        # D-a: the non-cognitive components ride in the exported IR as a
        # sibling block, outside the cognitively hashed sections (the
        # ir_hash was computed before this injection, and the IR
        # deserializer ignores unknown top-level keys), so a replay can
        # recompose the same commitment from the declared environment.
        if validated_inputs is not None and isinstance(ir_payload, dict):
            ir_payload = {
                **ir_payload,
                "commitment_inputs": validated_inputs.to_dict(),
            }

        return CognitiveResultView(
            decision=getattr(execution, "action_decision", None),
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
            execution_view=execution_view,
            commitment_policy=commitment_policy.value,
            commitment_reason=commitment_reason,
            commitment_degraded=commitment_degraded,
        )

    def to_dict(self) -> dict[str, Any]:
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
            "commitment_policy": self.commitment_policy,
            "commitment_reason": self.commitment_reason,
            "commitment_degraded": self.commitment_degraded,
            "trace": (self.trace_view.to_dict() if self.trace_view else None),
            "timeline": (self.timeline_view.to_dict() if self.timeline_view else None),
            "execution": (
                self.execution_view.to_dict()
                if self.execution_view is not None
                else None
            ),
        }

    def to_ir(self) -> dict[str, Any] | None:
        # F-013: export a defensive deep copy; mutating the export
        # can never diverge the view from its audit commitment.
        if self._ir is None:
            return None
        return copy.deepcopy(self._ir)

    @staticmethod
    def _public_status(*, allowed: bool, requires_validation: bool) -> str:
        """Tri-state public status.

        A confirmation-required decision is neither a clean pass nor a hard
        block: it is surfaced as REQUIRES_CONFIRMATION so the medium-risk band
        is visibly distinct from an outright ABSTAIN/BLOCK.
        """
        if allowed:
            return "ALLOWED"
        if requires_validation:
            return "REQUIRES_CONFIRMATION"
        return "BLOCKED"

    def quickstart_payload(self) -> dict[str, Any]:
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
            "status": self._public_status(
                allowed=allowed, requires_validation=requires_validation
            ),
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

        status = self._public_status(
            allowed=allowed, requires_validation=requires_validation
        )
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
