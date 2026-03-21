# tests/math/switching/test_switching_runtime.py

from arvis.math.switching.switching_runtime import SwitchingRuntime

def test_switching_runtime_counts_switches():
    rt = SwitchingRuntime()

    rt.update("stable")
    rt.update("stable")
    rt.update("unstable")

    assert rt.total_switches == 1
    assert rt.steps_since_switch == 0


def test_switching_runtime_dwell_time():
    rt = SwitchingRuntime()

    for _ in range(10):
        rt.update("stable")

    assert rt.dwell_time() > 0


