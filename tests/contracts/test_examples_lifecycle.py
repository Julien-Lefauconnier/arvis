# tests/contracts/test_examples_lifecycle.py

"""Contract test: every shipped example follows the documented lifecycle.

The doctrine (docs/architecture/RUNTIME_LIFECYCLE.md, audit a14,
A14-BETA-03) is one engine instance per governed turn. Examples are the
first thing a host reads: an example that reuses an instance across
runs teaches the contradicted pattern, which is exactly how the a14
contradiction shipped. This test statically enforces, for every file in
examples/:

- a ``.run(`` / ``.ask(`` call inside a loop requires the receiving
  engine to be instantiated inside that same loop body (fresh instance
  per iteration);
- outside loops, each instantiated engine receives at most one
  ``.run(`` / ``.ask(`` call.

The isolation tests deliberately reuse instances to prove isolation;
that is their documented purpose and they are not examples.
"""

import ast
import pathlib

import pytest

_EXAMPLES = sorted(
    (pathlib.Path(__file__).resolve().parents[2] / "examples").glob("*.py")
)
_ENGINE_FACTORIES = {"ArvisEngine", "CognitiveOS"}
_RUN_METHODS = {"run", "ask"}


def _is_engine_instantiation(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in _ENGINE_FACTORIES
    if isinstance(func, ast.Attribute):
        return func.attr in _ENGINE_FACTORIES
    return False


def _assigned_engine_names(body_nodes: list[ast.stmt]) -> set[str]:
    """Names bound to a fresh engine anywhere under the given statements.

    Covers plain assignments and functions returning a fresh engine
    (the host factory pattern): a call to a local function whose body
    returns an engine instantiation counts as instantiation.
    """
    names: set[str] = set()
    for stmt in body_nodes:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Assign) and _creates_engine(node.value):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        names.add(target.id)
    return names


_FACTORY_FUNCTIONS: set[str] = set()


def _creates_engine(value: ast.AST) -> bool:
    if _is_engine_instantiation(value):
        return True
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id in _FACTORY_FUNCTIONS
    )


def _collect_factories(tree: ast.Module) -> None:
    """A local function whose body returns an engine instantiation is a
    host factory: calling it is instantiating."""
    _FACTORY_FUNCTIONS.clear()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for inner in ast.walk(node):
                if isinstance(inner, ast.Return) and inner.value is not None:
                    if _is_engine_instantiation(inner.value):
                        _FACTORY_FUNCTIONS.add(node.name)


def _run_receivers(nodes: list[ast.stmt]) -> list[str]:
    receivers: list[str] = []
    for stmt in nodes:
        for node in ast.walk(stmt):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr in _RUN_METHODS
                and isinstance(node.func.value, ast.Name)
            ):
                receivers.append(node.func.value.id)
    return receivers


@pytest.mark.parametrize("path", _EXAMPLES, ids=[p.name for p in _EXAMPLES])
def test_example_uses_one_engine_per_turn(path: pathlib.Path) -> None:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    _collect_factories(tree)

    violations: list[str] = []

    loops = [node for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While))]
    loop_body_ids = {id(stmt) for loop in loops for stmt in ast.walk(loop)}

    # Rule 1: inside a loop, the receiver must be instantiated in that
    # same loop body.
    for loop in loops:
        fresh_names = _assigned_engine_names(loop.body)
        for receiver in _run_receivers(loop.body):
            if receiver not in fresh_names:
                violations.append(
                    f"{path.name}: '{receiver}.run/.ask' inside a loop reuses "
                    "an engine created outside it; instantiate per iteration"
                )

    # Rule 2: outside loops, at most one run/ask per engine name.
    outside: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr in _RUN_METHODS
            and isinstance(node.func.value, ast.Name)
            and id(node) not in loop_body_ids
        ):
            outside.append(node.func.value.id)
    for name in set(outside):
        if outside.count(name) > 1:
            violations.append(
                f"{path.name}: engine '{name}' receives "
                f"{outside.count(name)} run/ask calls; the lifecycle is one "
                "instance per governed turn"
            )

    assert not violations, "\n".join(violations)
