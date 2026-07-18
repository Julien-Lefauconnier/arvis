# tests/tools/test_tool_governance_lot_c.py

"""Tool execution governance (lot C: F-014, F-016, F-020).

F-014: timeout_seconds is a deadline on result acceptance: a tool that
runs past its declared budget gets its late result rejected (the effect
may still have happened; interruption and process isolation are a later
chantier). F-016: automatic retry requires declared idempotence: a
side-effectful, non-idempotent effect is never replayed automatically,
and a missing spec means no automatic retry (fail-closed). F-020:
declared input schemas are validated before the call (a violating
payload never reaches the tool), declared output schemas after the call
(an invalid response gets its specific failure status). ZK: schema
violations surface structural paths only, never offending values.
"""

import time
from types import SimpleNamespace

from arvis.adapters.tools.invocation import ToolInvocation
from arvis.errors.codes import ErrorCode
from arvis.tools.base import BaseTool
from arvis.tools.executor import ToolExecutor
from arvis.tools.registry import ToolRegistry
from arvis.tools.retry_policy import ToolRetryPolicy
from arvis.tools.spec import ToolSpec


def _ctx() -> SimpleNamespace:
    return SimpleNamespace(extra={})


def _decision(tool: str, payload: dict | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        action_decision=SimpleNamespace(tool=tool, tool_payload=payload or {})
    )


def _executor_with(tool: BaseTool) -> ToolExecutor:
    registry = ToolRegistry()
    registry.register(tool)
    return ToolExecutor(registry)


# Campaign 6 (Lot 3): the mint is claimable exactly once per executor;
# the test helper claims on first use and memoizes, exactly as the
# manager holds the claimed authority for the executor's lifetime.
# Keyed by the executor OBJECT (identity hash), never by id(): a
# garbage-collected executor's id can be reused by a fresh one, which
# would hand the fresh executor a foreign authority.
_CLAIMED_MINTS: dict[ToolExecutor, object] = {}


def _mint(executor: ToolExecutor):
    if executor not in _CLAIMED_MINTS:
        _CLAIMED_MINTS[executor] = executor.claim_minting_authority()
    return _CLAIMED_MINTS[executor]


def _run(executor: ToolExecutor, tool: str, ctx, payload: dict | None = None):
    """Execute through a legitimately minted capability (D-7).

    The executor no longer runs a bare invocation; a test exercising
    executor governance mints a single-use capability from the
    executor's claimed authority, exactly as the manager does after
    policy.
    """
    invocation = ToolInvocation(tool_name=tool, payload=payload or {}, process_id="p")
    authorized = _mint(executor).authorize(invocation)
    result = _decision(tool, payload)
    return executor.execute_invocation(authorized, result, ctx)


# ---------------------------------------------------------------
# F-014: deadline on result acceptance
# ---------------------------------------------------------------


class _SlowTool(BaseTool):
    name = "slow_tool"
    spec = ToolSpec(name="slow_tool", description="", timeout_seconds=0.01)

    def execute(self, input_data):
        time.sleep(0.03)
        return {"ok": True}

    def execute_invocation(self, invocation):
        return self.execute({})


def test_late_result_is_rejected_by_the_deadline():
    ctx = _ctx()
    result = _run(_executor_with(_SlowTool()), "slow_tool", ctx)
    assert result.success is False
    assert result.error.code == ErrorCode.TOOL_TIMEOUT
    assert result.latency_ms is not None
    assert ctx._tool_failure is True


class _FastTool(BaseTool):
    name = "fast_tool"
    spec = ToolSpec(name="fast_tool", description="", timeout_seconds=5.0)

    def execute(self, input_data):
        return {"ok": True}

    def execute_invocation(self, invocation):
        return self.execute({})


def test_result_within_the_deadline_is_accepted():
    result = _run(_executor_with(_FastTool()), "fast_tool", _ctx())
    assert result.success is True


# ---------------------------------------------------------------
# F-020: schema validation
# ---------------------------------------------------------------

_INPUT_SCHEMA = {
    "type": "object",
    "properties": {"amount": {"type": "number"}},
    "required": ["amount"],
}

_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {"ok": {"type": "boolean"}},
    "required": ["ok"],
}


def _schema_tool(output, calls):
    class _SchemaTool(BaseTool):
        name = "schema_tool"
        spec = ToolSpec(
            name="schema_tool",
            description="",
            input_schema=_INPUT_SCHEMA,
            output_schema=_OUTPUT_SCHEMA,
        )

        def execute(self, input_data):
            calls["n"] += 1
            return output

        def execute_invocation(self, invocation):
            return self.execute({})

    return _SchemaTool()


def test_invalid_input_is_denied_before_the_call():
    calls = {"n": 0}
    ctx = _ctx()
    result = _run(
        _executor_with(_schema_tool({"ok": True}, calls)),
        "schema_tool",
        ctx,
        {"amount": "not_a_number"},
    )
    assert result.success is False
    assert result.error.code == ErrorCode.TOOL_INPUT_INVALID
    assert calls["n"] == 0
    assert ctx._tool_failure is True
    # ZK: the offending value never surfaces in the error.
    assert "not_a_number" not in str(result.error.to_dict())


def test_valid_input_reaches_the_tool():
    calls = {"n": 0}
    result = _run(
        _executor_with(_schema_tool({"ok": True}, calls)),
        "schema_tool",
        _ctx(),
        {"amount": 3},
    )
    assert result.success is True
    assert calls["n"] == 1


def test_invalid_output_gets_its_specific_status():
    calls = {"n": 0}
    ctx = _ctx()
    result = _run(
        _executor_with(_schema_tool({"nope": 1}, calls)),
        "schema_tool",
        ctx,
        {"amount": 3},
    )
    assert result.success is False
    assert result.error.code == ErrorCode.TOOL_OUTPUT_INVALID
    assert calls["n"] == 1
    assert ctx._tool_failure is True


class _UnconstrainedTool(BaseTool):
    name = "free_tool"
    spec = ToolSpec(name="free_tool", description="")

    def execute(self, input_data):
        return {"anything": 1}

    def execute_invocation(self, invocation):
        return self.execute({})


def test_empty_schemas_do_not_constrain():
    result = _run(
        _executor_with(_UnconstrainedTool()),
        "free_tool",
        _ctx(),
        {"whatever": True},
    )
    assert result.success is True


# ---------------------------------------------------------------
# F-016: retry requires idempotence
# ---------------------------------------------------------------


def _retry_ctx(spec: ToolSpec | None) -> SimpleNamespace:
    ctx = SimpleNamespace(
        _tool_failure=True,
        collapse_risk=0.0,
        runtime_policy=SimpleNamespace(retry_requested=False, retry_count=0),
        extra={},
    )
    if spec is not None:
        ctx._last_tool_spec = spec
    return ctx


def test_idempotent_effect_is_retryable():
    ctx = _retry_ctx(ToolSpec(name="t", description="", idempotent=True))
    ToolRetryPolicy().evaluate(ctx)
    assert ctx.runtime_policy.retry_requested is True
    assert ctx.runtime_policy.retry_count == 1


def test_side_effectful_non_idempotent_is_never_replayed():
    # Defaults: side_effectful=True, idempotent=False (double e-mail,
    # double payment territory).
    ctx = _retry_ctx(ToolSpec(name="t", description=""))
    ToolRetryPolicy().evaluate(ctx)
    assert ctx.runtime_policy.retry_requested is False


def test_pure_tool_is_retryable():
    ctx = _retry_ctx(ToolSpec(name="t", description="", side_effectful=False))
    ToolRetryPolicy().evaluate(ctx)
    assert ctx.runtime_policy.retry_requested is True


def test_missing_spec_means_no_automatic_retry():
    ctx = _retry_ctx(None)
    ToolRetryPolicy().evaluate(ctx)
    assert ctx.runtime_policy.retry_requested is False


def test_non_retryable_spec_wins_over_idempotence():
    ctx = _retry_ctx(
        ToolSpec(name="t", description="", retryable=False, idempotent=True)
    )
    ToolRetryPolicy().evaluate(ctx)
    assert ctx.runtime_policy.retry_requested is False
