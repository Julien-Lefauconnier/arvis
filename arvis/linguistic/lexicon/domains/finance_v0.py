# arvis/linguistic/lexicon/domains/finance_v0.py

from arvis.linguistic.lexicon.lexicon_entry import LexiconEntry
from arvis.linguistic.lexicon.lexicon_snapshot import LexiconSnapshot


def build_finance_lexicon_v0() -> LexiconSnapshot:
    return LexiconSnapshot(
        snapshot_id="lexicon-finance-v0",
        entries=[
            LexiconEntry(
                entry_id="finance.balance",
                canonical_form="Solde",
                description="Account balance",
                status="preferred",
            ),
            LexiconEntry(
                entry_id="finance.transaction",
                canonical_form="Transaction",
                description="Financial transaction",
                status="preferred",
            ),
        ],
        author="system",
        created_at="init",
        scope="domain:finance",
    )
