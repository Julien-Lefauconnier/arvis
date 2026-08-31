# arvis/control/control_inertia.py

from dataclasses import dataclass


@dataclass
class ControlInertiaSnapshot:
    mode: str
    smoothed_risk: float
    persistence: int


class ControlInertia:
    """
    Temporal inertia and hysteresis for cognitive mode stability.

    Prevents oscillations between SAFE / NORMAL / ABSTAIN.
    """

    def __init__(
        self,
        alpha: float = 0.3,
        safe_enter: float = 0.7,
        safe_exit: float = 0.5,
        abstain_enter: float = 0.9,
        abstain_exit: float = 0.7,
        persistence_steps: int = 3,
    ):
        self.alpha = alpha
        self.safe_enter = safe_enter
        self.safe_exit = safe_exit
        self.abstain_enter = abstain_enter
        self.abstain_exit = abstain_exit
        self.persistence_steps = persistence_steps

        self._state: dict[str, str] = {}
        self._risk: dict[str, float] = {}
        self._count: dict[str, int] = {}

    def update(
        self,
        user_id: str,
        collapse_risk: float | None,
    ) -> ControlInertiaSnapshot:
        r = float(collapse_risk or 0.0)

        # --------------------------------
        # EMA smoothing
        # --------------------------------
        prev = self._risk.get(user_id, r)
        smoothed = self.alpha * r + (1 - self.alpha) * prev
        self._risk[user_id] = smoothed

        mode = self._state.get(user_id, "NORMAL")
        count = self._count.get(user_id, 0)

        target = mode

        # --------------------------------
        # Target mode from smoothed risk
        # --------------------------------
        if smoothed >= self.abstain_enter:
            target = "ABSTAIN"
        elif smoothed >= self.safe_enter:
            target = "SAFE"
        elif smoothed <= self.safe_exit:
            target = "NORMAL"

        # --------------------------------
        # Persistence logic
        # --------------------------------
        if target != mode:
            count += 1
            if count >= self.persistence_steps:
                mode = target
                count = 0
        else:
            count = 0

        self._state[user_id] = mode
        self._count[user_id] = count

        return ControlInertiaSnapshot(
            mode=mode,
            smoothed_risk=smoothed,
            persistence=count,
        )
