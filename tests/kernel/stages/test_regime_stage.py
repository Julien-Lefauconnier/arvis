# tests/kernel/stages/test_regime_stage.py


from arvis.kernel.pipeline.stages.regime_stage import RegimeStage


# ============================================================
# Helpers
# ============================================================

class DummySnapshot:
    def __init__(self, regime="stable", confidence=0.8):
        self.regime = regime
        self.confidence = confidence


class DummyEstimator:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def push(self, x):
        return self.snapshot


class DummyPipeline:
    def __init__(self, estimator):
        self.regime_estimator = estimator


class DummyCtx:
    pass


class DummySwitchingRuntime:
    def __init__(self):
        self.updated = None

    def update(self, value):
        self.updated = value


# ============================================================
# 1. FULL HAPPY PATH
# ============================================================

def test_full_flow():
    ctx = DummyCtx()
    ctx.drift_score = 0.2
    ctx.switching_runtime = DummySwitchingRuntime()

    pipeline = DummyPipeline(DummyEstimator(DummySnapshot("stable", 0.9)))

    RegimeStage().run(pipeline, ctx)

    assert ctx.regime == "stable"
    assert ctx.regime_confidence == 0.9
    assert ctx.theoretical_regime is not None
    assert ctx.switching_runtime.updated == "stable"


# ============================================================
# 2. SNAPSHOT NONE → FALLBACK
# ============================================================

def test_snapshot_none():
    ctx = DummyCtx()
    ctx.drift_score = 0.1
    ctx.switching_runtime = DummySwitchingRuntime()

    pipeline = DummyPipeline(DummyEstimator(None))

    RegimeStage().run(pipeline, ctx)

    assert ctx.regime == "transition"
    assert ctx.regime_confidence == 0.0


# ============================================================
# 3. SWITCHING RUNTIME AUTO-CREATION
# ============================================================

def test_runtime_auto_creation(monkeypatch):
    ctx = DummyCtx()
    ctx.drift_score = 0.1

    # fake SwitchingRuntime
    class FakeRuntime:
        def update(self, *a, **k):
            pass

    monkeypatch.setattr(
        "arvis.math.switching.switching_runtime.SwitchingRuntime",
        FakeRuntime,
    )

    pipeline = DummyPipeline(DummyEstimator(DummySnapshot()))

    RegimeStage().run(pipeline, ctx)

    assert ctx.switching_runtime is not None


# ============================================================
# 4. SWITCHING RUNTIME IMPORT FAILURE
# ============================================================

def test_runtime_import_failure(monkeypatch):
    ctx = DummyCtx()
    ctx.drift_score = 0.1

    # force import error
    monkeypatch.setitem(
        __import__("sys").modules,
        "arvis.math.switching.switching_runtime",
        None,
    )

    pipeline = DummyPipeline(DummyEstimator(DummySnapshot()))

    RegimeStage().run(pipeline, ctx)

    assert ctx.switching_runtime is None


# ============================================================
# 5. MAP_REGIME FAILURE
# ============================================================

def test_map_regime_exception(monkeypatch):
    ctx = DummyCtx()
    ctx.drift_score = 0.1
    ctx.switching_runtime = DummySwitchingRuntime()

    pipeline = DummyPipeline(DummyEstimator(DummySnapshot()))

    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.regime_stage.map_regime",
        lambda *a, **k: (_ for _ in ()).throw(ValueError),
    )

    RegimeStage().run(pipeline, ctx)

    assert ctx.theoretical_regime is None


# ============================================================
# 6. SWITCHING UPDATE FAILURE
# ============================================================

def test_switching_update_exception():
    class BrokenRuntime:
        def update(self, *a, **k):
            raise ValueError

    ctx = DummyCtx()
    ctx.drift_score = 0.1
    ctx.switching_runtime = BrokenRuntime()

    pipeline = DummyPipeline(DummyEstimator(DummySnapshot()))

    # should NOT crash
    RegimeStage().run(pipeline, ctx)


# ============================================================
# 7. NO SWITCHING RUNTIME
# ============================================================

def test_no_switching_runtime_and_no_import(monkeypatch):
    ctx = DummyCtx()
    ctx.drift_score = 0.1
    ctx.switching_runtime = None

    # force import failure
    monkeypatch.setattr(
        "arvis.kernel.pipeline.stages.regime_stage.map_regime",
        lambda *a, **k: None,
    )

    pipeline = DummyPipeline(DummyEstimator(DummySnapshot()))

    RegimeStage().run(pipeline, ctx)

    # should not crash