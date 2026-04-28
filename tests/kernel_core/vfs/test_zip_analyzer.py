# tests/kernel_core/vfs/test_zip_analyzer.py

from __future__ import annotations

import zipfile

from arvis.kernel_core.vfs.zip.analyzer import ZipAnalyzer


def _make_zip(tmp_path, files: dict[str, bytes]):
    zip_path = tmp_path / "test.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return zip_path


def test_zip_analyzer_builds_tree(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ENV", "test")

    zip_path = _make_zip(
        tmp_path,
        {
            "docs/a.txt": b"hello",
            "docs/sub/b.md": b"# test",
        },
    )

    analyzer = ZipAnalyzer()
    root = analyzer.analyze(str(zip_path))

    all_nodes = root.iter_tree()
    names = [node.name for node in all_nodes]

    assert "/" in names
    assert "docs" in names
    assert "sub" in names
    assert "a.txt" in names
    assert "b.md" in names


def test_zip_analyzer_marks_supported_and_unsupported_files(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("ENV", "test")

    zip_path = _make_zip(
        tmp_path,
        {
            "docs/a.txt": b"hello",
            "docs/b.xyz": b"unknown",
        },
    )

    analyzer = ZipAnalyzer()
    root = analyzer.analyze(str(zip_path))

    file_nodes = [node for node in root.iter_tree() if node.is_file()]
    by_name = {node.name: node for node in file_nodes}

    assert by_name["a.txt"].supported is True
    assert by_name["a.txt"].reason is None

    assert by_name["b.xyz"].supported is False
    assert by_name["b.xyz"].reason == "unsupported_file_type"


def test_zip_analyzer_sets_zip_path_for_files(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ENV", "test")

    zip_path = _make_zip(
        tmp_path,
        {
            "docs/a.txt": b"hello",
        },
    )

    analyzer = ZipAnalyzer()
    root = analyzer.analyze(str(zip_path))

    file_nodes = [node for node in root.iter_tree() if node.is_file()]
    assert len(file_nodes) == 1
    assert file_nodes[0].zip_path == "docs/a.txt"
