# arvis/tools/registry.py


import hashlib
import json
from typing import Any

from arvis.errors.base import ArvisSecurityError
from arvis.tools.base import BaseTool
from arvis.tools.spec import ToolSpec

# Version of the manifest structure, embedded in the fingerprint: a
# change in what the manifest covers is a change in what the host has
# pinned, and must be visible as a fingerprint change.
MANIFEST_SCHEMA_VERSION = 1


def _schema_sha256(name: str, which: str, schema: dict[str, Any]) -> str | None:
    """Hash a declared tool schema for the manifest (F-018 coherence).

    The manifest never carries schema content in clear, only a
    canonical hash. A schema that cannot be canonicalized cannot be
    committed to: pinning an unpinnable surface is refused.
    """
    if not schema:
        return None
    try:
        canonical = json.dumps(
            schema, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
    except (TypeError, ValueError) as exc:
        raise ArvisSecurityError(
            f"tool {name!r} declares a non-canonicalizable {which} schema; "
            "the registry surface cannot be pinned",
            details={"tool": name, "schema": which},
        ) from exc
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._frozen: bool = False

    def register(self, tool: BaseTool, *, replace: bool = False) -> None:
        """Register a tool under its declared name.

        F-004: a governed registry is never mutated silently. A
        frozen registry refuses any registration, and re-registering
        an existing name requires an explicit replace=True.
        """
        name = tool.name
        if self._frozen:
            raise ArvisSecurityError(
                f"tool registry is frozen; cannot register {name!r}",
                details={"tool": name},
            )
        if name in self._tools and not replace:
            raise ArvisSecurityError(
                f"tool {name!r} is already registered; explicit "
                "replace=True is required to replace it",
                details={"tool": name},
            )
        self._tools[name] = tool

    def freeze(self) -> str:
        """Freeze the registry after bootstrap.

        Returns the registry fingerprint so the host can pin and
        audit the frozen tool surface.
        """
        self._frozen = True
        return self.fingerprint()

    @property
    def frozen(self) -> bool:
        return self._frozen

    def manifest(self) -> dict[str, Any]:
        """Canonical, governance-complete description of the surface.

        One entry per registered tool: identity (registry name,
        implementation qualname, declared spec name) and every
        governance-relevant spec field. Declared schemas appear as
        canonical sha256 hashes, never in clear (F-018 coherence): the
        manifest commits to the schemas without carrying content. Tools
        without a spec expose ``"spec": None``.
        """
        tools: list[dict[str, Any]] = []
        for name in sorted(self._tools):
            tool = self._tools[name]
            spec = getattr(tool, "spec", None)
            spec_entry: dict[str, Any] | None = None
            if isinstance(spec, ToolSpec):
                spec_entry = {
                    "declared_name": spec.name,
                    "input_schema_sha256": _schema_sha256(
                        name, "input", spec.input_schema
                    ),
                    "output_schema_sha256": _schema_sha256(
                        name, "output", spec.output_schema
                    ),
                    "idempotent": spec.idempotent,
                    "retryable": spec.retryable,
                    "side_effectful": spec.side_effectful,
                    "timeout_seconds": spec.timeout_seconds,
                    "max_risk": spec.max_risk,
                    "requires_confirmation": spec.requires_confirmation,
                    "audit_required": spec.audit_required,
                    "reversible": spec.reversible,
                    "provider": spec.provider,
                    "data_egress": spec.data_egress,
                    "data_class": spec.data_class,
                    "required_consent": spec.required_consent,
                }
            tools.append(
                {
                    "name": name,
                    "qualname": type(tool).__qualname__,
                    "spec": spec_entry,
                }
            )
        return {
            "manifest_schema_version": MANIFEST_SCHEMA_VERSION,
            "tools": tools,
        }

    def fingerprint(self) -> str:
        """Deterministic hash of the governance manifest of the surface.

        sha256 of the canonical JSON serialization of :meth:`manifest`.
        Any governance-relevant change (a tool added or replaced, a spec
        flag, a schema, the manifest structure version) changes the
        fingerprint the host has pinned.
        """
        canonical = json.dumps(
            self.manifest(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list(self) -> list[str]:
        return list(self._tools.keys())

    # -------------------------
    # SPEC API
    # -------------------------

    def get_spec(self, name: str) -> ToolSpec | None:
        tool = self.get(name)
        if tool is None:
            return None
        return getattr(tool, "spec", None)

    def list_specs(self) -> dict[str, ToolSpec]:
        specs: dict[str, ToolSpec] = {}

        for name, tool in self._tools.items():
            spec = getattr(tool, "spec", None)
            if spec is not None:
                specs[name] = spec

        return specs
