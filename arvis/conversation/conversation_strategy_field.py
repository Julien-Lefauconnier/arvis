# arvis/conversation/conversation_strategy_field.py

from dataclasses import dataclass
from typing import Dict

from arvis.conversation.response_strategy_type import (
    ResponseStrategyType,
)


@dataclass
class StrategyField:
    distribution: Dict[ResponseStrategyType, float]

    @staticmethod
    def uniform() -> "StrategyField":
        strategies = list(ResponseStrategyType)
        p = 1.0 / len(strategies)

        return StrategyField(distribution={s: p for s in strategies})

    def update(
        self,
        target: ResponseStrategyType,
        *,
        alpha: float = 0.2,
        collapse_risk: float | None = None,
    ) -> None:
        # Adapt alpha using stability signal
        if collapse_risk is not None:
            try:
                alpha = max(
                    0.05,
                    min(
                        0.4,
                        0.25 * (1.0 - float(collapse_risk)),
                    ),
                )
            except Exception:
                pass

        for s in self.distribution:
            target_val = 1.0 if s == target else 0.0

            self.distribution[s] = (1 - alpha) * self.distribution[
                s
            ] + alpha * target_val

        self._normalize()

    def best(self) -> ResponseStrategyType:
        return max(
            self.distribution.items(),
            key=lambda item: item[1],
        )[0]

    def _normalize(self) -> None:
        total = sum(self.distribution.values())

        if total <= 0:
            return

        for s in self.distribution:
            self.distribution[s] /= total
