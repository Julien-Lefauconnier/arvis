# tests/kernel/test_gray_zone_exercise.py
"""Campaign FIX (LOT F2): exercise for the referenced-but-untested
gray zones the audit surfaced.

Three small components were wired but never driven: the unified
Lyapunov observer's production path (a 50-line block at 61 percent),
the temporal timeline memory (52 percent), and the governance
evaluator (44 percent). These pins drive their real behavior.
"""

from __future__ import annotations

from datetime import UTC, datetime

from arvis.cognition.governance.governance_decision import (
    GovernanceDecision,
    GovernanceDecisionType,
)
from arvis.cognition.governance.governance_evaluator import GovernanceEvaluator
from arvis.cognition.governance.governance_suggestion import (
    GovernanceSuggestion,
)
from arvis.math.lyapunov.lyapunov import LyapunovState
from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_memory import (
    IRGTimelineTemporalMemory,
)
from arvis.reflexive.timeline.aggregation.irg_timeline_temporal_snapshot import (
    IRGTimelineTemporalSnapshot,
)
from arvis.timeline.timeline_types import TimelineEntryType

# ---------------------------------------------------------------
# LyapunovObserver: the pure math evaluation path
# ---------------------------------------------------------------


def test_lyapunov_observer_evaluate_contracts_and_verdicts() -> None:
    from arvis.kernel.observability.lyapunov_observer import LyapunovObserver

    observer = LyapunovObserver()
    calm = LyapunovState(budget_used=0.1, risk=0.1, uncertainty=0.1, governance=0.1)
    calmer = LyapunovState(
        budget_used=0.05, risk=0.05, uncertainty=0.05, governance=0.05
    )

    obs = observer.evaluate(calm, calmer)

    assert obs.delta < 0
    assert obs.v_new < obs.v_prev
    assert obs.verdict.name in {"ALLOW", "REQUIRE_CONFIRMATION", "ABSTAIN"}


def test_lyapunov_observer_reset_clears_history() -> None:
    from arvis.kernel.observability.lyapunov_observer import LyapunovObserver

    observer = LyapunovObserver()
    observer._last_state = LyapunovState(
        budget_used=0.5, risk=0.5, uncertainty=0.5, governance=0.5
    )

    observer.reset()

    assert observer._last_state is None


# ---------------------------------------------------------------
# IRGTimelineTemporalMemory: the bounded diff window
# ---------------------------------------------------------------


def _snapshot(index: int) -> IRGTimelineTemporalSnapshot:
    return IRGTimelineTemporalSnapshot(
        observed_at=datetime(2026, 9, 1, 12, index, tzinfo=UTC),
        observed_views=(f"view-{index}",),
        dominant_entry_types=(TimelineEntryType.SYSTEM_NOTICE,),
        confidence=round(0.5 + index / 100, 3),
    )


def test_temporal_memory_window_and_diffs() -> None:
    memory = IRGTimelineTemporalMemory(maxlen=3)

    assert memory.latest() is None
    assert memory.previous() is None
    assert list(memory.iter_diffs()) == []

    for count in range(1, 6):
        memory.append(_snapshot(count))

    # bounded: only the last three survive
    assert len(memory) == 3
    latest = memory.latest()
    previous = memory.previous()
    assert latest is not None and latest.observed_views == ("view-5",)
    assert previous is not None and previous.observed_views == ("view-4",)

    diffs = list(memory.iter_diffs())
    assert len(diffs) == 2


# ---------------------------------------------------------------
# GovernanceEvaluator: suggestion/decision matching
# ---------------------------------------------------------------


def test_governance_evaluator_matches_and_rejects() -> None:
    evaluator = GovernanceEvaluator()
    suggestion = GovernanceSuggestion(
        suggestion_id="sug-1",
        source_policy="memory_policy",
        dimension="memory",
        suggestion_type="write",
        rationale="store preference",
    )

    assert evaluator.evaluate(suggestion=suggestion, decision=None) is None

    mismatched = GovernanceDecision(
        suggestion_id="sug-OTHER",
        decision=GovernanceDecisionType.ACCEPTED,
        decided_by="operator",
    )
    assert evaluator.evaluate(suggestion=suggestion, decision=mismatched) is None

    matched = GovernanceDecision(
        suggestion_id="sug-1",
        decision=GovernanceDecisionType.ACCEPTED,
        decided_by="operator",
    )
    assert evaluator.evaluate(suggestion=suggestion, decision=matched) is matched
