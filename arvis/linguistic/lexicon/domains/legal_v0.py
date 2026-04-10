# arvis/linguistic/lexicon/domains/legal_v0.py

from arvis.linguistic.lexicon.lexicon_entry import LexiconEntry
from arvis.linguistic.lexicon.lexicon_snapshot import LexiconSnapshot


def build_legal_lexicon_v0() -> LexiconSnapshot:
    return LexiconSnapshot(
        snapshot_id="lexicon-legal-v0",
        entries=[
            LexiconEntry(
                entry_id="legal.contract",
                canonical_form="Contrat",
                description="Legal contract",
                status="preferred",
            ),
            LexiconEntry(
                entry_id="legal.obligation",
                canonical_form="Obligation",
                description="Legal obligation",
                status="preferred",
            ),
        ],
        author="system",
        created_at="init",
        scope="domain:legal",
    )
