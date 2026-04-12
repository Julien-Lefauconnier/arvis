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

IMPORTANT:

Public Objects define the **external contract boundary of ARVIS**.

They are distinct from:

- internal execution structures (pipeline state)
- interoperability projections (e.g. canonical signals)

The CognitiveIR defines the canonical boundary between cognition and response construction.
All response-related public objects MUST be strictly derived from the IR.

Public objects are defined at the **interface boundary of the IR**.

They correspond to:
- canonical cognitive representations (IR)
- deterministic post-cognitive transformations (response, memory, execution)

NOTE:

The CognitiveIR is the **core canonical object** of ARVIS.

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
- embed transient runtime execution state (scheduler state, process state, execution budgets)
- contain hidden or implicit fields
- depend on implementation-specific structures

---


### 2.5 Separation from Interoperability Layers

Public Objects are NOT equivalent to external canonical signal systems.

In particular:

- Public Objects are expressive and information-complete
- Canonical Signals are constrained and registry-bound

The transformation:

```text
CognitiveIR → Canonical Signals
```

is handled by the **Kernel Adapter Layer** and is:

- deterministic
- rule-based
- lossy

Public Objects MUST NOT:

- depend on canonical signal representations
- embed signal registry constraints

---

### 2.6 Syscall Authority (CRITICAL)

All side-effects MUST be represented as SyscallResults.

Public objects MUST NOT:

- expose side-effects outside syscall representation
- introduce alternative execution artifacts

SyscallResults are the canonical representation of execution.

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

Public objects are defined at the **interface boundary of the IR**.

They correspond to:
- canonical cognitive representations (IR)
- deterministic post-cognitive transformations (response, memory, execution)

NOTE:

The CognitiveIR is the **core canonical object** of ARVIS.

However, not all public objects are equal in role:

- CognitiveIR → full canonical representation
- Other objects → partial projections or structured views

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
  syscalls: list[SyscallResult] | null
```
#### Invariants

- MUST be normalized before exposure
- MUST be deterministic
- MUST be replayable
- MUST be consistent with Gate output
- MUST be the single source of truth for external projection layers

IMPORTANT:

- SyscallResults represent ALL side-effects
- Tools are a specialization of syscalls

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

### 4.10 SyscallResult (IR Field)

Represents execution results of syscalls attached to CognitiveIR.

```yaml
SyscallResult:
  syscall: str
  success: bool
  result: Any | null
  error: str | null
```

Invariants:
- MUST reflect kernel-executed side-effects
- MUST be deterministic (recorded, not executed)
- MUST NOT influence decision semantics
- MUST be the canonical runtime artifact

---

### 4.11 ToolResult (Derived Object)

Represents a derived view of a syscall execution where:

```text
syscall == "tool.execute"
```

ToolResult is NOT a primary runtime object.

It is a projection of SyscallResult.

```yaml
ToolResult:
  tool_name: str
  success: bool
  output: Any | null
  error: str | null
```

Mapping:

```text
SyscallResult → ToolResult
```

Rules:

- ToolResult MUST be derivable from SyscallResult
- ToolResult MUST NOT introduce new information
- ToolResult is OPTIONAL and presentation-oriented

IMPORTANT:

SyscallResult is the ONLY source of truth.

---

### 4.12 ResponseStrategyDecision

#### Role

Represents the canonical response strategy selected after cognitive decision validation.

This object defines **how the system intends to communicate**, not what it has decided.

```yaml
ResponseStrategyDecision:
  strategy: Enum(ABSTENTION, CONFIRMATION, INFORMATIONAL, ACTION)
  requires_confirmation: bool
  can_execute: bool
```

#### Invariants

- MUST be derived from validated decision outputs
- MUST be derived strictly from CognitiveIR
- MUST NOT alter decision semantics
- MUST be deterministic given identical inputs
- MUST NOT depend on linguistic realization
- MUST NOT depend on runtime execution

---

### 4.13 ResponsePlan

#### Role

Represents the canonical pre-linguistic communication plan.

It defines how a validated cognitive intent is structured for communication.

```yaml
ResponsePlan:
  strategy: ResponseStrategyDecision
  act_type: str
  structure: dict
  constraints: dict
  realization_hints: dict | null
```

#### Invariants

- MUST be deterministic
- MUST NOT contain natural language
- MUST NOT contain runtime-only artifacts
- MUST NOT modify cognitive decision semantics
- MUST be sufficient to drive realization deterministically
- MUST be fully derivable from CognitiveIR + ResponseStrategyDecision
- MUST NOT introduce new information not present in IR

IMPORTANT:

ResponsePlan is a language-agnostic communication contract.

---

### 4.14 MemoryLongEntry

#### Role

Represents a canonical long-term memory unit.

```yaml
MemoryLongEntry:
  memory_id: str
  content: structured deterministic data
  constraints: list[str]
  metadata: dict
  created_at: timestamp
```

#### Invariants

- MUST be immutable once created
- MUST be identifiable via memory_id
- MUST NOT contain runtime-only state

---

### 4.15 MemoryLongSnapshot

#### Role

Represents the deterministic memory state used during a cognitive execution.

```yaml
MemoryLongSnapshot:
  entries: list[MemoryLongEntry]
  constraints: list[str]
  preferences: dict
```

#### Invariants

- MUST reflect filtered memory (post-policy)
- MUST be deterministic
- MUST NOT expose unauthorized memory
- MUST match CognitiveContextIR constraints
- MUST be consistent with CognitiveContextIR

IMPORTANT:

MemoryLongSnapshot is the audit surface of memory.

---

### 4.16 LinguisticAct

#### Role

Represents the canonical communicative act derived from a ResponsePlan.

```yaml
LinguisticAct:
  act_type: str
  strategy: ResponseStrategyDecision
```

#### Invariants

- MUST be derived from ResponsePlan
- MUST be deterministic
- MUST NOT introduce new decision semantics
- MUST remain consistent with ResponseStrategyDecision
- MUST NOT introduce new information beyond ResponsePlan

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

## 6.1 Exposure Model

Not all Public Objects are necessarily exposed in all contexts.

Exposure is controlled by:

- API layer
- reflexive rendering layer
- compliance / audit interfaces

Rules:

- exposed objects MUST remain deterministic
- partial exposure MUST preserve semantic consistency
- hidden fields MUST NOT affect exposed semantics
- exposure MUST NOT alter object semantics

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