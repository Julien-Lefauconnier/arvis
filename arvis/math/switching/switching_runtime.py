# arvis/math/switching/switching_runtime.py

from dataclasses import dataclass


@dataclass
class SwitchingRuntime:
    last_regime: str | None = None
    steps_since_switch: int = 0
    total_switches: int = 0

    def update(self, regime: str) -> None:
        if self.last_regime is None:
            self.last_regime = regime
            return

        if regime != self.last_regime:
            self.total_switches += 1
            self.steps_since_switch = 0
            self.last_regime = regime
        else:
            self.steps_since_switch += 1

    # -----------------------------------------
    # Dwell-time (paper alignment)
    # -----------------------------------------
    def dwell_time(self) -> float:
        """
        Average dwell-time proxy.

        If no switch occurred:
            return time spent in current regime.

        Otherwise:
            return average steps between switches.
        """
        if self.total_switches == 0:
            return float(self.steps_since_switch)

        return float(self.steps_since_switch) / float(self.total_switches)
