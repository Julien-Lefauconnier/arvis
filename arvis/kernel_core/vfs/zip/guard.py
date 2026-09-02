# arvis/kernel_core/vfs/zip/guard.py

from __future__ import annotations

import os
import zipfile
from pathlib import Path

from arvis.errors import ArvisSecurityError


class ZipSecurityError(ArvisSecurityError):
    """Blocking security error raised during ZIP validation."""


class ZipConfigurationError(ArvisSecurityError):
    """A ZIP ingestion limit is misconfigured in the environment.

    Raised at guard construction, never at import time, and always
    naming the offending variable (DM-H6, campaign HARDEN).
    """


_LIMIT_DEFAULTS: dict[str, float] = {
    "ZIP_MAX_TOTAL_SIZE": 500 * 1024 * 1024,
    "ZIP_MAX_FILE_COUNT": 5_000,
    "ZIP_MAX_FILE_SIZE": 100 * 1024 * 1024,
    "ZIP_MAX_COMPRESSION_RATIO": 100.0,
}


def _resolve_limit(name: str, *, as_int: bool) -> int | float:
    """Resolve one ingestion limit from the environment, validated.

    DM-H6 (campaign HARDEN, audit P1-14): the prefixed ``ARVIS_<name>``
    wins; the legacy unprefixed ``<name>`` stays honored during the
    beta as a deprecated fallback (docs/CONFIGURATION.md). Resolution
    happens at guard construction, never at import: a malformed or
    non-positive value raises :class:`ZipConfigurationError` naming
    the variable instead of crashing ``import arvis`` with a bare
    ValueError, and it can never silently fall back to a default.
    """
    prefixed = f"ARVIS_{name}"
    for variable in (prefixed, name):
        raw = os.getenv(variable)
        if raw is None:
            continue
        try:
            value = int(raw) if as_int else float(raw)
        except ValueError as exc:
            raise ZipConfigurationError(
                f"{variable} must be a positive number, got {raw!r}"
            ) from exc
        if value <= 0:
            raise ZipConfigurationError(
                f"{variable} must be a positive number, got {raw!r}"
            )
        return value
    default = _LIMIT_DEFAULTS[name]
    return int(default) if as_int else float(default)


def effective_zip_limits() -> dict[str, int | float]:
    """The ingestion limits currently in force, for the governance
    fingerprint (a deployment that loosens a cap through the
    environment is a differently governed deployment)."""
    return {
        "max_total_uncompressed_size": _resolve_limit(
            "ZIP_MAX_TOTAL_SIZE", as_int=True
        ),
        "max_file_count": _resolve_limit("ZIP_MAX_FILE_COUNT", as_int=True),
        "max_file_size": _resolve_limit("ZIP_MAX_FILE_SIZE", as_int=True),
        "max_compression_ratio": _resolve_limit(
            "ZIP_MAX_COMPRESSION_RATIO", as_int=False
        ),
    }


class ZipGuard:
    """
    Security firewall for ZIP archives.

    Responsibilities:
    - reject ZIP bombs
    - reject unsafe paths
    - reject forbidden extensions
    - enforce size and file-count limits

    Limits resolve at construction (env, validated; DM-H6) unless the
    call site injects explicit values, which always win.
    """

    def __init__(
        self,
        *,
        max_total_uncompressed_size: int | None = None,
        max_file_count: int | None = None,
        max_file_size: int | None = None,
        max_compression_ratio: float | None = None,
    ) -> None:
        self.MAX_TOTAL_UNCOMPRESSED_SIZE = (
            max_total_uncompressed_size
            if max_total_uncompressed_size is not None
            else int(_resolve_limit("ZIP_MAX_TOTAL_SIZE", as_int=True))
        )
        self.MAX_FILE_COUNT = (
            max_file_count
            if max_file_count is not None
            else int(_resolve_limit("ZIP_MAX_FILE_COUNT", as_int=True))
        )
        self.MAX_FILE_SIZE = (
            max_file_size
            if max_file_size is not None
            else int(_resolve_limit("ZIP_MAX_FILE_SIZE", as_int=True))
        )
        self.MAX_COMPRESSION_RATIO = (
            max_compression_ratio
            if max_compression_ratio is not None
            else float(_resolve_limit("ZIP_MAX_COMPRESSION_RATIO", as_int=False))
        )

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
