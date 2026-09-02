# tests/docs/test_no_stale_planned_claims.py
"""No doc calls the executed M10 protocol 'planned'.

Campaign FINITION (audit #2 P2-1, 2026-09-02). HONEST-DOCS corrected
M13's three 'M10: planned' claims, and audit #2 found three more
survivors in less-travelled pages (M5, M11, M15). Six campaigns of
M10 have run; a page calling the protocol planned or not-yet-executed
contradicts the repo's central evidence. This ratchet closes the
phrase class instead of the instances.
"""

from __future__ import annotations

import re
from pathlib import Path

DOCS = Path(__file__).resolve().parents[2] / "docs"

FORBIDDEN = re.compile(
    r"M10[^.\n]{0,40}\bplanned\b"
    r"|planned[^.\n]{0,40}\bM10\b"
    r"|M10[^.\n]{0,60}not yet executed",
    re.IGNORECASE,
)


def test_no_doc_calls_the_executed_protocol_planned() -> None:
    offenders: dict[str, list[str]] = {}
    for path in sorted(DOCS.rglob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if FORBIDDEN.search(line):
                offenders.setdefault(str(path.relative_to(DOCS.parent)), []).append(
                    line.strip()[:100]
                )
    assert not offenders, (
        f"doc(s) still call the executed M10 protocol planned: {offenders}"
    )
