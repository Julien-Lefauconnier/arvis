# tests/contracts/test_annotation_shadowing.py
"""No method named after a builtin annotates itself with that builtin.

Campaign ACCESSIBILITY follow-up (first test-next-python signal,
2026-09-03). Under PEP 649 (Python 3.14) annotations of a method are
evaluated lazily in the class scope, where the method name is already
bound: ``def list(self) -> list[str]`` resolves ``list`` to the method
itself and ``inspect.signature`` raises ``TypeError: 'function' object
is not subscriptable``. On 3.13 and earlier the annotation was
evaluated before the name was bound, which is why the hazard is
invisible to the gate's own interpreter. This ratchet closes the
pattern statically: a method whose name shadows a builtin must not
reference that same name in its own annotations (qualify it through
``builtins.<name>`` instead, which evaluates to the identical object).
"""

from __future__ import annotations

import ast
import builtins
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARVIS = ROOT / "arvis"

_BUILTIN_NAMES = frozenset(dir(builtins))


def _annotation_names(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Bare names referenced by the def's own annotations.

    Attribute accesses such as ``builtins.list`` contribute only their
    base name (``builtins``), which is exactly what makes the qualified
    form the sanctioned fix.
    """
    nodes: list[ast.expr] = []
    if fn.returns is not None:
        nodes.append(fn.returns)
    all_args = [
        *fn.args.posonlyargs,
        *fn.args.args,
        *fn.args.kwonlyargs,
    ]
    for arg in [*all_args, fn.args.vararg, fn.args.kwarg]:
        if arg is not None and arg.annotation is not None:
            nodes.append(arg.annotation)
    names: set[str] = set()
    for node in nodes:
        for sub in ast.walk(node):
            if isinstance(sub, ast.Name):
                names.add(sub.id)
    return names


def _shadowing_defs() -> list[str]:
    offenders: list[str] = []
    for path in sorted(ARVIS.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for cls in ast.walk(tree):
            if not isinstance(cls, ast.ClassDef):
                continue
            for stmt in cls.body:
                if not isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                if stmt.name not in _BUILTIN_NAMES:
                    continue
                if stmt.name in _annotation_names(stmt):
                    offenders.append(
                        f"{path.relative_to(ROOT)}:{stmt.lineno} {cls.name}.{stmt.name}"
                    )
    return offenders


def test_no_method_annotates_itself_with_the_builtin_it_shadows() -> None:
    offenders = _shadowing_defs()
    assert not offenders, (
        "method(s) named after a builtin reference that builtin in their "
        f"own annotations (breaks under PEP 649 on Python 3.14): {offenders}. "
        "Qualify the annotation through builtins.<name>; the annotation "
        "object and the rendered signature are unchanged."
    )
