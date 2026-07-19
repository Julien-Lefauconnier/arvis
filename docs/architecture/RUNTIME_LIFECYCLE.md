# Runtime lifecycle, state and concurrency

Status: contract documentation updated for `0.1.0a11`. Shared-runtime
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
