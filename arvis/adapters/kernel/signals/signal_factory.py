# arvis/adapters/kernel/signals/signal_factory.py

from __future__ import annotations

from typing import ClassVar, Dict, Protocol, Iterable
from uuid import uuid4
from datetime import datetime, timedelta, timezone

from veramem_kernel.api.signals import CanonicalSignal
from veramem_kernel.signals.canonical import CanonicalSignalRegistry
from veramem_kernel.signals.canonical import CanonicalSignalKey
import itertools
from typing import Iterator



class _SignalSpecProtocol(Protocol):
    @property
    def key(self) -> CanonicalSignalKey: ...

    @property
    def states_allowed(self) -> Iterable[str]: ...

    @property
    def origin_allowed(self) -> Iterable[str]: ...


class SignalFactory:
    _spec_by_code: ClassVar[Dict[str, _SignalSpecProtocol]] = {}
    _fallback_counter: ClassVar[Iterator[int]] = itertools.count()
    _last_ts: ClassVar[float] = 0.0

    @classmethod
    def _bootstrap(cls) -> None:
        if not cls._spec_by_code:
            cls._spec_by_code = {
                spec.key.code: spec
                for spec in CanonicalSignalRegistry.all()
            }

    @classmethod
    def create(
        cls,
        code: str,
        *,
        subject_ref: str = "timeline:entry:ir",
        temporal_anchor: str = "t0",
        timestamp: int | float | None = None,
    ) -> CanonicalSignal:
        cls._bootstrap()

        spec = cls._spec_by_code.get(code)
        if spec is None:
            raise ValueError(f"Unknown canonical signal code: {code}")

        state = cls._select_state(spec)
        origin = cls._select_origin(spec)

        signal = CanonicalSignal(
            signal_id=f"sig-{uuid4()}",
            key=spec.key,
            state=state,
            subject_ref=subject_ref,
            temporal_anchor=temporal_anchor,
            origin=origin,
            supersedes=None,
        )

        if timestamp is None:
            ts = next(cls._fallback_counter) * 1e-6
        else:
            ts = float(timestamp)

        # GLOBAL MONOTONIC GUARANTEE
        if ts <= cls._last_ts:
            ts = cls._last_ts + 1e-6

        cls._last_ts = ts

        dt = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=ts)

        object.__setattr__(signal, "timestamp", dt)

        return signal

    @staticmethod
    def _select_state(spec: _SignalSpecProtocol) -> str:
        if "ACTIVE" in spec.states_allowed:
            return "ACTIVE"
        return next(iter(spec.states_allowed))

    @staticmethod
    def _select_origin(spec: _SignalSpecProtocol) -> str:
        if "arvis" in spec.origin_allowed:
            return "arvis"
        return next(iter(spec.origin_allowed))