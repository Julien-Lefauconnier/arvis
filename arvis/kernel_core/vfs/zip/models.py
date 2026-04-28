# arvis/kernel_core/vfs/zip/models.py

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from arvis.kernel_core.vfs.models import VFSItem

ZipNodeType = Literal["file", "folder"]
ZipCollisionReason = Literal["already_exists", "parent_is_file"]
ZipImportAction = Literal["import", "skip", "rename"]


@dataclass
class ZipNode:
    """
    Logical in-memory representation of a ZIP entry.

    This model is temporary and does not touch persistence,
    indexing, or external storage.
    """

    name: str
    node_type: ZipNodeType
    parent: Optional["ZipNode"] = None
    children: list["ZipNode"] = field(default_factory=list)

    size: Optional[int] = None
    extension: Optional[str] = None
    supported: Optional[bool] = None
    reason: Optional[str] = None

    # Relative path inside the ZIP archive.
    zip_path: Optional[str] = None

    def is_file(self) -> bool:
        return self.node_type == "file"

    def is_folder(self) -> bool:
        return self.node_type == "folder"

    def add_child(self, child: "ZipNode") -> None:
        if not self.is_folder():
            raise ValueError("cannot add child to a file node")
        child.parent = self
        self.children.append(child)

    def iter_tree(self) -> list["ZipNode"]:
        nodes = [self]
        for child in self.children:
            nodes.extend(child.iter_tree())
        return nodes

    def full_path_debug(self) -> str:
        parts: list[str] = []
        node: Optional[ZipNode] = self
        while node is not None:
            parts.append(node.name)
            node = node.parent
        return "/".join(reversed(parts))


@dataclass(frozen=True)
class ZipCollision:
    zip_node: ZipNode
    vfs_item: VFSItem
    reason: ZipCollisionReason


@dataclass(frozen=True)
class ZipCollisionReport:
    has_conflicts: bool
    collisions: list[ZipCollision]


@dataclass(frozen=True)
class ZipImportPlanEntry:
    action: ZipImportAction
    new_name: Optional[str] = None


@dataclass(frozen=True)
class ZipImportPlan:
    """
    Explicit ZIP import plan.

    Keys are normalized relative ZIP paths such as:
    - docs/file.txt
    - images/logo.png
    """

    entries: dict[str, ZipImportPlanEntry]
