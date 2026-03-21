# tests/stability/test_stability_statistics.py

import pytest

from arvis.stability.stability_statistics import (
    StabilityStatistics,
    StabilityStatsSnapshot,
)


# ============================================================
# 1. EMPTY BUFFER
# ============================================================

def test_empty_snapshot():
    stats = StabilityStatistics()

    snap = stats.snapshot()

    assert snap.mean_delta == 0.0
    assert snap.contraction_rate == 0.0
    assert snap.instability_rate == 0.0
    assert snap.samples == 0


# ============================================================
# 2. ONLY NEGATIVE → FULL CONTRACTION
# ============================================================

def test_all_negative():
    stats = StabilityStatistics()

    for x in [-1.0, -2.0, -3.0]:
        stats.push(x)

    snap = stats.snapshot()

    assert snap.mean_delta < 0
    assert snap.contraction_rate == 1.0
    assert snap.instability_rate == 0.0
    assert snap.samples == 3


# ============================================================
# 3. ONLY POSITIVE → FULL INSTABILITY
# ============================================================

def test_all_positive():
    stats = StabilityStatistics()

    for x in [1.0, 2.0, 3.0]:
        stats.push(x)

    snap = stats.snapshot()

    assert snap.mean_delta > 0
    assert snap.contraction_rate == 0.0
    assert snap.instability_rate == 1.0
    assert snap.samples == 3


# ============================================================
# 4. MIXED VALUES
# ============================================================

def test_mixed_values():
    stats = StabilityStatistics()

    values = [-1.0, 1.0, -2.0, 2.0]  # 2 neg / 2 pos
    for v in values:
        stats.push(v)

    snap = stats.snapshot()

    assert snap.mean_delta == 0.0
    assert snap.contraction_rate == 0.5
    assert snap.instability_rate == 0.5
    assert snap.samples == 4


# ============================================================
# 5. ZERO VALUES (NEUTRAL)
# ============================================================

def test_zero_values():
    stats = StabilityStatistics()

    stats.push(0.0)
    stats.push(0.0)

    snap = stats.snapshot()

    assert snap.mean_delta == 0.0
    assert snap.contraction_rate == 0.0
    assert snap.instability_rate == 0.0
    assert snap.samples == 2


# ============================================================
# 6. WINDOW LIMIT
# ============================================================

def test_window_limit():
    stats = StabilityStatistics(window=3)

    for x in [1, 2, 3, 4]:  # dépasse window
        stats.push(x)

    snap = stats.snapshot()

    # doit garder seulement [2,3,4]
    assert snap.samples == 3
    assert snap.mean_delta == pytest.approx((2 + 3 + 4) / 3)


# ============================================================
# 7. COMPUTE PASSTHROUGH
# ============================================================

def test_compute_passthrough():
    stats = StabilityStatistics()

    snap = StabilityStatsSnapshot(
        mean_delta=1.0,
        contraction_rate=0.2,
        instability_rate=0.8,
        samples=10,
    )

    out = stats.compute(snap)

    assert out is snap