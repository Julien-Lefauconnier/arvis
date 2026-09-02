# tests/kernel/test_api_module_exports.py
"""The dead public-namespace facades stay deleted.

Campaign SURFACE (DM-S1, audit P1-7, 2026-09-02). The integral audit
found four ``arvis.api`` modules (cognition, math, memory, reasoning)
that presented themselves as "Public ... primitives" while being
imported by nothing: not by ``arvis``, not by ``host_api``, not by any
example, only by this file's previous incarnation. Four dead facades
labeled public are four contradictions of the two-surface contract
(root ``arvis`` + ``arvis.host_api``), so they were deleted; this
test keeps them deleted and keeps the surviving aggregator modules
importable.
"""

import importlib

import pytest

DELETED_FACADES = [
    "arvis.api.cognition",
    "arvis.api.math",
    "arvis.api.memory",
    "arvis.api.reasoning",
]

API_MODULES = [
    "arvis.api.stability",
]


def test_api_modules_have_public_symbols():
    for modname in API_MODULES:
        module = importlib.import_module(modname)
        public = [name for name in dir(module) if not name.startswith("_")]
        assert public, f"{modname} exposes no public symbols"


@pytest.mark.parametrize("modname", DELETED_FACADES)
def test_dead_facades_stay_deleted(modname: str):
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module(modname)
