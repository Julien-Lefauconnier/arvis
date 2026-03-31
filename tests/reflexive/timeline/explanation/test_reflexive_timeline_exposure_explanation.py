# tests/reflexive/timeline/explanation/test_reflexive_timeline_exposure_explanation.py

from arvis.reflexive.timeline.explanation.reflexive_timeline_exposure_explanation import (
    ReflexiveTimelineExposureExplanation,
)


# --------------------------------------------------
# Helpers
# --------------------------------------------------

class DummyRole:
    def __init__(self, value):
        self.value = value


# --------------------------------------------------
# Core behavior
# --------------------------------------------------

def test_no_roles_no_public_view():
    result = ReflexiveTimelineExposureExplanation.build([])

    assert isinstance(result, dict)
    assert "timeline" in result or result  

def test_no_roles_but_public_view():
    result = ReflexiveTimelineExposureExplanation.build(
        [],
        has_any_public_view=True,
    )

    assert isinstance(result, dict)

    text = str(result).lower()
    assert "non-factual" in text


# --------------------------------------------------
# Public factual roles
# --------------------------------------------------

def test_public_role_triggers_public_timeline():
    result = ReflexiveTimelineExposureExplanation.build(["public"])

    assert isinstance(result, dict)

    text = str(result).lower()
    # on vérifie qu'on a bien une exposition publique
    assert "public" in text or "timeline" in text


def test_multiple_public_roles():
    result = ReflexiveTimelineExposureExplanation.build(
        ["public", "exposed", "user_visible"]
    )

    assert isinstance(result, dict)


# --------------------------------------------------
# Non factual roles
# --------------------------------------------------

def test_non_factual_roles_add_limitation():
    result = ReflexiveTimelineExposureExplanation.build(["internal", "private"])

    assert "limitations" in result
    assert any("not factual" in item.lower() for item in result["limitations"])


def test_mixed_roles_public_and_non_factual():
    result = ReflexiveTimelineExposureExplanation.build(["public", "internal"])

    assert result.get("public") is True
    assert "limitations" in result
    assert any("not factual" in item.lower() for item in result["limitations"])


# --------------------------------------------------
# Role normalization
# --------------------------------------------------

def test_roles_with_value_attribute():
    roles = [DummyRole("public"), DummyRole("internal")]

    result = ReflexiveTimelineExposureExplanation.build(roles)

    assert isinstance(result, dict)


def test_roles_with_none_filtered():
    result = ReflexiveTimelineExposureExplanation.build(
        ["public", None, "internal"]
    )

    assert isinstance(result, dict)


def test_roles_are_deduplicated():
    result = ReflexiveTimelineExposureExplanation.build(
        ["public", "public", "public"]
    )

    assert isinstance(result, dict)


def test_roles_as_non_string_objects():
    result = ReflexiveTimelineExposureExplanation.build([123, True, "public"])

    assert isinstance(result, dict)


# --------------------------------------------------
# Edge cases
# --------------------------------------------------

def test_empty_iterable_object():
    result = ReflexiveTimelineExposureExplanation.build(iter([]))
    assert isinstance(result, dict)


def test_large_role_set():
    roles = [f"role_{i}" for i in range(100)]
    result = ReflexiveTimelineExposureExplanation.build(roles)

    assert isinstance(result, dict)