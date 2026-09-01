# validation/m10/__main__.py
"""Campaign entry point: python -m validation.m10 <command>.

Commands:
  corpus    write the corpus manifest (the published identity of D)
  run       run the full campaign: measurements, metrics, estimator
            outputs and the threshold judgment, as JSON artifacts
  sweep     run the LOT B4 sensitivity sweeps (flip distances plus
            the warm-risk declared_risk variants) into sweeps.json
  run2      run campaign 2 on the D-2.0 state-feedback corpus; its
            artifacts land under artifacts_d2/ (MATH-C LOT C3)
  smoke     run the tiny gate corpus and print the metric summary

Artifacts land under validation/m10/artifacts/ (tracked once a
campaign is published; see M10 section 9).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from validation.m10.corpus import (
    build_corpus,
    build_corpus_d2,
    build_smoke_corpus,
)
from validation.m10.estimators import (
    estimate_alpha,
    estimate_target_map_lipschitz,
    small_gain_verdict,
)
from validation.m10.metrics import compute_all
from validation.m10.runner import TurnMeasurement, run_corpus
from validation.m10.thresholds import (
    PROPOSED,
    PROPOSED_D2,
    REGISTRATION,
    REGISTRATION_D2,
    judge,
)

ARTIFACTS = Path(__file__).parent / "artifacts"
ARTIFACTS_D2 = Path(__file__).parent / "artifacts_d2"


def _observed(ms: list[TurnMeasurement]) -> dict[str, Any]:
    """Metric tree: overall plus per-family."""
    observed: dict[str, Any] = {"overall": compute_all(ms)}
    observed["families"] = {
        family: compute_all([m for m in ms if m.family == family])
        for family in sorted({m.family for m in ms})
    }
    return observed


def _write(name: str, payload: dict[str, Any], root: Path | None = None) -> Path:
    target = root if root is not None else ARTIFACTS
    target.mkdir(parents=True, exist_ok=True)
    path = target / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def cmd_corpus() -> int:
    corpus = build_corpus()
    path = _write("corpus_manifest.json", corpus.manifest())
    print(
        f"corpus {corpus.corpus_version}: {len(corpus.trajectories)} "
        f"trajectories, manifest -> {path}"
    )
    return 0


def cmd_run() -> int:
    corpus = build_corpus()
    print(
        f"running corpus {corpus.corpus_version} "
        f"({len(corpus.trajectories)} trajectories)..."
    )
    ms = run_corpus(corpus)
    observed = _observed(ms)
    alpha = estimate_alpha(ms)
    lipschitz = estimate_target_map_lipschitz()
    constants = small_gain_verdict(alpha, lipschitz)
    judgment = judge(observed)
    _write("corpus_manifest.json", corpus.manifest())
    _write(
        "measurements.json",
        {"turns": [m.to_dict() for m in ms]},
    )
    _write("metrics.json", observed)
    _write(
        "constants.json",
        {
            "alpha": alpha.to_dict(),
            "l_t": lipschitz.to_dict(),
            "small_gain": constants,
        },
    )
    _write("judgment.json", judgment)
    summary = judgment["_summary"]
    print(
        f"turns={len(ms)}  criteria passed={summary['passed']} "
        f"failed={summary['failed']}  registration={REGISTRATION['status']}"
    )
    print(f"artifacts -> {ARTIFACTS}")
    return 0


def cmd_run2() -> int:
    corpus = build_corpus_d2()
    print(
        f"running campaign 2 on {corpus.corpus_version} "
        f"({len(corpus.trajectories)} trajectories)..."
    )
    ms = run_corpus(corpus)
    observed = _observed(ms)
    judgment = judge(observed, PROPOSED_D2, REGISTRATION_D2)
    _write("corpus_manifest.json", corpus.manifest(), ARTIFACTS_D2)
    _write("measurements.json", {"turns": [m.to_dict() for m in ms]}, ARTIFACTS_D2)
    _write("metrics.json", observed, ARTIFACTS_D2)
    _write("judgment.json", judgment, ARTIFACTS_D2)
    summary = judgment["_summary"]
    print(
        f"turns={len(ms)}  criteria passed={summary['passed']} "
        f"failed={summary['failed']}  "
        f"registration={summary['registration']['status']}"
    )
    print(f"artifacts -> {ARTIFACTS_D2}")
    return 0


def cmd_sweep() -> int:
    from validation.m10.sweeps import compute_sweeps

    corpus = build_corpus()
    print(
        f"sweeping corpus {corpus.corpus_version} "
        f"({len(corpus.trajectories)} trajectories)..."
    )
    ms = run_corpus(corpus)
    path = _write("sweeps.json", compute_sweeps(corpus, ms))
    print(f"sweeps -> {path}")
    return 0


def cmd_smoke() -> int:
    corpus = build_smoke_corpus()
    ms = run_corpus(corpus)
    observed = _observed(ms)
    print(json.dumps(observed["overall"], indent=2, sort_keys=True))
    return 0


def main(argv: list[str]) -> int:
    command = argv[0] if argv else "smoke"
    if command == "corpus":
        return cmd_corpus()
    if command == "run":
        return cmd_run()
    if command == "sweep":
        return cmd_sweep()
    if command == "run2":
        return cmd_run2()
    if command == "smoke":
        return cmd_smoke()
    print(__doc__)
    print(f"unknown command: {command}")
    print(f"criteria families: {', '.join(sorted(PROPOSED))}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
