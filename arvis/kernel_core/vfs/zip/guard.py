# arvis/kernel_core/vfs/zip/guard.py

from __future__ import annotations

import os
import zipfile
from pathlib import Path


class ZipSecurityError(RuntimeError):
    """Blocking security error raised during ZIP validation."""


class ZipGuard:
    """
    Security firewall for ZIP archives.

    Responsibilities:
    - reject ZIP bombs
    - reject unsafe paths
    - reject forbidden extensions
    - enforce size and file-count limits
    """

    MAX_TOTAL_UNCOMPRESSED_SIZE = int(
        os.getenv("ZIP_MAX_TOTAL_SIZE", 500 * 1024 * 1024)
    )
    MAX_FILE_COUNT = int(os.getenv("ZIP_MAX_FILE_COUNT", 5_000))
    MAX_FILE_SIZE = int(os.getenv("ZIP_MAX_FILE_SIZE", 100 * 1024 * 1024))
    MAX_COMPRESSION_RATIO = float(os.getenv("ZIP_MAX_COMPRESSION_RATIO", 100.0))

    BLOCKED_EXTENSIONS = {
        ".exe",
        ".dll",
        ".bat",
        ".cmd",
        ".sh",
        ".js",
        ".jar",
        ".py",
        ".php",
        ".pl",
        ".rb",
        ".so",
        ".bin",
    }

    def validate_path(self, zip_path: str) -> None:
        path = Path(zip_path)

        if not path.exists():
            raise ZipSecurityError("zip file does not exist")

        if not path.is_file():
            raise ZipSecurityError("zip path is not a file")

        if path.suffix.lower() != ".zip":
            raise ZipSecurityError("file is not a ZIP archive")

        try:
            with zipfile.ZipFile(path) as zf:
                self._validate_zip(zf)
        except zipfile.BadZipFile as exc:
            raise ZipSecurityError("invalid or corrupted ZIP file") from exc

    def _validate_zip(self, zf: zipfile.ZipFile) -> None:
        infos = zf.infolist()

        if not infos:
            raise ZipSecurityError("ZIP archive is empty")

        if len(infos) > self.MAX_FILE_COUNT:
            raise ZipSecurityError(
                f"ZIP contains too many files ({len(infos)} > {self.MAX_FILE_COUNT})"
            )

        total_uncompressed = 0

        for info in infos:
            self._validate_entry(info)

            total_uncompressed += info.file_size

            if info.file_size > self.MAX_FILE_SIZE:
                raise ZipSecurityError(f"file too large in ZIP: {info.filename}")

            if info.compress_size > 0:
                ratio = info.file_size / info.compress_size
                if ratio > self.MAX_COMPRESSION_RATIO:
                    raise ZipSecurityError(
                        f"suspicious compression ratio in {info.filename} ({ratio:.1f})"
                    )

        if total_uncompressed > self.MAX_TOTAL_UNCOMPRESSED_SIZE:
            raise ZipSecurityError(
                f"ZIP total uncompressed size too large ({total_uncompressed} bytes)"
            )

    def _validate_entry(self, info: zipfile.ZipInfo) -> None:
        name = info.filename
        path = Path(name)

        if path.is_absolute():
            raise ZipSecurityError(f"absolute path forbidden: {name}")

        if ".." in path.parts:
            raise ZipSecurityError(f"path traversal detected: {name}")

        if name.endswith("/"):
            return

        ext = path.suffix.lower()
        if ext in self.BLOCKED_EXTENSIONS:
            raise ZipSecurityError(f"forbidden file type in ZIP: {name}")
