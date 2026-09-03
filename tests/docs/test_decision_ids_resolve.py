# tests/docs/test_decision_ids_resolve.py
"""Every decision identifier cited in the code resolves in the repo.

Campaign ACCESSIBILITY (audit #2 P2-5, 2026-09-03). The code cites
65 distinct decision identifiers (F-*** invariants, DM-** campaign
decisions, P0-*/A1x-BETA-* audit findings, D-a, DS3) that used to
resolve only in the author's private notes: an outside reader could
not tell a load-bearing invariant from a historical remark. The
docs/decisions/ pages now define every cited identifier, and this
ratchet keeps it that way in both directions: a comment citing an
undefined identifier fails the gate, and a defined identifier no
longer cited anywhere is flagged for removal.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARVIS = ROOT / "arvis"
DECISIONS = ROOT / "docs" / "decisions"

ID_PATTERN = re.compile(
    r"\b("
    r"DM-[A-Z][A-Za-z0-9]*(?:bis)?"
    r"|F-\d{3}(?:-a\d+)?"
    r"|P0-\d(?:-a\d+)?"
    r"|A1[45]-BETA-\d+"
    r"|D-a"
    r"|DS\d"
    r")\b"
)


def _cited_ids() -> set[str]:
    cited: set[str] = set()
    for path in ARVIS.rglob("*.py"):
        cited.update(ID_PATTERN.findall(path.read_text(encoding="utf-8")))
    return cited


def _defined_ids() -> set[str]:
    defined: set[str] = set()
    for page in DECISIONS.glob("*.md"):
        text = page.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("#"):
                defined.update(ID_PATTERN.findall(line))
    return defined


def test_every_cited_identifier_is_defined() -> None:
    undefined = sorted(_cited_ids() - _defined_ids())
    assert not undefined, (
        f"identifier(s) cited in arvis/ but not defined under "
        f"docs/decisions/: {undefined}. Add an entry (a heading carrying "
        "the identifier) in the matching page: INVARIANTS.md for F-***, "
        "DECISIONS.md for DM-**, AUDITS.md for the rest."
    )


def test_no_defined_identifier_is_orphaned() -> None:
    """A defined identifier nothing cites is stale documentation:
    remove the entry (or the citation drift is the bug)."""
    orphans = sorted(_defined_ids() - _cited_ids())
    assert not orphans, (
        f"identifier(s) defined under docs/decisions/ but cited nowhere "
        f"in arvis/: {orphans}"
    )


def test_the_scan_is_not_vacuous() -> None:
    cited = _cited_ids()
    assert len(cited) >= 40, f"the citation scan collapsed: {len(cited)} ids"
    assert (DECISIONS / "README.md").is_file()
