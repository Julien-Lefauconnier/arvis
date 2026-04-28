# tests/control/test_control_inertia.py

from arvis.control.control_inertia import ControlInertia


def test_control_inertia_importable():
    assert ControlInertia is not None


def test_inertia_basic_update():
    inertia = ControlInertia()

    snap = inertia.update("u", collapse_risk=0.5)

    assert snap.mode in {"NORMAL", "SAFE", "ABSTAIN"}
    assert 0.0 <= snap.smoothed_risk <= 1.0
    assert isinstance(snap.persistence, int)


def test_inertia_smoothing_effect():
    inertia = ControlInertia(alpha=0.5)

    inertia.update("u", collapse_risk=1.0)
    snap2 = inertia.update("u", collapse_risk=0.0)

    # EMA should smooth → not equal to raw 0
    assert snap2.smoothed_risk > 0.0


def test_inertia_mode_transition_with_persistence():
    inertia = ControlInertia(
        safe_enter=0.6,
        persistence_steps=2,
    )

    # first step → no switch yet
    snap1 = inertia.update("u", collapse_risk=1.0)
    assert snap1.mode == "NORMAL"

    # second step → switch
    snap2 = inertia.update("u", collapse_risk=1.0)
    assert snap2.mode in {"SAFE", "ABSTAIN"}


def test_inertia_abstain_priority():
    inertia = ControlInertia(abstain_enter=0.8)

    for _ in range(5):
        snap = inertia.update("u", collapse_risk=1.0)

    assert snap.mode == "ABSTAIN"


def test_inertia_reset_persistence():
    inertia = ControlInertia(persistence_steps=2)

    inertia.update("u", collapse_risk=1.0)
    inertia.update("u", collapse_risk=0.0)

    snap = inertia.update("u", collapse_risk=0.0)

    # Due to EMA smoothing  hysteresis, mode may still be SAFE
    assert snap.mode in {"NORMAL", "SAFE"}


def test_inertia_multiple_users_independent():
    inertia = ControlInertia()

    a = inertia.update("a", collapse_risk=0.1)
    b = inertia.update("b", collapse_risk=1.0)

    assert a.smoothed_risk != b.smoothed_risk


def test_inertia_none_risk():
    inertia = ControlInertia()

    snap = inertia.update("u", collapse_risk=None)

    assert snap.smoothed_risk == 0.0


def test_smooth_api_basic():
    inertia = ControlInertia(alpha=0.5)

    v = inertia.smooth(new_value=1.0, previous_value=0.0)

    assert 0.0 < v < 1.0


def test_smooth_api_no_previous():
    inertia = ControlInertia()

    v = inertia.smooth(new_value=0.7, previous_value=None)

    assert v == 0.7


def test_inertia_eventual_return_to_normal():
    inertia = ControlInertia(persistence_steps=1)

    inertia.update("u", collapse_risk=1.0)

    for _ in range(10):
        snap = inertia.update("u", collapse_risk=0.0)

    assert snap.mode == "NORMAL"
