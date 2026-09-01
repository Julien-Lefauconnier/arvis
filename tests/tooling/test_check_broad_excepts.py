# tests/tooling/test_check_broad_excepts.py
"""The broad-except gate ratchet catches silent swallowers and
accepts the honest patterns (campaign FIX, LOT F2)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from check_broad_excepts import ROOT, check  # noqa: E402


def _violations(tmp_path: Path, body: str) -> list[str]:
    p = tmp_path / "probe.py"
    p.write_text(body)
    return check([p])


def test_silent_swallower_is_flagged(tmp_path: Path) -> None:
    out = _violations(
        tmp_path,
        "try:\n    x = 1\nexcept Exception:\n    pass\n",
    )

    assert len(out) == 1
    assert "swallows silently" in out[0]


def test_honest_patterns_are_accepted(tmp_path: Path) -> None:
    body = (
        "def a():\n"
        "    try:\n"
        "        x = 1\n"
        "    except Exception as e:\n"
        "        raise ValueError('typed') from e\n"
        "def b(mgr, ctx):\n"
        "    try:\n"
        "        x = 1\n"
        "    except Exception as exc:\n"
        "        mgr.capture_exception(ctx, exc)\n"
        "def c():\n"
        "    try:\n"
        "        x = 1\n"
        "    except Exception:  # arvis-broad: probe justification\n"
        "        pass\n"
    )

    assert _violations(tmp_path, body) == []


def test_the_tree_is_clean() -> None:
    assert check(sorted((ROOT / "arvis").rglob("*.py"))) == []
