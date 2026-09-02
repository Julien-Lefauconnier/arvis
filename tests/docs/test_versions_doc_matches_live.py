# tests/docs/test_versions_doc_matches_live.py
"""docs/VERSIONS.md states the live version constants.

Campaign FINITION (audit #2 P1-A, 2026-09-02). The page whose only
job is to be the map of the version constants still displayed the
pre-b6 values (canonicalization 3, commitment 5, confirmation 4,
redaction 5) one release after RELEASE-b6 bumped all four, and still
described the pre-HARDEN IR_VERSION naming. Same structural cause as
the M10 drift the doc-vs-artifact ratchet closed: no test compared
the prose to the code. This one does, with the same recipe: every
constant the doc tables state is read live and grepped back.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

DOC = Path(__file__).resolve().parents[2] / "docs" / "VERSIONS.md"


def _doc() -> str:
    if not DOC.is_file():
        pytest.skip("source checkout required (docs/VERSIONS.md not found)")
    return DOC.read_text(encoding="utf-8")


def _live_values() -> dict[str, str]:
    from arvis import RESULT_SCHEMA_VERSION
    from arvis.api.commitment import COMMITMENT_VERSION
    from arvis.api.ir import IR_ENVELOPE_VERSION
    from arvis.ir.version import IR_SCHEMA_VERSION
    from arvis.kernel_core.canonicalization import CANONICALIZATION_VERSION
    from arvis.kernel_core.syscalls.engagement import REDACTION_POLICY_VERSION
    from arvis.math.stability.hard_block_policy import HARD_BLOCK_TABLE_VERSION
    from arvis.tools.confirmation import CONFIRMATION_FORMAT_VERSION
    from arvis.tools.registry import MANIFEST_SCHEMA_VERSION

    return {
        "CANONICALIZATION_VERSION": str(CANONICALIZATION_VERSION),
        "COMMITMENT_VERSION": str(COMMITMENT_VERSION),
        "CONFIRMATION_FORMAT_VERSION": str(CONFIRMATION_FORMAT_VERSION),
        "REDACTION_POLICY_VERSION": str(REDACTION_POLICY_VERSION),
        "MANIFEST_SCHEMA_VERSION": str(MANIFEST_SCHEMA_VERSION),
        "HARD_BLOCK_TABLE_VERSION": str(HARD_BLOCK_TABLE_VERSION),
        "IR_ENVELOPE_VERSION": str(IR_ENVELOPE_VERSION),
        "IR_SCHEMA_VERSION": str(IR_SCHEMA_VERSION),
        "RESULT_SCHEMA_VERSION": str(RESULT_SCHEMA_VERSION),
    }


def _doc_value(text: str, constant: str) -> str | None:
    """The value a doc table row states for a constant, if present."""
    pattern = (
        rf"\|[^|\n]*`(?:[a-z_][a-z_.]*\.)?{re.escape(constant)}`"
        rf"[^|\n]*\|\s*`?([^`|\n]+?)`?\s*\|"
    )
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def test_every_stated_constant_matches_the_live_value() -> None:
    text = _doc()
    stale = {}
    for constant, live in _live_values().items():
        stated = _doc_value(text, constant)
        if stated is None:
            stale[constant] = "missing from the doc tables"
        elif stated != live:
            stale[constant] = f"doc says {stated!r}, live value is {live!r}"
    assert not stale, (
        f"docs/VERSIONS.md is stale: {stale}. Update the map in the same "
        "change that moves a version constant."
    )


def test_the_old_ir_naming_stays_retired() -> None:
    """DM-H9e renamed the three IR_VERSION constants by meaning; the
    map must describe the current names, not the retired confusion."""
    text = _doc()
    assert "IR_ENVELOPE_VERSION" in text
    assert "IR_SCHEMA_VERSION" in text
    assert "Two constants are called `IR_VERSION`" not in text
