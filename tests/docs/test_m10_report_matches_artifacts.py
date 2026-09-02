# tests/docs/test_m10_report_matches_artifacts.py
"""The report's current headline numbers match the tracked artifacts.

Campaign HONEST-DOCS (LOT H2, audit P1-3/P1-4, 2026-09-02). The
integral audit found eight places where the M10 report quoted numbers
its own republished artifacts contradicted, plus one conclusion a
later fix had inverted; nothing caught it because no test compares
the prose to the artifacts. This ratchet greps the CURRENT headline
numbers (M10 section 15.3 and the PATH_TO_ALLOW table) against the
tracked ``judgment.json`` and ``metrics.json``: a republication that
moves a headline without moving the prose fails the gate. Historical
sections (10 through 14) are stamped, not checked; section 16
documents the reading rules.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
M10 = (
    ROOT
    / "docs"
    / "math"
    / ("M10_empirical_stability_validation_and_runtime_validation.md")
)
PATH_TO_ALLOW = ROOT / "docs" / "PATH_TO_ALLOW.md"
ARTIFACTS = {
    "d1": ROOT / "validation" / "m10" / "artifacts",
    "d2": ROOT / "validation" / "m10" / "artifacts_d2",
}


def _counts(corpus: str) -> dict[str, int]:
    metrics = json.loads((ARTIFACTS[corpus] / "metrics.json").read_text())
    overall = metrics["overall"]
    turns = int(overall["adaptive_estimation"]["turns"])
    rates = overall["gate_distribution"]["overall"]
    counts = {verdict: round(float(rate) * turns) for verdict, rate in rates.items()}
    counts["turns"] = turns
    return counts


def _violation_rate(corpus: str) -> float:
    metrics = json.loads((ARTIFACTS[corpus] / "metrics.json").read_text())
    return float(metrics["overall"]["kappa_violations"]["violation_rate"])


def _judgment_summary(corpus: str) -> tuple[int, int]:
    judgment = json.loads((ARTIFACTS[corpus] / "judgment.json").read_text())
    summary = judgment["_summary"]
    return int(summary["passed"]), int(summary["failed"])


def _require(path: Path) -> str:
    if not path.is_file():
        pytest.skip(f"source checkout required ({path.name} not found)")
    return path.read_text(encoding="utf-8")


def test_section_15_3_verdict_table_matches_the_artifacts() -> None:
    text = _require(M10)
    d1 = _counts("d1")
    d2 = _counts("d2")

    rows = {
        "ALLOW": ("ALLOW", d1["ALLOW"], d2["ALLOW"]),
        "REQUIRES_CONFIRMATION": (
            "REQUIRES_CONFIRMATION",
            d1["REQUIRE_CONFIRMATION"],
            d2["REQUIRE_CONFIRMATION"],
        ),
        "ABSTAIN": ("ABSTAIN", d1["ABSTAIN"], d2["ABSTAIN"]),
    }
    for label, (verdict, current_d1, current_d2) in rows.items():
        pattern = rf"\| {verdict} \| \d+ -> (\d+) \| \d+ -> (\d+) \|"
        match = re.search(pattern, text)
        assert match is not None, f"section 15.3 row for {label} not found"
        assert int(match.group(1)) == current_d1, (
            f"section 15.3 {label} D-1.0 says {match.group(1)}, "
            f"artifacts say {current_d1}"
        )
        assert int(match.group(2)) == current_d2, (
            f"section 15.3 {label} D-2.0 says {match.group(2)}, "
            f"artifacts say {current_d2}"
        )


def test_path_to_allow_table_matches_the_artifacts() -> None:
    text = _require(PATH_TO_ALLOW)
    d1 = _counts("d1")
    d2 = _counts("d2")

    allow = re.search(
        r"\| ALLOW \| (\d+) \(([\d.]+)%\) \| (\d+) \(([\d.]+)%\) \|", text
    )
    assert allow is not None, "PATH_TO_ALLOW ALLOW row not found"
    assert int(allow.group(1)) == d1["ALLOW"]
    assert int(allow.group(3)) == d2["ALLOW"]
    assert float(allow.group(2)) == round(100 * d1["ALLOW"] / d1["turns"], 2)
    assert float(allow.group(4)) == round(100 * d2["ALLOW"] / d2["turns"], 2)

    rc = re.search(r"\| REQUIRES_CONFIRMATION \| (\d+) \| (\d+) \|", text)
    assert rc is not None, "PATH_TO_ALLOW REQUIRES_CONFIRMATION row not found"
    assert int(rc.group(1)) == d1["REQUIRE_CONFIRMATION"]
    assert int(rc.group(2)) == d2["REQUIRE_CONFIRMATION"]

    abstain = re.search(r"\| ABSTAIN \| (\d+) \| (\d+) \|", text)
    assert abstain is not None, "PATH_TO_ALLOW ABSTAIN row not found"
    assert int(abstain.group(1)) == d1["ABSTAIN"]
    assert int(abstain.group(2)) == d2["ABSTAIN"]


def test_section_16_violation_rates_match_the_artifacts() -> None:
    text = _require(M10)
    d1 = round(_violation_rate("d1"), 3)
    d2 = round(_violation_rate("d2"), 3)

    assert f"is {d1} on D-1.0" in text, (
        f"section 16.2 D-1.0 violation rate is stale (artifacts: {d1})"
    )
    assert f"and {d2} on D-2.0" in text, (
        f"section 16.2 D-2.0 violation rate is stale (artifacts: {d2})"
    )


def test_judgment_summaries_match_the_headline() -> None:
    """Both judgments as the docs quote them everywhere: 11 of 12 on
    D-1.0 (5.1 reported failed) and 12 of 12 on D-2.0."""
    assert _judgment_summary("d1") == (11, 1)
    assert _judgment_summary("d2") == (12, 0)
