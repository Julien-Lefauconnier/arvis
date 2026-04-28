# arvis/linguistic/lexicon/resolvers/lexicon_resolver.py

from arvis.linguistic.lexicon.core.minimal_v0 import (
    build_minimal_lexicon_v0,
)
from arvis.linguistic.lexicon.domains.finance_v0 import (
    build_finance_lexicon_v0,
)
from arvis.linguistic.lexicon.domains.legal_v0 import (
    build_legal_lexicon_v0,
)
from arvis.linguistic.lexicon.domains.security_v0 import (
    build_security_lexicon_v0,
)
from arvis.linguistic.lexicon.lexicon_snapshot import LexiconSnapshot

_DOMAIN_BUILDERS = {
    "finance": build_finance_lexicon_v0,
    "legal": build_legal_lexicon_v0,
    "security": build_security_lexicon_v0,
}


class LexiconResolver:
    """
    Deterministic lexicon resolver.

    - No reasoning
    - No mutation
    - Composition only
    """

    @staticmethod
    def resolve(
        *,
        scope: str = "core",
        domain: str | None = None,
    ) -> LexiconSnapshot:
        core = build_minimal_lexicon_v0()

        # core only
        if scope == "core" or not domain:
            return core

        # domain composition
        builder = _DOMAIN_BUILDERS.get(domain)
        if not builder:
            return core

        domain_lexicon = builder()

        return LexiconSnapshot(
            snapshot_id=f"{core.snapshot_id}+{domain_lexicon.snapshot_id}",
            entries=core.entries + domain_lexicon.entries,
            author="system",
            created_at="composed",
            scope=f"core+domain:{domain}",
        )
