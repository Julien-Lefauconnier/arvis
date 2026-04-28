# arvis/kernel_core/vfs/zip/reader.py

from __future__ import annotations

import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Optional, Type, BinaryIO, Iterator, cast
from types import TracebackType


@dataclass(frozen=True)
class ZipEntry:
    """
    Safe representation of a ZIP entry.
    """

    path: str
    size: int
    is_dir: bool


class ZipSafeReader:
    """
    Safe ZIP reader:
    - no extraction to disk
    - normalized paths
    - controlled file access
    """

    def __init__(self, zip_path: str):
        self.zip_path = zip_path
        self._zip = zipfile.ZipFile(zip_path, mode="r")
        self._entries = {
            self._normalize_path(info.filename): info for info in self._zip.infolist()
        }

    def iter_entries(self) -> Iterator[ZipEntry]:
        for path, info in self._entries.items():
            yield ZipEntry(
                path=path,
                size=info.file_size,
                is_dir=path.endswith("/"),
            )

    def open_file(self, path: str) -> BinaryIO:
        norm = self._normalize_path(path)

        info = self._entries.get(norm)
        if info is None:
            raise FileNotFoundError(f"ZIP entry not found: {path}")

        if norm.endswith("/"):
            raise IsADirectoryError(f"ZIP entry is a directory: {path}")

        return cast(BinaryIO, self._zip.open(info, mode="r"))

    @staticmethod
    def _normalize_path(raw: str) -> str:
        path = PurePosixPath(raw)

        if path.is_absolute():
            raise ValueError(f"absolute path forbidden in ZIP: {raw}")

        if ".." in path.parts:
            raise ValueError(f"path traversal detected in ZIP: {raw}")

        return str(path)

    def close(self) -> None:
        self._zip.close()

    def __enter__(self) -> "ZipSafeReader":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.close()
