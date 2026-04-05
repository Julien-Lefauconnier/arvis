# tests/runtime/test_runtime_integration.py

from arvis.api.os import CognitiveOS

def test_runtime_executes_pipeline_via_scheduler():

    os = CognitiveOS()

    result = os.run(
        user_id="u1",
        cognitive_input={"test": "value"},
    )

    # comportement attendu
    assert result is not None

    # important : vérifier que ça passe toujours par pipeline
    ir = result.to_ir()
    assert ir is not None

def test_runtime_creates_process():

    os = CognitiveOS()

    runtime = os.runtime

    assert len(runtime.runtime_state.processes) == 0

    os.run(user_id="u1", cognitive_input={})

    assert len(runtime.runtime_state.processes) == 1

def test_runtime_scheduler_selects_process():

    os = CognitiveOS()

    os.run(user_id="u1", cognitive_input={})

    processes = list(os.runtime.runtime_state.processes.values())

    assert len(processes) == 1

    proc = processes[0]

    # In iterative scheduler, process may still be READY after run()
    assert proc.status.name in [
        "READY",
        "COMPLETED",
        "WAITING_CONFIRMATION",
    ]


def test_runtime_multiple_processes():

    os = CognitiveOS()

    for i in range(3):
        os.run(user_id=f"u{i}", cognitive_input={})

    assert len(os.runtime.runtime_state.processes) == 3