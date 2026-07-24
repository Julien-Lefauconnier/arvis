# tests/contracts/beta_manifest.py

"""Generator of the beta contract manifest (audit a13, BETA-02).

The manifest describes, by introspection, the surface the beta contract
freezes: the facade (ArvisEngine, every public method with its full
signature) and every host_api symbol (dataclass fields, class method
signatures, enum members, function signatures). It goes beyond names:
a parameter added, a default changed, a field retyped, an enum member
removed, all change the manifest.

Determinism: with ``from __future__ import annotations`` everywhere,
annotations are source text, so signatures render identically across
Python versions. The generator refuses any non-deterministic repr (a
memory address in a default) fail-closed rather than producing a golden
that flaps.

The golden file is ``beta_contract_manifest.json``; regeneration is a
deliberate act via ``scripts/regenerate_beta_manifest.py``.
"""

from __future__ import annotations

import dataclasses
import enum
import importlib
import inspect
from typing import Any

import pydantic

from tests.contracts.test_host_api_surface import HOST_API_SURFACE

MANIFEST_VERSION = 1


def _canonical_default(value: Any) -> str:
    """Deterministic rendering of a parameter default.

    Simple immutable values render as their repr. Anything else (an
    object whose repr may embed set ordering or memory addresses)
    renders as its type name only: the manifest then pins the presence
    and the type of the default, not a non-deterministic value.
    """
    if value is None or isinstance(value, (bool, int, float, str, bytes)):
        return repr(value)
    if isinstance(value, tuple) and all(
        v is None or isinstance(v, (bool, int, float, str, bytes)) for v in value
    ):
        return repr(value)
    if isinstance(value, enum.Enum):
        return f"{type(value).__name__}.{value.name}"
    return f"<{type(value).__name__}>"


def _render_annotation(annotation: Any) -> str:
    """Stable rendering whether annotations are source text or objects.

    Modules using ``from __future__ import annotations`` carry text and
    render as-is; modules with evaluated annotations render classes as
    their qualified name and anything else via str().
    """
    if isinstance(annotation, str):
        return annotation
    if isinstance(annotation, type):
        return f"{annotation.__module__}.{annotation.__qualname__}"
    return str(annotation)


def _signature_of(fn: Any) -> str:
    sig = inspect.signature(fn)
    parts: list[str] = []
    star_emitted = False
    parameters = list(sig.parameters.values())
    for index, parameter in enumerate(parameters):
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            star_emitted = True
        elif parameter.kind is inspect.Parameter.KEYWORD_ONLY and not star_emitted:
            parts.append("*")
            star_emitted = True

        rendered = parameter.name
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            rendered = f"*{rendered}"
        elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
            rendered = f"**{rendered}"
        if parameter.annotation is not inspect.Parameter.empty:
            rendered += f": {_render_annotation(parameter.annotation)}"
        if parameter.default is not inspect.Parameter.empty:
            rendered += f" = {_canonical_default(parameter.default)}"
        parts.append(rendered)

        if parameter.kind is inspect.Parameter.POSITIONAL_ONLY and (
            index + 1 == len(parameters)
            or parameters[index + 1].kind is not inspect.Parameter.POSITIONAL_ONLY
        ):
            parts.append("/")

    rendered_sig = f"({', '.join(parts)})"
    if sig.return_annotation is not inspect.Signature.empty:
        rendered_sig += f" -> {_render_annotation(sig.return_annotation)}"
    return rendered_sig


def _public_methods(cls: type) -> dict[str, str]:
    """Public methods defined by arvis code only.

    Methods inherited from external bases (pydantic, abc, ...) are not
    our contract and their signatures vary with the dependency version:
    including them would make the golden depend on the installed
    environment instead of on arvis.
    """
    methods: dict[str, str] = {}
    for name, member in inspect.getmembers(cls):
        if not (inspect.isfunction(member) or inspect.ismethod(member)):
            continue
        if name.startswith("_") and name != "__init__":
            continue
        if not getattr(member, "__module__", "").startswith("arvis"):
            continue
        methods[name] = _signature_of(member)
    return methods


def _properties(cls: type) -> dict[str, str]:
    props: dict[str, str] = {}
    for name, member in inspect.getmembers(cls, lambda m: isinstance(m, property)):
        if name.startswith("_"):
            continue
        fget = member.fget
        if fget is None or not getattr(fget, "__module__", "").startswith("arvis"):
            continue
        annotation = ""
        if fget is not None:
            raw = fget.__annotations__.get("return", "")
            annotation = _render_annotation(raw) if raw != "" else ""
        props[name] = annotation
    return props


def _describe(symbol_name: str, obj: Any) -> dict[str, Any]:
    if inspect.isclass(obj) and issubclass(obj, pydantic.BaseModel):
        # The contract of a pydantic model is its declared fields (our
        # code), never the surface inherited from pydantic itself.
        fields = {
            name: _render_annotation(info.annotation)
            for name, info in obj.model_fields.items()
        }
        return {
            "kind": "pydantic_model",
            "fields": fields,
            "methods": _public_methods(obj),
            "properties": _properties(obj),
        }
    if inspect.isclass(obj) and issubclass(obj, enum.Enum):
        return {
            "kind": "enum",
            "members": {member.name: member.value for member in obj},
        }
    if inspect.isclass(obj) and dataclasses.is_dataclass(obj):
        fields: dict[str, Any] = {}
        for field in dataclasses.fields(obj):
            fields[field.name] = {
                "type": _render_annotation(field.type),
                "has_default": (
                    field.default is not dataclasses.MISSING
                    or field.default_factory is not dataclasses.MISSING
                ),
            }
        return {
            "kind": "dataclass",
            "fields": fields,
            "methods": _public_methods(obj),
            "properties": _properties(obj),
        }
    if inspect.isclass(obj):
        return {
            "kind": "class",
            "methods": _public_methods(obj),
            "properties": _properties(obj),
        }
    if inspect.isfunction(obj):
        return {
            "kind": "function",
            "signature": _signature_of(obj),
        }
    raise TypeError(  # pragma: no cover - the surface holds none today
        f"unsupported contract symbol kind for {symbol_name}: {type(obj)!r}"
    )


def generate_manifest() -> dict[str, Any]:
    from arvis import host_api
    from arvis.api.engine import ArvisEngine

    manifest: dict[str, Any] = {
        "manifest_version": MANIFEST_VERSION,
        "host_api_version": host_api.HOST_API_VERSION,
        "provisional_modules": sorted(host_api.PROVISIONAL_MODULES),
        "facade": {
            "ArvisEngine": {
                "kind": "class",
                "methods": _public_methods(ArvisEngine),
                "properties": _properties(ArvisEngine),
            }
        },
        "host_api": {},
    }
    for module_name in sorted(HOST_API_SURFACE):
        module = importlib.import_module(f"arvis.host_api.{module_name}")
        described: dict[str, Any] = {}
        for symbol in sorted(HOST_API_SURFACE[module_name]):
            described[symbol] = _describe(symbol, getattr(module, symbol))
        manifest["host_api"][module_name] = described

    _refuse_non_deterministic(manifest)
    return manifest


def _refuse_non_deterministic(node: Any) -> None:
    """Fail closed on any repr carrying a memory address."""
    if isinstance(node, dict):
        for value in node.values():
            _refuse_non_deterministic(value)
    elif isinstance(node, list):
        for value in node:
            _refuse_non_deterministic(value)
    elif isinstance(node, str) and " at 0x" in node:
        raise ValueError(f"non-deterministic repr in the contract manifest: {node!r}")
