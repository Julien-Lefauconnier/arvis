# tests/docs/test_reason_code_registry.py
"""The reason-code registry describes codes that exist, and only those.

Fifteen of the registry's codes were labeled normative while emitted by
no code path (audit O3, 2026-08): two entire layers existed only in
Markdown. The registry now distinguishes normative/informative (emitted)
from reserved (registered, unimplemented), and this ratchet holds the
boundary in both directions:

- a normative or informative code must appear as a string literal in
  ``arvis/`` (it is emitted, or at least emittable, by real code);
- a reserved code must NOT appear: the day it is emitted, its table row
  must be promoted so its documented effect starts binding.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs" / "standard" / "ARVIS_REASON_CODE_REGISTRY.md"

_ROW = re.compile(
    r"^\| `([a-z0-9_]+)` \| \w+ \| (normative|informative|reserved) \|", re.M
)


def _registry_rows() -> list[tuple[str, str]]:
    rows = _ROW.findall(REGISTRY.read_text(encoding="utf-8"))
    assert rows, "registry table format changed; update this ratchet"
    return rows


def _source_literals() -> set[str]:
    literals: set[str] = set()
    for py in (ROOT / "arvis").rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        literals.update(re.findall(r'"([a-z0-9_]+)"', py.read_text(encoding="utf-8")))
    return literals


def test_emitted_codes_exist_and_reserved_codes_do_not() -> None:
    literals = _source_literals()
    phantom = [
        code
        for code, kind in _registry_rows()
        if kind in ("normative", "informative") and code not in literals
    ]
    unpromoted = [
        code
        for code, kind in _registry_rows()
        if kind == "reserved" and code in literals
    ]
    assert not phantom, (
        "registry codes labeled normative/informative but emitted by "
        f"nothing in arvis/: {phantom}. Mark them reserved or emit them."
    )
    assert not unpromoted, (
        f"reserved codes now emitted by arvis/: {unpromoted}. Promote "
        "their table rows so the documented effect binds."
    )
