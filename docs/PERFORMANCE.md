# What a governed turn costs

The documented lifecycle is one engine per governed turn, and the
first capacity question every integrator asks is what that costs.
This page publishes indicative numbers and, more importantly, the
script that produces them on your hardware, which is the only
measurement that matters:

```bash
python scripts/bench_turn.py
```

## Indicative numbers

Measured with `scripts/bench_turn.py` (10 warmup rounds, 100 timed
rounds, explicit-risk payload) on a small 2-vCPU x86-64 Linux
container (Intel Xeon @ 2.80GHz), CPython 3.11, arvis 0.1.0b8.dev0,
2026-09-03. Indicative only; regenerate on your target hardware.

| Measure | median ms | p95 ms |
| --- | --- | --- |
| engine construction alone | 0.15 | 0.25 |
| full turn (construct + run, the documented lifecycle) | 6.42 | 8.38 |
| full threaded turn (scientific state passed back) | 6.23 | 7.60 |
| run on a reused instance (NOT the documented lifecycle) | 6.12 | 7.51 |

Resident memory on that machine: 57 MiB before the benchmark, 67 MiB
after 330 governed turns (max RSS of the whole process, interpreter
included).

## How to read this

The number that surprises people: **construction is a rounding
error.** Building a fresh engine costs about 0.15 ms against a ~6 ms
turn, so the one-engine-per-turn lifecycle costs roughly 5 percent
over reusing an instance, and reuse is not the documented lifecycle
anyway (a reused instance accumulates measurement state by design;
`examples/09_multi_engine_hosting.py` shows the per-turn factory
pattern for concurrent hosts). There is no pool to manage and
nothing to warm up.

The turn itself is milliseconds, not microseconds: a full governed
turn runs the whole pipeline (projection, gate stack, commitment
composition, IR export). Against a model call measured in hundreds
of milliseconds to seconds, governance adds well under one percent
of end-to-end latency; in front of a sub-millisecond local function,
it is material and you should measure against your budget.

No optimization is claimed. These are the costs of the current tree,
published so integrators can plan instead of guessing; if a future
campaign changes them materially, this page and its script are the
record.
