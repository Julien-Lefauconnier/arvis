# arvis/adapters/kernel/mappers/ir_to_canonical.py

from __future__ import annotations

from veramem_kernel.api.signals import CanonicalSignal

from arvis.adapters.kernel.rules import ALL_RULES
from arvis.adapters.kernel.signals.signal_factory import SignalFactory
from arvis.ir.cognitive_ir import CognitiveIR


def ir_to_canonical(ir: CognitiveIR) -> list[CanonicalSignal]:
    signals: list[CanonicalSignal] = []
    emitted_codes: set[str] = set()

    logical_counter: int = 0

    def emit(code: str) -> None:
        nonlocal logical_counter

        if code not in emitted_codes:
            logical_counter += 1

            ts = logical_counter * 1e-6

            signals.append(
                SignalFactory.create(
                    code,
                    timestamp=ts,
                )
            )
            emitted_codes.add(code)

    for rule in ALL_RULES:
        if rule.applies(ir):
            for code in rule.emit_codes(ir):
                emit(code)

    return signals