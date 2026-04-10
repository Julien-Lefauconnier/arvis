# arvis/linguistic/lexicon/registry/lexicon_registry.py

"""
Lexicon Registry

Declarative access point to available lexicon snapshots.
"""


class LexiconRegistry:
    """
    Read-only registry of available lexicon snapshots.

    The registry:
    - declares what lexicons exist
    - exposes them by identifier or scope

    The registry does NOT:
    - resolve conflicts
    - merge lexicons
    - decide applicability
    """

    def __init__(self, *, snapshots: dict[str, object]):
        """
        :param snapshots: Mapping of snapshot_id to LexiconSnapshot.
        """
        self.snapshots = snapshots
