# arvis/cognition/bundle/cognitive_bundle_invariants.py

from typing import Sequence

from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot
from arvis.cognition.explanation.explanation_snapshot import ExplanationSnapshot
from arvis.timeline.timeline_entry import TimelineEntry
from arvis.timeline.timeline_types import TimelineEntryType


class CognitiveBundleInvariantError(Exception):
    """Violation explicite des invariants du CognitiveBundle."""


def assert_cognitive_bundle_invariants(bundle: CognitiveBundleSnapshot) -> None:
    _assert_no_prescriptive_fields(bundle)
    _assert_explanation_is_declarative(bundle.explanation)
    _assert_timeline_is_declarative(bundle.timeline)
    _assert_no_hidden_logic(bundle)
    _assert_memory_long_is_optional_and_passive(bundle)
    _assert_context_hints_are_safe(bundle)


def _assert_no_prescriptive_fields(bundle: CognitiveBundleSnapshot) -> None:
    allowed_fields = {
        "decision_result",
        "introspection",
        "explanation",
        "timeline",
        "memory_long",
        "retrieval_snapshot",
        "generated_at",
        "context_hints",
    }

    forbidden_keywords = {
        "recommended",
        "execute",
        "policy",
        "next_step",
        "command",
        "action_to_take",
    }

    for field_name in vars(bundle).keys():
        if field_name in allowed_fields:
            continue

        lowered = field_name.lower()
        for keyword in forbidden_keywords:
            if keyword in lowered:
                raise CognitiveBundleInvariantError(
                    f"Prescriptive field forbidden in CognitiveBundle: {field_name}"
                )


def _assert_explanation_is_declarative(explanation: ExplanationSnapshot) -> None:
    forbidden_words = {
        "because",
        "therefore",
        "we decided",
        "the system chose",
        "should",
        "must",
    }

    for item in explanation.items:
        text = str(item).lower()

        for word in forbidden_words:
            if word in text:
                raise CognitiveBundleInvariantError(
                    f"Causal language forbidden: {word}"
                )


def _assert_timeline_is_declarative(timeline: Sequence[TimelineEntry]) -> None:
    forbidden_types = {
        TimelineEntryType.ACTION_PROPOSED,
        TimelineEntryType.ACTION_VALIDATED,
        TimelineEntryType.ACTION_REFUSED,
        TimelineEntryType.ACTION_BLOCKED,
    }

    for entry in timeline:
        if entry.type in forbidden_types:
            raise CognitiveBundleInvariantError(
                f"Actionable timeline entry forbidden in CognitiveBundle: {entry.type}"
            )


def _assert_context_hints_are_safe(bundle: CognitiveBundleSnapshot) -> None:
    hints = getattr(bundle, "context_hints", None)

    if not hints:
        return

    if not isinstance(hints, dict):
        raise CognitiveBundleInvariantError("context_hints must be a dict")

    for key, value in hints.items():
        if not isinstance(key, str):
            raise CognitiveBundleInvariantError("context_hints keys must be str")

        if not isinstance(value, (str, bool, int, float, type(None))):
            raise CognitiveBundleInvariantError(
                f"context_hints value for '{key}' must be primitive (got {type(value)})"
            )


def _assert_no_hidden_logic(bundle: CognitiveBundleSnapshot) -> None:
    for value in vars(bundle).values():
        if callable(value):
            raise CognitiveBundleInvariantError("Callable forbidden in CognitiveBundle")


def _assert_memory_long_is_optional_and_passive(
    bundle: CognitiveBundleSnapshot,
) -> None:
    if bundle.memory_long is None:
        return

    if hasattr(bundle.memory_long, "write") or hasattr(bundle.memory_long, "mutate"):
        raise CognitiveBundleInvariantError("Mutation forbidden on MemoryLongSnapshot")
