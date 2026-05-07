# arvis/adapters/llm/observability/math_utils.py

import math
from collections.abc import Sequence


def compute_entropy(logprobs: Sequence[float]) -> float | None:
    if not logprobs:
        return None

    probs = [math.exp(lp) for lp in logprobs if isinstance(lp, (int, float))]

    if not probs:
        return None
    total = sum(probs)

    if total <= 0:
        return None

    probs = [p / total for p in probs]

    return -sum(p * math.log(p) for p in probs if p > 0)


def compute_variance(logprobs: Sequence[float]) -> float | None:
    if not logprobs:
        return None

    probs = [math.exp(lp) for lp in logprobs if isinstance(lp, (int, float))]
    if not probs:
        return None
    total = sum(probs)

    if total <= 0:
        return None

    probs = [p / total for p in probs]

    mean = sum(probs) / len(probs)
    return sum((p - mean) ** 2 for p in probs) / len(probs)


def compute_confidence(logprobs: Sequence[float]) -> float | None:
    if not logprobs:
        return None

    probs = [math.exp(lp) for lp in logprobs if isinstance(lp, (int, float))]
    if not probs:
        return None
    total = sum(probs)

    if total <= 0:
        return None

    probs = [p / total for p in probs]

    return max(probs) if probs else None
