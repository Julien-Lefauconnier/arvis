# arvis/kernel/pipeline/stages/gate/input_risk_gate.py
"""
Gate layer for explicit risk-scalar inputs.

Applied once, near the end of the action-path gate composition (immediately
before confirmation flags are synced), so the resulting verdict propagates
correctly to execution.

Behaviour:
- No explicit top-level risk in the input -> verdict unchanged (the common
  case; structured/observational turns are unaffected).
- A real safety veto already fired (kappa / adaptive instability, or any
  traced hardening whose provenance is outside the sparse-projection
  artifact set) -> the incoming verdict is kept. The input-risk policy
  never relaxes a real veto (audit F-006), and an exception inside the
  gate forces ABSTAIN (fail-closed).
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
from arvis.kernel.pipeline.stages.gate.trace_helpers import (
    record_verdict_transition,
    verdict_provenance,
)
from arvis.math.lyapunov.lyapunov_gate import LyapunovVerdict
from arvis.math.lyapunov.verdict_order import is_relaxation

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

# Provenance stages whose hardening the policy may supersede when it
# governs a pure risk scalar: sparse-projection artifacts and the
# validity envelope they invalidate. A verdict hardened by any other
# stage (memory, global policy, pi, kappa, adaptive, fail-closed paths)
# is a real veto and is never relaxed (audit F-006).
_RELAXABLE_PROVENANCE: frozenset[str] = frozenset(
    {
        "projection_hard_block",
        "projection_lyapunov_enforcement",
        "projection_boundary_enforcement",
        "projection_unsafe_soft",
        "validity_envelope_enforcement",
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

        if is_relaxation(verdict, risk_verdict):
            provenance = verdict_provenance(ctx, verdict)
            if provenance is not None and provenance not in _RELAXABLE_PROVENANCE:
                # A real veto (traced provenance outside the artifact
                # set) is never relaxed by a declared input risk.
                record_verdict_transition(
                    ctx,
                    stage="input_risk_relax_denied",
                    before=verdict,
                    after=verdict,
                    reason="verdict_provenance_not_artifact",
                )
                return verdict

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
        # F-002: a failing guarantee mechanism can never relax; an
        # exception inside the gate forces ABSTAIN (fail-closed).
        record_verdict_transition(
            ctx,
            stage="input_risk_fail_closed",
            before=verdict,
            after=LyapunovVerdict.ABSTAIN,
            reason="gate_exception",
        )
        return LyapunovVerdict.ABSTAIN


__all__ = ["apply_input_risk_gate"]
