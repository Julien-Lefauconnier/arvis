# arvis/math/switching/switching_runtime.py

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass
class SwitchingRuntime:
    last_regime: str | None = None
    steps_since_switch: int = 0
    total_switches: int = 0

    # -----------------------------------------
    # Cross-turn threading (campaign PROJ, P3)
    # -----------------------------------------
    # The dwell clock rides the opaque scientific state blob as a
    # "switching" section, so a host that carries the blob (the
    # documented ArvisEngine contract) accumulates dwell time across
    # turns. The runtime owns its own (de)serialization, mirroring
    # the monitor's ownership of the rest of the blob.

    def to_state(self) -> dict[str, Any]:
        return {
            "last_regime": self.last_regime,
            "steps_since_switch": int(self.steps_since_switch),
            "total_switches": int(self.total_switches),
        }

    @classmethod
    def from_state(cls, raw: Any) -> SwitchingRuntime | None:
        """Rebuild from a blob section; None on anything malformed.

        Fail-safe, not fail-turn: a host replaying an old blob (no
        section) or a corrupted one gets a fresh clock, which is
        exactly the pre-threading behavior, never an error.
        """
        if not isinstance(raw, Mapping):
            return None
        try:
            last_regime = raw.get("last_regime")
            if last_regime is not None and not isinstance(last_regime, str):
                return None
            steps = int(raw["steps_since_switch"])
            switches = int(raw["total_switches"])
        except (KeyError, TypeError, ValueError):
            return None
        if steps < 0 or switches < 0:
            return None
        return cls(
            last_regime=last_regime,
            steps_since_switch=steps,
            total_switches=switches,
        )

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
        """Conservative dwell-time proxy (NOT the literature's average
        dwell).

        No switch yet: the steps spent in the current regime. After
        any switch: steps since the last switch divided by the total
        switch count, which SHRINKS as switches accumulate. A smaller
        value makes the T1 reading harder to satisfy, so frequent
        switching reads as less safe, never more; the trade-off is
        that a long-stable system that switched often in the past is
        under-credited. Documented in the core specification's
        reference-implementation disclosures (campaign HONEST-DOCS).
        """
        if self.total_switches == 0:
            return float(self.steps_since_switch)

        return float(self.steps_since_switch) / float(self.total_switches)
