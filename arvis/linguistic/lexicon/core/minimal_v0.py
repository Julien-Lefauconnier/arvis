# arvis/linguistic/lexicon/core/minimal_v0.py

from arvis.linguistic.lexicon.lexicon_entry import LexiconEntry
from arvis.linguistic.lexicon.lexicon_snapshot import LexiconSnapshot


def build_minimal_lexicon_v0() -> LexiconSnapshot:
    """
    Minimal global lexicon for ARVIS linguistic v0.
    """

    entries = [
        # INFORMATION
        LexiconEntry(
            entry_id="info.available",
            canonical_form="Information disponible",
            description="Neutral information exposure",
            status="preferred",
            synonyms=["Donnée connue", "État actuel"],
        ),

        # DECISION
        LexiconEntry(
            entry_id="decision.result",
            canonical_form="Décision",
            description="Explicit decision result",
            status="preferred",
        ),

        # REFUS
        LexiconEntry(
            entry_id="refusal.action",
            canonical_form="Action refusée",
            description="Explicit refusal",
            status="preferred",
        ),

        # ABSTENTION
        LexiconEntry(
            entry_id="abstention.impossible",
            canonical_form="Impossible de trancher",
            description="Explicit abstention",
            status="preferred",
        ),

        # REQUEST_CONFIRMATION
        LexiconEntry(
            entry_id="confirmation.required",
            canonical_form="Validation requise",
            description="Explicit user confirmation request",
            status="preferred",
        ),
    ]

    return LexiconSnapshot(
        snapshot_id="lexicon-v0",
        entries=entries,
        author="system",
        created_at="init",
        scope="global",
    )
