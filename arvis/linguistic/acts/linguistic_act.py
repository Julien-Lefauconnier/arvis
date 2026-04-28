# arvis/linguistic/acts/linguistic_act.py

from arvis.linguistic.acts.act_types import LinguisticActType

"""
Linguistic Act

Defines the intention of expression for ARVIS.
"""


class LinguisticAct:
    """
    Declarative representation of an ARVIS linguistic act.

    A LinguisticAct specifies *what kind of speech* is being produced,
    independently of the actual wording.

    This object:
    - does not generate text
    - does not contain logic
    - does not depend on any LLM provider
    """

    def __init__(self, act_type: LinguisticActType):
        """
        :param act_type: One of the predefined linguistic act types.
        :param description: Human-readable explanation of the act intent.
        """
        self.act_type = act_type

    def __repr__(self) -> str:
        return f"LinguisticAct(type={self.act_type})"
