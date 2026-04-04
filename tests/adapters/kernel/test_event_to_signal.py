# tests/adapters/kernel/test_event_to_signal.py

from veramem_kernel.invariants.signal.canonical.canonical_signal_invariants import (
    validate_canonical_signal
)
from tests.adapters.kernel.fixtures import dummy_ir
from arvis.adapters.kernel.mappers.ir_to_canonical import ir_to_canonical


def test_canonical_signal_is_valid():
    ir = dummy_ir()

    canonicals = ir_to_canonical(ir)

    assert len(canonicals) > 0

    for canonical in canonicals:
        validate_canonical_signal(canonical)


def test_ir_produces_expected_categories():
    ir = dummy_ir()

    canonicals = ir_to_canonical(ir)

    categories = {c.key.category for c in canonicals}

    assert len(categories) >= 1


