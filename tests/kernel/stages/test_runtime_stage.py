# tests/kernel/stages/test_runtime_stage.py

from arvis.kernel.pipeline.stages.runtime_stage import RuntimeStage
from tests.fixtures.builders.runtime_builder import (
    build_runtime_test_context,
)

# ============================================================
# Helpers
# ============================================================


class DummyRuntime:
    def __init__(self):
        self.last_risk = None
        self.inertia_risk = None
        self.last_action = None


class DummyAction:
    def __init__(self, mode):
        self.mode = mode


class DummySwitchingRuntime:
    def __init__(self):
        self.updated = None

    def update(self, value):
        self.updated = value


class DummyObserver:
    def update(self, ctx):
        return {"ok": True}


class BrokenObserver:
    def update(self, ctx):
        raise ValueError


class DummyPipeline:
    def __init__(self, observer=None):
        self.global_stability_observer = observer


# ============================================================
# 1. FULL HAPPY PATH
# ============================================================


def test_runtime_full():
    ctx = build_runtime_test_context()

    ctx.runtime_bindings.control_runtime = DummyRuntime()
    ctx.collapse_risk = 0.3
    ctx.execution.action_decision = DummyAction("RUN")
    ctx.switching_runtime = DummySwitchingRuntime()
    ctx.regime = "stable"

    pipeline = DummyPipeline(observer=DummyObserver())

    RuntimeStage().run(pipeline, ctx)

    # runtime
    runtime = ctx.runtime_bindings.control_runtime

    assert runtime is not None
    assert runtime.last_risk == 0.3
    assert runtime.inertia_risk == 0.3
    assert runtime.last_action == "RUN"

    # switching
    assert ctx.switching_runtime.updated == "stable"

    # observer
    assert ctx.global_stability_metrics == {"ok": True}


# ============================================================
# 2. RUNTIME BLOCK EXCEPTION
# ============================================================


def test_runtime_exception():
    ctx = build_runtime_test_context()

    # force failure
    ctx.runtime_bindings.control_runtime = None
    ctx.collapse_risk = 0.3
    ctx.execution.action_decision = None

    pipeline = DummyPipeline()

    # must NOT crash
    RuntimeStage().run(pipeline, ctx)


# ============================================================
# 3. SWITCHING NOT CALLED (missing runtime)
# ============================================================


def test_switching_missing_runtime():
    ctx = build_runtime_test_context()
    ctx.regime = "stable"

    pipeline = DummyPipeline()

    RuntimeStage().run(pipeline, ctx)

    # nothing should happen (no crash)


# ============================================================
# 4. SWITCHING NOT CALLED (missing regime)
# ============================================================


def test_switching_missing_regime():
    ctx = build_runtime_test_context()
    ctx.switching_runtime = DummySwitchingRuntime()

    pipeline = DummyPipeline()

    RuntimeStage().run(pipeline, ctx)

    assert ctx.switching_runtime.updated is None


# ============================================================
# 5. SWITCHING EXCEPTION
# ============================================================


def test_switching_exception():
    class BrokenSwitch:
        def update(self, *a, **k):
            raise ValueError

    ctx = build_runtime_test_context()
    ctx.switching_runtime = BrokenSwitch()
    ctx.regime = "stable"

    pipeline = DummyPipeline()

    RuntimeStage().run(pipeline, ctx)


# ============================================================
# 6. OBSERVER NONE
# ============================================================


def test_observer_none():
    ctx = build_runtime_test_context()

    pipeline = DummyPipeline(observer=None)

    RuntimeStage().run(pipeline, ctx)

    # nothing set
    assert not hasattr(ctx, "global_stability_metrics")


# ============================================================
# 7. OBSERVER EXCEPTION
# ============================================================


def test_observer_exception():
    ctx = build_runtime_test_context()

    pipeline = DummyPipeline(observer=BrokenObserver())

    RuntimeStage().run(pipeline, ctx)

    assert ctx.global_stability_metrics is None
