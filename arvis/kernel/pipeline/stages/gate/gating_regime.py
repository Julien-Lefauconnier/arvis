# arvis/kernel/pipeline/stages/gate/gating_regime.py
"""
Gating regime selection.

The gate decision stack (validity, projection, kappa, global stability,
adaptive veto, memory policy, pi-gate) governs the safe EXECUTION of actions.
A purely informational/conversational turn proposes no action to execute, so
it must not be governed by that machinery: it is routed to the lighter ANSWER
regime instead.

This module is the single source of truth for the ACTION vs ANSWER
distinction. It is keyed on the existing cognitive taxonomy (surface_kind,
decision_kind, proposed_actions) and is fail-safe: any turn not positively
classified as answer-only stays in the ACTION regime, where the full
execution-safety stack applies unchanged.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from arvis.kernel.pipeline.stages.gate.trace_helpers import record_verdict_transition
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict

# Decision kinds that, absent any proposed action, describe a turn that only
# produces an answer (nothing to execute).
_ANSWER_DECISION_KINDS: frozenset[str] = frozenset({"informational", "conversational"})


class GatingRegime(StrEnum):
    """Which gating policy governs a turn."""

    ACTION = "action"
    ANSWER = "answer"


def select_gating_regime(ctx: Any) -> GatingRegime:
    """
    Select the gating regime for the current turn.

    Returns ANSWER only when the turn is positively classified as answer-only:
    a linguistic surface, an informational/conversational decision, and no
    proposed action. Every other case (including unclassified turns) falls back
    to ACTION, so the execution-safety stack is never silently skipped.
    """
    ir_decision = getattr(getattr(ctx, "decision_layer", None), "ir_decision", None)
    decision_kind = getattr(ir_decision, "decision_kind", None)
    proposed_actions = getattr(ir_decision, "proposed_actions", None) or []
    surface_kind = getattr(getattr(ctx, "ir_input", None), "surface_kind", None)

    is_answer_only = (
        surface_kind == "linguistic"
        and decision_kind in _ANSWER_DECISION_KINDS
        and not proposed_actions
    )
    return GatingRegime.ANSWER if is_answer_only else GatingRegime.ACTION


def apply_answer_gate(ctx: Any, *, verdict: LyapunovVerdict) -> LyapunovVerdict:
    """
    Answer-regime gate.

    Producing an answer is not an action execution, so the answer gate allows
    the turn. The stability assessment computed upstream is preserved for
    observability; it simply does not gate the answer.

    This is the extension point for any future conversational gating (e.g.
    conversational-coherence or content-governance checks): such checks belong
    here, in one place, rather than scattered across the action enforcement
    layers.
    """
    decided = LyapunovVerdict.ALLOW
    if decided != verdict:
        record_verdict_transition(
            ctx,
            stage="answer_gate",
            before=verdict,
            after=decided,
            reason="answer_regime",
        )
    return decided
