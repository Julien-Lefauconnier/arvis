# Runtime lifecycle, state and concurrency

Status: contract documentation, current as of `0.1.0a16`. Shared-runtime
enforcement remains backlog (P2). This document closes the documentation side of audit
findings F-022 (unbounded runtime state) and F-023 (implicit concurrency
model) by making the supported usage pattern explicit.

## Concurrency model: one instance per request

`CognitiveOS` and `ArvisEngine` instances are neither thread-safe nor
session-safe. The supported usage pattern is one instance per request
(or per logical turn), discarded afterwards.

- Do not share a live instance across threads.
- Do not interleave `run()` calls from concurrent sessions on the same
  instance.
- Perform replay on a dedicated instance, never on one serving traffic.

Hosts that require a shared long-lived runtime must serialize access
themselves: ARVIS provides no internal locking today, and no guard yet
rejects concurrent reuse.

## Runtime state lifetime

A reused instance accumulates state without bound: processes, control
runtimes, signals, timeline entries and observers are retained for the
life of the instance. There is no TTL, eviction, archival or size limit
mechanism yet. This is compatible with, and is the reason for, the
instance-per-request pattern above.

Sequential reuse of one instance on a single thread is functionally
supported and deliberately exercised by the isolation tests
(`tests/api/test_multi_instance_isolation.py`), which prove that
instances do not leak into each other; that is a proof of isolation,
not a usage recommendation. The recommended pattern remains one
instance per governed turn, and every shipped example follows it,
enforced by `tests/contracts/test_examples_lifecycle.py`.

## Planned hardening (backlog P2)

- Eviction of finished processes.
- TTL for control runtimes.
- Bounded or externalized timeline.
- Identifiers independent of structure sizes.
- A runtime guard rejecting concurrent reuse of a live instance.
- Concurrency and load tests once a shared-runtime mode is designed.


## Effect-path registry scope

The tool confirmation and capability registries use locks for atomic transitions
inside one Python process. They are not distributed registries. A host must not
share one effectful ARVIS instance across workers or processes. The production
doctrine remains one instance per request/turn, with durable intents and
idempotency records persisted by the host. Multi-worker capability consumption
requires a future external transactional registry and is not claimed by
`0.1.0a11`.

## Threaded scientific state (the trajectory contract)

The one-instance-per-turn lifecycle above deliberately leaves cross-turn
continuity to the host. The scientific trajectory follows the same
doctrine (campaign MATH-A, M2): each governed run measures its own turn
through the core model (the contraction monitor by default) and emits a
compact, replayable state for the host to thread.

The wire contract:

- input: `run(..., extra={"scientific_state": <previous state>})`
- output: after the run, `extra["scientific_state_next"]` carries the
  next state (a plain JSON-safe dict; hosts treat it as an opaque blob
  and never import its type)

Properties a host can rely on:

- **First, unthreaded turn is conservative.** Without a previous state
  the monitor has no trajectory: delta-V is zero, the regime starts in
  `warmup`, and the gate's trajectory branch keeps its conservative
  fallback.
- **From the second threaded turn, the trajectory is live**: delta-V,
  hybrid drift, the PAC risk window and the regime estimator advance
  with each threaded state (`turn_index` increments; the risk window
  grows to its configured length).
- **Replayable**: the state round-trips as JSON; threading the same
  states through the same inputs reproduces the same measurements and
  commitments.
- **Dropping the thread is safe**: a lost state degrades to a first
  turn, never to an error and never to a relaxed verdict.

`examples/12_threaded_stability.py` is the runnable form of this
contract; the reference host integration threads the state per user
next to its own conversation continuity.

