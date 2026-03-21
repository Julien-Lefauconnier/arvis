# tests/math/switching/test_regime_mapper.py

from arvis.math.switching.regime_mapper import map_regime
from arvis.math.switching.regime_state import TheoreticalRegime


# ============================================================
# 1. EACH REGIME
# ============================================================

def test_map_stable():
    r = map_regime("stable", 0.5)
    assert r.q_t == TheoreticalRegime.STABLE
    assert r.confidence == 0.5


def test_map_oscillatory():
    r = map_regime("oscillatory")
    assert r.q_t == TheoreticalRegime.OSCILLATORY


def test_map_critical():
    r = map_regime("critical")
    assert r.q_t == TheoreticalRegime.CRITICAL


def test_map_chaotic():
    r = map_regime("chaotic")
    assert r.q_t == TheoreticalRegime.CHAOTIC


def test_map_neutral():
    r = map_regime("neutral")
    assert r.q_t == TheoreticalRegime.NEUTRAL


# ============================================================
# 2. DEFAULT / FALLBACK
# ============================================================

def test_map_unknown():
    r = map_regime("unknown")
    assert r.q_t == TheoreticalRegime.TRANSITION


def test_map_none():
    r = map_regime(None)
    assert r.q_t == TheoreticalRegime.TRANSITION


# ============================================================
# 3. CASE INSENSITIVE
# ============================================================

def test_case_insensitive():
    r = map_regime("StAbLe")
    assert r.q_t == TheoreticalRegime.STABLE


# ============================================================
# 4. CONFIDENCE DEFAULT / COERCION
# ============================================================

def test_confidence_default():
    r = map_regime("stable")
    assert r.confidence == 0.0


def test_confidence_coercion():
    r = map_regime("stable", confidence=None)
    assert r.confidence == 0.0


def test_confidence_cast():
    r = map_regime("stable", confidence=1)
    assert isinstance(r.confidence, float)
    assert r.confidence == 1.0