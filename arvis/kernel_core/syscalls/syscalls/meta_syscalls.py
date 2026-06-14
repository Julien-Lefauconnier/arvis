# arvis/kernel_core/syscalls/syscalls/meta_syscalls.py

from __future__ import annotations

from typing import Any

from arvis.kernel_core.syscalls.syscall import SyscallResult
from arvis.kernel_core.syscalls.syscall_registry import (
    SyscallDescriptor,
    SyscallEffect,
    all_descriptors,
    register_syscall,
)

# Authored, factual statements about arvis's kernel-level operating frame.
# These are stable structural facts, NOT generated prose: the self-model must
# never confabulate. The governance verdict itself is owned by the cognitive
# layer above the kernel and is therefore described as a mechanism here, not
# claimed as a per-syscall value.
_LIMITATIONS: tuple[str, ...] = (
    "Capabilities are exactly the registered syscalls; arvis cannot perform an "
    "operation that is absent from this list.",
    "Syscalls are the only mechanism for side-effects; everything else is pure "
    "reasoning with no external effect.",
    "The governance verdict (allow / require_confirmation / abstain) is decided "
    "per turn by the cognitive layer above the kernel, not as a static property "
    "of a syscall.",
    "Abstention is the fail-safe outcome when an operation is not authorized.",
    "arvis decides and governs; it does not author the final user-facing text "
    "(ZKCS). Realization is performed by the host product.",
)

_SELF_MODEL_VERSION = "v0"

# Authored, factual description of HOW arvis operates at the kernel level.
# Like _LIMITATIONS these are stable structural facts (not generated prose):
# the self-model explains the mechanism and is explicit about what is NOT
# claimed, so the kernel can describe its own mathematics without
# confabulating.
_ARCHITECTURE_KIND = "governed cognitive kernel"
_ARCHITECTURE_SUMMARY = (
    "arvis decides and governs reasoning under bounded governed signals; it "
    "does not author the final user-facing text (ZKCS, performed by the host)."
)
_MECHANISMS: tuple[tuple[str, str], ...] = (
    (
        "contraction monitor",
        "Tracks a composite Lyapunov energy over bounded governed signals "
        "and its turn-to-turn contraction, so the reasoning state is pulled "
        "toward a stable region rather than drifting.",
    ),
    (
        "stability certificate",
        "Establishes a compact bounded-input/bounded-state invariant and a "
        "bounded adversarial leverage (Lipschitz constant), machine-checked "
        "under adversarial search.",
    ),
    (
        "anytime-valid risk bound",
        "A confidence sequence (no i.i.d. assumption) upper-bounds the "
        "risk-violation rate and stays valid under sequential, open-ended "
        "evaluation rather than only at a single fixed horizon.",
    ),
    (
        "governance gate",
        "Resolves each turn to allow, require-confirmation, or abstain; "
        "abstention is the fail-safe outcome.",
    ),
)
_NOT_CLAIMED: tuple[str, ...] = (
    "This is not a global Lyapunov stability proof; the guarantee is "
    "practical and holds under the certified operating conditions.",
    "The risk bound limits the observed violation rate (a PAC-style "
    "guarantee), not the factual correctness of any individual answer.",
    "The kernel does not verify external truth; grounding and provenance "
    "are the responsibility of the host product.",
)


def _architecture() -> dict[str, Any]:
    return {
        "kind": _ARCHITECTURE_KIND,
        "summary": _ARCHITECTURE_SUMMARY,
        "mechanisms": [
            {"name": name, "summary": summary} for name, summary in _MECHANISMS
        ],
        "not_claimed": list(_NOT_CLAIMED),
    }


def _capability(descriptor: SyscallDescriptor) -> dict[str, Any]:
    return {
        "name": descriptor.name,
        "effect": descriptor.effect.value,
        "triggers_external": descriptor.triggers_external,
        "summary": descriptor.summary,
    }


@register_syscall(
    "arvis.describe_self",
    effect=SyscallEffect.READ,
    summary="Return arvis's self-model: registered capabilities and limits.",
)
def describe_self(handler: Any, **_: Any) -> SyscallResult:
    """Return a self-model derived from the living syscall registry.

    The capability list IS the registry (single machine-truth), so the
    self-description can never claim a capability arvis does not have.
    """
    capabilities = [_capability(d) for d in all_descriptors()]
    self_model: dict[str, Any] = {
        "version": _SELF_MODEL_VERSION,
        "kind": "arvis.self_model",
        "capability_count": len(capabilities),
        "capabilities": capabilities,
        "limitations": list(_LIMITATIONS),
        "architecture": _architecture(),
    }
    return SyscallResult(success=True, result=self_model)
