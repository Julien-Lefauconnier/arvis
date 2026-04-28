# tests/kernel/test_import_cycles.py

import ast
import pathlib
from collections import defaultdict

ROOT = pathlib.Path(__file__).resolve().parents[2] / "arvis"


def build_import_graph():
    graph = defaultdict(set)

    for file in ROOT.rglob("*.py"):
        module = file.relative_to(ROOT).with_suffix("").as_posix().replace("/", ".")

        tree = ast.parse(file.read_text())

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("arvis"):
                    graph[module].add(node.module)

            if isinstance(node, ast.Import):
                for name in node.names:
                    if name.name.startswith("arvis"):
                        graph[module].add(name.name)

    return graph


def detect_cycle(graph):
    visited = set()
    stack = set()

    def visit(node):
        if node in stack:
            return True

        if node in visited:
            return False

        visited.add(node)
        stack.add(node)

        for neigh in graph.get(node, []):
            if visit(neigh):
                return True

        stack.remove(node)
        return False

    return any(visit(n) for n in graph)


def test_no_import_cycles():
    graph = build_import_graph()

    assert not detect_cycle(graph)
