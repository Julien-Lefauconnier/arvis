# arvis/uncertainty/uncertainty_frame.py

from dataclasses import dataclass
from typing import Set

from arvis.uncertainty.uncertainty_axis import UncertaintyAxis


@dataclass(frozen=True)
class UncertaintyFrame:
    """
    Declarative uncertainty frame.

    A frame groups uncertainty axes to describe
    a zone of cognitive prudence.

    ⚠️ No decision
    ⚠️ No execution
    ⚠️ No inference
    """

    frame_id: str
    label: str
    description: str
    axes: Set[UncertaintyAxis]
