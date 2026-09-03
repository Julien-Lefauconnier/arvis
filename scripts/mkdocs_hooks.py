# scripts/mkdocs_hooks.py
"""MkDocs hook: repo-relative links keep working on the site.

Documentation pages legitimately link files that live above docs_dir
(../CONTRIBUTING.md, ../VERSIONING.md, ../examples/...). Those links
are validated against the repository by check_md_refs at gate time,
but the built site has no target for them. This hook rewrites, at
render time, any href that escapes docs/ into the corresponding
GitHub URL for the main branch, so the site reader lands on the file
instead of a 404. In-site links are left untouched and stay covered
by the strict build.
"""

from __future__ import annotations

import posixpath
import re
from typing import Any

REPO_BLOB = "https://github.com/Julien-Lefauconnier/arvis/blob/main/"

_HREF = re.compile(r'href="((?:\.\./)+[^"#]+)(#[^"]*)?"')


def on_page_content(html: str, page: Any, config: Any, files: Any) -> str:
    # Directory of the page inside docs/, e.g. "architecture" for
    # architecture/EFFECT_PATH.md; the page URL is the reliable form.
    page_dir = posixpath.dirname(page.file.src_uri)

    def _rewrite(match: re.Match[str]) -> str:
        target, fragment = match.group(1), match.group(2) or ""
        joined = posixpath.normpath(posixpath.join("docs", page_dir, target))
        if joined.startswith(".."):
            # Escapes the repository root: leave it alone.
            return match.group(0)
        if joined == "docs" or joined.startswith("docs/"):
            # Still inside docs_dir: mkdocs resolves it natively.
            return match.group(0)
        return f'href="{REPO_BLOB}{joined}{fragment}"'

    return _HREF.sub(_rewrite, html)
