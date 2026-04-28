# arvis/adapters/kernel/signals/signal_semantics.py

from __future__ import annotations

from typing import Any

from arvis.api.signals import Signal


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
    def fingerprint(signal: Signal) -> tuple[str, Any, tuple[Any, Any, Any]]:
        payload: dict[str, Any] = signal.payload

        signal_type = payload["type"]

        return (
            signal.origin or "unknown",
            signal_type,
            SignalSemantics._normalize_payload(payload.get("payload", {})),
        )

    @staticmethod
    def _normalize_payload(payload: dict[str, Any]) -> tuple[Any, Any, Any]:
        return (
            payload.get("state"),
            payload.get("subject_ref"),
            payload.get("temporal_anchor"),
        )
