# ARVIS Kernel Adapters

## Status

- Scope: Architecture (Extension Layer)
- Position: Post-IR / Runtime-adjacent (non-cognitive)
- Implementation frontier (2026-08, campaign STRUCT LOT S1): the
  canonical signal factory and the timeline projection are the
  implemented layer. The IR-to-canonical rule engine this document
  used to specify (orchestration entrypoint, mappers, rule system,
  semantic fingerprinting) was never wired into the runtime and has
  been removed from the tree; its specification lives in this file's
  git history and can be revived the day an external signal kernel
  actually consumes it.

---

## 1. Purpose

The kernel adapter layer keeps the boundary between cognition and
external signal systems deterministic. What exists today:

- a **closed-world canonical signal registry**: only registered
  canonical signals can be constructed, unknown signal codes raise;
- a **signal factory** that constructs canonical signals against the
  registry (allowed states, allowed origins, deterministic defaults);
- a **timeline projection** that turns a signal journal into a
  timeline snapshot for observability.

This layer performs no cognition. It projects already computed
outputs into constrained external representations; the IR remains the
source of truth.

---

## 2. Structure

```text
arvis/adapters/kernel/
│
├── __init__.py                # bootstrap: registers canonical signals
│
├── signals/
│   └── signal_factory.py      # registry-validated construction
│
└── timeline_from_signals.py   # SignalJournal -> TimelineSnapshot
```

The canonical signal contract itself (keys, categories, specs,
registry) lives in `arvis/signals/canonical/`.

---

## 3. Bootstrap

Importing `arvis.adapters.kernel` registers the canonical signal
specs exactly once (`bootstrap_kernel_adapters`). The registry is
closed-world after bootstrap: the factory rejects any signal code the
registry does not know.

---

## 4. Signal Factory

`SignalFactory` resolves the spec for a signal code from the registry
and enforces it:

- unknown signal codes MUST raise;
- states and origins are validated against the spec's allowed sets;
- identifiers and timestamps are runtime metadata, generated at
  construction and excluded from any semantic comparison.

Given identical semantic inputs, the factory produces signals whose
semantic payloads are identical; only runtime identity (IDs,
timestamps) may differ.

---

## 5. Timeline Projection

`signal_journal_to_timeline_snapshot` projects a `SignalJournal` into
a `TimelineSnapshot`:

- entries are ordered by a lamport counter derived from journal
  order, never by wall clock;
- a signal without `signal_id` is refused (no anonymous timeline
  entries);
- a missing timestamp falls back to a STABLE epoch value, never to
  "now", so replaying a journal yields the same snapshot.

---

## 6. Design Constraints (for any future extension)

Anything added to this layer MUST:

- stay post-pipeline and read-only with respect to IR;
- be semantically deterministic (runtime metadata excluded);
- comply with the closed-world registry;
- introduce no scoring, prioritization, or interpretation beyond
  explicit rule conditions.

The removed rule-engine specification (in git history) remains the
reference design if an IR-to-canonical mapping layer is ever needed
again; it MUST come back together with a consumer, not ahead of one.
