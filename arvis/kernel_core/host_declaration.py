# arvis/kernel_core/host_declaration.py
"""Host-declared governance context and component manifests (campaign 5).

An ARVIS host injects governing components (gates, sinks, models,
registries) and runs several governed boundaries against them. Two
disanalogies with a7 that this module closes:

- **Component identity** (audit constat 17). a7 fingerprinted an
  injected component by ``type(obj).__qualname__`` only, so two gates
  of the same class configured differently shared a fingerprint: the
  config commitment did not distinguish two different governance
  postures. A component MAY now expose ``governance_manifest()``, and
  :func:`component_fingerprint_material` binds that full manifest when
  present, falling back to the qualname otherwise. The host declares
  WHAT its component governs, ARVIS binds it.

- **Host context** (D-1). A host needs to attach opaque declarative
  attributes to every governed intent (the boundary instance label
  today, other provenance tomorrow) without ARVIS interpreting them.
  :func:`resolve_host_context` normalizes a host-provided mapping into
  a canonical, JSON-safe context. ``instance_label`` is the one
  conventional key ARVIS reads (only to stamp it on intents); every
  other key is transported verbatim.

Doctrine (same as grants): ARVIS carries the generic mechanism, the
host provides the realization. Nothing here interprets host semantics;
it only transports and binds them, injectively, through the campaign-5
canonical encoder.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from arvis.kernel_core.canonicalization import (
    JSONValue,
    NonCanonicalizableError,
    canonicalize,
)

# The conventional host_context key ARVIS reads: an opaque label naming
# the governed boundary instance an intent originates from. ARVIS never
# interprets its value; it only stamps it on the journaled intent and
# the sink copy (structural provenance metadata, ZK-safe).
INSTANCE_LABEL_KEY = "instance_label"


@runtime_checkable
class GovernanceManifestProvider(Protocol):
    """A governing component that declares its full governance identity.

    A component implementing this returns a JSON-safe mapping describing
    WHAT it governs (module, version, code digest, instance state,
    endpoint, region, credentials profile, network options, whatever is
    governance-relevant). ARVIS binds the whole mapping into the config
    fingerprint instead of the class name alone, so two differently
    configured instances of the same class no longer collide.
    """

    def governance_manifest(self) -> dict[str, JSONValue]: ...


def component_fingerprint_material(obj: Any) -> JSONValue:
    """Fingerprint material for one injected governing component.

    - ``None`` -> ``None`` (absent component).
    - a :class:`GovernanceManifestProvider` -> a mapping binding the
      class qualname AND the declared manifest, canonicalized
      injectively. A raising or non-canonicalizable manifest is a host
      contract violation surfaced as :class:`NonCanonicalizableError`
      (fail-closed: a component that cannot declare its identity must
      not be silently reduced to its class name).
    - any other object -> the qualname only (a7-compatible fallback for
      components that do not yet declare a manifest).
    """
    if obj is None:
        return None
    manifest_fn = getattr(obj, "governance_manifest", None)
    if callable(manifest_fn):
        manifest = manifest_fn()
        # Bind class identity together with the declared manifest, both
        # canonicalized injectively.
        return canonicalize(
            {
                "type": type(obj).__qualname__,
                "manifest": manifest,
            }
        )
    return type(obj).__qualname__


def resolve_host_context(
    host_context: Any,
) -> dict[str, JSONValue] | None:
    """Normalize a host-provided context mapping into canonical form.

    ``None`` stays ``None`` (no host context; intents remain
    byte-identical to a run without it). A mapping is canonicalized
    injectively: keys must be strings (a host context is a declarative
    namespace, not arbitrary keyed data), values may be any
    canonicalizable JSON value. A non-string key or a non-canonicalizable
    value raises :class:`NonCanonicalizableError` — the host context is
    a governed input, so it fails closed rather than aliasing.

    ARVIS reads only :data:`INSTANCE_LABEL_KEY` from the result (to
    stamp it); every other key is transported without interpretation.
    """
    if host_context is None:
        return None
    if not isinstance(host_context, dict):
        raise NonCanonicalizableError(host_context, path="host_context")
    for key in host_context:
        if not isinstance(key, str):
            raise NonCanonicalizableError(
                host_context, path=f"host_context (non-string key {key!r})"
            )
    # canonicalize validates every value injectively and raises on any
    # non-canonicalizable one; the result is JSON-safe and deterministic.
    resolved = canonicalize(dict(host_context))
    if not isinstance(resolved, dict):
        # Structurally unreachable (a dict in yields a dict out), kept
        # as an explicit fail-closed raise: an assert vanishes under
        # ``python -O`` and this is a governed input boundary (Bandit
        # B101, a8 section 20).
        raise NonCanonicalizableError(resolved, path="host_context (canonical form)")
    return resolved


def instance_label_of(host_context: dict[str, JSONValue] | None) -> str | None:
    """Extract the conventional instance label, if declared as a string.

    Returns the label only when present and a plain string; any other
    shape yields ``None`` (ARVIS never coerces host values). The label
    is the one host_context key ARVIS acts on, and only to stamp it.
    """
    if not host_context:
        return None
    value = host_context.get(INSTANCE_LABEL_KEY)
    return value if isinstance(value, str) else None


__all__ = [
    "INSTANCE_LABEL_KEY",
    "GovernanceManifestProvider",
    "component_fingerprint_material",
    "instance_label_of",
    "resolve_host_context",
]
