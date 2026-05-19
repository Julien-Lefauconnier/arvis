# tests/contracts/test_no_print_in_source.py

from __future__ import annotations

import ast
from pathlib import Path


def test_no_print_in_arvis_source() -> None:
    root = Path("arvis")

    offenders: list[str] = []

    for path in root.rglob("*.py"):
        source = path.read_text(encoding="utf-8")

        try:
            tree = ast.parse(source)
        except SyntaxError:
            offenders.append(f"{path} (syntax error)")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func

                if isinstance(func, ast.Name) and func.id == "print":
                    offenders.append(str(path))
                    break

    assert offenders == []
