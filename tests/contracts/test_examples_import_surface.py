# tests/contracts/test_examples_import_surface.py
"""Every example imports only the two supported surfaces.

Campaign SURFACE (DM-S2, audit P1-16, 2026-09-02). The examples are
the first integration code a newcomer copies, so an example importing
an internal path teaches a dependency VERSIONING.md explicitly says
may change in any release (examples/05 imported
``arvis.tools.effect_context`` and ``arvis.adapters.tools.*`` while
example 11 did the same job through ``host_api.tools``). This ratchet
parses every example statically: an import of an ``arvis`` module is
allowed only for the root package or ``arvis.host_api`` modules.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

EXAMPLES = sorted((Path(__file__).resolve().parents[2] / "examples").glob("*.py"))


def _arvis_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(
                alias.name for alias in node.names if alias.name.startswith("arvis")
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("arvis"):
                found.append(node.module)
    return found


def _is_supported(module: str) -> bool:
    return module == "arvis" or module.startswith("arvis.host_api")


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.name for p in EXAMPLES])
def test_example_imports_only_the_supported_surfaces(path: Path) -> None:
    internal = [m for m in _arvis_imports(path) if not _is_supported(m)]
    assert not internal, (
        f"{path.name} imports internal path(s) {internal}: examples must "
        "import only the root surface (arvis) or arvis.host_api.*"
    )


def test_the_contract_scans_the_examples() -> None:
    """The glob is not silently empty (a moved directory would turn the
    parametrized test into a vacuous pass)."""
    assert len(EXAMPLES) >= 13
