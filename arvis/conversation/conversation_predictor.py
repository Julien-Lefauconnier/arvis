# arvis/conversation/conversation_predictor.py

from arvis.conversation.response_strategy_type import (
    ResponseStrategyType,
)

from arvis.conversation.conversation_energy_model import (
    ConversationEnergyModel,
)


class ConversationPredictor:
    """
    Lightweight predictive controller for conversation strategies.

    It evaluates possible strategies and selects the one expected
    to minimize conversational instability.
    """

    @staticmethod
    def choose_strategy(
        *,
        proposed_strategy: ResponseStrategyType,
        collapse_risk: float | None,
        uncertainty: float | None,
    ) -> ResponseStrategyType:

        base_energy = ConversationEnergyModel.compute_energy(
            collapse_risk=collapse_risk,
            uncertainty=uncertainty,
            temporal_pressure=None,
        )

        # If conversation is stable, keep original strategy
        if base_energy < 0.3:
            return proposed_strategy

        candidates = [
            proposed_strategy,
            ResponseStrategyType.CONFIRMATION,
            ResponseStrategyType.ABSTENTION,
        ]

        best_strategy = proposed_strategy
        best_energy = base_energy

        for strategy in candidates:

            predicted_energy = ConversationPredictor._predict_energy(
                strategy=strategy,
                energy=base_energy,
            )

            if predicted_energy < best_energy:
                best_energy = predicted_energy
                best_strategy = strategy

        return best_strategy

    @staticmethod
    def _predict_energy(
        *,
        strategy: ResponseStrategyType,
        energy: float,
    ) -> float:

        if strategy == ResponseStrategyType.ABSTENTION:
            return energy * 0.2

        if strategy == ResponseStrategyType.CONFIRMATION:
            return energy * 0.5

        return energy