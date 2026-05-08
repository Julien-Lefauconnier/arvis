# tests/runtime/test_cognitive_execution_state.py

from arvis.runtime.execution import CognitiveExecutionState, ExecutionLLMState


def test_cognitive_execution_state_defaults():
    state = CognitiveExecutionState()

    assert state.process_id is None
    assert state.tick == 0
    assert isinstance(state.llm, ExecutionLLMState)
    assert state.syscall_results == []
    assert state.errors == []
    assert state.metadata == {}


def test_cognitive_execution_state_tracks_llm_observation():
    state = CognitiveExecutionState()

    state.llm.observation = {"confidence_mean": 0.8}
    state.llm.evaluation = {"risk": 0.2}
    state.llm.risk_signal = {"risk_pressure": 0.2}

    assert state.llm.observation["confidence_mean"] == 0.8
    assert state.llm.evaluation["risk"] == 0.2
    assert state.llm.risk_signal["risk_pressure"] == 0.2
