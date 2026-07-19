"""Maintainability ratchets for the Campaign 7 effect-path refactor."""

from __future__ import annotations

import ast
from pathlib import Path

import arvis
import arvis.api as public_api
from arvis.kernel_core.syscalls.intent_outbox import IntentOutboxService
from arvis.tools.authorization_service import ToolAuthorizationService
from arvis.tools.effect_dispatcher import EffectDispatcher

ROOT = Path(__file__).resolve().parents[2]


def _function_size(path: str, class_name: str | None, function_name: str) -> int:
    tree = ast.parse((ROOT / path).read_text(encoding="utf-8"))
    nodes: list[ast.AST] = list(tree.body)
    if class_name is not None:
        class_nodes = [
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == class_name
        ]
        assert len(class_nodes) == 1
        nodes = list(class_nodes[0].body)
    functions = [
        node
        for node in nodes
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == function_name
    ]
    assert len(functions) == 1
    function = functions[0]
    assert function.end_lineno is not None
    return function.end_lineno - function.lineno + 1


def test_effect_path_services_are_internal_not_public_api() -> None:
    assert ToolAuthorizationService is not None
    assert IntentOutboxService is not None
    assert EffectDispatcher is not None
    for module in (arvis, public_api):
        assert not hasattr(module, "ToolAuthorizationService")
        assert not hasattr(module, "IntentOutboxService")
        assert not hasattr(module, "EffectDispatcher")


def test_security_critical_entrypoints_remain_orchestrators() -> None:
    limits = {
        ("arvis/tools/manager.py", "ToolManager", "authorize"): 70,
        (
            "arvis/kernel_core/syscalls/syscall_handler.py",
            "SyscallHandler",
            "handle",
        ): 90,
        (
            "arvis/kernel_core/syscalls/syscall_handler.py",
            "SyscallHandler",
            "_record_intent",
        ): 70,
        ("arvis/tools/executor.py", "ToolExecutor", "_execute_invocation"): 20,
        (
            "arvis/kernel_core/syscalls/syscalls/tool_syscalls.py",
            None,
            "tool_execute",
        ): 80,
    }
    for (path, class_name, function_name), maximum in limits.items():
        assert _function_size(path, class_name, function_name) <= maximum
