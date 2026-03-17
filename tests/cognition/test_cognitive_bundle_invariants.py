# tests/cognition/test_cognitive_bundle_invariants.py

import importlib


def test_cognitive_bundle_invariants_module_importable():

    module = importlib.import_module(
        "arvis.cognition.bundle.cognitive_bundle_invariants"
    )

    assert module is not None


def test_cognitive_bundle_invariants_has_public_symbols():

    module = importlib.import_module(
        "arvis.cognition.bundle.cognitive_bundle_invariants"
    )

    public = [name for name in dir(module) if not name.startswith("_")]

    assert len(public) > 0