# tests/adapters/kernel/test_canonical_to_event.py

from arvis.adapters.kernel.kernel_adapter import KernelAdapter
from arvis.signals.signal_invariants import (
    assert_signal_has_timestamp,
    assert_signal_payload_exists,
)
from tests.adapters.kernel.fixtures import dummy_ir


def test_signal_respects_kernel_invariants():
    adapter = KernelAdapter()
    ir = dummy_ir()

    signals = adapter.ingest_ir(ir)

    assert isinstance(signals, list)
    assert len(signals) > 0

    for signal in signals:
        assert_signal_has_timestamp(signal)
        assert_signal_payload_exists(signal)


def test_kernel_adapter_outputs_valid_signals():
    adapter = KernelAdapter()
    ir = dummy_ir()

    signals = adapter.ingest_ir(ir)

    for s in signals:
        assert hasattr(s, "payload")
        assert hasattr(s, "timestamp")
