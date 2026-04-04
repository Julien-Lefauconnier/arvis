# arvis/adapters/kernel/signals/signal_factory.py

from __future__ import annotations

from typing import ClassVar, Dict, Protocol, Iterable
from uuid import uuid4

from veramem_kernel.api.signals import CanonicalSignal
from veramem_kernel.signals.canonical import CanonicalSignalRegistry
from veramem_kernel.signals.canonical import CanonicalSignalKey


class _SignalSpecProtocol(Protocol):
    @property
    def key(self) -> CanonicalSignalKey: ...

    @property
    def states_allowed(self) -> Iterable[str]: ...

    @property
    def origin_allowed(self) -> Iterable[str]: ...


class SignalFactory:
    _spec_by_code: ClassVar[Dict[str, _SignalSpecProtocol]] = {}

    @classmethod
    def _bootstrap(cls) -> None:
        if not cls._spec_by_code:
            cls._spec_by_code = {
                spec.key.code: spec
                for spec in CanonicalSignalRegistry.all()
            }

    @classmethod
    def create(cls, code: str) -> CanonicalSignal:
        cls._bootstrap()

        spec = cls._spec_by_code.get(code)
        if spec is None:
            raise ValueError(f"Unknown canonical signal code: {code}")

        state = cls._select_state(spec)
        origin = cls._select_origin(spec)

        return CanonicalSignal(
            signal_id=f"sig-{uuid4()}",
            key=spec.key,
            state=state,
            subject_ref="timeline:entry:ir",
            temporal_anchor="t0",
            origin=origin,
            supersedes=None,
        )

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