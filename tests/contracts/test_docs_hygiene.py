# tests/contracts/test_docs_hygiene.py

"""Editorial hygiene ratchet for the documentation corpus (a16).

The a15 audit found docs/math/M4 duplicated in full, glued together by
French conversational text from an LLM session ("Tu peux copier-coller
cette version directement... Prêt pour le document suivant ?"). The
doctrinal sweeps of previous campaigns hunted overclaims, not editorial
debt, and missed it. Two mechanical rules now hold:

- every mathematical document carries exactly one H1 title (fenced code
  blocks ignored): a pasted duplicate necessarily brings a second one;
- no conversational session residue anywhere in docs/.
"""

import pathlib

import pytest

_DOCS = pathlib.Path(__file__).resolve().parents[2] / "docs"
_MATH_DOCS = sorted((_DOCS / "math").glob("*.md"))
_ALL_DOCS = sorted(_DOCS.rglob("*.md"))

_CONVERSATIONAL_RESIDUE = (
    "copier-coller",
    "Envoie-le-moi",
    "Prêt pour le document",
    "Tu peux copier",
)


def _h1_count_outside_code(text: str) -> int:
    count = 0
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence and line.startswith("# "):
            count += 1
    return count


@pytest.mark.parametrize("path", _MATH_DOCS, ids=[p.name for p in _MATH_DOCS])
def test_math_doc_has_exactly_one_title(path: pathlib.Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert _h1_count_outside_code(text) == 1, (
        f"{path.name}: multiple H1 titles outside code blocks; "
        "a pasted duplicate is the usual cause"
    )
    # The M4 defect glued the second title mid-line after a dialogue
    # sentence; catch inline occurrences of a repeated title too.
    title = text.splitlines()[0]
    assert text.count(title) == 1, f"{path.name}: the H1 title appears more than once"


@pytest.mark.parametrize(
    "path", _ALL_DOCS, ids=[str(p.relative_to(_DOCS)) for p in _ALL_DOCS]
)
def test_doc_carries_no_conversational_residue(path: pathlib.Path) -> None:
    text = path.read_text(encoding="utf-8")
    hits = [motif for motif in _CONVERSATIONAL_RESIDUE if motif in text]
    assert not hits, f"{path.name}: conversational session residue {hits}"
