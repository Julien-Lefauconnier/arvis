# tests/math/projection/test_pi_operator.py

from arvis.math.projection.pi_operator import PiOperator


def test_pi_operator_bounds_values():
    pi = PiOperator()

    view = {
        "state.system_tension": 10.0,
        "risk.conflict_pressure": -5.0,
        "control.control_signal": 0.5,
    }

    projected = pi.project(view)

    assert abs(projected["state.system_tension"]) < 1.0
    assert abs(projected["risk.conflict_pressure"]) < 1.0
    assert projected["control.control_signal"] != 0.5


def test_pi_operator_handles_empty_input():
    pi = PiOperator()

    projected = pi.project({})

    assert projected.to_dict() == {}


def test_pi_operator_ignores_non_numeric():
    pi = PiOperator()

    view = {
        "state.system_tension": "invalid",
        "risk.conflict_pressure": None,
        "control.control_signal": 0.2,
    }

    projected = pi.project(view)

    assert "state.system_tension" not in projected
    assert "risk.conflict_pressure" not in projected
    assert abs(projected["control.control_signal"]) < 0.2


def test_pi_operator_is_deterministic():
    pi = PiOperator()

    view = {"state.system_tension": 2.5}

    p1 = pi.project(view)
    p2 = pi.project(view)

    assert p1 == p2


def test_pi_operator_aggressive_when_invalid():
    class Ctx:
        validity_envelope = type("V", (), {"valid": False})()
        adaptive_snapshot = type("A", (), {"regime": "stable"})()

    pi = PiOperator()

    view = {"x": 10.0}
    projected = pi.project(view, Ctx())

    assert abs(projected["x"]) < 1.0


def test_pi_operator_stable_preserves_values():
    class Ctx:
        validity_envelope = type("V", (), {"valid": True})()
        adaptive_snapshot = type("A", (), {"regime": "stable"})()

    pi = PiOperator()

    view = {"x": 0.1}
    projected = pi.project(view, Ctx())

    assert abs(projected["x"] - 0.1) < 0.05


def test_pi_operator_critical_is_between():
    class Ctx:
        validity_envelope = type("V", (), {"valid": True})()
        adaptive_snapshot = type("A", (), {"regime": "critical"})()

    pi = PiOperator()

    view = {"x": 10.0}
    projected = pi.project(view, Ctx())

    assert abs(projected["x"]) < 10.0
    assert abs(projected["x"]) > 0.0


def test_pi_operator_is_bounded():
    pi = PiOperator()

    view = {
        "a": 1000.0,
        "b": -1000.0,
        "c": 0.0,
    }

    projected = pi.project(view)

    for v in projected.values():
        assert -1.0 < v < 1.0


def test_pi_operator_reacts_to_instability_not_to_drift():
    """Campaign PROJ moved this test.

    It used to seed ``_dv = 0.5`` labeled "forte divergence" and
    require strong contraction. ``_dv`` carries the drift score, a
    magnitude clamped to [0, 1], so the assertion pinned a reaction
    that fired on every turn with any drift at all, not a measured
    divergence (DM-P1, the same misread campaign ALLOW closed in the
    certificate). The operator now reacts to the instability channels
    that actually exist at projection time: the validity envelope and
    the adaptive regime, read from the canonical scientific nesting.
    """
    from types import SimpleNamespace

    def ctx(valid: bool) -> SimpleNamespace:
        return SimpleNamespace(
            scientific=SimpleNamespace(
                adaptive=SimpleNamespace(
                    validity_envelope=SimpleNamespace(valid=valid),
                    adaptive_snapshot=SimpleNamespace(regime="stable"),
                )
            ),
            _dv=0.5,
        )

    pi = PiOperator()
    view = {"x": 10.0}

    healthy = pi.project(view, ctx(valid=True))
    unstable = pi.project(view, ctx(valid=False))

    assert abs(unstable["x"]) < abs(healthy["x"])
    assert abs(unstable["x"]) < 0.9
