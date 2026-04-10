# arvis/linguistic/lexicon/lexicon_entry.py

"""
Lexicon Entry

Defines the smallest unit of governed linguistic expression.

A LexiconEntry represents a word or expression with an explicit semantic status.
It does not contain logic, rules, or behavior.
"""


class LexiconEntry:
    """
    Atomic linguistic unit.

    A LexiconEntry describes a term or expression and its explicit status
    within a governed lexicon.

    This object is:
    - declarative
    - immutable by default
    - non-contextual unless explicitly scoped

    This object is NOT:
    - a rule
    - a transformation
    - an instruction to a language model
    """

    def __init__(
        self,
        *,
        entry_id: str,
        canonical_form: str,
        description: str,
        status: str,
        synonyms: list[str] | None = None,
        forbidden_equivalents: list[str] | None = None,
    ):
        """
        :param entry_id: Stable identifier of the lexicon entry.
        :param canonical_form: Preferred canonical wording.
        :param description: Human-readable explanation (audit / UI).
        :param status: Linguistic status (e.g. allowed, preferred, forbidden).
        :param synonyms: Optional list of acceptable alternative forms.
        :param forbidden_equivalents: Optional list of explicitly forbidden forms.
        """
        self.entry_id = entry_id
        self.canonical_form = canonical_form
        self.description = description
        self.status = status
        self.synonyms = synonyms or []
        self.forbidden_equivalents = forbidden_equivalents or []
