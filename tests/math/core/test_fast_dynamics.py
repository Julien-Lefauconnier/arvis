# tests/math/core/test_fast_dynamics.py

from arvis.math.core.fast_dynamics import FastDynamicsSnapshot


def test_fast_dynamics_snapshot_valid():
    snap = FastDynamicsSnapshot(
        regime="STABLE",
        x_prev=1.0,
        x_next=0.5,
        delta_norm=0.5,
    )

    assert snap.is_valid() is True


def test_fast_dynamics_snapshot_invalid():
    snap = FastDynamicsSnapshot(
        regime="STABLE",
        x_prev=None,
        x_next=0.5,
        delta_norm=None,
    )

    assert snap.is_valid() is False


def test_fast_dynamics_delta_consistency():
    x_prev = 2.0
    x_next = 1.5

    snap = FastDynamicsSnapshot(
        regime="TEST",
        x_prev=x_prev,
        x_next=x_next,
        delta_norm=abs(x_next - x_prev),
    )

    assert snap.delta_norm == 0.5