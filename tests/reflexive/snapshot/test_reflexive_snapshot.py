# tests/reflexive/snapshot/test_reflexive_snapshot.py


def test_import_snapshot_modules():
    pass


def test_snapshot_builder_instantiation():
    from arvis.reflexive.snapshot.reflexive_snapshot_builder import (
        ReflexiveSnapshotBuilder,
    )

    builder = ReflexiveSnapshotBuilder()
    assert builder is not None
