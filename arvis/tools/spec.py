# arvis/tools/spec.py

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str

    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)

    idempotent: bool = False
    retryable: bool = True
    side_effectful: bool = True
    timeout_seconds: float | None = None

    # -----------------------------
    # GOVERNANCE
    # -----------------------------
    # max_risk and requires_confirmation are enforced by ToolPolicyEvaluator.
    # audit_required is declarative: tool.execute journals an ExecutionArtifact
    # unconditionally, so it flags a tool whose execution must never go
    # unrecorded. reversible marks whether the effect can be undone, so a host
    # can demand extra scrutiny (or confirmation) for irreversible actions.

    max_risk: float = 1.0
    requires_confirmation: bool = False
    audit_required: bool = False
    reversible: bool = True

    # -----------------------------
    # CAPABILITY MANIFEST
    # -----------------------------
    # Declarative description of where a tool's data goes and what gates its
    # execution, so a host can govern sovereignty, egress and consent uniformly
    # across local and external (e.g. MCP) tools. ARVIS does not interpret the
    # opaque labels below (provider, data_class, required_consent); the host maps
    # them onto its own consent system, data taxonomy and egress policy.

    # Identity of the third-party service the tool talks to (e.g. "google",
    # "notion"), or None for a purely local tool with no external party.
    provider: str | None = None

    # Whether executing this tool sends the caller's data outbound to the
    # provider (a write/publish), as opposed to a read-only inbound fetch.
    data_egress: bool = False

    # Sensitivity class of the data the tool handles, from a host-defined
    # taxonomy (e.g. "public", "personal", "confidential"). Opaque to ARVIS.
    data_class: str = "unspecified"

    # Opaque consent key the host must have granted for this tool to run, or
    # None when the tool needs no purpose-scoped consent.
    required_consent: str | None = None

    @property
    def crosses_trust_boundary(self) -> bool:
        """Whether executing this tool involves a third party (a provider),
        so it is not a purely local, in-boundary execution. A host reads this
        to separate sovereign tools (no provider) from connected ones."""
        return self.provider is not None
