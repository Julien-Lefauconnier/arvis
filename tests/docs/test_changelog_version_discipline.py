# tests/docs/test_changelog_version_discipline.py
"""A checkout never impersonates a published release.

Campaign RELEASE-b6 (audit P0-3, 2026-09-02). Between v0.1.0b5 and
this campaign, main accumulated 50+ commits of behavior, public API
and canonical-bytes changes while pyproject, the source fallback and
every emitted payload kept saying 0.1.0b5: the checkout and the PyPI
wheel reported the SAME version for materially different code, and an
integrator following the main-branch docs against `pip install arvis`
hit an AttributeError.

The rule pinned here: whenever the changelog's ``[Unreleased]``
section carries content, the declared version must be a PEP 440
development version (``.devN``). Cutting a release empties
Unreleased; the very next change that reopens it must ride a
``.dev0`` bump, so no two different trees ever share a release
version string again.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _unreleased_body() -> str:
    if not CHANGELOG.is_file():
        pytest.skip("source checkout required (CHANGELOG.md not found)")
    text = CHANGELOG.read_text(encoding="utf-8")
    match = re.search(r"^## \[Unreleased\]\n(.*?)(?=^## \[)", text, re.S | re.M)
    assert match is not None, "CHANGELOG.md has no [Unreleased] section"
    return match.group(1).strip()


def _declared_version() -> str:
    if not PYPROJECT.is_file():
        pytest.skip("source checkout required (pyproject.toml not found)")
    with PYPROJECT.open("rb") as fh:
        data = tomllib.load(fh)
    version = data["project"]["version"]
    assert isinstance(version, str) and version
    return version


def test_a_populated_unreleased_section_requires_a_dev_version() -> None:
    body = _unreleased_body()
    version = _declared_version()

    if body:
        assert re.search(r"\.dev\d+$", version), (
            "CHANGELOG [Unreleased] carries content but the declared "
            f"version {version!r} is a release string: this checkout "
            "impersonates a published release. Bump to a .dev0 version "
            "in the same change that reopens Unreleased."
        )


def test_a_release_version_means_unreleased_is_empty() -> None:
    body = _unreleased_body()
    version = _declared_version()

    if not re.search(r"\.dev\d+$", version):
        assert body == "", (
            f"declared version {version!r} is a release string but "
            "[Unreleased] is not empty"
        )
