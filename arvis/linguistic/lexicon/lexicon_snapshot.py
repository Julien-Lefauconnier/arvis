# arvis/linguistic/lexicon/lexicon_snapshot.py

from arvis.linguistic.lexicon.lexicon_entry import LexiconEntry

"""
Lexicon Snapshot

Immutable representation of a lexicon at a specific point in time.
"""


class LexiconSnapshot:
    """
    Immutable snapshot of a governed lexicon.

    A LexiconSnapshot represents a frozen, auditable state of a lexicon.
    It is the only form of lexicon that may be consumed at runtime.

    Properties:
    - versioned
    - traceable
    - serializable
    - immutable

    The runtime MUST NEVER operate on a mutable lexicon structure.
    """

    def __init__(
        self,
        *,
        snapshot_id: str,
        entries: list[LexiconEntry],
        author: str,
        created_at: str,
        scope: str,
    ):
        """
        :param snapshot_id: Unique identifier of the snapshot.
        :param entries: List of LexiconEntry objects.
        :param author: Human authority responsible for this snapshot.
        :param created_at: Creation timestamp.
        :param scope: Applicability scope (global, domain, user).
        """
        self.snapshot_id = snapshot_id
        self.entries = entries
        self.author = author
        self.created_at = created_at
        self.scope = scope
