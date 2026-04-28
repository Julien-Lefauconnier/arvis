# arvis/kernel_core/vfs/tree.py

from __future__ import annotations

from dataclasses import dataclass, field

from arvis.kernel_core.vfs.models import VFSItem


@dataclass
class VFSTreeNode:
    """
    Logical VFS projection node.

    This structure is:
    - not persisted
    - not indexed
    - purely derived from VFS items
    """

    item: VFSItem
    children: list["VFSTreeNode"] = field(default_factory=list)


def build_vfs_tree(items: list[VFSItem]) -> list[VFSTreeNode]:
    """
    Build a deterministic VFS tree from persisted VFS items.
    """
    nodes: dict[str, VFSTreeNode] = {}
    roots: list[VFSTreeNode] = []

    for item in items:
        nodes[item.item_id] = VFSTreeNode(item=item)

    for node in nodes.values():
        parent_id = node.item.parent_id
        if parent_id is not None and parent_id in nodes:
            nodes[parent_id].children.append(node)
        else:
            roots.append(node)

    _sort_tree_nodes(roots)
    return roots


def _sort_tree_nodes(nodes: list[VFSTreeNode]) -> None:
    nodes.sort(key=_tree_sort_key)
    for node in nodes:
        _sort_tree_nodes(node.children)


def _tree_sort_key(node: VFSTreeNode) -> tuple[int, str, str]:
    item_type_rank = 0 if node.item.item_type == "folder" else 1
    return (
        item_type_rank,
        node.item.display_name.lower(),
        node.item.item_id,
    )
