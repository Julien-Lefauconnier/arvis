# scripts/check_md_refs.py
"""Gate check: repository paths referenced from Markdown must exist.

Scans every tracked ``*.md`` file for references that look like repository
paths: Markdown links with relative targets, and backticked tokens shaped
like paths (``arvis/...``, ``docs/...``, ``tests/...``, ``scripts/...``,
``examples/...``, ``compliance/...``): and fails when a referenced path
does not exist in the working tree.

A documentation file that attests the existence of an artifact which is not
there is a defect of the same class as a failing test: it produces false
assurance. This check is the ratchet that keeps prose and tree aligned.

Exit code 0 when every reference resolves; 1 otherwise, listing each
offender as ``file:line: path``.

Deliberately conservative: only tokens that unambiguously look like repo
paths are checked. External URLs, bare filenames, and glob-like tokens are
ignored. False positives are silenced by adding the token to ALLOWLIST with
a dated justification.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Tokens that look like paths but are legitimately absent or symbolic.
# Format: exact token -> dated one-line justification.
ALLOWLIST: dict[str, str] = {
    # "docs/example.md": "2026-08-31 illustrative placeholder in spec X",
}

TOP_DIRS = (
    "arvis/",
    "docs/",
    "tests/",
    "scripts/",
    "examples/",
    "compliance/",
    ".github/",
)

MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s#]+)(?:#[^)]*)?\)")
BACKTICK = re.compile(r"`([^`\n]+)`")


def _tracked_md_files() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "*.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [ROOT / line for line in out.stdout.splitlines() if line]


def _looks_like_repo_path(token: str) -> bool:
    if token.startswith(("http://", "https://", "mailto:")):
        return False
    if any(ch in token for ch in "*{}<>|$ \t"):
        return False
    if token.startswith(TOP_DIRS):
        return "/" in token
    return False


def _candidates(md_file: Path) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for lineno, line in enumerate(
        md_file.read_text(encoding="utf-8").splitlines(), start=1
    ):
        for match in MD_LINK.finditer(line):
            target = match.group(1)
            if not target.startswith(("http://", "https://", "mailto:")):
                resolved = (md_file.parent / target).resolve()
                try:
                    rel = resolved.relative_to(ROOT)
                except ValueError:
                    continue
                found.append((lineno, str(rel)))
        for match in BACKTICK.finditer(line):
            token = match.group(1).strip().rstrip("/")
            if _looks_like_repo_path(token):
                found.append((lineno, token))
    return found


def main() -> int:
    errors: list[str] = []
    for md_file in _tracked_md_files():
        rel_md = md_file.relative_to(ROOT)
        for lineno, ref in _candidates(md_file):
            if ref in ALLOWLIST:
                continue
            if not (ROOT / ref).exists():
                errors.append(f"{rel_md}:{lineno}: {ref}")
    if errors:
        print(f"{len(errors)} Markdown reference(s) point to missing paths:")
        for err in errors:
            print(f"  {err}")
        print("\nFix the reference, or allowlist it with a dated justification.")
        return 1
    print("check_md_refs: all Markdown path references resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
