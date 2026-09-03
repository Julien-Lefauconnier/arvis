# tests/docs/test_citation_metadata.py
"""The citation surfaces agree, or the gate says so.

Campaign CITATION (2026-09-03). The preprint has a permanent DOI, and
that DOI now appears in three places a reader can reach independently:
the README badge, the "Citing ARVIS" section, and CITATION.cff (which
GitHub and reference managers parse). Three hand-maintained copies of
one identifier is exactly the arrangement that drifts: a corrected
title in the README while the machine-readable record keeps the old
one produces citations that disagree with the paper, silently and
forever, because a citation is copied and never revisited.

This module pins the agreement rather than the values: the DOI, the
paper title and the repository URL are read FROM CITATION.cff and
required to be present in the prose. Publishing a new version of the
preprint means editing the .cff, and the README then has to follow.

It also refuses the one drift the file invites by construction: an
optional top-level ``version:`` that no release process updates. It
may be absent (the current choice, documented in the file), but if it
is there it must equal the declared package version.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CITATION = REPO_ROOT / "CITATION.cff"
README = REPO_ROOT / "README.md"
DOCS_INDEX = REPO_ROOT / "docs" / "README.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"

# Citation File Format version this file is written against. Bumping it
# is a deliberate act: the schema changed under us.
CFF_VERSION = "1.2.0"

_EMPHASIS = re.compile(r"[*_]")
_BLOCKQUOTE = re.compile(r"^\s*>\s?", re.M)


def _load_citation() -> dict[str, Any]:
    if not CITATION.is_file():
        pytest.skip("source checkout required (CITATION.cff not found)")
    data = yaml.safe_load(CITATION.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "CITATION.cff must parse to a mapping"
    return data


def _read(path: Path) -> str:
    if not path.is_file():
        pytest.skip(f"source checkout required ({path.name} not found)")
    return path.read_text(encoding="utf-8")


def _prose(text: str) -> str:
    """Markdown prose reduced to comparable words.

    Blockquote markers, emphasis and line wrapping are presentation:
    a title split across three quoted lines is the same title.
    """
    stripped = _EMPHASIS.sub("", _BLOCKQUOTE.sub("", text))
    return " ".join(stripped.split())


def test_the_citation_file_carries_a_complete_record() -> None:
    data = _load_citation()

    assert data.get("cff-version") == CFF_VERSION, (
        f"CITATION.cff declares cff-version {data.get('cff-version')!r}; "
        f"this repository is written against {CFF_VERSION}"
    )
    for key in ("message", "title", "type", "authors", "repository-code", "license"):
        assert data.get(key), f"CITATION.cff is missing the required key {key!r}"

    authors = data["authors"]
    assert isinstance(authors, list) and authors, "CITATION.cff lists no author"
    for author in authors:
        assert author.get("family-names") and author.get("given-names"), (
            "every CITATION.cff author needs family-names and given-names"
        )


def test_the_preferred_citation_is_the_preprint() -> None:
    preferred = _load_citation().get("preferred-citation")
    assert isinstance(preferred, dict), (
        "CITATION.cff must carry a preferred-citation: the paper states the "
        "claims and their limits, the repository does not"
    )
    for key in ("type", "title", "authors", "year", "doi", "url"):
        assert preferred.get(key), f"preferred-citation is missing {key!r}"

    doi = str(preferred["doi"])
    assert not doi.startswith("http"), (
        f"preferred-citation.doi must be the bare DOI, not a URL: {doi!r}"
    )
    assert preferred["url"] == f"https://doi.org/{doi}", (
        "preferred-citation.url must resolve the declared DOI so the two "
        "fields cannot point at different records"
    )


def test_the_doi_is_identical_everywhere_a_reader_finds_it() -> None:
    doi = str(_load_citation()["preferred-citation"]["doi"])
    readme = _read(README)

    assert f"https://doi.org/{doi}" in readme, (
        f"README.md does not resolve the DOI {doi} declared in CITATION.cff"
    )
    assert f"zenodo.org/badge/DOI/{doi}.svg" in readme, (
        f"the README DOI badge does not point at {doi}: the badge and the "
        "citation file name different records"
    )
    assert f"https://doi.org/{doi}" in _read(DOCS_INDEX), (
        f"docs/README.md does not resolve the DOI {doi}: the documentation "
        "map sends a citing reader somewhere else"
    )


def test_the_paper_title_and_repository_agree_with_the_prose() -> None:
    data = _load_citation()
    readme = _prose(_read(README))

    title = _prose(str(data["preferred-citation"]["title"]))
    assert title in readme, (
        "README.md does not quote the preprint title declared in "
        f"CITATION.cff:\n  {title}"
    )

    repository = str(data["repository-code"])
    assert repository in _read(README), (
        f"CITATION.cff points at {repository}, which the README never names"
    )


def test_the_declared_license_matches_the_packaged_one() -> None:
    with PYPROJECT.open("rb") as handle:
        project = tomllib.load(handle)["project"]

    assert _load_citation()["license"] == project["license"], (
        "CITATION.cff and pyproject.toml declare different licenses; the "
        "one a citing reader sees must be the one that ships"
    )


def test_an_optional_version_is_not_allowed_to_drift() -> None:
    version = _load_citation().get("version")
    if version is None:
        return  # The documented choice: no version, nothing to drift.

    with PYPROJECT.open("rb") as handle:
        declared = tomllib.load(handle)["project"]["version"]

    assert str(version) == declared, (
        f"CITATION.cff pins version {version!r} while the package declares "
        f"{declared!r}: remove the key or update it with the release"
    )
