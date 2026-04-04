# arvis/adapters/kernel/kernel_adapter.py

from typing import List


from veramem_kernel.signals.signal_journal import get_signal_journal
from veramem_kernel.api.signals import Signal

from .mappers.ir_to_canonical import ir_to_canonical
from .canonical_to_event import canonical_to_event
from .event_to_signal import event_to_signal
from arvis.ir.cognitive_ir import CognitiveIR


class KernelAdapter:

    def __init__(self) -> None:
        self.journal = get_signal_journal()

    def ingest_ir(self, ir: CognitiveIR) -> List[Signal]:
        canonicals = ir_to_canonical(ir)

        signals: List[Signal] = []
        for c in canonicals:
            event = canonical_to_event(c)
            signal = event_to_signal(event)
            self.journal.append(signal)
            signals.append(signal)

        return signals
