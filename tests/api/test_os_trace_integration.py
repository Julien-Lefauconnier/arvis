# tests/api/test_os_trace_integration.py

from arvis.api.os import CognitiveOS


def test_os_returns_trace_view():
    os = CognitiveOS()

    result = os.run(user_id="u1", cognitive_input="hello")

    # version full trace activée
    assert hasattr(result, "trace_view") or "trace" in result
