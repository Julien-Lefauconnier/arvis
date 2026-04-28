# tests/kernel/test_architecture_dependencies.py

import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2] / "arvis"


def _imports(file):
    tree = ast.parse(file.read_text())

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                yield name.name

        if isinstance(node, ast.ImportFrom):
            if node.module:
                yield node.module


def _scan(folder):
    for py in folder.rglob("*.py"):
        yield py, list(_imports(py))


def test_math_does_not_import_timeline():
    math_dir = ROOT / "math"

    for file, imports in _scan(math_dir):
        for imp in imports:
            assert not imp.startswith("arvis.timeline"), f"{file} imports timeline"


def test_timeline_does_not_import_cognition():
    timeline_dir = ROOT / "timeline"

    for file, imports in _scan(timeline_dir):
        for imp in imports:
            assert not imp.startswith("arvis.cognition"), f"{file} imports cognition"
