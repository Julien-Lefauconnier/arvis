# arvis/uncertainty/uncertainty_axis.py

from enum import Enum


class UncertaintyAxis(str, Enum):
    """
    Declarative dimensions of uncertainty.

    An axis describes *why* a situation is fragile,
    not *what to do about it*.
    """

    CONTEXT_DEPENDENT = "context_dependent"
    IRREVERSIBLE_RISK = "irreversible_risk"
    HIGH_IMPACT = "high_impact"
    AMBIGUOUS_REFERENCE = "ambiguous_reference"
    USER_SENSITIVE = "user_sensitive"
    DOMAIN_SPECIFIC = "domain_specific"
