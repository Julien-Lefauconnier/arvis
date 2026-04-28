# tests/kernel/test_source_never_imports_tests.py

import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2] / "arvis"


def test_source_never_imports_tests_package():
    for py in ROOT.rglob("*.py"):
        tree = ast.parse(py.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    assert not name.name.startswith("tests"), (
                        f"{py} imports tests package"
                    )

            if isinstance(node, ast.ImportFrom):
                if node.module:
                    assert not node.module.startswith("tests"), (
                        f"{py} imports tests package"
                    )
