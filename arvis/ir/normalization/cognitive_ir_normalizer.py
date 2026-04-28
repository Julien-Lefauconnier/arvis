# arvis/ir/normalization/cognitive_ir_normalizer.py

from __future__ import annotations

from arvis.ir.cognitive_ir import CognitiveIR
from arvis.ir.gate import CognitiveGateIR
from arvis.ir.decision import CognitiveDecisionIR


class CognitiveIRNormalizer:
    @classmethod
    def normalize(cls, ir: CognitiveIR) -> CognitiveIR:
        """
        Return a canonical version of the IR (sorted, stable, deterministic).
        """

        # -------------------------
        # Gate normalization
        # -------------------------
        gate = ir.gate

        normalized_gate: CognitiveGateIR | None = None
        if gate is not None:
            normalized_gate = CognitiveGateIR(
                verdict=gate.verdict,
                bundle_id=gate.bundle_id,
                reason_codes=tuple(sorted(gate.reason_codes)),
                decision_trace=gate.decision_trace,  # preserve (normative trace)
            )

        # -------------------------
        # Decision normalization
        # -------------------------
        decision = ir.decision

        normalized_decision: CognitiveDecisionIR | None = None
        if decision is not None:
            normalized_decision = CognitiveDecisionIR(
                decision_id=decision.decision_id,
                decision_kind=decision.decision_kind,
                memory_intent=decision.memory_intent,
                reason_codes=tuple(sorted(decision.reason_codes)),
                proposed_actions=tuple(
                    sorted(decision.proposed_actions, key=lambda a: a.action_id)
                ),
                gaps=tuple(
                    sorted(decision.gaps, key=lambda g: (g.gap_type, g.severity))
                ),
                conflicts=tuple(
                    sorted(
                        decision.conflicts, key=lambda c: (c.conflict_type, c.severity)
                    )
                ),
                reasoning_intents=tuple(sorted(decision.reasoning_intents)),
                uncertainty_frames=tuple(
                    sorted(decision.uncertainty_frames, key=lambda u: u.axis)
                ),
                knowledge=decision.knowledge,
                context_hints=dict(sorted(decision.context_hints.items())),
            )

        # -------------------------
        # Projection normalization (NEW - NORMATIVE)
        # -------------------------
        projection = ir.projection

        normalized_projection = None
        if projection is not None:
            # ⚠️ pour l’instant pass-through (safe)
            # on ajoutera une normalisation stricte avec la Projection Spec
            normalized_projection = projection

        # -------------------------
        # Validity normalization (NEW - NORMATIVE)
        # -------------------------
        validity = ir.validity

        normalized_validity = None
        if validity is not None:
            # ⚠️ pass-through pour l’instant
            normalized_validity = validity

        # -------------------------
        # Return new IR
        # -------------------------
        return CognitiveIR(
            input=ir.input,
            context=ir.context,
            decision=normalized_decision,
            state=ir.state,
            gate=normalized_gate,
            stability=ir.stability,
            adaptive=ir.adaptive,
            projection=normalized_projection,
            validity=normalized_validity,
        )
