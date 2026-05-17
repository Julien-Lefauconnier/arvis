# tests/adapters/kernel/test_canonical_to_event.py

from arvis.adapters.kernel.kernel_adapter import KernelAdapter
from arvis.signals.canonical.canonical_signal_invariants import (
    assert_canonical_signal_valid,
)
from arvis.signals.signal_invariants import (
    assert_signal_has_timestamp,
)
from tests.adapters.kernel.fixtures import dummy_ir


def test_canonicals_signal_respects_kernel_invariants():
    adapter = KernelAdapter()
    ir = dummy_ir()

    signals = adapter.ingest_ir(ir)

    assert isinstance(signals, list)
    assert len(signals) > 0

    for signal in signals:
        assert_signal_has_timestamp(signal)
        assert_canonical_signal_valid(signal)


def test_kernel_adapter_outputs_valid_canonicals_signals():
    adapter = KernelAdapter()
    ir = dummy_ir()

    signals = adapter.ingest_ir(ir)

    for s in signals:
        assert hasattr(s, "key")
        assert hasattr(s, "state")
        assert hasattr(s, "subject_ref")
        assert hasattr(s, "temporal_anchor")
        assert hasattr(s, "timestamp")
