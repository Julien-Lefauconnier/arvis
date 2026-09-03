#!/usr/bin/env python3
# scripts/bench_turn.py
"""Measure what one governed turn costs on THIS machine.

Campaign ONBOARD (audit #3 P1, 2026-09-03). The documented lifecycle
is one engine per governed turn, so the number an integrator needs
for capacity planning is the full construct-and-run cycle, not a hot
loop on a reused instance. This script measures both, plus the
threaded variant and resident memory, and prints the table
docs/PERFORMANCE.md publishes. Run it yourself; the published
numbers are indicative, yours are the truth for your hardware:

    python scripts/bench_turn.py
"""

from __future__ import annotations

import platform
import resource
import statistics
import sys
import time

from arvis import ArvisEngine

WARMUP = 10
ROUNDS = 100


def _rss_mib() -> float:
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is KiB on Linux, bytes on macOS.
    divisor = 1024 if sys.platform != "darwin" else 1024 * 1024
    return usage / divisor


def _timed(fn) -> list[float]:
    for _ in range(WARMUP):
        fn()
    samples: list[float] = []
    for _ in range(ROUNDS):
        start = time.perf_counter()
        fn()
        samples.append((time.perf_counter() - start) * 1000.0)
    return samples


def _row(label: str, samples: list[float]) -> str:
    quantiles = statistics.quantiles(samples, n=20)
    return f"| {label} | {statistics.median(samples):8.2f} | {quantiles[18]:8.2f} |"


def main() -> None:
    rss_before = _rss_mib()

    construct = _timed(lambda: ArvisEngine())

    def full_cycle() -> None:
        ArvisEngine().run("bench", {"risk": 0.10})

    cycle = _timed(full_cycle)

    state: dict | None = None

    def threaded_cycle() -> None:
        nonlocal state
        extra = {"scientific_state": state} if state is not None else {}
        state = (
            ArvisEngine()
            .run("bench", {"risk": 0.10}, extra=extra)
            .next_scientific_state
        )

    threaded = _timed(threaded_cycle)

    engine = ArvisEngine()
    reused = _timed(lambda: engine.run("bench", {"risk": 0.10}))

    rss_after = _rss_mib()

    print(
        f"python {platform.python_version()} on {platform.machine()} "
        f"{platform.system().lower()}; {WARMUP} warmup, {ROUNDS} rounds"
    )
    print()
    print("| Measure | median ms | p95 ms |")
    print("| --- | --- | --- |")
    print(_row("engine construction alone", construct))
    print(_row("full turn (construct + run, the documented lifecycle)", cycle))
    print(_row("full threaded turn (scientific state passed back)", threaded))
    print(_row("run on a reused instance (NOT the documented lifecycle)", reused))
    print()
    print(
        f"resident memory: {rss_before:.0f} MiB before, {rss_after:.0f} MiB "
        f"after {3 * (WARMUP + ROUNDS)} turns (max RSS)"
    )
    print()
    print("Reminder: a reused instance accumulates state by design and is")
    print("measured here only to show the construction share; production")
    print("hosting is one engine per turn (examples/09_multi_engine_hosting.py).")


if __name__ == "__main__":
    main()
