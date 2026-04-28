# tests/math/core/test_local_dynamics.py

from arvis.math.core.local_dynamics import LocalCognitiveDynamics


def test_local_dynamics_initial_state():
    dyn = LocalCognitiveDynamics()

    assert dyn.size() == 0


def test_local_dynamics_push_and_size():
    dyn = LocalCognitiveDynamics()

    dyn.push(0.1, {"a": 0.5})
    dyn.push(-0.2, {"a": 0.2})

    assert dyn.size() == 2


def test_local_dynamics_estimate_none_if_not_enough_samples():
    dyn = LocalCognitiveDynamics(min_samples=5)

    dyn.push(0.1, {"a": 0.5})

    assert dyn.estimate_sensitivity() is None


def test_local_dynamics_estimate_valid():
    dyn = LocalCognitiveDynamics(min_samples=2)

    dyn.push(0.1, {"a": 1.0})
    dyn.push(0.2, {"a": 1.0})

    sens = dyn.estimate_sensitivity()

    assert sens is not None
    assert "a" in sens
