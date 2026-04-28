# tests/kernel_core/vfs/test_zip_reader.py

from __future__ import annotations

import zipfile

import pytest

from arvis.kernel_core.vfs.zip.reader import ZipSafeReader


def _make_zip(tmp_path, files: dict[str, bytes]):
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return zip_path


def test_zip_reader_iter_entries(tmp_path) -> None:
    zip_path = _make_zip(
        tmp_path,
        {
            "docs/a.txt": b"hello",
            "docs/b.md": b"# test",
        },
    )

    with ZipSafeReader(str(zip_path)) as reader:
        paths = [entry.path for entry in reader.iter_entries()]

    assert "docs/a.txt" in paths
    assert "docs/b.md" in paths


def test_zip_reader_open_file(tmp_path) -> None:
    zip_path = _make_zip(
        tmp_path,
        {
            "docs/a.txt": b"hello",
        },
    )

    with ZipSafeReader(str(zip_path)) as reader:
        with reader.open_file("docs/a.txt") as raw:
            content = raw.read()

    assert content == b"hello"


def test_zip_reader_missing_entry(tmp_path) -> None:
    zip_path = _make_zip(
        tmp_path,
        {
            "docs/a.txt": b"hello",
        },
    )

    with ZipSafeReader(str(zip_path)) as reader:
        with pytest.raises(FileNotFoundError):
            reader.open_file("missing.txt")


def test_zip_reader_rejects_absolute_path_normalization() -> None:
    with pytest.raises(ValueError):
        ZipSafeReader._normalize_path("/etc/passwd")


def test_zip_reader_rejects_traversal_normalization() -> None:
    with pytest.raises(ValueError):
        ZipSafeReader._normalize_path("../evil.txt")
