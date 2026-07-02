# arvis/kernel/pipeline/stages/gate/input_risk_gate.py
"""
Gate layer for explicit risk-scalar inputs.

Applied once, near the end of the action-path gate composition (immediately
before confirmation flags are synced), so the resulting verdict propagates
correctly to execution.

Behaviour:
- No explicit top-level risk in the input -> verdict unchanged (the common
  case; structured/observational turns are unaffected).
- A real safety veto already fired (kappa / adaptive instability) -> the
  incoming verdict is kept. The input-risk policy never relaxes a real veto.
- Otherwise the governed input-risk policy determines the verdict (low ->
  ALLOW, medium -> REQUIRE_CONFIRMATION, high -> ABSTAIN). This makes a pure
  risk assertion gradeable instead of being dominated by the sparse-projection
  fail-closed.

When the policy governs the decision, it supersedes the sparse-projection
artifact: projection-derived veto reasons (which are an artifact of running the
kernel projection on a contentless risk scalar) are dropped and a single
governing reason ("input_risk_gate") is recorded, so the emitted IR stays
consistent with the verdict.
"""

from __future__ import annotations

from typing import Any

from arvis.errors.manager import ErrorManager
from arvis.kernel.gate.input_risk import read_input_risk, resolve_input_risk_verdict
from arvis.kernel.pipeline.stages.gate.trace_helpers import record_verdict_transition
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict

_VERDICT_BY_NAME: dict[str, LyapunovVerdict] = {
    "allow": LyapunovVerdict.ALLOW,
    "require_confirmation": LyapunovVerdict.REQUIRE_CONFIRMATION,
    "abstain": LyapunovVerdict.ABSTAIN,
}

# Real safety vetoes the input-risk policy must never relax.
_REAL_SAFETY_VETOES: frozenset[str] = frozenset(
    {"kappa_violation", "adaptive_instability_veto"}
)

# Projection-derived reasons superseded when the input-risk policy governs.
# These are an artifact of running the kernel projection on a contentless risk
# scalar and are inconsistent with a policy-governed ALLOW.
_PROJECTION_ARTIFACT_REASONS: frozenset[str] = frozenset(
    {
        "projection_invalid",
        "projection_boundary",
        "projection_unsafe",
        "projection_lyapunov_incompatible",
    }
)

_GOVERNING_REASON = "input_risk_gate"


def apply_input_risk_gate(ctx: Any, verdict: LyapunovVerdict) -> LyapunovVerdict:
    try:
        risk = read_input_risk(getattr(ctx, "cognitive_input", None))
        if risk is None:
            return verdict

        extra = getattr(ctx, "extra", None)
        if not isinstance(extra, dict):
            # Without a mutable extra we cannot keep the IR consistent, so stay
            # conservative and leave the verdict untouched.
            return verdict

        extra["input_risk"] = risk

        fusion_reasons = extra.get("fusion_reasons")
        current_reasons = fusion_reasons if isinstance(fusion_reasons, list) else []

        # Never relax a real safety veto (kappa / adaptive instability).
        if extra.get("kappa_hard_block") or any(
            reason in _REAL_SAFETY_VETOES for reason in current_reasons
        ):
            return verdict

        risk_verdict = _VERDICT_BY_NAME[resolve_input_risk_verdict(risk)]

        if risk_verdict != verdict:
            record_verdict_transition(
                ctx,
                stage=_GOVERNING_REASON,
                before=verdict,
                after=risk_verdict,
                reason="input_risk_policy",
            )

        # The policy governs: supersede the projection artifact and record a
        # single governing reason so the IR stays consistent with the verdict.
        superseded = [
            reason
            for reason in current_reasons
            if reason not in _PROJECTION_ARTIFACT_REASONS
        ]
        if _GOVERNING_REASON not in superseded:
            superseded.append(_GOVERNING_REASON)
        extra["fusion_reasons"] = superseded

        return risk_verdict

    except Exception as exc:
        ErrorManager.capture_exception(
            ctx,
            exc,
            code="input_risk_gate_failure",
        )
        return verdict


__all__ = ["apply_input_risk_gate"]
