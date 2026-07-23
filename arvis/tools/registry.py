# arvis/tools/registry.py


import dataclasses
import hashlib
import json
from typing import Any, cast

from arvis.errors.base import ArvisSecurityError
from arvis.tools.base import BaseTool
from arvis.tools.spec import ToolSpec

# Version of the manifest structure, embedded in the fingerprint: a
# change in what the manifest covers is a change in what the host has
# pinned, and must be visible as a fingerprint change.
MANIFEST_SCHEMA_VERSION = 1


def _canonical_schema_bytes(
    name: str, which: str, schema: dict[str, Any]
) -> bytes | None:
    """Canonical JSON bytes of a declared tool schema, or None if empty.

    The canonical form is the same one the manifest has always hashed
    (sorted keys, compact separators, ASCII), so fingerprints of a sane
    surface are unchanged. A schema that cannot be canonicalized cannot
    be committed to: pinning an unpinnable surface is refused (F-018
    coherence). Non-finite floats are refused for the same reason: they
    do not round-trip injectively.
    """
    if not schema:
        return None
    try:
        canonical = json.dumps(
            schema,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ArvisSecurityError(
            f"tool {name!r} declares a non-canonicalizable {which} schema; "
            "the registry surface cannot be pinned",
            details={"tool": name, "schema": which},
        ) from exc
    return canonical.encode("utf-8")


def _sha256_or_none(payload: bytes | None) -> str | None:
    if payload is None:
        return None
    return hashlib.sha256(payload).hexdigest()


@dataclasses.dataclass(frozen=True, slots=True)
class _CapturedSpec:
    """Registration-time capture of a tool's governed surface.

    ``spec`` is a private sanitized copy: its schemas are rebuilt from
    the canonical bytes below, so the captured surface shares no
    reference with the caller's objects and later mutation of those
    objects cannot reach the registry. The private copy is never handed
    out: public readers receive defensive copies (:meth:`ToolRegistry.get_spec`,
    :meth:`ToolRegistry.list_specs`), the governed effect path goes
    through :meth:`ToolRegistry.verified_spec`.
    """

    spec: ToolSpec | None
    input_bytes: bytes | None
    output_bytes: bytes | None


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, BaseTool] = {}
        self._captured: dict[str, _CapturedSpec] = {}
        self._frozen: bool = False
        self._frozen_manifest_bytes: bytes | None = None
        self._frozen_fingerprint: str | None = None

    def register(self, tool: BaseTool, *, replace: bool = False) -> None:
        """Register a tool under its declared name.

        F-004: a governed registry is never mutated silently. A
        frozen registry refuses any registration, and re-registering
        an existing name requires an explicit replace=True.

        The tool's declared spec is captured here, once: schemas are
        canonicalized and the private copy is rebuilt from those bytes.
        Registration is atomic; if the capture is refused, nothing is
        registered (and an explicit replacement leaves the previous
        registration in place).
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
        captured = self._capture(name, tool)
        self._tools[name] = tool
        self._captured[name] = captured

    def _capture(self, name: str, tool: BaseTool) -> _CapturedSpec:
        """Build the private, sanitized capture of a tool's spec."""
        raw = getattr(tool, "spec", None)
        if raw is None:
            return _CapturedSpec(spec=None, input_bytes=None, output_bytes=None)
        if not isinstance(raw, ToolSpec):
            raise ArvisSecurityError(
                f"tool {name!r} declares a spec that is not a ToolSpec; "
                "the registry surface cannot be pinned",
                details={"tool": name, "spec_type": type(raw).__name__},
            )
        input_bytes = _canonical_schema_bytes(name, "input", raw.input_schema)
        output_bytes = _canonical_schema_bytes(name, "output", raw.output_schema)
        private = dataclasses.replace(
            raw,
            input_schema=_schema_from_bytes(input_bytes),
            output_schema=_schema_from_bytes(output_bytes),
        )
        return _CapturedSpec(
            spec=private,
            input_bytes=input_bytes,
            output_bytes=output_bytes,
        )

    def freeze(self) -> str:
        """Freeze the registry after bootstrap.

        The manifest is snapshotted here, as canonical bytes, and the
        fingerprint is computed from that snapshot exactly once; neither
        is ever recomputed from live objects afterwards. Freezing an
        already frozen registry is idempotent and returns the pinned
        fingerprint. Returns the registry fingerprint so the host can
        pin and audit the frozen tool surface.
        """
        if self._frozen:
            pinned = self._frozen_fingerprint
            if pinned is None:
                raise ArvisSecurityError(
                    "tool registry is frozen but carries no pinned fingerprint"
                )
            return pinned
        manifest_bytes = self._canonical_manifest_bytes()
        self._frozen_manifest_bytes = manifest_bytes
        self._frozen_fingerprint = hashlib.sha256(manifest_bytes).hexdigest()
        self._frozen = True
        return self._frozen_fingerprint

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

        Once frozen, the manifest is decoded from the frozen snapshot
        bytes: every call returns a fresh document, and mutating a
        returned document cannot reach the pinned surface.
        """
        if self._frozen and self._frozen_manifest_bytes is not None:
            return cast(dict[str, Any], json.loads(self._frozen_manifest_bytes))
        return self._build_manifest()

    def _build_manifest(self) -> dict[str, Any]:
        """Manifest built from the registration-time captures only."""
        tools: list[dict[str, Any]] = []
        for name in sorted(self._tools):
            tool = self._tools[name]
            captured = self._captured[name]
            spec = captured.spec
            spec_entry: dict[str, Any] | None = None
            if spec is not None:
                spec_entry = {
                    "declared_name": spec.name,
                    "input_schema_sha256": _sha256_or_none(captured.input_bytes),
                    "output_schema_sha256": _sha256_or_none(captured.output_bytes),
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

    def _canonical_manifest_bytes(self) -> bytes:
        canonical = json.dumps(
            self._build_manifest(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
        return canonical.encode("utf-8")

    def fingerprint(self) -> str:
        """Deterministic hash of the governance manifest of the surface.

        sha256 of the canonical JSON serialization of :meth:`manifest`.
        Any governance-relevant change (a tool added or replaced, a spec
        flag, a schema, the manifest structure version) changes the
        fingerprint the host has pinned. Once frozen, the pinned
        fingerprint is returned as-is and never recomputed.
        """
        if self._frozen and self._frozen_fingerprint is not None:
            return self._frozen_fingerprint
        return hashlib.sha256(self._canonical_manifest_bytes()).hexdigest()

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def list(self) -> list[str]:
        return list(self._tools.keys())

    # -------------------------
    # SPEC API
    # -------------------------

    def get_spec(self, name: str) -> ToolSpec | None:
        """Defensive copy of the captured spec, for inspection.

        Mutating the returned spec's schemas cannot reach the registry:
        every call rebuilds them from the canonical bytes captured at
        registration.
        """
        captured = self._captured.get(name)
        if captured is None or captured.spec is None:
            return None
        return _defensive_spec_copy(captured)

    def list_specs(self) -> dict[str, ToolSpec]:
        """Defensive copies of every captured spec, for inspection."""
        specs: dict[str, ToolSpec] = {}
        for name, captured in self._captured.items():
            if captured.spec is not None:
                specs[name] = _defensive_spec_copy(captured)
        return specs

    def verified_spec(self, name: str) -> ToolSpec | None:
        """Spec for the governed effect path, integrity-checked when frozen.

        Authorization and dispatch read the tool surface through this
        method, never through the live tool object. Once the registry is
        frozen, the private capture is re-canonicalized and compared to
        the bytes pinned at registration; any divergence (an internal
        mutation of the captured surface) refuses the read fail-closed
        instead of validating against a surface the host never pinned.
        """
        captured = self._captured.get(name)
        if captured is None or captured.spec is None:
            return None
        if self._frozen:
            self._verify_captured_integrity(name, captured)
        return captured.spec

    def _verify_captured_integrity(self, name: str, captured: _CapturedSpec) -> None:
        spec = captured.spec
        if spec is None:
            return
        current_input = _canonical_schema_bytes(name, "input", spec.input_schema)
        if current_input != captured.input_bytes:
            raise ArvisSecurityError(
                f"tool {name!r} input schema diverged from the frozen "
                "surface; refusing the governed read",
                details={"tool": name, "schema": "input"},
            )
        current_output = _canonical_schema_bytes(name, "output", spec.output_schema)
        if current_output != captured.output_bytes:
            raise ArvisSecurityError(
                f"tool {name!r} output schema diverged from the frozen "
                "surface; refusing the governed read",
                details={"tool": name, "schema": "output"},
            )


def _schema_from_bytes(payload: bytes | None) -> dict[str, Any]:
    if payload is None:
        return {}
    return cast(dict[str, Any], json.loads(payload))


def _defensive_spec_copy(captured: _CapturedSpec) -> ToolSpec:
    spec = captured.spec
    if spec is None:  # pragma: no cover - callers check before
        raise ArvisSecurityError("cannot copy an absent tool spec")
    return dataclasses.replace(
        spec,
        input_schema=_schema_from_bytes(captured.input_bytes),
        output_schema=_schema_from_bytes(captured.output_bytes),
    )
