# arvis/conversation/conversation_orchestrator.py

import logging
from typing import cast

from arvis.conversation.act_strategy_mapper import map_act_to_strategy
from arvis.conversation.conversation_adaptive_controller import (
    ConversationAdaptiveController,
    _StateProtocol,
)
from arvis.conversation.conversation_adversarial_detector import (
    ConversationAdversarialDetector,
)
from arvis.conversation.conversation_attractor_model import ConversationAttractorModel
from arvis.conversation.conversation_cognitive_bridge import (
    ConversationCognitiveBridge,
    _ConversationContextProtocol,
)
from arvis.conversation.conversation_coherence_metric import ConversationCoherenceMetric
from arvis.conversation.conversation_collapse_guard import ConversationCollapseGuard
from arvis.conversation.conversation_context import ConversationContext
from arvis.conversation.conversation_entropy_regulator import (
    ConversationEntropyRegulator,
)
from arvis.conversation.conversation_feedback_signal import ConversationFeedbackSignal
from arvis.conversation.conversation_future_simulator import ConversationFutureSimulator
from arvis.conversation.conversation_global_stability_adapter import (
    ConversationGlobalStabilityAdapter,
)
from arvis.conversation.conversation_lyapunov_adapter import ConversationLyapunovAdapter
from arvis.conversation.conversation_memory_bridge import ConversationMemoryBridge
from arvis.conversation.conversation_policy_engine import ConversationPolicyEngine
from arvis.conversation.conversation_predictive_strategy import (
    ConversationPredictiveStrategy,
)
from arvis.conversation.conversation_regime_controller import (
    ConversationRegimeController,
)
from arvis.conversation.conversation_stability_controller import (
    ConversationStabilityController,
)
from arvis.conversation.conversation_stability_signals import (
    ConversationStabilitySignalsBuilder,
)
from arvis.conversation.conversation_strategy_dynamics import (
    ConversationStrategyDynamics,
)
from arvis.conversation.conversation_trajectory_controller import (
    ConversationTrajectoryController,
)
from arvis.conversation.conversation_world_prediction_bridge import (
    ConversationWorldPredictionBridge,
)
from arvis.conversation.response_plan import ResponsePlan
from arvis.conversation.response_plan_builder import ResponsePlanBuilder
from arvis.conversation.response_strategy_decision import ResponseStrategyDecision
from arvis.conversation.response_strategy_resolver import ResponseStrategyResolver
from arvis.conversation.response_strategy_type import ResponseStrategyType
from arvis.linguistic.acts.gate_mapping import map_gate_verdict_to_act

_log = logging.getLogger(__name__)


class ConversationOrchestrator:
    """
    High-level orchestration of the conversational pipeline.
    """

    @staticmethod
    def _apply_feedback(context: ConversationContext) -> None:
        """
        Apply feedback loop in a ZKCS-safe way.

        Guarantees:
        - always produces feedback (even empty)
        - never breaks pipeline
        - no payload access
        """
        try:
            feedback = ConversationFeedbackSignal.build(context.state) or {}
            context.state.signals["feedback"] = feedback
            ConversationAdaptiveController.adapt(cast(_StateProtocol, context.state))
        except Exception:
            pass

    @staticmethod
    def process(context: ConversationContext) -> ResponsePlan:
        gate_verdict = context.gate_verdict
        if gate_verdict is None:
            raise RuntimeError("ConversationContext.gate_verdict is required")

        # Bridge conversation with cognitive engine
        cognitive_snapshot = ConversationCognitiveBridge.evaluate(
            cast(_ConversationContextProtocol, context)
        )

        # Optional control state propagation (ARVIS full pipeline)
        if getattr(context, "control_state", None):
            try:
                context.state.cognitive_snapshot = context.control_state
            except Exception:
                pass

        # Ensure snapshot is accessible from state
        context.state.cognitive_snapshot = cognitive_snapshot

        ConversationWorldPredictionBridge.inject(
            context,
            cognitive_snapshot,
        )

        # --------------------------------------------
        # MEMORY INJECTION (ZKCS-safe)
        # --------------------------------------------
        ConversationMemoryBridge.inject(context)

        # --------------------------------------------
        # USER ADAPTIVE PROFILE INJECTION
        # --------------------------------------------
        if getattr(context, "user_profile", None):
            context.state.user_profile = context.user_profile

        # --------------------------------------------
        # STEP 1 — Derive linguistic act from cognition
        # --------------------------------------------
        act = context.act or map_gate_verdict_to_act(
            verdict=gate_verdict,
            has_decision=context.has_decision,
        )

        context.act = act

        # --------------------------------------------
        # STEP 2 — Base strategy from act
        # --------------------------------------------
        base_strategy = map_act_to_strategy(act.act_type)

        # --------------------------------------------
        # STEP 3 — Strategy refinement via resolver
        # --------------------------------------------
        decision = ResponseStrategyResolver.resolve(
            gate_verdict=gate_verdict,
            has_decision=context.has_decision,
            state=context.state,
            intent_type=context.intent_type,
        )

        strategy = decision.strategy or base_strategy

        _log.info(
            {
                "msg": "conversation.strategy.after_resolver",
                "strategy": strategy.value,
                "intent": context.intent_type,
            }
        )

        # --------------------------------------------
        # STEP FINAL — Memory write hook (safe minimal)
        # --------------------------------------------
        hook = context.memory_write_hook
        if hook is not None:
            try:
                hook(
                    context=context,
                    strategy=strategy,
                )
            except Exception:
                _log.warning("memory_write_hook.failed", exc_info=True)

        # ------------------------------------------------
        # SAFE FALLBACK MODE
        # ------------------------------------------------
        no_cognitive_signals = cognitive_snapshot is None
        if no_cognitive_signals:
            strategy = ConversationPolicyEngine.apply_policy(
                proposed_strategy=strategy,
                state=context.state,
            )
            context.state.update_strategy(strategy, collapse_risk=None)

            decision_for_plan = ResponseStrategyDecision(
                strategy=strategy,
                reason=decision.reason,
                confidence=decision.confidence,
                signals=decision.signals,
            )

            ConversationOrchestrator._apply_feedback(context)

            _log.info(
                {
                    "msg": "conversation.strategy.fallback",
                    "strategy": strategy.value,
                }
            )

            return ResponsePlanBuilder.build(decision_for_plan)

        # Apply predictive strategy adjustment
        strategy = ConversationPredictiveStrategy.choose(
            strategy,
            context.state,
        )

        # Apply temporal dynamics
        strategy = ConversationStrategyDynamics.apply(
            proposed_strategy=strategy,
            state=context.state,
        )

        # Update mathematical stability signals
        signals_builder = ConversationStabilitySignalsBuilder()
        signals_builder.update(context.state)

        # Apply mathematical stability control
        stability = ConversationStabilityController()

        lyapunov_verdict = ConversationLyapunovAdapter.extract_verdict(context.state)

        global_verdict = ConversationGlobalStabilityAdapter.extract_verdict(
            context.state
        )

        # Collapse prevention
        if ConversationCollapseGuard.detect(context.state):
            strategy = ResponseStrategyType.ABSTENTION

        strategy = stability.stabilize(
            proposed_strategy=strategy,
            state=context.state,
            lyapunov_verdict=lyapunov_verdict,
            global_stability_verdict=global_verdict,
        )

        # Apply policy stabilization
        strategy = ConversationPolicyEngine.apply_policy(
            proposed_strategy=strategy,
            state=context.state,
        )

        # Apply cognitive regime regulation
        collapse_risk = context.state.signals.get("collapse_risk")
        uncertainty = context.state.signals.get("uncertainty")

        world = context.state.world_prediction

        strategy = ConversationRegimeController.regulate(
            proposed_strategy=strategy,
            collapse_risk=collapse_risk,
            uncertainty=uncertainty,
            world_regime=getattr(world, "regime", None) if world else None,
            early_warning=getattr(world, "early_warning", None) if world else None,
            state=context.state,
        )

        _log.info(
            {
                "msg": "conversation.strategy.after_regime",
                "strategy": strategy.value,
                "collapse_risk": collapse_risk,
                "uncertainty": uncertainty,
            }
        )

        strategy = ConversationFutureSimulator.simulate(
            strategy=strategy,
            collapse_risk=collapse_risk,
            uncertainty=uncertainty,
        )

        adversarial_score = ConversationAdversarialDetector.detect(
            prompt=context.prompt,
            collapse_risk=collapse_risk,
            uncertainty=uncertainty,
        )

        strategy = ConversationAdversarialDetector.regulate(
            strategy=strategy,
            adversarial_score=adversarial_score,
        )

        coherence = ConversationCoherenceMetric.compute(context.state)
        context.state.signals["coherence"] = coherence

        strategy = ConversationTrajectoryController.regulate(
            proposed_strategy=strategy,
            state=context.state,
        )

        strategy = ConversationAttractorModel.attract(
            strategy=strategy,
            uncertainty=context.state.signals.get("uncertainty"),
            coherence=context.state.signals.get("coherence"),
            state=context.state,
        )

        strategy = ConversationEntropyRegulator.regulate(
            strategy=strategy,
            state=context.state,
        )

        if (
            decision.strategy == ResponseStrategyType.INFORMATIONAL
            and not context.has_decision
        ):
            strategy = ResponseStrategyType.INFORMATIONAL

        context.state.update_strategy(
            strategy,
            collapse_risk=collapse_risk,
        )

        decision_for_plan = ResponseStrategyDecision(
            strategy=strategy,
            reason=decision.reason,
            confidence=decision.confidence,
            signals=decision.signals,
        )

        _log.info(
            {
                "msg": "conversation.strategy.final",
                "strategy": strategy.value,
            }
        )

        ConversationOrchestrator._apply_feedback(context)

        return ResponsePlanBuilder.build(decision_for_plan)
