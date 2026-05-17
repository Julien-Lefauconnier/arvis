# arvis/adapters/kernel/signals/signal_semantics.py

from __future__ import annotations

from typing import Any

from arvis.signals.canonical.canonical_signal import CanonicalSignal


class SignalSemantics:
    """
    Defines semantic equivalence for signals.

    Determinism model:

    Non-deterministic (excluded):
    - signal_id
    - timestamps
    - event_id (nested in payload)

    Deterministic fields (included):
    - signal_type
    - payload (filtered)
    - origin
    """

    @staticmethod
    def fingerprint(
        signal: CanonicalSignal,
    ) -> tuple[str, str, str, str, str]:
        return (
            signal.key.code,
            signal.state,
            signal.subject_ref,
            signal.temporal_anchor,
            signal.origin,
        )

    @staticmethod
    def _normalize_payload(payload: dict[str, Any]) -> tuple[Any, Any, Any]:
        return (
            payload.get("state"),
            payload.get("subject_ref"),
            payload.get("temporal_anchor"),
        )
