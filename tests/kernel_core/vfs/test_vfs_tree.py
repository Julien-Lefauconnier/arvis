# tests/kernel_core/vfs/test_vfs_tree.py

from __future__ import annotations

from arvis.kernel_core.vfs.models import VFSItem
from arvis.kernel_core.vfs.tree import build_vfs_tree


def test_build_vfs_tree_single_root_file() -> None:
    items = [
        VFSItem(
            item_id="1",
            display_name="file.txt",
            item_type="file",
            parent_id=None,
            mime="text/plain",
            file_size=10,
            created_at=123,
        )
    ]

    tree = build_vfs_tree(items)

    assert len(tree) == 1
    assert tree[0].item.display_name == "file.txt"
    assert tree[0].children == []


def test_build_vfs_tree_folder_with_child() -> None:
    items = [
        VFSItem(
            item_id="folder",
            display_name="docs",
            item_type="folder",
            parent_id=None,
        ),
        VFSItem(
            item_id="file",
            display_name="a.txt",
            item_type="file",
            parent_id="folder",
            mime="text/plain",
            file_size=5,
        ),
    ]

    tree = build_vfs_tree(items)

    assert len(tree) == 1
    assert tree[0].item.display_name == "docs"
    assert len(tree[0].children) == 1
    assert tree[0].children[0].item.display_name == "a.txt"


def test_build_vfs_tree_deep_tree() -> None:
    items = [
        VFSItem(
            item_id="root",
            display_name="root",
            item_type="folder",
            parent_id=None,
        ),
        VFSItem(
            item_id="child",
            display_name="child",
            item_type="folder",
            parent_id="root",
        ),
        VFSItem(
            item_id="leaf",
            display_name="leaf.txt",
            item_type="file",
            parent_id="child",
            mime="text/plain",
            file_size=3,
        ),
    ]

    tree = build_vfs_tree(items)

    assert len(tree) == 1
    assert tree[0].children[0].children[0].item.display_name == "leaf.txt"


def test_build_vfs_tree_orphan_becomes_root() -> None:
    items = [
        VFSItem(
            item_id="orphan",
            display_name="orphan.txt",
            item_type="file",
            parent_id="missing-parent",
            mime="text/plain",
            file_size=1,
        )
    ]

    tree = build_vfs_tree(items)

    assert len(tree) == 1
    assert tree[0].item.item_id == "orphan"
    assert tree[0].item.parent_id == "missing-parent"


def test_build_vfs_tree_is_deterministic_for_roots() -> None:
    items = [
        VFSItem(item_id="3", display_name="b.txt", item_type="file", parent_id=None),
        VFSItem(item_id="2", display_name="a.txt", item_type="file", parent_id=None),
        VFSItem(item_id="1", display_name="Docs", item_type="folder", parent_id=None),
    ]

    tree = build_vfs_tree(items)
    names = [node.item.display_name for node in tree]

    assert names == ["Docs", "a.txt", "b.txt"]


def test_build_vfs_tree_is_deterministic_for_children() -> None:
    items = [
        VFSItem(item_id="root", display_name="root", item_type="folder", parent_id=None),
        VFSItem(item_id="3", display_name="b.txt", item_type="file", parent_id="root"),
        VFSItem(item_id="2", display_name="a.txt", item_type="file", parent_id="root"),
        VFSItem(item_id="1", display_name="docs", item_type="folder", parent_id="root"),
    ]

    tree = build_vfs_tree(items)
    children = tree[0].children
    names = [node.item.display_name for node in children]

    assert names == ["docs", "a.txt", "b.txt"]


def test_build_vfs_tree_breaks_ties_with_item_id() -> None:
    items = [
        VFSItem(item_id="b", display_name="same.txt", item_type="file", parent_id=None),
        VFSItem(item_id="a", display_name="same.txt", item_type="file", parent_id=None),
    ]

    tree = build_vfs_tree(items)
    ids = [node.item.item_id for node in tree]

    assert ids == ["a", "b"]