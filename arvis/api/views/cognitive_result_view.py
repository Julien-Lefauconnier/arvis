# arvis/api/views/cognitive_result_view.py

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from pprint import pformat
from typing import Any, cast

from arvis.action.action_decision import ActionDecision
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
from arvis.api.contracts.result_schema import RESULT_SCHEMA_VERSION
from arvis.api.execution import ExecutionTraceView
from arvis.api.ir import build_ir_view
from arvis.api.stability import StabilityView
from arvis.api.timeline import TimelineView
from arvis.api.trace import DecisionTraceView
from arvis.api.version import API_FINGERPRINT, API_VERSION
from arvis.api.views.decision_status import DecisionStatus
from arvis.cognition.state.cognitive_state import CognitiveState
from arvis.errors.base import ArvisSecurityError
from arvis.reflexive.snapshot.reflexive_snapshot import ReflexiveSnapshot
from arvis.signals.signal_journal import SignalJournal


@dataclass(frozen=True)
class CognitiveResultView:
    """Public result of a governed run (beta contract).

    The public decision contract is :attr:`status` (typed) and the
    structured ``decision`` block of :meth:`to_dict`; ``decision``
    itself carries the rich kernel object. ``stability`` and ``trace``
    are deliberately ``Any``: heterogeneous internal enrichment
    channels, surfaced through their typed ``*_view`` companions.
    """

    decision: ActionDecision | None
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
    # a17 (audit a16, blocker 1): the applied policy is part of the
    # serialized contract; a view carrying an unknown commitment policy
    # cannot exist (see __post_init__). Other fields rely on their type
    # annotations; the full schema is enforced by the contract tests.
    commitment_policy: str = AuditCommitmentPolicy.DEGRADED.value
    commitment_reason: str | None = None
    commitment_degraded: bool = False
    # Opaque cross-turn state (DM-F3): a host feeds this blob back as
    # extra["scientific_state"] on the next turn so the monitor keeps
    # its trajectory. Deliberately absent from to_dict(): it is host
    # plumbing, not part of the serialized decision contract.
    next_scientific_state: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Contract invariants at construction (a17): the serialized
        schema is closed over commitment_policy, so an out-of-contract
        view must be impossible to build, not merely untested."""
        valid = {policy.value for policy in AuditCommitmentPolicy}
        if self.commitment_policy not in valid:
            raise ValueError(
                "commitment_policy must be one of "
                f"{sorted(valid)}, got {self.commitment_policy!r}"
            )

    @staticmethod
    def from_state(
        state: CognitiveState,
        result: Any,
        *,
        commitment_policy: AuditCommitmentPolicy = AuditCommitmentPolicy.DEGRADED,
        commitment_inputs: dict[str, Any] | None = None,
        commitment_inputs_reason: str | None = None,
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
                allow_nan=False,
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
                # P0-1-a6: the caller can name why the inputs are
                # unavailable (audit_incomplete: an effect happened
                # whose result could not be journaled and paired).
                commitment_reason = (
                    commitment_inputs_reason or "commitment_inputs_unavailable"
                )

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
            stability_view=_stability_view_or_none(stability),
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
            next_scientific_state=(
                getattr(observability, "next_scientific_state", None)
                if observability is not None
                else None
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": RESULT_SCHEMA_VERSION,
            "version": API_VERSION,
            "fingerprint": API_FINGERPRINT,
            "decision": self._decision_block(),
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
            "audit_incomplete": self.commitment_reason == "audit_incomplete",
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

    @property
    def status(self) -> DecisionStatus:
        """Typed public verdict of the run (beta contract, a15)."""
        return DecisionStatus.from_decision(self.decision)

    def _decision_block(self) -> dict[str, Any]:
        """Structured public decision, never a repr (A14-BETA-02)."""
        decision = self.decision
        if decision is None:
            return {
                "status": DecisionStatus.NONE.value,
                "allowed": None,
                "requires_user_validation": None,
                "denied_reason": None,
            }
        return {
            "status": self.status.value,
            "allowed": bool(getattr(decision, "allowed", False)),
            "requires_user_validation": bool(
                getattr(decision, "requires_user_validation", False)
            ),
            "denied_reason": getattr(decision, "denied_reason", None),
        }

    def quickstart_payload(self) -> dict[str, Any]:
        """
        Compact structured payload intended for examples,
        onboarding, demos, and README snippets.
        """
        decision = self.decision

        requires_validation = bool(getattr(decision, "requires_user_validation", False))
        denied_reason = getattr(decision, "denied_reason", None)

        return {
            "version": API_VERSION,
            "status": self.status.value,
            "approval_required": requires_validation,
            "reason": denied_reason,
            "has_trace": self.trace_view is not None,
            "has_timeline": self.timeline_view is not None,
            "commitment": self.global_commitment,
        }

    def to_json(self, *, indent: int = 2) -> str:
        """Stable JSON serialization of public structured output.

        Strict JSON (b1, audit a17, 13.1): a non-finite float would
        serialize as NaN/Infinity, which are not valid JSON numbers;
        this fails loudly instead of emitting an out-of-contract
        document.
        """
        return json.dumps(
            self.to_dict(),
            indent=indent,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
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

        requires_validation = bool(getattr(decision, "requires_user_validation", False))
        denied_reason = getattr(decision, "denied_reason", None) or "-"

        status = self.status.value
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

    def _declared_input_risk(self) -> float | None:
        """The caller-declared risk scalar of this run, when there was one.

        Read from the exported IR's input block: it is an INPUT the
        caller asserted (and the input-risk gate graded), not a measured
        stability quantity, and the summary labels it accordingly.
        """
        ir = self._ir
        if not isinstance(ir, dict):
            return None
        input_block = ir.get("input")
        if not isinstance(input_block, dict):
            return None
        metadata = input_block.get("metadata")
        if not isinstance(metadata, dict):
            return None
        value = metadata.get("risk")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        return float(value)

    def summary(self) -> str:
        # An axis the run did not measure prints as n/a; zeros here used
        # to be fabricated defaults (audit C5, 2026-08). The declared
        # input risk, when the run was gated on one, is shown under its
        # own honest label.
        def _fmt(value: float | None) -> str:
            return f"{value:.2f}" if value is not None else "n/a"

        view = self.stability_view
        parts = [f"Decision={self.decision}"]
        if view is not None:
            parts.append(f"Stability={_fmt(view.stability_score)}")
            parts.append(f"Risk={_fmt(view.risk_level)}")
            parts.append(f"Regime={view.regime if view.regime is not None else 'n/a'}")
        else:
            parts.append("Stability=n/a | Risk=n/a | Regime=n/a")

        declared = self._declared_input_risk()
        if declared is not None:
            parts.append(f"DeclaredRisk={declared:.2f}")

        return " | ".join(parts)


def _stability_view_or_none(stability: Any) -> StabilityView | None:
    """Build the stability view, or report honest absence.

    A run that measured nothing (opt-out core model, or a snapshot with
    no conclusion) yields no view at all rather than a view of Nones:
    downstream consumers can rely on ``stability_view is None`` meaning
    "this run carried no stability assessment" (campaign MATH-A, M1).
    """
    if not stability:
        return None
    view = StabilityView.from_snapshot(stability)
    if view.stability_score is None and view.risk_level is None and view.regime is None:
        return None
    return view
