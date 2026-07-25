# tests/kernel_core/vfs/test_vfs_item_with_changes_unit.py

"""The VFSItem.with_changes safe-reconstruction primitive (audit A-02).

A mutation states what it changes; every field it does not name is
preserved. This is the primitive that makes it structurally impossible to
drop a security-bearing field (owner_id, organization_id, resource_scope)
when reconstructing an item after a rename or a move.
"""

import pytest

from arvis.kernel_core.vfs.models import VFSItem


def _scoped_item() -> VFSItem:
    return VFSItem(
        item_id="i1",
        display_name="f.txt",
        item_type="file",
        parent_id="p1",
        owner_id="alice",
        organization_id="acme",
        mime="text/plain",
        file_size=10,
        created_at=42,
        resource_scope="scope:A",
    )


def test_with_changes_preserves_every_unnamed_field():
    item = _scoped_item()
    renamed = item._with_changes(display_name="renamed.txt")
    assert renamed.display_name == "renamed.txt"
    # Everything else, including the three security-bearing fields, preserved.
    assert renamed.item_id == "i1"
    assert renamed.parent_id == "p1"
    assert renamed.owner_id == "alice"
    assert renamed.organization_id == "acme"
    assert renamed.resource_scope == "scope:A"
    assert renamed.mime == "text/plain"
    assert renamed.file_size == 10
    assert renamed.created_at == 42


def test_with_changes_move_preserves_scope_and_org():
    item = _scoped_item()
    moved = item._with_changes(parent_id="p2")
    assert moved.parent_id == "p2"
    assert moved.organization_id == "acme"
    assert moved.resource_scope == "scope:A"


def test_with_changes_can_change_multiple_fields():
    item = _scoped_item()
    changed = item._with_changes(display_name="x", parent_id="p2")
    assert changed.display_name == "x"
    assert changed.parent_id == "p2"
    assert changed.resource_scope == "scope:A"


def test_with_changes_rejects_unknown_field():
    """A typo in a field name raises rather than silently building a
    divergent object: the guard against a future reconstruction that would
    forget or misname a security field."""
    item = _scoped_item()
    with pytest.raises(TypeError):
        item._with_changes(reso_scope="scope:B")


def test_with_changes_returns_a_new_frozen_object():
    item = _scoped_item()
    other = item._with_changes(display_name="y")
    assert other is not item
    assert item.display_name == "f.txt"  # original untouched
