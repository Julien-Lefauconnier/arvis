# tests/reflexive/timeline/explanation/test_irg_timeline_explanation_builder.py

from arvis.reflexive.timeline.explanation.irg_timeline_explanation_builder import (
    IRGTimelineExplanationBuilder,
)

# --------------------------------------------------
# Fake objects (ZK-safe mocks)
# --------------------------------------------------


class FakeDiff:
    def __init__(
        self,
        *,
        views_added=None,
        views_removed=None,
        entry_types_added=None,
        is_stable=True,
    ):
        self.views_added = views_added or []
        self.views_removed = views_removed or []
        self.entry_types_added = entry_types_added or []
        self.is_stable = is_stable


class FakeMemory:
    def __init__(self, diffs):
        self._diffs = diffs

    def iter_diffs(self):
        return iter(self._diffs)


# --------------------------------------------------
# Core behavior
# --------------------------------------------------


def test_no_diffs_returns_default_explanation():
    memory = FakeMemory([])

    result = IRGTimelineExplanationBuilder.build(memory)

    assert result.summary.lower().startswith("no significant evolution")
    assert result.signals == []
    assert result.stability == "stable"


# --------------------------------------------------
# Stable diffs
# --------------------------------------------------


def test_views_added_generates_signal():
    memory = FakeMemory([FakeDiff(views_added=["public_view"])])

    result = IRGTimelineExplanationBuilder.build(memory)

    assert any("new timeline views appeared" in s.lower() for s in result.signals)
    assert result.stability == "stable"


def test_views_removed_generates_signal():
    memory = FakeMemory([FakeDiff(views_removed=["old_view"])])

    result = IRGTimelineExplanationBuilder.build(memory)

    assert any("no longer observed" in s.lower() for s in result.signals)


def test_entry_types_added_generates_signal():
    memory = FakeMemory([FakeDiff(entry_types_added=["conflict"])])

    result = IRGTimelineExplanationBuilder.build(memory)

    assert any("new types of timeline entries" in s.lower() for s in result.signals)


# --------------------------------------------------
# Unstable diffs
# --------------------------------------------------


def test_unstable_diff_sets_evolving():
    memory = FakeMemory([FakeDiff(is_stable=False)])

    result = IRGTimelineExplanationBuilder.build(memory)

    assert result.stability == "evolving"
    assert "changes" in result.summary.lower()


# --------------------------------------------------
# Mixed diffs
# --------------------------------------------------


def test_mixed_diffs_accumulate_signals():
    memory = FakeMemory(
        [
            FakeDiff(views_added=["v1"]),
            FakeDiff(views_removed=["v2"]),
            FakeDiff(entry_types_added=["conflict"]),
        ]
    )

    result = IRGTimelineExplanationBuilder.build(memory)

    assert len(result.signals) >= 3


def test_mixed_stability_results_in_evolving():
    memory = FakeMemory(
        [
            FakeDiff(is_stable=True),
            FakeDiff(is_stable=False),
        ]
    )

    result = IRGTimelineExplanationBuilder.build(memory)

    assert result.stability == "evolving"


# --------------------------------------------------
# Edge cases
# --------------------------------------------------


def test_empty_diff_object():
    memory = FakeMemory([FakeDiff()])

    result = IRGTimelineExplanationBuilder.build(memory)

    assert result.stability == "stable"
    assert isinstance(result.signals, list)


def test_multiple_views_added_joined_correctly():
    memory = FakeMemory([FakeDiff(views_added=["v1", "v2", "v3"])])

    result = IRGTimelineExplanationBuilder.build(memory)

    signal_text = " ".join(result.signals).lower()
    assert "v1" in signal_text
    assert "v2" in signal_text
    assert "v3" in signal_text
