# validation/m10/__init__.py
"""M10 empirical stability validation: corpus, harness, metrics.

Implements the protocol of docs/math/M10 on the closed loop of
M10 section 3.1 (projection -> composite Lyapunov -> adaptive kappa ->
gate -> final verdict -> control), driven at the pipeline level so the
observation channels the projection certifies are under corpus
control, with the scientific state and the slow/symbolic states
threaded across governed turns.

The corpus is synthetic and deterministic by construction (published
seeds, bit-for-bit regenerable). Executed on it, the campaign
validates the MECHANISM under the protocol's families of trajectories;
it does not and cannot validate behavior on real production traffic,
which stays outside this package's claims.
"""

from validation.m10.corpus import CorpusSpec, TrajectorySpec, build_corpus
from validation.m10.runner import TurnMeasurement, run_corpus, run_trajectory

__all__ = [
    "CorpusSpec",
    "TrajectorySpec",
    "TurnMeasurement",
    "build_corpus",
    "run_corpus",
    "run_trajectory",
]
