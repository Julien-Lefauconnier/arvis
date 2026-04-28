# tests/contracts/test_no_float_leakage.py

import inspect

import arvis.math.signals as signals


def test_no_direct_float_usage_in_signals():
    for _name, obj in inspect.getmembers(signals):
        if inspect.ismodule(obj):
            source = inspect.getsource(obj)

            # Allow float() in:
            # - coercion layer
            # - operator overloads
            if "def to_float" in source:
                continue

            if any(op in source for op in ["__lt__", "__le__", "__gt__", "__ge__"]):
                continue

            assert "float(" not in source
