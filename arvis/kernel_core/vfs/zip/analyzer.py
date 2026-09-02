# arvis/kernel_core/vfs/zip/analyzer.py

from __future__ import annotations

from pathlib import PurePosixPath

from arvis.kernel_core.vfs.zip.guard import ZipGuard
from arvis.kernel_core.vfs.zip.models import ZipNode
from arvis.kernel_core.vfs.zip.reader import ZipSafeReader

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".md",
    ".png",
    ".jpg",
    ".jpeg",
    ".docx",
    ".xlsx",
    ".pptx",
}


class ZipAnalyzer:
    """
    Passive and safe ZIP analyzer.

    Produces a logical ZipNode tree with:
    - no disk writes
    - no ingestion
    - no VFS persistence dependency
    """

    def __init__(self, guard: ZipGuard | None = None) -> None:
        """The firewall is ALWAYS present (campaign KERNEL, LOT K3).

        It used to be dropped whenever ``os.getenv("ENV") == "test"``,
        so an ambient variable removed the file-count cap, the size
        caps, the zip-bomb ratio check and the blocked-extension list
        on an archive ingestion path: a monotone-hardening violation
        (F-001) whatever the intent. A caller needing different limits
        injects a configured guard, which is a decision at the call
        site rather than an ambient one.
        """
        self.guard = guard if guard is not None else ZipGuard()

    def analyze(self, zip_path: str) -> ZipNode:
        self.guard.validate_path(zip_path)

        root = ZipNode(
            name="/",
            node_type="folder",
            parent=None,
        )

        folders: dict[str, ZipNode] = {
            "": root,
        }

        with ZipSafeReader(zip_path) as reader:
            for entry in reader.iter_entries():
                raw = entry.path
                path = PurePosixPath(raw)

                if path.is_absolute() or ".." in path.parts:
                    continue

                parts = list(path.parts)
                is_dir = entry.is_dir

                current_parent = root
                accumulated = ""

                for part in parts if is_dir else parts[:-1]:
                    accumulated = f"{accumulated}/{part}" if accumulated else part

                    if accumulated not in folders:
                        node = ZipNode(
                            name=part,
                            node_type="folder",
                            parent=current_parent,
                        )
                        current_parent.add_child(node)
                        folders[accumulated] = node

                    current_parent = folders[accumulated]

                if not is_dir:
                    name = parts[-1]
                    ext = PurePosixPath(name).suffix.lower()
                    supported = ext in SUPPORTED_EXTENSIONS

                    file_node = ZipNode(
                        name=name,
                        node_type="file",
                        parent=current_parent,
                        size=entry.size,
                        extension=ext,
                        supported=supported,
                        reason=None if supported else "unsupported_file_type",
                        zip_path=str(path),
                    )
                    current_parent.add_child(file_node)

        return root
