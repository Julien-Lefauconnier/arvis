# tests/kernel/stages/test_core_stage_edges.py


from arvis.kernel.pipeline.stages.core_stage import CoreStage
from arvis.math.lyapunov.lyapunov import LyapunovState



# ============================================================
# Helpers
# ============================================================

class DummyCore:
    def __init__(self, result):
        self._result = result

    def process(self, bundle):
        return self._result


class DummyPipeline:
    def __init__(self, result, family=None):
        self.core = DummyCore(result)
        self.quadratic_lyapunov_family = family
        self.quadratic_comparability = "ok"


class DummyCtx:
    def __init__(self):
        self.bundle = {}
        self.regime = "test"


class DummyScientific:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# ============================================================
# 1. NONE / FALLBACK PATHS
# ============================================================

def test_core_none_lyap():
    ctx = DummyCtx()
    pipeline = DummyPipeline(DummyScientific())

    CoreStage().run(pipeline, ctx)

    assert ctx.cur_lyap is None
    assert ctx.stable is None


# ============================================================
# 2. LYAP NORMALIZATION
# ============================================================

def test_core_scalar_lyap_normalization():
    ctx = DummyCtx()
    pipeline = DummyPipeline(
        DummyScientific(cur_lyap=1.23)
    )

    CoreStage().run(pipeline, ctx)

    assert isinstance(ctx.cur_lyap, LyapunovState)


# ============================================================
# 3. FAST DYNAMICS EXCEPTION PATH
# ============================================================

def test_fast_dynamics_exception(monkeypatch):
    ctx = DummyCtx()
    ctx.cur_lyap = LyapunovState.from_scalar(1.0)
    ctx.prev_lyap = LyapunovState.from_scalar(2.0)

    def broken(*args, **kwargs):
        raise ValueError

    from arvis.math.lyapunov import lyapunov as module
    monkeypatch.setattr(module, "lyapunov_value", broken)

    pipeline = DummyPipeline(DummyScientific(cur_lyap=1.0))

    CoreStage().run(pipeline, ctx)

    assert ctx.fast_dynamics is not None  # fallback works


# ============================================================
# 4. QUADRATIC FAMILY ABSENT
# ============================================================

def test_quadratic_family_none():
    ctx = DummyCtx()
    pipeline = DummyPipeline(
        DummyScientific(cur_lyap=1.0),
        family=None,
    )

    CoreStage().run(pipeline, ctx)

    assert ctx.quadratic_lyap_snapshot is None


# ============================================================
# 5. QUADRATIC FAMILY REGIME FALLBACK
# ============================================================

class FakeFamily:
    def has_regime(self, name):
        return False

    def value(self, name, state):
        return 1.0

    def delta(self, name, a, b):
        return 0.1


def test_quadratic_regime_fallback():
    ctx = DummyCtx()
    pipeline = DummyPipeline(
        DummyScientific(cur_lyap=1.0),
        family=FakeFamily(),
    )

    CoreStage().run(pipeline, ctx)

    assert ctx.quadratic_lyap_snapshot.regime == "transition"


# ============================================================
# 6. REFLEXIVE STATE NORMAL
# ============================================================

def test_reflexive_state():
    ctx = DummyCtx()

    pipeline = DummyPipeline(
        DummyScientific(
            reflexive_state={
                "stability_memory": 1,
                "structural_risk": 2,
                "regime_persistence": 3,
                "uncertainty_drift": 4,
            }
        )
    )

    CoreStage().run(pipeline, ctx)

    assert ctx.slow_state is not None


# ============================================================
# 7. REFLEXIVE STATE FAILURE
# ============================================================

def test_reflexive_state_exception(monkeypatch):
    ctx = DummyCtx()

    pipeline = DummyPipeline(
        DummyScientific(reflexive_state=object())
    )

    CoreStage().run(pipeline, ctx)

    assert ctx.slow_state is None


# ============================================================
# 8. PAPER SLOW DYNAMICS BRANCH 🔥
# ============================================================

def test_paper_slow_dynamics():
    ctx = DummyCtx()

    ctx.use_paper_slow_dynamics = True
    ctx.cur_lyap = LyapunovState.from_scalar(1.0)

    from arvis.math.lyapunov.slow_state import SlowState
    ctx.slow_state = SlowState.zero()

    pipeline = DummyPipeline(DummyScientific(cur_lyap=1.0))

    CoreStage().run(pipeline, ctx)

    assert ctx.slow_state is not None


# ============================================================
# 9. TARGET_MAP FAILURE
# ============================================================

def test_target_map_failure(monkeypatch):
    ctx = DummyCtx()

    ctx.use_paper_slow_dynamics = True
    ctx.cur_lyap = LyapunovState.from_scalar(1.0)

    from arvis.math.lyapunov.slow_state import SlowState
    ctx.slow_state = SlowState.zero()
    ctx.symbolic_state = object()

    from arvis.math.lyapunov import target_map as module

    monkeypatch.setattr(module, "target_map", lambda *a, **k: (_ for _ in ()).throw(ValueError))

    pipeline = DummyPipeline(DummyScientific(cur_lyap=1.0))

    CoreStage().run(pipeline, ctx)

    assert ctx.slow_state is not None  # fallback


# ============================================================
# 10. PERTURBATION FAILURE
# ============================================================

def test_perturbation_failure(monkeypatch):
    ctx = DummyCtx()

    import arvis.kernel.pipeline.stages.core_stage as module

    monkeypatch.setattr(module, "compute_perturbation", lambda *a, **k: (_ for _ in ()).throw(ValueError))

    pipeline = DummyPipeline(DummyScientific())

    CoreStage().run(pipeline, ctx)

    assert ctx.perturbation is None