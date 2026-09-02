# tests/contracts/test_import_closure.py
"""Ratchet: no module of ``arvis/`` may quietly become unreachable.

Reachability is computed statically (ast-level imports) from four
root sets that together define the supported surface:

- ``arvis`` itself (the public ``__init__``),
- every ``arvis.api`` module (the internal aggregator layer behind
  the root surface; campaign SURFACE deleted the four dead re-export
  facades cognition/math/memory/reasoning that nothing imported),
- every ``arvis.host_api`` module (the documented host surface),
- every module of the veramem consumed surface
  (``tests/contracts/test_veramem_consumed_surface.py``), since the
  host imports deep paths the public ``__init__`` does not reach.

A module reachable from none of these is dead weight: it still counts
in the coverage denominator, keeps its tests alive, and collides with
living names (audit A2, 2026-08, found 91 such modules).

History of the burn-down: the audit froze 91 entries; campaign
"mise au propre" LOT 7 built this ratchet; campaign STRUCT LOT S1
deleted the dead conversation layer (38), the unwired
predictive/probabilistic math layer (14) and the remaining dead
chains (32: kernel adapter rule engine, dead LLM contracts and
observability providers, lexicon and dead linguistic acts, runtime
snapshots, raw signal layer, redaction, orphan cognition flows),
and promoted the four ``arvis.api`` namespaces to roots.

KNOWN_UNREACHABLE is now NOT a burn-down anymore: every remaining
entry is a deliberate keep, unreachable from the production roots
but consumed by the test and compliance suites as a harness. The
ratchet still enforces both directions:

- a module that becomes unreachable and is NOT listed fails the test
  (no new dead code);
- a listed module that becomes reachable, or disappears, also fails
  (the list must keep matching reality).

Adding an entry requires the same justification as adding dead code,
because outside the harness case it is one.
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.contracts.test_veramem_consumed_surface import CONSUMED_SURFACE

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "arvis"

# Deliberate keeps (last reviewed 2026-08-31, campaign STRUCT LOT S1):
# unreachable from the production roots, but load-bearing test
# harnesses. Each entry names its consumers.
#
# - projection_api: the trajectory harness behind the projection
#   property suite (tests/math/test_projection_*.py,
#   tests/fixtures/projection_cases.py, and the adaptive kappa
#   trajectory test). It IS the M3/M10 validation program.
# - vfs.repositories(.in_memory): the in-memory VFS repository the
#   adversarial access-control tests drive
#   (tests/kernel_core/access/test_vfs_scope_*.py).
KNOWN_UNREACHABLE: frozenset[str] = frozenset(
    {
        "arvis.cognition.projection.projection_api",
        "arvis.kernel_core.vfs.repositories",
        "arvis.kernel_core.vfs.repositories.in_memory",
    }
)


def _module_name(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    parts = list(rel.parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _all_modules() -> dict[str, Path]:
    return {
        _module_name(p): p
        for p in PACKAGE.rglob("*.py")
        if "__pycache__" not in p.parts
    }


def _imports_of(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("arvis"):
                    found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                # relative import: resolve against this module's package
                base = _module_name(path).split(".")
                if path.name != "__init__.py":
                    base = base[:-1]
                base = base[: len(base) - (node.level - 1)]
                prefix = ".".join(base)
                module = f"{prefix}.{node.module}" if node.module else prefix
            else:
                module = node.module or ""
            if module.startswith("arvis"):
                found.add(module)
                for alias in node.names:
                    found.add(f"{module}.{alias.name}")
    return found


def _closure(roots: set[str], modules: dict[str, Path]) -> set[str]:
    reached: set[str] = set()
    stack = [r for r in roots if r in modules]
    while stack:
        name = stack.pop()
        if name in reached:
            continue
        reached.add(name)
        # importing a module executes every ancestor package __init__
        parts = name.split(".")
        for i in range(1, len(parts)):
            ancestor = ".".join(parts[:i])
            if ancestor in modules and ancestor not in reached:
                stack.append(ancestor)
        for imported in _imports_of(modules[name]):
            candidates = [imported]
            # "from pkg.mod import symbol" adds pkg.mod.symbol; keep the
            # module part too when the symbol is not itself a module.
            if imported not in modules and "." in imported:
                candidates.append(imported.rsplit(".", 1)[0])
            for candidate in candidates:
                if candidate in modules and candidate not in reached:
                    stack.append(candidate)
    return reached


def _unreachable_now() -> set[str]:
    modules = _all_modules()
    roots = {"arvis"}
    # arvis.api.* is the aggregator layer behind the root surface:
    # its modules stay roots so the closure covers what they re-export.
    roots.update(name for name in modules if name.startswith("arvis.api"))
    roots.update(name for name in modules if name.startswith("arvis.host_api"))
    roots.update(CONSUMED_SURFACE.keys())
    reached = _closure(roots, modules)
    return {name for name in modules if name not in reached}


def test_no_new_unreachable_modules() -> None:
    unreachable = _unreachable_now()
    new = unreachable - KNOWN_UNREACHABLE
    assert not new, (
        f"{len(new)} module(s) became unreachable from the supported "
        "surface (public API + host_api + veramem consumed surface). "
        "Either wire them, delete them, or add them to KNOWN_UNREACHABLE "
        "with a justification:\n  " + "\n  ".join(sorted(new))
    )


def test_burn_down_list_matches_reality() -> None:
    unreachable = _unreachable_now()
    stale = KNOWN_UNREACHABLE - unreachable
    assert not stale, (
        "these KNOWN_UNREACHABLE entries are now reachable or deleted; "
        "remove them from the list so it keeps matching reality:\n  "
        + "\n  ".join(sorted(stale))
    )
