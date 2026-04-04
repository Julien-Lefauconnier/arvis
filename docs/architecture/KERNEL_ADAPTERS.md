# ARVIS Kernel Adapters

## Status
- Scope: Architecture (Extension Layer)
- Type: Semantically Deterministic Interoperability Layer
- Position: Post-IR / Runtime-adjacent (non-cognitive)

---

## 1. Purpose

The Kernel Adapter Layer enables **deterministic interoperability** between ARVIS and external systems based on **canonical signals** (e.g. Veramem Kernel).

It provides a structured way to:

- project CognitiveIR into external signal systems
- apply rule-based transformations
- maintain determinism and replayability
- preserve separation between cognition and execution

IMPORTANT:

This layer performs a **lossy projection** from IR to canonical signals.

This means:

- not all IR information is preserved
- signals are a constrained representation
- the IR remains the source of truth

---

## 2. Core Principle

> The Kernel Adapter Layer does NOT perform cognition.  
> It translates already computed cognitive outputs into external representations.

This layer is:

- post-pipeline
- post-IR
- read-only with respect to IR
- semantically deterministic (excluding runtime metadata)

---

## 3. Architectural Position

```text
Cognitive Pipeline (pure)
    ↓
CognitiveState (canonical)
    ↓
CognitiveIR (external contract)
    ↓
Kernel Adapter Layer (THIS)
    ↓
Canonical Signals (external systems)
```

---

## 4. Design Constraints

The Kernel Adapter Layer MUST:

- be semantically deterministic (excluding runtime metadata)
- be replay-safe
- not mutate IR
- not influence decision semantics
- not introduce hidden logic
- comply with a **closed-world signal registry**

This means:

- only registered canonical signals may be emitted
- unknown signal codes MUST raise an error

The Kernel Adapter Layer MUST NOT:

- access runtime side-effects
- depend on external system state
- modify cognitive outputs
- perform scoring, weighting, or prioritization
- resolve conflicts between signals
- introduce interpretation beyond rule conditions

Signals are runtime artifacts and MUST NOT be considered canonical representations.
They are projections of canonical IR-derived structures enriched with runtime metadata.

### 4.1 Semantic Determinism 

Given identical IR input:

- the same canonical signal types MUST be emitted
- the same semantic payload MUST be produced
- the same signal ordering MUST be preserved

This guarantees:

 > identical IR → identical semantic signals

#### Runtime Metadata (NON-DETERMINISTIC)

The following fields are explicitly **excluded from determinism guarantees**:

- signal_id (UUID)
- event_id (UUID)
- timestamps (event creation, signal emission)

These fields:

- are generated at runtime
- are not part of the semantic contract
- MUST NOT affect replay validation
 
#### Replay Model

Replay compatibility is defined as:

 > semantic equivalence of emitted signals, independent of runtime metadata

Implementations MUST:

- ignore runtime-generated identifiers during replay comparison
- rely on semantic fingerprints derived from signal payloads

#### Rationale

The Kernel Adapter Layer bridges:

- a deterministic IR system
- an external signal system requiring runtime identity and time anchoring

Therefore:

- semantic structure MUST remain deterministic
- runtime identity MAY remain non-deterministic

---

### 4.2 Semantic Fingerprinting

To enforce semantic determinism, the Kernel Adapter Layer defines
a **semantic fingerprinting mechanism** for signals.

#### Definition

A semantic fingerprint is a deterministic representation of a signal,
excluding all runtime-generated metadata.

Formally:

```text
fingerprint(signal) = (origin, signal_type, normalized_payload)
```

Where:
- `origin` is the signal source (default: "unknown")
- `signal_type` is derived from the canonical payload
- `normalized_payload` is a reduced, deterministic projection

#### Excluded Fields

The following fields MUST be excluded from the fingerprint:

- signal_id
- event_id
- timestamps

These fields are considered **runtime identity**, not semantics.

#### Normalization Rules

Payload normalization MUST:

- extract only deterministic semantic fields
- ignore runtime-generated identifiers
- produce a stable, hashable structure

Example:

```python
(
    payload.get("state"),
    payload.get("subject_ref"),
    payload.get("temporal_anchor"),
)
```

#### Guarantees

The system MUST guarantee:

```text
identical IR → identical semantic fingerprints
```

Even if:

- signal IDs differ
- timestamps differ

#### Compliance Requirement

Implementations MUST:

- provide a semantic fingerprinting mechanism
- use it for replay validation
- ensure testable equivalence of signals across executions

### Reference Implementation

See:

- `SignalSemantics.fingerprint`
- `tests/adapters/kernel/test_signal_semantics.py`

---

## 5. Structure

```text
arvis/adapters/kernel/
│
├── kernel_adapter.py          # orchestration entrypoint
├── canonical_to_event.py      # canonical → event mapping
├── event_to_signal.py         # event → signal mapping
│
├── mappers/
│   └── ir_to_canonical.py     # IR → canonical signals
│
├── rules/
│   ├── base_rule.py
│   ├── state_rules.py
│   ├── decision_rules.py
│   ├── gate_rules.py
│   └── fallback_rules.py
│
└── signals/
    └── signal_factory.py
```

## 6. IR → Canonical Signal Mapping

### 6.1 Principle

The mapping is:

- explicit
- rule-based
- deterministic

```text
CognitiveIR → Rule Engine → CanonicalSignals
```

---

### 6.2 Mapping Domains

| IR Component | Signal Domain                      |
| ------------ | ---------------------------------- |
| state        | stability / risk signals           |
| decision     | cognition / conflict / uncertainty |
| gate         | control / validation / instability |

---

### 6.3 Example

```python
if state.stable is False:
    emit("early_warning_detected")

if decision.conflicts:
    emit("conflict_detected")

if gate.instability_score > 0.7:
    emit("instability_detected")
```

---

## 7. Rule System

### 7.1 Philosophy

The rule system defines how IR is interpreted as signals.

It is:

- declarative
- modular
- composable
- deterministic

--

### 7.2 Rule Engine Execution Model

Rules are executed in a fixed deterministic order:

```text
state_rules → decision_rules → gate_rules → fallback_rules
```

Execution guarantees:

- each rule is independent
- no shared mutable state
- idempotent execution
- no ordering ambiguity

The engine MUST guarantee:

- same IR → same emitted signals (set + order)

---

### 7.3 Rule Types

| Rule Type      | Responsibility                   |
| -------------- | -------------------------------- |
| state_rules    | stability interpretation         |
| decision_rules | cognitive interpretation         |
| gate_rules     | control / verdict interpretation |
| fallback_rules | default emission behavior        |

---

### 7.4 Rule Contract

Each rule:

- receives (ir, emit)
- may emit signals
- must be side-effect free

```python
def rule(ir, emit):
    if condition:
        emit("signal_code")
```

---

## 8. Signal Factory

### 8.1 Purpose

The SignalFactory ensures:

- canonical signal construction
- registry validation
- deterministic defaults

---

### 8.2 Responsibilities

- resolve signal spec from registry
- enforce allowed states
- enforce allowed origins
- generate canonical identifiers

---

### 8.3 Properties

- no randomness except UUID (non-semantic)
- registry-driven
- invariant-safe

The factory MUST:

- reject unknown signal codes
- enforce registry constraints strictly

---

## 9. Determinism & Replay

The adapter layer MUST preserve:

- identical IR → identical signals (ordering + content)
- no dependency on runtime state
- no hidden randomness

Signal IDs MAY vary (UUID), but:

- semantic identity MUST remain identical

---

## 10. Compliance Alignment

The Kernel Adapter Layer MUST comply with:

- IR determinism requirements
- timeline invariants
- signal registry constraints
- replay determinism

It MUST NOT violate:

- Gate semantics
- decision constraints
- validity envelope logic

---

## 11. Relationship with External Systems

The adapter enables integration with systems such as:

- Veramem Kernel
- signal-based monitoring systems
- observability pipelines
- audit / certification layers

---

## 12. Key Insight

The Kernel Adapter Layer turns ARVIS into a signal-emitting cognitive system.

However:

The IR remains the **canonical and complete representation** of cognition.

Canonical signals are:

- a projection
- a constrained external representation
- not suitable for full reconstruction of cognition

It enables:

- modular interoperability
- external reasoning systems
- decoupled architecture evolution

---

## 13. Future Extensions

Potential evolutions:

- rule registry (dynamic loading)
- versioned mapping strategies
- multi-kernel support
- bidirectional adapters (signal → IR)
- streaming signal pipelines

---

## 14. Non-Goals

This layer does NOT:

- modify cognition
- replace IR
- define decision logic
- perform execution

---

## 15. Summary

The Kernel Adapter Layer is:

- a deterministic projection layer
- a rule-based mapping system
- a bridge between ARVIS and external signal ecosystems

It preserves:

- stability guarantees
- determinism
- auditability

while enabling:

- extensibility
- interoperability
- system composability