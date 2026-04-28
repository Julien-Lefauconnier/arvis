# tests/reflexive/snapshot/test_reflexive_snapshot_builder.py

from datetime import UTC, datetime

from arvis.reflexive.snapshot.reflexive_snapshot_builder import (
    ReflexiveSnapshotBuilder,
)

# --------------------------------------------------
# Helpers
# --------------------------------------------------


class DummyRole:
    def __init__(self, value, is_public=False):
        self.value = value
        self.is_public = is_public


class DummyView:
    def __init__(self, role=None):
        self.role = role


class FakeMemory:
    def iter_diffs(self):
        return iter([])


# --------------------------------------------------
# Core behavior
# --------------------------------------------------


def test_build_minimal_snapshot():
    snapshot = ReflexiveSnapshotBuilder.build(
        capabilities={},
        timeline_views={},
    )

    assert snapshot is not None
    assert snapshot.timeline_explanation is not None
    assert snapshot.irg_explanation is None


# --------------------------------------------------
# generated_at behavior
# --------------------------------------------------


def test_generated_at_default_is_set():
    snapshot = ReflexiveSnapshotBuilder.build(
        capabilities={},
        timeline_views={},
    )

    assert snapshot.generated_at is not None
    assert snapshot.generated_at.tzinfo == UTC


def test_generated_at_override():
    ts = datetime(2020, 1, 1, tzinfo=UTC)

    snapshot = ReflexiveSnapshotBuilder.build(
        capabilities={},
        timeline_views={},
        generated_at=ts,
    )

    assert snapshot.generated_at == ts


# --------------------------------------------------
# Timeline roles extraction
# --------------------------------------------------


def test_roles_are_extracted_from_views():
    views = {
        "v1": DummyView(role=DummyRole("public")),
        "v2": DummyView(role=DummyRole("internal")),
    }

    snapshot = ReflexiveSnapshotBuilder.build(
        capabilities={},
        timeline_views=views,
    )

    assert snapshot.timeline_explanation is not None


def test_public_role_detection():
    views = {
        "v1": DummyView(role=DummyRole("internal", is_public=False)),
        "v2": DummyView(role=DummyRole("public", is_public=True)),
    }

    snapshot = ReflexiveSnapshotBuilder.build(
        capabilities={},
        timeline_views=views,
    )

    explanation = snapshot.timeline_explanation

    # structure-based check (robuste)
    assert explanation.get("public") is True


def test_views_without_role_are_ignored():
    views = {
        "v1": DummyView(role=None),
        "v2": DummyView(),
    }

    snapshot = ReflexiveSnapshotBuilder.build(
        capabilities={},
        timeline_views=views,
    )

    assert snapshot.timeline_explanation is not None


# --------------------------------------------------
# IRG explanation integration
# --------------------------------------------------


def test_irg_explanation_is_none_when_no_memory():
    snapshot = ReflexiveSnapshotBuilder.build(
        capabilities={},
        timeline_views={},
        irg_temporal_memory=None,
    )

    assert snapshot.irg_explanation is None


def test_irg_explanation_is_built_when_memory_present():
    memory = FakeMemory()

    snapshot = ReflexiveSnapshotBuilder.build(
        capabilities={},
        timeline_views={},
        irg_temporal_memory=memory,
    )

    assert snapshot.irg_explanation is not None
    assert snapshot.irg_explanation.stability == "stable"


# --------------------------------------------------
# Full integration
# --------------------------------------------------


def test_full_snapshot_structure():
    views = {
        "v1": DummyView(role=DummyRole("public", is_public=True)),
    }

    memory = FakeMemory()

    snapshot = ReflexiveSnapshotBuilder.build(
        capabilities={"a": 1},
        timeline_views=views,
        irg_temporal_memory=memory,
        cognitive_state={"state": True},
        introspection={"introspect": True},
    )

    assert snapshot.capabilities == {"a": 1}
    assert snapshot.cognitive_state == {"state": True}
    assert snapshot.introspection == {"introspect": True}

    assert snapshot.timeline_explanation is not None
    assert snapshot.irg_explanation is not None
