# tests/kernel/test_api_module_exports.py

import importlib

API_MODULES = [
    "arvis.api.cognition",
    "arvis.api.math",
    "arvis.api.memory",
    "arvis.api.reasoning",
    "arvis.api.stability",
]


def test_api_modules_have_public_symbols():
    for modname in API_MODULES:
        module = importlib.import_module(modname)
        public = [name for name in dir(module) if not name.startswith("_")]
        assert public, f"{modname} exposes no public symbols"
