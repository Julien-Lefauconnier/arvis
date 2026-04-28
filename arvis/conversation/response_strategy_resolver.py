# arvis/conversation/response_strategy_resolver.py

from arvis.conversation.response_strategy_decision import ResponseStrategyDecision
from arvis.conversation.response_strategy_type import ResponseStrategyType
from arvis.conversation.conversation_state import ConversationState

from arvis.cognition.gate.cognitive_gate_verdict import CognitiveGateVerdict


class ResponseStrategyResolver:
    """
    Determines the high-level conversational strategy.

    This component translates cognitive signals into a response strategy.
    It does NOT generate text and does NOT call the LLM.
    """

    @staticmethod
    def _resolve_memory_guard(
        *,
        state: ConversationState | None,
        has_decision: bool,
    ) -> ResponseStrategyDecision | None:
        """
        Early COS memory guard.

        If long-memory declarative constraints are present, the resolver
        can downgrade risky ACTION strategies before later policy layers.
        """
        if state is None:
            return None

        signals = state.signals or {}

        if has_decision and signals.get("has_constraints"):
            return ResponseStrategyDecision(
                strategy=ResponseStrategyType.CONFIRMATION,
                reason="memory_constraints_require_confirmation",
                signals=dict(signals),
            )

        return None

    @staticmethod
    def resolve(
        *,
        gate_verdict: CognitiveGateVerdict,
        has_decision: bool,
        intent_type: str | None = None,
        state: ConversationState | None = None,
    ) -> ResponseStrategyDecision:
        """
        Resolve the conversational response strategy.

        Parameters
        ----------
        gate_verdict:
            Result of the cognitive gate evaluation.

        has_decision:
            Indicates whether a decision/action exists.

        intent_type:
            Optional intent classification hint.
        """

        memory_guard = ResponseStrategyResolver._resolve_memory_guard(
            state=state,
            has_decision=has_decision,
        )

        if memory_guard is not None:
            return memory_guard

        signals = {
            "gate_verdict": gate_verdict.value,
            "has_decision": has_decision,
            "intent_type": intent_type,
        }

        # Abstention
        if gate_verdict == CognitiveGateVerdict.ABSTAIN:
            return ResponseStrategyDecision(
                strategy=ResponseStrategyType.ABSTENTION,
                reason="cognitive_abstention",
                signals=signals,
            )

        # Confirmation required
        if gate_verdict == CognitiveGateVerdict.REQUIRE_CONFIRMATION:
            # -------------------------------------------------
            # Conversational questions should not be blocked
            # by confirmation unless an action is requested
            # -------------------------------------------------
            # Conversational questions should always be informational
            if intent_type in ("question_general", "conversation"):
                return ResponseStrategyDecision(
                    strategy=ResponseStrategyType.INFORMATIONAL,
                    reason="informational_question",
                    signals=signals,
                )
            return ResponseStrategyDecision(
                strategy=ResponseStrategyType.CONFIRMATION,
                reason="confirmation_required",
                signals=signals,
            )

        # -------------------------------------------------
        # SOCIAL CONVERSATION (greetings, acknowledgements)
        # -------------------------------------------------
        if intent_type == "conversation":
            return ResponseStrategyDecision(
                strategy=ResponseStrategyType.SOCIAL,
                reason="social_conversation",
                signals=signals,
            )

        # Decision/action strategy
        if has_decision:
            return ResponseStrategyDecision(
                strategy=ResponseStrategyType.ACTION,
                reason="action_decision_present",
                signals=signals,
            )

        # Informational strategy (default)
        return ResponseStrategyDecision(
            strategy=ResponseStrategyType.INFORMATIONAL,
            reason="informational_response",
            signals=signals,
        )
