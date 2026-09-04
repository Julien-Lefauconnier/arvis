# arvis/host_api/errors.py

"""The exceptions a host catches.

Two symbols, deliberately. ``ArvisError`` is the root of everything the
kernel raises, so a host can write one honest ``except`` at its
integration boundary instead of catching ``Exception``.
``ArvisSecurityError`` is the one a host must distinguish, because a
security boundary refusing is not a runtime hiccup to retry: it is a
governed refusal to be surfaced and audited.

The full typed error model is much larger (domains, semantics,
severities, per-layer subclasses). It is not re-exported here, because a
host integration surface should pin what hosts actually catch rather
than everything that exists: the internal hierarchy stays free to grow
without expanding a compatibility promise nobody asked for.

Re-export layer only: every symbol is defined where it lives; this
module pins the import path (see VERSIONING.md, host integration
surface).
"""

from arvis.errors.base import ArvisError, ArvisSecurityError

__all__ = [
    "ArvisError",
    "ArvisSecurityError",
]
