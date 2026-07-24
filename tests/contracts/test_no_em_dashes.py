# tests/contracts/test_no_em_dashes.py

"""Ratchet: no em-dash anywhere in the repository (a15, A14-P2-02).

CONTRIBUTING.md forbids em-dashes in code and documentation. Until a15
the rule was only enforced on the package, the tests and the README;
the documentation corpus carried ~176 of them, making the contribution
guide untrue. The corpus is now clean and this ratchet keeps the whole
repository that way: prose punctuation uses commas, semicolons, colons
or parentheses instead.
"""

import pathlib

_ROOT = pathlib.Path(__file__).resolve().parents[2]
_SKIP_PARTS = {
    ".git",
    "__pycache__",
    ".hypothesis",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "build",
    "dist",
    "node_modules",
}
_EXTENSIONS = {".py", ".md", ".toml", ".yml", ".yaml", ".sh", ".txt", ".json"}


def _tracked_files() -> list[pathlib.Path]:
    files = []
    for path in _ROOT.rglob("*"):
        if not path.is_file() or path.suffix not in _EXTENSIONS:
            continue
        if any(part in _SKIP_PARTS for part in path.parts):
            continue
        if ".egg-info" in str(path):
            continue
        files.append(path)
    return files


def test_repository_contains_no_em_dash() -> None:
    offenders = []
    for path in _tracked_files():
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if "\u2014" in content:
            line = next(
                i for i, text in enumerate(content.splitlines(), 1) if "\u2014" in text
            )
            offenders.append(f"{path.relative_to(_ROOT)}:{line}")
    assert not offenders, (
        "em-dashes found (CONTRIBUTING.md forbids them; use commas, "
        "semicolons, colons or parentheses):\n" + "\n".join(offenders)
    )
