"""A production effect cannot execute under a run its sealed context omits.

When the handler has opened a run envelope, the intent carries that run. If the
authorization sealed no run of its own, the effect executes under a run its own
sealed context does not name, and the audit trail has nothing tying the two
together. That is tolerated for a direct local composition, which historically
omits the runtime binding, and refused under production posture.

These tests pin both halves: production refuses the unbound composition, and a
local one keeps working, so the tolerance stays where it belongs.
"""

from __future__ import annotations

from types import SimpleNamespace

from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.kernel_core.access.models import AuthenticatedPrincipal
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec

_RUN = "0123456789abcdef0123456789abcdef"


class _Probe(BaseTool):
    name = "bindings_probe"
    spec = ToolSpec(name="bindings_probe", description="bindings probe")

    def __init__(self) -> None:
        self.executed = False

    def execute(self, input_data):
        self.executed = True
        return {"ok": True}


def _rig(monkeypatch, *, production: bool):
    registry = ToolRegistry()
    tool = _Probe()
    registry.register(tool)
    executor = ToolExecutor(registry)
    manager = ToolManager(registry=registry, executor=executor)
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            tool_executor=executor,
            tool_manager=manager,
            require_authenticated_principal=production,
        ),
    )
    monkeypatch.setattr(
        ToolPolicyEvaluator,
        "evaluate",
        staticmethod(
            lambda invocation, reg, **kwargs: SimpleNamespace(allowed=True, reason=None)
        ),
    )
    return handler, manager, tool


def _ctx(*, bound_run: str | None):
    ctx = SimpleNamespace(extra={}, user_id="u1")
    ctx.principal = AuthenticatedPrincipal(
        user_id="u1",
        authentication_source="test",
        authentication_strength="strong",
    )
    if bound_run is not None:
        ctx.runtime_bindings = SimpleNamespace(
            process_id="test-process", run_id=bound_run
        )
    return ctx


def _call(handler, manager, ctx):
    decision = SimpleNamespace(tool="bindings_probe", tool_payload={})
    pipeline_result = SimpleNamespace(action_decision=decision)
    authorization = manager.authorize(pipeline_result, ctx)
    return handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": pipeline_result,
                "ctx": ctx,
                "authorization": authorization,
            },
        )
    )


def test_production_refuses_an_effect_whose_run_is_not_bound(monkeypatch):
    handler, manager, tool = _rig(monkeypatch, production=True)
    handler.begin_run(_RUN)

    result = _call(handler, manager, _ctx(bound_run=None))

    assert result.success is False
    assert tool.executed is False


def test_production_accepts_an_effect_bound_to_the_open_run(monkeypatch):
    handler, manager, tool = _rig(monkeypatch, production=True)
    handler.begin_run(_RUN)

    result = _call(handler, manager, _ctx(bound_run=_RUN))

    assert result.success is True
    assert tool.executed is True


def test_a_local_composition_keeps_its_unbound_tolerance(monkeypatch):
    """Outside production, omitting the run binding stays legitimate."""
    handler, manager, tool = _rig(monkeypatch, production=False)
    handler.begin_run(_RUN)

    result = _call(handler, manager, _ctx(bound_run=None))

    assert result.success is True
    assert tool.executed is True
