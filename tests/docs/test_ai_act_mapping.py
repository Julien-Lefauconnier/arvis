# tests/docs/test_ai_act_mapping.py
"""The EU AI Act capability mapping stays honest and resolvable.

Campaign AI-ACT-MAP (2026-09-03). The mapping page claims mechanisms
by their decision identifiers and rates coverage in a closed status
vocabulary; this test keeps both loud: an identifier the decisions
pages do not define, a status outside the vocabulary, a summary row
without its section (or the reverse), or a dropped disclaimer fails
the gate. The Markdown gate already checks the page's path
references.
"""

from __future__ import annotations

import re
from pathlib import Path

from tests.docs.test_decision_ids_resolve import ID_PATTERN, _defined_ids

ROOT = Path(__file__).resolve().parents[2]
MAPPING = ROOT / "docs" / "compliance" / "EU_AI_ACT_CAPABILITY_MAPPING.md"

DISCLAIMER = (
    "This page is a capability mapping, not legal advice, and not a "
    "conformity assessment."
)

ALLOWED_STATUSES = {"Provided", "Partial", "Host obligation", "Out of scope"}


def _text() -> str:
    return MAPPING.read_text(encoding="utf-8")


def test_every_cited_identifier_resolves() -> None:
    cited = set(ID_PATTERN.findall(_text()))
    undefined = sorted(cited - _defined_ids())
    assert not undefined, (
        f"identifier(s) cited in the AI Act mapping but not defined "
        f"under docs/decisions/: {undefined}"
    )
    assert len(cited) >= 10, f"the mapping cites too few anchors: {len(cited)}"


def test_the_disclaimer_is_present_verbatim() -> None:
    assert DISCLAIMER in " ".join(_text().split()), (
        "the capability-mapping disclaimer was changed or removed; it is "
        "the sentence that keeps this page from being read as a "
        "compliance claim"
    )


def test_statuses_use_the_closed_vocabulary() -> None:
    statuses = re.findall(r"\*\*Status: ([^.*]+)\.\*\*", _text())
    assert len(statuses) >= 6, f"too few status lines: {statuses}"
    unknown = sorted(set(statuses) - ALLOWED_STATUSES)
    assert not unknown, f"status(es) outside the closed vocabulary: {unknown}"


def test_summary_table_matches_the_sections() -> None:
    text = _text()
    table_articles = set(re.findall(r"^\| (Article \d+) \|", text, re.M))
    section_articles = set(re.findall(r"^## (Article \d+):", text, re.M))
    assert table_articles == section_articles, (
        f"summary table and article sections disagree: "
        f"table only {sorted(table_articles - section_articles)}, "
        f"sections only {sorted(section_articles - table_articles)}"
    )
    assert len(section_articles) >= 6
