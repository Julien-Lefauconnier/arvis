from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import arvis
import arvis.api as api
from arvis.adapters.tools.policy import ToolPolicyEvaluator
from arvis.kernel_core.syscalls.service_registry import KernelServiceRegistry
from arvis.kernel_core.syscalls.syscall import Syscall
from arvis.kernel_core.syscalls.syscall_handler import SyscallHandler
from arvis.tools.authorized_invocation import UnauthorizedExecutionError
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.manager import ToolManager
from arvis.tools.registry import ToolRegistry
from arvis.tools.spec import ToolSpec


class _ProbeTool(BaseTool):
    name = "route_probe"
    spec = ToolSpec(name=name, description="effect route probe")

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def execute(self, input_data: dict[str, Any]) -> dict[str, bool]:
        self.calls.append(dict(input_data["tool_payload"]))
        return {"ok": True}


def _rig(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[ToolManager, ToolExecutor, _ProbeTool]:
    registry = ToolRegistry()
    tool = _ProbeTool()
    registry.register(tool)
    executor = ToolExecutor(registry)
    manager = ToolManager(registry=registry, executor=executor)
    monkeypatch.setattr(
        ToolPolicyEvaluator,
        "evaluate",
        staticmethod(
            lambda invocation, registry, **kwargs: SimpleNamespace(
                allowed=True,
                reason="allowed",
            )
        ),
    )
    return manager, executor, tool


def _decision() -> SimpleNamespace:
    return SimpleNamespace(
        action_decision=SimpleNamespace(tool="route_probe", tool_payload={"x": 1})
    )


def _ctx() -> SimpleNamespace:
    return SimpleNamespace(extra={}, user_id="u1")


def test_manager_run_is_a_hard_refusal(monkeypatch: pytest.MonkeyPatch) -> None:
    manager, _executor, tool = _rig(monkeypatch)

    with pytest.raises(UnauthorizedExecutionError, match="not an effect route"):
        manager.run(_decision(), _ctx())

    assert tool.calls == []


def test_public_manager_effect_methods_require_private_boundary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, _executor, tool = _rig(monkeypatch)
    result = _decision()
    ctx = _ctx()
    outcome = manager.authorize(result, ctx)
    assert outcome is not None and outcome.authorized is not None
    authorized = outcome.authorized

    with pytest.raises(UnauthorizedExecutionError, match="direct tool effects"):
        manager.activate_authorized(
            authorized,
            receipt=None,
            intent_sha256="a" * 64,
            run_id=None,
            causal_id="forbidden",
        )
    with pytest.raises(UnauthorizedExecutionError, match="direct tool effects"):
        manager.execute_authorized(authorized, result, ctx)
    with pytest.raises(UnauthorizedExecutionError, match="direct tool effects"):
        manager.abort_authorized(authorized)

    assert tool.calls == []


def test_public_executor_mint_and_capability_execution_are_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, executor, tool = _rig(monkeypatch)
    outcome = manager.authorize(_decision(), _ctx())
    assert outcome is not None and outcome.authorized is not None

    with pytest.raises(
        UnauthorizedExecutionError, match="minting authority is internal"
    ):
        executor.claim_minting_authority()
    with pytest.raises(
        UnauthorizedExecutionError, match="internal to the syscall boundary"
    ):
        executor.execute_invocation(outcome.authorized, _decision(), _ctx())

    assert tool.calls == []


def test_syscall_handler_is_the_effect_route(monkeypatch: pytest.MonkeyPatch) -> None:
    manager, executor, tool = _rig(monkeypatch)
    handler = SyscallHandler(
        runtime_state=None,
        scheduler=None,
        services=KernelServiceRegistry(
            tool_executor=executor,
            tool_manager=manager,
        ),
    )
    result = _decision()
    ctx = _ctx()
    authorization = manager.authorize(result, ctx)

    syscall_result = handler.handle(
        Syscall(
            name="tool.execute",
            args={
                "result": result,
                "ctx": ctx,
                "authorization": authorization,
            },
        )
    )

    assert syscall_result.success is True
    assert tool.calls == [{"x": 1}]


def test_security_authorities_are_absent_from_public_object_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manager, executor, _tool = _rig(monkeypatch)

    assert not hasattr(manager, "_authority")
    assert not hasattr(manager, "_effect_boundary_token")
    assert not hasattr(manager, "_confirmation_reservations")
    assert not hasattr(executor, "_authority")


def test_api_surface_does_not_export_effect_internals() -> None:
    forbidden = {"ToolExecutor", "ToolManager", "InvocationAuthority"}
    assert forbidden.isdisjoint(set(arvis.__all__))
    assert forbidden.isdisjoint(set(api.__all__))
