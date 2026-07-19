"""Keep the pinned security scanner wired identically in local and CI gates."""

from __future__ import annotations

import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_bandit_is_exactly_pinned_in_dev_dependencies() -> None:
    with (REPOSITORY_ROOT / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)

    dev_dependencies = project["project"]["optional-dependencies"]["dev"]
    bandit_dependencies = [
        dependency
        for dependency in dev_dependencies
        if dependency.lower().startswith("bandit")
    ]

    assert bandit_dependencies == ["bandit==1.9.4"]


def test_ci_uses_the_shared_security_gate_and_wheel_check() -> None:
    quality_gate = (REPOSITORY_ROOT / "scripts/run_quality_gate.sh").read_text(
        encoding="utf-8"
    )
    workflow = (REPOSITORY_ROOT / ".github/workflows/CI.yml").read_text(
        encoding="utf-8"
    )

    assert '"$PY" -m bandit -r arvis -ll -q' in quality_gate
    assert "bash scripts/run_quality_gate.sh security" in workflow
    assert "python scripts/check_wheel_contents.py dist/*.whl" in workflow
