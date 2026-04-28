# arvis/reflexive/architecture/arvis_system_architecture.py

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemLayer:
    name: str
    description: str
    modules: list[str]


class ArvisSystemArchitecture:
    @staticmethod
    def layers() -> list[SystemLayer]:
        return [
            SystemLayer(
                name="cognition",
                description="Reasoning and uncertainty analysis",
                modules=[
                    "context analysis",
                    "gap detection",
                    "uncertainty exposure",
                    "decision proposals",
                ],
            ),
            SystemLayer(
                name="reflexive",
                description="System self-observation and explanation",
                modules=[
                    "reflexive snapshot",
                    "attestation",
                    "timeline exposure",
                ],
            ),
            SystemLayer(
                name="governance",
                description="Constraints and safety guarantees",
                modules=[
                    "human authority",
                    "no autonomous execution",
                    "explicit uncertainty",
                ],
            ),
        ]
