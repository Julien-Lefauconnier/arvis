# tests/kernel/stages/test_runtime_stage.py


from arvis.kernel.pipeline.stages.runtime_stage import RuntimeStage


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


class DummyCtx:
    pass


class DummyPipeline:
    def __init__(self, observer=None):
        self.global_stability_observer = observer


# ============================================================
# 1. FULL HAPPY PATH
# ============================================================


def test_runtime_full():
    ctx = DummyCtx()
    ctx.control_runtime = DummyRuntime()
    ctx.collapse_risk = 0.3
    ctx.action_decision = DummyAction("RUN")
    ctx.switching_runtime = DummySwitchingRuntime()
    ctx.regime = "stable"

    pipeline = DummyPipeline(observer=DummyObserver())

    RuntimeStage().run(pipeline, ctx)

    # runtime
    assert ctx.control_runtime.last_risk == 0.3
    assert ctx.control_runtime.inertia_risk == 0.3
    assert ctx.control_runtime.last_action == "RUN"

    # switching
    assert ctx.switching_runtime.updated == "stable"

    # observer
    assert ctx.global_stability_metrics == {"ok": True}


# ============================================================
# 2. RUNTIME BLOCK EXCEPTION
# ============================================================


def test_runtime_exception():
    ctx = DummyCtx()

    # force failure
    ctx.control_runtime = None
    ctx.collapse_risk = 0.3
    ctx.action_decision = None

    pipeline = DummyPipeline()

    # must NOT crash
    RuntimeStage().run(pipeline, ctx)


# ============================================================
# 3. SWITCHING NOT CALLED (missing runtime)
# ============================================================


def test_switching_missing_runtime():
    ctx = DummyCtx()
    ctx.regime = "stable"

    pipeline = DummyPipeline()

    RuntimeStage().run(pipeline, ctx)

    # nothing should happen (no crash)


# ============================================================
# 4. SWITCHING NOT CALLED (missing regime)
# ============================================================


def test_switching_missing_regime():
    ctx = DummyCtx()
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

    ctx = DummyCtx()
    ctx.switching_runtime = BrokenSwitch()
    ctx.regime = "stable"

    pipeline = DummyPipeline()

    RuntimeStage().run(pipeline, ctx)


# ============================================================
# 6. OBSERVER NONE
# ============================================================


def test_observer_none():
    ctx = DummyCtx()

    pipeline = DummyPipeline(observer=None)

    RuntimeStage().run(pipeline, ctx)

    # nothing set
    assert not hasattr(ctx, "global_stability_metrics")


# ============================================================
# 7. OBSERVER EXCEPTION
# ============================================================


def test_observer_exception():
    ctx = DummyCtx()

    pipeline = DummyPipeline(observer=BrokenObserver())

    RuntimeStage().run(pipeline, ctx)

    assert ctx.global_stability_metrics is None
