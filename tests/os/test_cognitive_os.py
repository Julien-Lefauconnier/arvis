# tests/os/test_cognitive_os.py


from arvis.api.os import CognitiveOS, CognitiveOSConfig
from arvis.ir.cognitive_ir import CognitiveIR

# =====================================================
# BASIC RUN
# =====================================================


def test_cognitive_os_run_basic():
    os = CognitiveOS()

    result = os.run(
        user_id="user_1",
        cognitive_input={"text": "hello world"},
    )

    assert result is not None
    assert result.decision is not None


# =====================================================
# RESULT STRUCTURE
# =====================================================


def test_cognitive_result_structure():
    os = CognitiveOS()

    result = os.run("user_1", {"text": "test"})

    data = result.to_dict()

    assert "version" in data
    assert "decision" in data
    assert "stability" in data
    assert "trace" in data


# =====================================================
# IR EXPORT
# =====================================================


def test_cognitive_os_ir_export():
    os = CognitiveOS()

    result = os.run("user_1", {"text": "hello"})
    ir = result.to_ir()

    assert ir is not None
    assert isinstance(ir, dict)


# =====================================================
# IR API DIRECT
# =====================================================


def test_cognitive_os_run_ir():
    os = CognitiveOS()

    ir = os.run_ir("user_1", {"text": "hello"})

    assert ir is not None
    assert isinstance(ir, dict)


# =====================================================
# IR ROUNDTRIP (CRITICAL)
# =====================================================


def test_cognitive_os_ir_roundtrip():
    os = CognitiveOS()

    result = os.run("user_1", {"text": "hello"})
    ir_dict = result.to_ir()

    assert ir_dict is not None

    ir = CognitiveIR.from_dict(ir_dict)

    replay_result = os.pipeline.run_from_ir(ir)

    assert replay_result is not None
    assert replay_result.action_decision is not None


# =====================================================
# REPLAY API
# =====================================================


def test_cognitive_os_replay():
    os = CognitiveOS()

    result = os.run("user_1", {"text": "hello"})
    ir_dict = result.to_ir()

    replay = os.replay(ir_dict)

    assert replay is not None
    assert replay.decision is not None


# =====================================================
# RUNTIME ADAPTER INJECTION
# =====================================================


def test_runtime_adapter_injection():
    config = CognitiveOSConfig(adapter_registry={"llm": "dummy"})

    os = CognitiveOS(config=config)

    ctx = os._build_context("user_1", {"text": "hello"})

    os.runtime.execute(ctx)

    assert "adapters" in ctx.extra
    assert ctx.extra["adapters"]["llm"] == "dummy"


# =====================================================
# MULTI AGENT
# =====================================================


def test_multi_agent_run():
    os = CognitiveOS()

    inputs = [
        {"text": "hello"},
        {"text": "world"},
    ]

    results = os.run_multi(inputs)

    assert len(results) == 2
    for r in results:
        assert r.decision is not None


# =====================================================
# INSPECT API
# =====================================================


def test_inspect_api():
    os = CognitiveOS()

    result = os.run("user_1", {"text": "hello"})

    inspection = os.inspect(result)

    assert "summary" in inspection
    assert "stability" in inspection
    assert "trace" in inspection


# =====================================================
# SAFE EXECUTION (NO CRASH)
# =====================================================


def test_no_crash_on_empty_input():
    os = CognitiveOS()

    result = os.run("user_1", {})

    assert result is not None


def test_cognitive_os_register_and_list_tools():
    from arvis.api.os import CognitiveOS
    from arvis.tools.base import BaseTool

    class DummyTool(BaseTool):
        name = "dummy"

        def execute(self, input_data):
            return {"ok": True}

    os = CognitiveOS()
    os.register_tool(DummyTool())

    assert "dummy" in os.list_tools()
