# tests/cognition/control/test_cognitive_control_runtime.py


def test_runtime_initial_state():
    from arvis.cognition.control.cognitive_control_runtime import (
        CognitiveControlRuntime,
    )

    runtime = CognitiveControlRuntime()

    assert runtime.last_risk is None
    assert runtime.inertia_risk is None
    assert runtime.last_action is None


def test_runtime_updates_values():
    from arvis.cognition.control.cognitive_control_runtime import (
        CognitiveControlRuntime,
    )

    runtime = CognitiveControlRuntime()

    runtime.last_risk = 0.5
    runtime.inertia_risk = 0.5
    runtime.last_action = "ALLOW"

    assert runtime.last_risk == 0.5
    assert runtime.inertia_risk == 0.5
    assert runtime.last_action == "ALLOW"


def test_runtime_isolation_between_instances():
    from arvis.cognition.control.cognitive_control_runtime import (
        CognitiveControlRuntime,
    )

    r1 = CognitiveControlRuntime()
    r2 = CognitiveControlRuntime()

    r1.last_risk = 0.8

    assert r2.last_risk is None


def test_pipeline_assigns_runtime(ctx, pipeline):
    pipeline.run(ctx)

    assert hasattr(ctx, "control_runtime")
    assert ctx.control_runtime is not None
