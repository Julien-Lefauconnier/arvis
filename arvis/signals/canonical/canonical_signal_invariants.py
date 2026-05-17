# arvis/signals/canonical/canonical_signal_invariants.py

from arvis.signals.canonical.canonical_signal import CanonicalSignal


def assert_canonical_signal_valid(signal: CanonicalSignal) -> None:
    if not signal.signal_id:
        raise AssertionError("CanonicalSignal.signal_id missing")

    if not signal.state:
        raise AssertionError("CanonicalSignal.state missing")

    if not signal.subject_ref:
        raise AssertionError("CanonicalSignal.subject_ref missing")

    if not signal.temporal_anchor:
        raise AssertionError("CanonicalSignal.temporal_anchor missing")
