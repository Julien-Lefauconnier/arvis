# tests/reflexive/test_import_all_reflexive.py

import pkgutil
import importlib
import arvis.reflexive


def test_import_all_reflexive_modules():
    """
    Ensure that all reflexive modules can be imported.
    This guarantees coverage visibility and catches import errors.
    """
    for module in pkgutil.walk_packages(
        arvis.reflexive.__path__,
        arvis.reflexive.__name__ + ".",
    ):
        importlib.import_module(module.name)

