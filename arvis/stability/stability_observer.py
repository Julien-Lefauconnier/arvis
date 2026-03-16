# arvis/stability/stability_observer.py

from typing import Protocol, runtime_checkable
from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot


@runtime_checkable
class StabilitySnapshot(Protocol):
    """
    Snapshot générique pour tous les observers de stabilité.
    Permet fusion multi-horizon et audit scientifique.
    """
    verdict: str


@runtime_checkable
class StabilityObserver(Protocol):
    """
    Contrat mathématique ARVIS.

    Tous les observers doivent :
    - être déterministes
    - auditables
    - compatibles ZKCS
    """

    def observe(self, bundle: CognitiveBundleSnapshot) -> StabilitySnapshot:
        ...