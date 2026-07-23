# arvis/stability/stability_observer.py

from typing import Protocol, runtime_checkable

from arvis.cognition.bundle.cognitive_bundle_snapshot import CognitiveBundleSnapshot


@runtime_checkable
class StabilitySnapshot(Protocol):
    """
    Generic snapshot shared by every stability observer.
    Permet fusion multi-horizon et audit scientifique.
    """

    verdict: str


@runtime_checkable
class StabilityObserver(Protocol):
    """
    ARVIS mathematical contract.

    Tous les observers doivent :
    - be deterministic
    - auditables
    - compatibles ZKCS
    """

    def observe(self, bundle: CognitiveBundleSnapshot) -> StabilitySnapshot: ...
