"""Ratchet: every module shipped in the package is reachable.

A module that nothing imports still travels in the wheel, still has to be read
by anyone auditing the package, and still claims to be part of the architecture.
The a11 readiness audit found twelve such modules; a reachability sweep then
found fifty-two, three of which were whole subsystems that had never been wired.
That is the kind of drift this test exists to stop: adding a module without
wiring it now fails here, at the moment it is introduced rather than at the next
audit.

Reachable means REFERENCED: imported by any module in the package, by any
test, or by an example. This is deliberately a floor, not a claim of runtime
integration: a module exercised only by its tests counts as reachable, since
a component may legitimately be tested before it is wired into a path.
Whether a referenced module actually sits on a runtime path is a separate,
stronger property that this ratchet does not measure and does not assert
(audit a13, P2-04).

Import forms handled:

  - absolute imports, both `import a.b` and `from a.b import C`;
  - relative imports, resolved against the importing module's package (note
    that inside an __init__.py the package is the module itself, not its
    parent);
  - dynamic imports, matched on any string literal shaped like a dotted arvis
    path, which covers the importlib call in decision_stack.

__init__.py files are excluded: a package marker is reached through its package,
not by name.
"""

from __future__ import annotations

import ast
import pathlib
import re

# This file is tests/contracts/<n>.py
_ROOT = pathlib.Path(__file__).resolve().parents[2]

# Where imports may come from. A module reached from any of these is alive.
_IMPORT_SOURCES = ("arvis", "tests", "examples")

_DYNAMIC_IMPORT = re.compile(r"""["']((?:arvis)(?:\.[A-Za-z_][A-Za-z0-9_]*)+)["']""")


def _dotted(path: pathlib.Path) -> str:
    return ".".join(path.relative_to(_ROOT).with_suffix("").parts)


def _module_name(path: pathlib.Path) -> str:
    return _dotted(path).removesuffix(".__init__")


def _package_of(path: pathlib.Path) -> str:
    """The package a relative import in this file resolves against."""
    dotted = _dotted(path)
    if path.name == "__init__.py":
        return dotted.removesuffix(".__init__")
    return ".".join(dotted.split(".")[:-1])


def _imports_in(path: pathlib.Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    found: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:  # pragma: no cover - a broken file fails elsewhere
        return found

    package = _package_of(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package
                for _ in range(node.level - 1):
                    base = ".".join(base.split(".")[:-1])
                module = f"{base}.{node.module}" if node.module else base
            else:
                module = node.module or ""
            found.add(module)
            for alias in node.names:
                found.add(f"{module}.{alias.name}")

    found.update(_DYNAMIC_IMPORT.findall(source))
    return found


def test_no_unreachable_module_ships_in_the_package():
    imported: set[str] = set()
    for source_dir in _IMPORT_SOURCES:
        base = _ROOT / source_dir
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            imported |= _imports_in(path)

    unreachable = sorted(
        str(path.relative_to(_ROOT))
        for path in (_ROOT / "arvis").rglob("*.py")
        if path.name != "__init__.py" and _module_name(path) not in imported
    )

    assert not unreachable, (
        "Modules shipped in the package that nothing imports.\n"
        "Wire them, or remove them; do not leave them in the wheel:\n"
        + "\n".join(unreachable)
    )
