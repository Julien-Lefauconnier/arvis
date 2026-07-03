# arvis/adapters/tools/gates.py

from typing import Protocol

from arvis.adapters.tools.invocation import ToolInvocation
from arvis.tools.spec import ToolSpec


class ConsentGate(Protocol):
    """Host-provided gate answering whether a purpose-scoped consent is granted
    for a tool invocation.

    ARVIS calls it when a tool's spec declares a ``required_consent``; the host
    maps the opaque consent key onto its own consent system. The invocation
    carries the runtime ``context`` from which the host resolves the acting
    principal.
    """

    def is_granted(self, invocation: ToolInvocation, consent_key: str) -> bool: ...


class EgressGate(Protocol):
    """Host-provided gate answering whether a data-egress tool may run for a
    given invocation.

    ARVIS calls it when a tool's spec declares ``data_egress``; the host
    enforces its own per-workspace egress policy (for example, refusing to send
    a confidential data class outbound).
    """

    def is_allowed(self, invocation: ToolInvocation, spec: ToolSpec) -> bool: ...
