# tests/telemetry/test_telemetry_core_adapter.py

from arvis.cognition.core.cognitive_core_result import CognitiveCoreResult
from arvis.telemetry import TelemetryKind, TelemetryLevel
from arvis.telemetry.adapters import CORE_STABILITY_COMPONENT, core_stability_event


def _core(**overrides: object) -> CognitiveCoreResult:
    kwargs: dict[str, object] = {
        "collapse_risk": 0.12,
        "dv": 0.03,
        "drift_score": 0.4,
        "regime": "stable",
        "stable": True,
        "prev_lyap": 0.9,
        "cur_lyap": 0.7,
    }
    kwargs.update(overrides)
    return CognitiveCoreResult(**kwargs)  # type: ignore[arg-type]


def test_core_event_maps_all_math_fields() -> None:
    event = core_stability_event(_core())
    assert event.kind is TelemetryKind.STABILITY
    assert event.level is TelemetryLevel.INFO
    assert event.component == CORE_STABILITY_COMPONENT
    assert event.attributes["collapse_risk"] == 0.12
    assert event.attributes["dv"] == 0.03
    assert event.attributes["drift_score"] == 0.4
    assert event.attributes["prev_lyap"] == 0.9
    assert event.attributes["cur_lyap"] == 0.7
    assert event.attributes["regime"] == "stable"
    assert event.attributes["stable"] is True


def test_cold_turn_zero_math_is_emitted_not_dropped() -> None:
    event = core_stability_event(
        CognitiveCoreResult(collapse_risk=0.0, dv=0.0, drift_score=0.0)
    )
    assert event.attributes["collapse_risk"] == 0.0
    assert event.attributes["regime"] is None
    assert event.attributes["stable"] is None
    assert event.attributes["prev_lyap"] is None
    assert event.attributes["cur_lyap"] is None


def test_lyapunov_wrapper_with_level_is_coerced() -> None:
    class _Lyap:
        def level(self) -> float:
            return 1.5

    event = core_stability_event(_core(cur_lyap=_Lyap()))
    assert event.attributes["cur_lyap"] == 1.5


def test_level_is_caller_supplied() -> None:
    event = core_stability_event(_core(), level=TelemetryLevel.WARNING)
    assert event.level is TelemetryLevel.WARNING
