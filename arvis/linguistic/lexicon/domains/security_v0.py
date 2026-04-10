# arvis/linguistic/lexicon/domains/security_v0.py

from arvis.linguistic.lexicon.lexicon_entry import LexiconEntry
from arvis.linguistic.lexicon.lexicon_snapshot import LexiconSnapshot


def build_security_lexicon_v0() -> LexiconSnapshot:
    """
    Security domain lexicon v0.

    Declarative only.
    No reasoning.
    No execution semantics.
    """

    return LexiconSnapshot(
        snapshot_id="lexicon-security-v0",
        entries=[
            LexiconEntry(
                entry_id="security.access_control",
                canonical_form="Contrôle d’accès",
                description="Access control mechanism",
                status="preferred",
            ),
            LexiconEntry(
                entry_id="security.incident",
                canonical_form="Incident de sécurité",
                description="Security incident",
                status="preferred",
            ),
            LexiconEntry(
                entry_id="security.risk",
                canonical_form="Risque",
                description="Identified security risk",
                status="preferred",
            ),
        ],
        author="system",
        created_at="init",
        scope="domain:security",
    )
