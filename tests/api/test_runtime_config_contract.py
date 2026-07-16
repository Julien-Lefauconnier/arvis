# tests/api/test_runtime_config_contract.py

"""Runtime configuration contract (lot B1-B4).

F-007: the configuration is frozen, so the construction-time validation
cannot be bypassed by mutating it afterwards. F-008: the runtime mode
set is closed and unknown values are refused. F-009: force_tool only
selects a tool; execution authority requires an explicit
force_execution=True (retries keep executing, a retry is an execution
request). F-012: REQUIRED audit commitment without the trace machinery
is a configuration contradiction and is refused.
"""

from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest

from arvis.api.audit import AuditCommitmentPolicy
from arvis.api.os import CognitiveOSConfig
from arvis.api.runtime_mode import RuntimeMode, coerce_runtime_mode
from arvis.kernel.pipeline.stages.action_stage import ActionStage

# ---------------------------------------------------------------
# F-008: closed runtime mode set
# ---------------------------------------------------------------


def test_runtime_mode_strings_are_normalized():
    config = CognitiveOSConfig(runtime_mode="production")
    assert config.runtime_mode is RuntimeMode.PRODUCTION


def test_default_runtime_mode_is_local():
    assert CognitiveOSConfig().runtime_mode is RuntimeMode.LOCAL


@pytest.mark.parametrize("value", ["prod", "Production", "production-strict", "saas"])
def test_unknown_runtime_mode_is_refused(value):
    with pytest.raises(ValueError, match="unknown runtime_mode"):
        CognitiveOSConfig(runtime_mode=value)


def test_coerce_passes_enum_values_through():
    assert coerce_runtime_mode(RuntimeMode.TEST) is RuntimeMode.TEST


# ---------------------------------------------------------------
# F-007: frozen configuration
# ---------------------------------------------------------------


def test_config_is_frozen():
    config = CognitiveOSConfig()
    with pytest.raises(FrozenInstanceError):
        config.enable_trace = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        config.runtime_controls = object()  # type: ignore[assignment, misc]


# ---------------------------------------------------------------
# F-012: REQUIRED audit commitment needs the trace
# ---------------------------------------------------------------


def test_required_audit_policy_without_trace_is_refused():
    with pytest.raises(ValueError, match="enable_trace"):
        CognitiveOSConfig(
            enable_trace=False,
            audit_commitment_policy=AuditCommitmentPolicy.REQUIRED,
        )


def test_required_audit_policy_with_trace_is_accepted():
    config = CognitiveOSConfig(audit_commitment_policy=AuditCommitmentPolicy.REQUIRED)
    assert config.audit_commitment_policy is AuditCommitmentPolicy.REQUIRED


def test_degraded_audit_policy_without_trace_is_accepted():
    config = CognitiveOSConfig(enable_trace=False)
    assert config.audit_commitment_policy is AuditCommitmentPolicy.DEGRADED


# ---------------------------------------------------------------
# F-009: force_tool selects, only force_execution executes
# ---------------------------------------------------------------


def _action_ctx(*, can_execute: bool, force_tool: str | None, force_execution: bool):
    runtime = SimpleNamespace(
        can_execute=can_execute,
        requires_confirmation=not can_execute,
    )
    return SimpleNamespace(
        execution=SimpleNamespace(execution_state=runtime, action_decision=None),
        runtime_policy=SimpleNamespace(
            force_tool=force_tool,
            force_execution=force_execution,
            retry_requested=False,
            retry_count=0,
        ),
        tooling=SimpleNamespace(tool_results=[], tool_payloads=[]),
        extra={},
        gate_result=None,
    )


def test_force_tool_alone_does_not_grant_execution():
    ctx = _action_ctx(can_execute=False, force_tool="host_tool", force_execution=False)
    ActionStage().run(SimpleNamespace(), ctx)
    decision = ctx.execution.action_decision
    assert decision.tool == "host_tool"
    assert decision.allowed is False
    assert decision.requires_user_validation is True
    assert decision.denied_reason == "execution_blocked"
    # F-009: selection never flips the execution authority.
    assert ctx.runtime_policy.force_execution is False


def test_force_tool_follows_an_open_gate_without_forcing():
    ctx = _action_ctx(can_execute=True, force_tool="host_tool", force_execution=False)
    ActionStage().run(SimpleNamespace(), ctx)
    decision = ctx.execution.action_decision
    assert decision.tool == "host_tool"
    assert decision.allowed is True
    assert ctx.runtime_policy.force_execution is False


def test_explicit_force_execution_executes():
    ctx = _action_ctx(can_execute=False, force_tool="host_tool", force_execution=True)
    ActionStage().run(SimpleNamespace(), ctx)
    decision = ctx.execution.action_decision
    assert decision.tool == "host_tool"
    assert decision.allowed is True
    assert decision.requires_user_validation is False
    assert ctx.runtime_policy.force_execution is True


def test_retry_is_an_execution_request_and_keeps_executing():
    ctx = _action_ctx(can_execute=False, force_tool=None, force_execution=False)
    ctx.runtime_policy.retry_requested = True
    ctx.tooling.tool_results = [SimpleNamespace(tool_name="retry_tool")]
    ctx.tooling.tool_payloads = [{"payload": {"a": 1}}]
    ActionStage().run(SimpleNamespace(), ctx)
    decision = ctx.execution.action_decision
    assert decision.tool == "retry_tool"
    assert decision.allowed is True
    assert decision.tool_payload == {"a": 1}
    assert ctx.runtime_policy.force_execution is True
