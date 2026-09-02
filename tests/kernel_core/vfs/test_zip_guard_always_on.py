# tests/kernel_core/vfs/test_zip_guard_always_on.py
"""Campaign KERNEL (LOT K3), RED-first: the ZIP firewall cannot be
switched off by the environment.

``ZipAnalyzer.__init__`` read ``os.getenv("ENV")`` and dropped its
guard entirely when it equalled "test". An ambient variable, set by
any deployment or CI shell for unrelated reasons, therefore removed
the file-count cap, the total and per-file size caps, the compression
-ratio (zip-bomb) check and the blocked-extension list. A protection
whose presence depends on the environment is a monotone-hardening
violation (F-001) whatever the intent, and this one guards an archive
ingestion path.

The guard is now always constructed; a caller that needs different
limits injects a configured ZipGuard, which is a decision at the call
site rather than an ambient one.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from arvis.kernel_core.vfs.zip.analyzer import ZipAnalyzer
from arvis.kernel_core.vfs.zip.guard import ZipGuard, ZipSecurityError


def _zip(tmp_path: Path, name: str = "t.zip") -> Path:
    path = tmp_path / name
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("docs/a.txt", b"hello")
    return path


def test_the_guard_is_present_whatever_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ENV", "test")

    assert ZipAnalyzer().guard is not None

    monkeypatch.setenv("ENV", "production")
    assert ZipAnalyzer().guard is not None

    monkeypatch.delenv("ENV", raising=False)
    assert ZipAnalyzer().guard is not None


def test_a_blocked_extension_is_refused_under_env_test(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The concrete consequence: an executable payload used to sail
    through whenever ENV happened to be "test"."""
    monkeypatch.setenv("ENV", "test")
    path = tmp_path / "payload.zip"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("setup.exe", b"MZ")

    with pytest.raises(ZipSecurityError):
        ZipAnalyzer().analyze(str(path))


def test_an_ordinary_archive_still_analyzes(tmp_path: Path) -> None:
    root = ZipAnalyzer().analyze(str(_zip(tmp_path)))

    assert [n.name for n in root.iter_tree() if n.name == "a.txt"]


def test_a_caller_may_inject_configured_limits(tmp_path: Path) -> None:
    """Injection at the call site replaces the ambient switch."""
    guard = ZipGuard()

    analyzer = ZipAnalyzer(guard=guard)

    assert analyzer.guard is guard


def test_an_omitted_supported_flag_stays_unknown() -> None:
    """Campaign KERNEL (LOT K3): the dataclass default is None
    ("not assessed"), but deserialization defaulted it to True, so a
    payload omitting the flag came back asserting support that nobody
    had determined. The flag is advisory metadata for the host, not a
    gate, which makes a fabricated True purely misleading."""
    from arvis.kernel_core.syscalls.syscalls.vfs_syscalls import (
        _deserialize_zip_node,
    )

    node = _deserialize_zip_node({"name": "a.bin", "node_type": "file"})

    assert node.supported is None

    assessed = _deserialize_zip_node(
        {"name": "a.txt", "node_type": "file", "supported": True}
    )
    assert assessed.supported is True
