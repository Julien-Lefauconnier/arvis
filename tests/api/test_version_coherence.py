# tests/api/test_version_coherence.py

"""Version coherence guards.

The distributed version has a single source of truth: pyproject.toml.
These tests fail the gate whenever a human-facing copy of that version
drifts (README Versioning table, source-checkout fallback literal in
arvis.api.version), so drift is caught at commit time instead of by an
external audit (finding: README still advertised 0.1.0a1 at 0.1.0a4).

They run against the source checkout and skip in wheel-only contexts.
"""

import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT = REPO_ROOT / "pyproject.toml"
README = REPO_ROOT / "README.md"
VERSION_MODULE = REPO_ROOT / "arvis" / "api" / "version.py"


def _pyproject_version() -> str:
    if not PYPROJECT.is_file():
        pytest.skip("source checkout required (pyproject.toml not found)")
    with PYPROJECT.open("rb") as fh:
        data = tomllib.load(fh)
    version = data["project"]["version"]
    assert isinstance(version, str) and version
    return version


def test_readme_versioning_table_matches_pyproject() -> None:
    version = _pyproject_version()
    if not README.is_file():
        pytest.skip("source checkout required (README.md not found)")
    readme = README.read_text(encoding="utf-8")
    match = re.search(r"\| Package version \| `([^`]+)` \|", readme)
    assert match is not None, "README Versioning table row not found"
    assert match.group(1) == version


def test_source_checkout_fallback_mirrors_pyproject() -> None:
    version = _pyproject_version()
    if not VERSION_MODULE.is_file():
        pytest.skip("source checkout required (version.py not found)")
    source = VERSION_MODULE.read_text(encoding="utf-8")
    match = re.search(r'PACKAGE_VERSION = "([^"]+)"', source)
    assert match is not None, "source-checkout fallback literal not found"
    assert match.group(1) == version
