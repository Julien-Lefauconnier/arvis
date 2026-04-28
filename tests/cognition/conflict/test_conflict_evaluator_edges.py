# test/cognition/conflict/test_conflict_evaluator_edges.py

from arvis.cognition.conflict.conflict_evaluator import ConflictEvaluator
from arvis.cognition.conflict.conflict_signal import ConflictSignal
from arvis.cognition.conflict.conflict_type import REASON_MISMATCH


def test_rule_exception_is_ignored():
    def bad_rule(results, conflict):
        raise Exception()

    evaluator = ConflictEvaluator(rules=[bad_rule])

    res = evaluator.apply(
        targets=["a"],
        conflicts=[ConflictSignal(REASON_MISMATCH, {})],
    )

    assert len(res) == 1


def test_rule_returns_none():
    def none_rule(results, conflict):
        return None

    evaluator = ConflictEvaluator(rules=[none_rule])

    res = evaluator.apply(
        targets=["a"],
        conflicts=[ConflictSignal(REASON_MISMATCH, {})],
    )

    assert len(res) == 1
