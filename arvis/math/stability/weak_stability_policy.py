# arvis/math/stability/weak_stability_policy.py
"""The registered weak-stability floor: a contraction RATE, not a step.

The local soft filter floors an ALLOW whose energy decrease is too
small to count as a demonstrated contraction. Until campaign SEUIL
the boundary was an absolute step, ``delta_w > -0.05``, living as a
``getattr`` default nothing ever configured. The M10 corpora measured
what that constant did: the ``nominal_feedback`` family, engineered
to contract on every turn (p_contraction 1.000), converges
geometrically, so its steps shrink as it succeeds (median |dW|
0.004), and the family got zero ALLOW. An absolute floor demands a
big step; contraction in the theory is proportional decrease.

DM-S1, registered by the owner on 2026-09-02 BEFORE the campaign
run, replaces the step with a rate:

    weak  iff  |delta_w| < max(RATE * W_current, ABSOLUTE_FLOOR)

RATE = 0.05: one third of the measured median contraction rate
(|dW|/W median 0.15 on contracting turns, both corpora), so a real
contraction clears it with margin. ABSOLUTE_FLOOR = 0.005: brackets
the p05-p10 of observed contracting |dW|, so a system hovering near
W = 0 cannot certify noise. Candidates -0.01, -0.025 and keeping
-0.05 were each measured on both full corpora before the choice: no
candidate produced one ALLOW outside the nominal, long_horizon and
feedback families, and D-1.0's ABSTAIN count is bit-identical under
all of them, the measured proof the filter never relaxes a refusal.

Changing either constant is a new registration with a new campaign
run, not a tuning pass; the test suite pins the registered values.
"""

from __future__ import annotations

from typing import Any

WEAK_STABILITY_RATE = 0.05
WEAK_STABILITY_ABSOLUTE_FLOOR = 0.005


def weak_stability_threshold(w_current: Any) -> float:
    """The (negative) delta_w boundary for the turn's energy.

    A delta strictly between this value and zero is a contraction too
    weak to certify. An absent or unreadable energy degrades to the
    absolute floor: fail-safe toward the registered policy, never an
    exception inside the gate.
    """
    try:
        w_value = float(w_current) if w_current is not None else 0.0
    except (TypeError, ValueError, OverflowError):
        w_value = 0.0
    if w_value < 0.0:
        w_value = 0.0
    return -max(WEAK_STABILITY_RATE * w_value, WEAK_STABILITY_ABSOLUTE_FLOOR)
