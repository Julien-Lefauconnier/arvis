# tests/math/switching/test_switching_gate_integration.py

from arvis.math.switching.switching_runtime import SwitchingRuntime
from arvis.math.switching.switching_params import SwitchingParams, switching_condition


def test_switching_condition_detects_instability():
    rt = SwitchingRuntime()

    # simulate rapid switching
    for i in range(10):
        rt.update("A" if i % 2 == 0 else "B")

    params = SwitchingParams(
        alpha=0.05,
        gamma_z=1.0,
        eta=0.5,
        L_T=2.0,
        J=5.0,
    )

    assert switching_condition(rt, params) is False
