# tests/contracts/test_public_docstrings.py
"""Every public symbol carries a docstring an IDE can show.

Campaign ONBOARD (audit #3 P1, 2026-09-03). The documentation lives
in docs/ by design, but an integrator exploring the API from an
editor sees ``__doc__``, and the audit measured the gap exactly
where it hurts: ``CognitiveOS`` itself and its most-used methods
(``run``, ``register_tool``) had none. This ratchet pins 100 percent
docstring coverage on the two supported surfaces: every symbol
exported by the root package and by each ``arvis.host_api`` module,
and every public method the two entrypoint classes define in arvis
code.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

import arvis
import arvis.host_api


def _documented(obj: object) -> bool:
    return bool((getattr(obj, "__doc__", None) or "").strip())


def _surface_symbols() -> list[tuple[str, object]]:
    symbols: list[tuple[str, object]] = [
        (f"arvis.{name}", getattr(arvis, name)) for name in arvis.__all__
    ]
    for sub in pkgutil.iter_modules(arvis.host_api.__path__):
        module = importlib.import_module(f"arvis.host_api.{sub.name}")
        for name in getattr(module, "__all__", []):
            symbols.append((f"arvis.host_api.{sub.name}.{name}", getattr(module, name)))
    return symbols


def test_every_public_surface_symbol_has_a_docstring() -> None:
    symbols = _surface_symbols()
    assert len(symbols) >= 60, f"surface scan collapsed: {len(symbols)}"
    missing = sorted(
        name
        for name, obj in symbols
        if not inspect.ismodule(obj) and not _documented(obj)
    )
    assert not missing, f"public symbol(s) without a docstring: {missing}"


def test_every_public_entrypoint_method_has_a_docstring() -> None:
    missing: list[str] = []
    for cls in (arvis.ArvisEngine, arvis.CognitiveOS):
        for name, member in inspect.getmembers(cls, inspect.isfunction):
            if name.startswith("_"):
                continue
            if not getattr(member, "__module__", "").startswith("arvis"):
                continue
            if not _documented(member):
                missing.append(f"{cls.__name__}.{name}")
    assert not missing, f"public method(s) without a docstring: {sorted(missing)}"
