# tests/kernel/test_immutability_contracts.py

import inspect
import dataclasses
import arvis


def iter_classes(module):

    for name in dir(module):
        obj = getattr(module, name)

        if inspect.isclass(obj):
            yield obj


def test_dataclasses_are_frozen():

    import arvis.timeline
    import arvis.cognition
    import arvis.memory

    modules = [
        arvis.timeline,
        arvis.cognition,
        arvis.memory,
    ]

    for module in modules:

        for cls in iter_classes(module):

            if dataclasses.is_dataclass(cls):

                params = getattr(cls, "__dataclass_params__", None)

                assert params.frozen, f"{cls} must be frozen"