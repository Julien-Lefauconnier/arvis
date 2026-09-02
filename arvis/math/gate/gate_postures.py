# arvis/math/gate/gate_postures.py

"""Typed gate postures (campaign SURFACE, DM-S5, 2026-09-02).

The three verdict-affecting postures of the pipeline context were free
strings ("soft", "confirm", "graded", ...) compared inline at each
reader: nothing named the closed set, and a typo in a host-provided
value silently selected whatever the reader's else branch did. These
StrEnums name the sets; wire values are unchanged, so a host that
still assigns the plain string compares equal and nothing breaks.

The readers deliberately do NOT parse or coerce: an unknown string
keeps exactly the fail-closed behavior each reader documents (soft
posture not matched means enforcement; graded not matched means
harden-only; a confirm/abstain switch not matched means the reader's
default arm).
"""

from __future__ import annotations

from enum import StrEnum


class GlobalStabilityAction(StrEnum):
    """Posture of the global-instability policy layer."""

    IGNORE = "ignore"
    CONFIRM = "confirm"
    ABSTAIN = "abstain"


class SwitchingEnvelopeMode(StrEnum):
    """Posture feeding measured switching safety into the envelope.

    SOFT keeps switching observability-only; ENFORCE (production) and
    any unknown value feed the measured safety into the validity
    envelope (unknown modes fail closed into enforcement).
    """

    SOFT = "soft"
    ENFORCE = "enforce"


class InputRiskMode(StrEnum):
    """Posture of the declared-input-risk gate.

    GRADED allows the pure-scalar grading path; HARDEN_ONLY
    (production) and any unknown value restrict a declared risk to
    harden-only.
    """

    GRADED = "graded"
    HARDEN_ONLY = "harden_only"


class TheoreticalEnforcementMode(StrEnum):
    """Posture of the strict theoretical-enforcement branch.

    MONITOR (default) observes; STRICT turns an envelope hard block
    into an immediate ABSTAIN. Campaign HARDEN (DM-H9d): the knob was
    read but never written anywhere, so the strict branch was
    unreachable; it is now a declared context field a host can set.
    """

    MONITOR = "monitor"
    STRICT = "strict"
