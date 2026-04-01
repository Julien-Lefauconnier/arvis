# ARVIS Public Objects Registry v1 (Draft)

## Status
- Version: v1 (Draft)
- Scope: Normative (Core)
- Component: ARVIS Core / Standard Interface

---

## 1. Purpose

The ARVIS Public Objects Registry defines the **canonical set of public data structures** exposed by the system.

These objects form the **external contract** of ARVIS and are used for:
- interoperability between implementations,
- audit and replay,
- compliance verification,
- certification processes.

Any object not listed here MUST be considered **internal** and non-normative.

---

## 2. Core Principles

### 2.1 Explicit Contract
Every public object MUST:
- have a defined schema,
- define required and optional fields,
- declare invariants,
- be versioned.

---

### 2.2 Stability
Public objects are part of the **standard contract**.

- Breaking changes are forbidden without version bump
- Field semantics MUST NOT change silently

---

### 2.3 Deterministic Serialization
All public objects MUST be:
- serializable to a canonical format (e.g. JSON)
- deterministic in field ordering and hashing

---

### 2.4 Separation of Concerns

Public objects MUST NOT:
- embed runtime-only state
- contain hidden or implicit fields
- depend on implementation-specific structures

---

## 3. Object Classification

Each object MUST declare its status:

- `public` → part of the standard
- `internal` → implementation-specific
- `experimental` → unstable, non-normative

Only `public` objects appear in this registry.

---

## 4. Canonical Public Objects (v1)

Public objects are defined at the **interface boundary of the pipeline**.

They correspond to **canonical, normalized, and validated structures**.

---

### 4.1 CognitiveGateIR

#### Role

Represents the canonical Gate output.

```yaml
CognitiveGateIR:
  verdict: Enum(ALLOW, REQUIRE_CONFIRMATION, ABSTAIN)
  bundle_id: str
  reason_codes: list[str]
```

#### Invariants
- verdict MUST follow the gate lattice
- reason_codes MUST be normalized and deterministic
- MUST be derived from CognitiveGateResult

---

### 4.2 DecisionTrace

#### Role

Represents the canonical execution trace.

#### Notes (implementation-aligned)

In ARVIS v1, DecisionTrace is richer than the minimal spec and includes:

- predictive state
- stability projection
- symbolic state
- control / governance signals

This extended trace is considered public and deterministic.
The extended trace MUST remain deterministic and replay-compatible

---

### 4.3 CognitiveStateIR

#### Role

Represents canonical cognitive state projection.

Derived from:

- CognitiveStateBuilder
- CognitiveStateContract

#### Invariants

- MUST pass contract validation
- MUST be deterministic
- MUST not contain runtime-only data

---

### 4.4 CognitiveIR

#### Role

Canonical intermediate representation of a cognitive execution.

```yaml
CognitiveIR:
  input: CognitiveInputIR
  context: CognitiveContextIR
  decision: CognitiveDecisionIR
  state: CognitiveStateIR | null
  gate: CognitiveGateIR
  stability: StabilityIR | null
  adaptive: AdaptiveIR | null
```
#### Invariants

- MUST be normalized before exposure
- MUST be deterministic
- MUST be replayable
- MUST be consistent with Gate output

---

### 4.5 CognitiveIREnvelope

#### Role

Portable representation of the IR.

```yaml
CognitiveIREnvelope:
  ir: CognitiveIR
  serialized: str
  hash: str
```

#### Invariants

- serialized MUST be canonical
- hash MUST be deterministic
- MUST match IR content exactly

---

### 4.6 ProjectionIR

#### Role

Represents projection certificate in IR form.

Derived via:

```python
ProjectionIRAdapter.from_projection(...)
```

---

### 4.7 ValidityIR

#### Role

Represents validity envelope in IR form.

Derived via:

```python
ValidityIRAdapter.from_validity(...)
```

---

### 4.8 StabilityIR

#### Role

Represents projected stability state.

Derived via:

```python
StabilityIRAdapter.from_stability(...)
```

---

### 4.9 AdaptiveIR

#### Role

Represents adaptive control snapshot.

Derived via:

```python
AdaptiveIRAdapter.from_adaptive(...)
```

---

## 5. Object Versioning

Each object SHOULD include schema_version 

```text
schema_version: str
```

Rules:

- Version MUST follow semantic versioning
- Breaking change → version increment required
- Backward compatibility MUST be documented

---

## 6. Serialization Requirements

All public objects MUST:

- be JSON serializable
- use canonical field ordering
- avoid floating ambiguity (explicit precision rules)
- produce stable hashes when serialized

---

## 7. Compliance Requirements

An implementation is object-compliant if:

- all public objects match their schema
- invariants are enforced
- serialization is deterministic
- no undocumented fields are exposed

---

## 8. Forbidden Practices

The system MUST NOT:

- expose internal objects as public
- mutate public object schemas dynamically
- omit required fields
- introduce undocumented fields

---

## 9. Non-Claims

Public objects do NOT guarantee:

- correctness of upstream computations
- completeness of system observability
- global system validity

They only guarantee structural and semantic consistency.

---

## 10. Future Extensions (Non-Normative)

Planned additions:

- multi-agent object extensions
- distributed timeline objects
- resource governance objects
- cognitive scheduler objects