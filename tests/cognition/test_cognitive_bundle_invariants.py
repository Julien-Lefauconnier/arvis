# tests/cognition/test_cognitive_bundle_invariants.py

import importlib

import pytest

from arvis.cognition.bundle.cognitive_bundle_invariants import (
    CognitiveBundleInvariantError,
    assert_cognitive_bundle_invariants,
)
from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot
from arvis.cognition.explanation.explanation_snapshot import ExplanationSnapshot
from arvis.timeline.timeline_entry import TimelineEntry
from arvis.timeline.timeline_types import TimelineEntryType


FORBIDDEN_TIMELINE_TYPES = {
    TimelineEntryType.ACTION_PROPOSED,
    TimelineEntryType.ACTION_VALIDATED,
    TimelineEntryType.ACTION_REFUSED,
    TimelineEntryType.ACTION_BLOCKED,
}


def _valid_timeline_type() -> TimelineEntryType:
    for entry_type in TimelineEntryType:
        if entry_type not in FORBIDDEN_TIMELINE_TYPES:
            return entry_type
    raise AssertionError("No valid TimelineEntryType available for invariant tests")


def _make_timeline_entry(entry_type: TimelineEntryType) -> TimelineEntry:
    return TimelineEntry.unsafe(
        entry_id="timeline01",
        type=entry_type,
        title="neutral event",
        description="neutral observation",
        action_id=None,
        place_id=None,
    )


def make_valid_bundle(**overrides):
    explanation = overrides.pop(
        "explanation",
        ExplanationSnapshot(items=["neutral observation"]),
    )

    timeline = overrides.pop(
        "timeline",
        [_make_timeline_entry(_valid_timeline_type())],
    )

    return CognitiveBundleSnapshot(
        decision_result=overrides.pop("decision_result", None),
        introspection=overrides.pop("introspection", None),
        explanation=explanation,
        timeline=timeline,
        memory_long=overrides.pop("memory_long", None),
        retrieval_snapshot=overrides.pop("retrieval_snapshot", None),
        generated_at=overrides.pop("generated_at", 0),
        context_hints=overrides.pop("context_hints", None),
        **overrides,
    )


def test_cognitive_bundle_invariants_module_importable():
    module = importlib.import_module(
        "arvis.cognition.bundle.cognitive_bundle_invariants"
    )
    assert module is not None


def test_cognitive_bundle_invariants_has_public_symbols():
    module = importlib.import_module(
        "arvis.cognition.bundle.cognitive_bundle_invariants"
    )
    public = [name for name in dir(module) if not name.startswith("_")]
    assert len(public) > 0


def test_valid_bundle_passes():
    bundle = make_valid_bundle()
    assert_cognitive_bundle_invariants(bundle)


def test_prescriptive_field_forbidden():
    bundle = make_valid_bundle()
    object.__setattr__(bundle, "next_step_action", "do something")

    with pytest.raises(CognitiveBundleInvariantError):
        assert_cognitive_bundle_invariants(bundle)


@pytest.mark.parametrize(
    "bad_text",
    [
        "because we did this",
        "therefore it works",
        "the system chose X",
        "we decided Y",
        "you should do that",
        "you must act",
    ],
)
def test_explanation_forbidden_words(bad_text):
    bundle = make_valid_bundle(explanation=ExplanationSnapshot(items=[bad_text]))

    with pytest.raises(CognitiveBundleInvariantError):
        assert_cognitive_bundle_invariants(bundle)


@pytest.mark.parametrize(
    "bad_type",
    [
        TimelineEntryType.ACTION_PROPOSED,
        TimelineEntryType.ACTION_VALIDATED,
        TimelineEntryType.ACTION_REFUSED,
        TimelineEntryType.ACTION_BLOCKED,
    ],
)
def test_timeline_forbidden_types(bad_type):
    bundle = make_valid_bundle(timeline=[_make_timeline_entry(bad_type)])

    with pytest.raises(CognitiveBundleInvariantError):
        assert_cognitive_bundle_invariants(bundle)


def test_context_hints_valid():
    bundle = make_valid_bundle(context_hints={"key": "value", "flag": True})
    assert_cognitive_bundle_invariants(bundle)


def test_context_hints_not_dict():
    bundle = make_valid_bundle(context_hints="bad")

    with pytest.raises(CognitiveBundleInvariantError):
        assert_cognitive_bundle_invariants(bundle)


def test_context_hints_bad_key():
    bundle = make_valid_bundle(context_hints={1: "value"})

    with pytest.raises(CognitiveBundleInvariantError):
        assert_cognitive_bundle_invariants(bundle)


def test_context_hints_bad_value():
    bundle = make_valid_bundle(context_hints={"key": object()})

    with pytest.raises(CognitiveBundleInvariantError):
        assert_cognitive_bundle_invariants(bundle)


def test_callable_forbidden():
    bundle = make_valid_bundle()
    object.__setattr__(bundle, "some_callable", lambda x: x)

    with pytest.raises(CognitiveBundleInvariantError):
        assert_cognitive_bundle_invariants(bundle)


class BadMemory:
    def write(self):
        pass


def test_memory_long_with_mutation_forbidden():
    bundle = make_valid_bundle(memory_long=BadMemory())

    with pytest.raises(CognitiveBundleInvariantError):
        assert_cognitive_bundle_invariants(bundle)


def test_memory_long_valid_object():
    class SafeMemory:
        pass

    bundle = make_valid_bundle(memory_long=SafeMemory())
    assert_cognitive_bundle_invariants(bundle)
