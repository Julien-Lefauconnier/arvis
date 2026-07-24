# tests/api/test_multi_instance_isolation.py

"""Engines in one process are isolated by construction (BETA-03).

The engine lifecycle doctrine: one engine executes one governed run at
a time and is not thread-safe; the host parallelizes by creating one
engine per unit of work. This suite pins the guarantee that doctrine
rests on: N engines in a single process share no observable state.
Module-level inventory (audit a13): arvis holds no per-run module
state; the only shared module-level dicts are the syscall dispatch
tables, populated once at import time with duplicate registration
refused, so instances share code and constants only.
"""

from concurrent.futures import ThreadPoolExecutor

from arvis.api import CognitiveOS
from arvis.tools.base import BaseTool
from arvis.tools.spec import ToolSpec


class _NamedTool(BaseTool):
    def __init__(self, name: str) -> None:
        self.name = name
        self.spec = ToolSpec(name=name, description="d")

    def execute(self, input_data):  # pragma: no cover - not run here
        return {"ok": True}


def _status(result) -> str:
    return result.status.value


def test_tool_surfaces_are_per_instance():
    first, second = CognitiveOS(), CognitiveOS()
    first.register_tool(_NamedTool("alpha_only"))
    second.register_tool(_NamedTool("beta_only"))

    pinned_first = first.freeze_tools()
    pinned_second = second.freeze_tools()

    assert pinned_first != pinned_second
    assert first.list_tools() == ["alpha_only"]
    assert second.list_tools() == ["beta_only"]


def test_interleaved_runs_do_not_move_decisions_or_pinned_surfaces():
    """Isolation proof, not a usage recommendation.

    Sequential reuse here is deliberate: it demonstrates that instances
    never leak into each other even across interleaved runs. The
    documented lifecycle stays one instance per governed turn
    (docs/architecture/RUNTIME_LIFECYCLE.md); the shipped examples
    follow it and tests/contracts/test_examples_lifecycle.py keeps
    them on it.
    """
    engines = [CognitiveOS() for _ in range(3)]
    for index, engine in enumerate(engines):
        engine.register_tool(_NamedTool(f"tool_{index}"))
    pinned = [engine.freeze_tools() for engine in engines]

    payloads = [{"risk": 0.10}, {"risk": 0.50}, {"risk": 0.90}]
    first_pass = [
        _status(engine.run(f"user_{index}", payloads[index]))
        for index, engine in enumerate(engines)
    ]
    assert first_pass == ["ALLOWED", "REQUIRES_CONFIRMATION", "BLOCKED"]

    # Interleave the same work in a different order across the same
    # engines: per-engine decisions and pinned surfaces must not move.
    for index in (2, 0, 1, 1, 2, 0):
        assert (
            _status(engines[index].run(f"user_{index}", payloads[index]))
            == (first_pass[index])
        )
    for engine, pin in zip(engines, pinned, strict=True):
        assert engine.freeze_tools() == pin


def test_threaded_hosting_one_engine_per_worker():
    def worker(index: int) -> str:
        engine = CognitiveOS()
        return _status(engine.run(f"worker_{index}", {"risk": 0.10}))

    with ThreadPoolExecutor(max_workers=4) as pool:
        outcomes = list(pool.map(worker, range(8)))

    assert outcomes == ["ALLOWED"] * 8
