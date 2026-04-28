# tests/kernel/test_kernel_invariants_full.py

import pytest

from arvis.kernel.kernel_invariants import assert_kernel_invariants


# -----------------------------
# Dummy bundle
# -----------------------------


class Bundle:
    def __init__(self, stability_score, reasoning_gap=None, reasoning_intent=None):
        self.stability_score = stability_score
        self.reasoning_gap = reasoning_gap
        self.reasoning_intent = reasoning_intent


# -----------------------------
# Nominal cases
# -----------------------------


def test_valid_bundle_no_gap():
    b = Bundle(stability_score=0.5)

    assert_kernel_invariants(b)


def test_valid_bundle_with_gap_and_intent():
    b = Bundle(
        stability_score=0.8,
        reasoning_gap="gap",
        reasoning_intent="intent",
    )

    assert_kernel_invariants(b)


# -----------------------------
# Stability bounds
# -----------------------------


def test_stability_lower_bound():
    b = Bundle(stability_score=0.0)

    assert_kernel_invariants(b)


def test_stability_upper_bound():
    b = Bundle(stability_score=1.0)

    assert_kernel_invariants(b)


def test_stability_below_zero():
    b = Bundle(stability_score=-0.1)

    with pytest.raises(AssertionError):
        assert_kernel_invariants(b)


def test_stability_above_one():
    b = Bundle(stability_score=1.1)

    with pytest.raises(AssertionError):
        assert_kernel_invariants(b)


# -----------------------------
# Reasoning invariant
# -----------------------------


def test_gap_without_intent_fails():
    b = Bundle(
        stability_score=0.5,
        reasoning_gap="gap",
        reasoning_intent=None,
    )

    with pytest.raises(AssertionError):
        assert_kernel_invariants(b)


def test_no_gap_no_intent_ok():
    b = Bundle(
        stability_score=0.5,
        reasoning_gap=None,
        reasoning_intent=None,
    )

    assert_kernel_invariants(b)
