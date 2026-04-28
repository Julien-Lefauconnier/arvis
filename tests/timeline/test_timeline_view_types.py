# tests/timeline/test_timeline_view_types.py

from arvis.timeline.timeline_view_types import TimelineViewRole

# --------------------------------------------------
# Basic enum behavior
# --------------------------------------------------


def test_enum_contains_expected_roles():
    roles = {r.value for r in TimelineViewRole}

    assert "trace_factual" in roles
    assert "public" in roles
    assert "exposed" in roles
    assert "user_visible" in roles


def test_enum_members_are_strings():
    for role in TimelineViewRole:
        assert isinstance(role.value, str)


# --------------------------------------------------
# Uniqueness / integrity
# --------------------------------------------------


def test_enum_values_are_unique():
    values = [role.value for role in TimelineViewRole]
    assert len(values) == len(set(values))


def test_enum_names_are_unique():
    names = [role.name for role in TimelineViewRole]
    assert len(names) == len(set(names))


# --------------------------------------------------
# Usage compatibility
# --------------------------------------------------


def test_enum_can_be_used_as_dict_key():
    d = {TimelineViewRole.PUBLIC: "ok"}

    assert d[TimelineViewRole.PUBLIC] == "ok"


def test_enum_string_comparison():
    assert TimelineViewRole.PUBLIC == "public"
    assert TimelineViewRole.PUBLIC.value == "public"


# --------------------------------------------------
# Edge / defensive
# --------------------------------------------------


def test_enum_no_empty_values():
    for role in TimelineViewRole:
        assert role.value != ""


def test_enum_is_iterable():
    roles = list(TimelineViewRole)
    assert len(roles) >= 4
