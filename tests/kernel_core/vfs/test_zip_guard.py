# tests/kernel_core/vfs/test_zip_guard.py

from __future__ import annotations

import zipfile

import pytest

from arvis.kernel_core.vfs.zip.guard import ZipGuard, ZipSecurityError


def _make_zip(tmp_path, name: str, files: dict[str, bytes]):
    zip_path = tmp_path / name
    with zipfile.ZipFile(zip_path, "w") as zf:
        for file_name, content in files.items():
            zf.writestr(file_name, content)
    return zip_path


def test_zip_guard_accepts_valid_zip(tmp_path) -> None:
    zip_path = _make_zip(
        tmp_path,
        "ok.zip",
        {
            "docs/a.txt": b"hello",
            "docs/b.md": b"# test",
        },
    )

    guard = ZipGuard()
    guard.validate_path(str(zip_path))


def test_zip_guard_rejects_missing_file() -> None:
    guard = ZipGuard()

    with pytest.raises(ZipSecurityError):
        guard.validate_path("/does/not/exist.zip")


def test_zip_guard_rejects_non_zip_extension(tmp_path) -> None:
    path = tmp_path / "bad.txt"
    path.write_text("nope")

    guard = ZipGuard()

    with pytest.raises(ZipSecurityError):
        guard.validate_path(str(path))


def test_zip_guard_rejects_empty_zip(tmp_path) -> None:
    zip_path = tmp_path / "empty.zip"
    with zipfile.ZipFile(zip_path, "w"):
        pass

    guard = ZipGuard()

    with pytest.raises(ZipSecurityError):
        guard.validate_path(str(zip_path))


def test_zip_guard_rejects_blocked_extension(tmp_path) -> None:
    zip_path = _make_zip(
        tmp_path,
        "bad.zip",
        {
            "run.sh": b"echo hi",
        },
    )

    guard = ZipGuard()

    with pytest.raises(ZipSecurityError):
        guard.validate_path(str(zip_path))


def test_zip_guard_rejects_path_traversal(tmp_path) -> None:
    zip_path = _make_zip(
        tmp_path,
        "bad.zip",
        {
            "../evil.txt": b"boom",
        },
    )

    guard = ZipGuard()

    with pytest.raises(ZipSecurityError):
        guard.validate_path(str(zip_path))