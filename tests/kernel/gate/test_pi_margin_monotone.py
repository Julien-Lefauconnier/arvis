# tests/kernel/gate/test_pi_margin_monotone.py
"""The certified projection margin acts monotonically on the Pi gate.

Campaign HARDEN (DM-H7, audit P1-10, 2026-09-02). The Pi layer
coerced an ABSENT margin to 0.0, and the gate treated margin == 0.0
(and residual >= 0.999) as "no certification": the WORST certified
state and the absent state were indistinguishable, and both switched
the layer off. Probed on the audit tree: margin 0.05 abstained,
0.001 required confirmation, 0.0 ALLOWED.

Fixed semantics:

- absence is typed (``safety_margin``/``projection_residual`` are
  ``float | None``), never a sentinel. A None margin is the DESIGNED
  absence of DM-F3 (the projection measures only dangerous bounds),
  so the layer stays neutral on it, explicitly, with the doctrine
  written where the None is produced;
- a CERTIFIED margin acts at face value: 0.0 is the worst certified
  state (hard zone), and the verdict never softens as the margin
  decreases anywhere on [0, 1] (the monotone pin below).
"""

from __future__ import annotations

from arvis.kernel.gate.pi_gate import PiBasedGate
from arvis.kernel.projection.pi_types import (
    PiState,
    QState,
    WState,
    XState,
    ZControlState,
    ZDecisionState,
    ZDynamicState,
    ZGateState,
    ZState,
)

_STRICTNESS = {"allow": 0, "require_confirmation": 1, "abstain": 2}


def _pi_state(margin: float | None) -> PiState:
    """A calm Pi state where the margin is the only pressure signal."""
    residual = None if margin is None else 1.0 - margin
    return PiState(
        x=XState(
            cognitive_load=0.1,
            coherence_score=0.9,
            conflict_pressure=0.0,
            uncertainty_mass=0.1,
            decision_commitment=0.8,
            memory_activation=0.2,
            symbolic_stability=0.9,
            retrieval_salience=0.3,
        ),
        z=ZState(
            decision=ZDecisionState(
                decision_kind="answer",
                actionability_score=0.8,
                confidence_score=0.9,
            ),
            gate=ZGateState(
                verdict="allow",
                safety_margin=margin,
                veto_intensity=0.0 if margin is None else 1.0 - margin,
                confirmation_required=False,
            ),
            control=ZControlState(
                control_mode="nominal",
                epsilon=0.1,
                beta=0.5,
                exploration_pressure=0.0,
            ),
            dynamics=ZDynamicState(
                regime="stable",
                temporal_pressure=0.0,
                recent_delta_norm=0.0,
                runtime_instability=0.0,
            ),
        ),
        q=QState(
            regime_mode="stable",
            gate_mode="allow",
            conversation_mode=None,
            execution_mode=None,
            switching_safe=True,
        ),
        w=WState(
            uncertainty_pressure=0.0,
            ambiguity_pressure=0.0,
            observation_gap=0.0,
            external_disturbance=0.0,
            projection_residual=residual,
            llm_risk_pressure=0.0,
        ),
    )


def _verdict(margin: float | None) -> str:
    result = PiBasedGate().evaluate(_pi_state(margin), bundle_id="probe")
    return str(result.verdict.value)


def test_the_worst_certified_margin_is_the_hardest_verdict() -> None:
    """The audit's probe, inverted: certified 0.0 must be at least as
    strict as every other certified margin, never ALLOW."""
    assert _verdict(0.0) != "allow"
    assert _STRICTNESS[_verdict(0.0)] >= _STRICTNESS[_verdict(0.05)]
    assert _STRICTNESS[_verdict(0.0)] >= _STRICTNESS[_verdict(0.001)]


def test_the_verdict_never_softens_as_the_certified_margin_decreases() -> None:
    margins = [round(0.05 * i, 2) for i in range(21)]  # 0.00 .. 1.00
    verdicts = [_STRICTNESS[_verdict(m)] for m in margins]
    for lower, higher in zip(verdicts, verdicts[1:], strict=False):
        assert lower >= higher, (
            f"verdict softened as the certified margin decreased: "
            f"{list(zip(margins, verdicts, strict=True))}"
        )


def test_designed_absence_stays_neutral_and_typed() -> None:
    """A None margin is DM-F3's designed absence (no dangerous bound
    in play): the layer passes the base verdict through, explicitly,
    instead of impersonating a certified 0.0."""
    assert _verdict(None) == "allow"


def test_the_builder_propagates_absence_as_none(ctx_with_ir) -> None:
    """The impl-side half of DM-H7: an absent margin source reaches
    the state as None, never coerced to 0.0 (the original defect)."""
    from arvis.kernel.projection.pi_impl import PiImpl

    ctx_with_ir.projection.margin = None
    for attr in ("projection_margin", "m_t"):
        if hasattr(ctx_with_ir, attr):
            setattr(ctx_with_ir, attr, None)
    state = PiImpl().project_structured(ctx_with_ir)
    assert state.z.gate.safety_margin is None
    assert state.w.projection_residual is None

    ctx_with_ir.projection.margin = 0.0
    state = PiImpl().project_structured(ctx_with_ir)
    assert state.z.gate.safety_margin == 0.0
    assert state.w.projection_residual == 1.0
