# ARVIS

**A deterministic Cognitive Operating System (Cognitive OS)**

> Not a model. Not an agent.
> A deterministic Cognitive OS that enforces stability-constrained decisions
> through a canonical cognitive state, a versioned IR layer, and a reflexive
> self-observation architecture.

---

## 🧠 What ARVIS is

ARVIS is a deterministic Cognitive Operating System built as:

- a closed-loop cognitive pipeline
- a canonical `CognitiveState` kernel
- a stable Intermediate Representation (IR)
- a reflexive self-observation layer
- a timeline-backed traceability system
- a runtime execution layer (tools, adapters, external actions)

The system enforces a strict separation between:

- decision (pipeline, deterministic cognition)
- execution (runtime layer, tools and side effects)
- canonical state (CognitiveState)
- external representation (IR)
- reflexive observation (read-only)

At each timestep:

$$ o_t \xrightarrow{\Pi_{\text{cert}}} P_t \xrightarrow{W_t} \hat{\kappa}_t \xrightarrow{G} C \rightarrow (x_{t+1}, z_{t+1}) $$

⚠️ Important:

 ARVIS currently implements a **runtime projection certification layer**:

 $$ \Pi_{\text{cert}} : \mathcal{O}_{runtime} \to P_t $$

 The full projection:

 $$ \Pi : \mathcal{C} \to (x, z, q, w) $$

 is **not yet fully implemented in production**.

Where:

- $\Pi$ : theoretical projection from cognition to state (not fully implemented)
- $\Pi_{\text{cert}}$ : runtime projection certification layer (implemented)
- $W$ : composite Lyapunov function
- $\hat{\kappa}$ : adaptive contraction estimate
- $G$ : decision gate
- $C$ : control modulation

This defines a **closed-loop cognitive system with feedback**.

→ Formal definition:
- [M0 — System Boundary](docs/math/M0_system_boundary.md)
- [M1 — Formal System Definition](docs/math/M1_formal_system_definition.md)

---

## 🔍 Cognitive State Kernel

ARVIS now exposes a canonical `CognitiveState` representation.

This state is:

- deterministic
- serializable
- contract-validated
- safe to export through IR

The CognitiveState layer includes:

- `CognitiveState`
- `CognitiveStateBuilder`
- `CognitiveStateContract`
- `StateIRAdapter`

This turns the pipeline output into a stable, inspectable system state rather
than a collection of loosely coupled runtime artifacts.

---

## Projection Layer (Current State)

ARVIS currently implements a **projection certification layer**, not the full theoretical projection.

Runtime projection produces a certificate:

$$ P_t = (\text{domain_valid}, \text{margin}, \text{safety}) $$

This certificate is:

- computed in the cognitive pipeline
- consumed by the Gate
- used for runtime safety enforcement

The projection layer includes:

- ProjectionDomain
- ProjectionValidator
- ProjectionCertificate
- ProjectionStage

→ Formalization:
- [M3.1 — Cognitive State Model & Target Projection](docs/math/M3_1_cognitive_state_model.md)
- [M3.2 — Observation & Certification Protocol](docs/math/M3_2_observation_and_projection.md)
- [M3.3 — Runtime Projection & Certificate](docs/math/M3_3_projection_validated_domain.md)
- [M3 Appendix — Projection Validation](docs/math/M3_appendix_projection_validation.md)

Important:

The current implementation exposes a **runtime projection certification layer**, not the full theoretical projection Π.

This layer:

- validates observations against a bounded domain
- produces a ProjectionCertificate
- is consumed by the Gate for safety enforcement

The full projection Π remains a target architecture and is not yet implemented.

---

## 📐 Mathematical Scope

ARVIS is defined within a **validated operational domain**.

All guarantees apply only if:

$$ \forall t, \quad o_t \in O_{\text{valid}} $$

This requires:
- bounded projection (theoretical Π, assumed)
- bounded certification layer (implemented Π_cert)
- Lipschitz continuity of state transitions
- bounded disturbances
- valid switching dynamics

Outside this domain:
→ **no stability guarantee is claimed**

→ Formalization:
- [M1 — Assumptions](docs/math/M1_assumptions.md)
- [M3.3 — Runtime Projection Domain](docs/math/M3_3_projection_validated_domain.md)

---

## 🧩 Core Stability Law

ARVIS enforces a stability condition on switching dynamics:

$$ \frac{\log(J)}{\tau_d} + \log(1 - k_{\text{eff}}) < 0 $$

Where:
- $J$ : switching gain
- $\tau_d$ : dwell time
- $k_{\text{eff}}$ : effective contraction factor

This condition defines the admissible trajectories of the reference switching system.

→ Specification:
- [Theoretical Stability Core (reference model)](./ARVIS_STABILITY_CORE_SPECIFICATIONS.md)
- [M6 — Gate Stability Result](docs/math/M6_gate_stabilty_result_and_decision_consistency.md)

---

## ⚙️ Decision Mechanism

Decisions are not generated.  
They are **validated through a constrained operator**:

$` G : (W, \Delta W, \kappa, V, P, H) \mapsto \{\text{ALLOW}, \text{REQUIRE CONFIRMATION}, \text{ABSTAIN}\} `$

The Gate is:

- Lyapunov-aware
- projection-aware
- validity-aware

It enforces:

- stability constraints
- projection domain validity
- runtime safety conditions

The Gate enforces:

- Lyapunov decrease constraints
- projection validity constraints
- projection boundary constraints
- adaptive instability detection
- switching constraints
- trajectory consistency

A decision violating constraints → is **degraded (REQUIRE_CONFIRMATION) or rejected (ABSTAIN) depending on severity and policy.**

→ Formalization:
- [M6 — Gate Condition](docs/math/M6_gate_stabilty_result_and_decision_consistency.md)

---

## 🔁 Closed-Loop Stability

ARVIS is a feedback system:

1. observation is certified ($\Pi_{\text{cert}}$)
2. stability is measured ($W$)
3. contraction is estimated ($\hat{\kappa}$)
4. decisions are filtered ($G$)
5. control adjusts system dynamics ($C$)

This produces a regulation loop:  
**instability ↑ → control ↓ → stabilization**

→ Formalization:
- [M7 — Closed-loop Adaptive Stability](docs/math/M7_closedloop_Adaptive_stability_result.md)

---

## 📊 Stability Guarantees (Conditional)

Under assumptions A1–A15:

$$ W(t) \leq C e^{-\beta t} W(0) + \Gamma(\|w\|) + r $$

→ Formalization:
- [M8 — Robust Practical Stability (ISS)](docs/math/M8_Robust_Practical_stability_and_ISS_interpretation.md)

---

## 🧭 Validity Envelope

At runtime, ARVIS enforces a **validity envelope**:

$$ V_t = \text{ValidityEnvelope} $$

If violated → the decision is **downgraded or rejected**

→ Formalization:
- [M9 — System Synthesis & Validity Envelope](docs/math/M9_system_synthesis_validity_envelop_and_global.md)

---

## 📡 Runtime validation

ARVIS combine theoretical guarantees (M6–M9) + runtime observers + adaptive estimation.

Decisions are **evaluated and constrained at runtime under observable conditions**, not assumed safe.

→ Formalization:
- [M10 — Runtime Validation](docs/math/M10_empirical_stability_validation_and_runtime_validation.md)

---

## ⚠️ Theory vs Implementation

ARVIS distinguishes between:

**Theoretical model:**
$$ \Pi : \mathcal{C} \to (x, z, q, w) $$

**Current implementation:**
$$ \Pi_{\text{cert}} : \mathcal{O}_{runtime} \to P_t $$

The system currently operates on:

- certified projection views
- bounded runtime signals
- safety-enforced decision filtering

Full projection remains a **target architecture**.

---

## 🧠 What ARVIS guarantees

- dynamically stable (within domain)
- bounded under perturbations
- rejected when instability is detected
- reproducible & traceable
- deterministic IR generation and hashing
- replayable cognitive execution

---

## 🚫 What ARVIS does NOT guarantee

- correctness of decisions
- optimality
- global stability outside validated domain

ARVIS guarantees **stability constraints**, not decision quality.

---

## 🧩 System Architecture

ARVIS is now structured around four major layers:

### 1. Cognitive Execution Layer
- deterministic pipeline
- staged cognition
- closed-loop control and gate enforcement

### 2. Canonical State Layer
- `CognitiveState`
- bundle/state normalization
- contract validation

### 3. Reflexive Layer
- capabilities
- introspection
- rendering
- reflexive snapshots
- timeline exposure explanation
- compliance and attestation

### 4. Public Contract Layer
- `CognitiveOS`
- result views
- IR export
- reflexive API entrypoint
- canonical IR pipeline (build → normalize → validate → serialize → hash → envelope)

→ [M12 — Cognitive Operating System](docs/math/M12_cognitive_operating_system_(COS)_architecture.md)

### 5. Runtime Execution Layer

ARVIS includes a dedicated Runtime Layer responsible for executing side-effectful actions after the 
cognitive pipeline has produced a decision.

This layer includes:

- Tool system (ToolRegistry, ToolExecutor)
- Adapters (LLM, external APIs, etc.)
- Execution orchestration

Properties:

- strictly separated from the pipeline
- does not influence decision logic
- fully observable and traceable
- produces ToolResults captured in IR

Important:

Tool execution is **not part of cognition**.

It is an externalized execution phase that preserves:

- determinism of decision-making
- replayability of cognitive logic
- full auditability of actions

---

## ⚡ In One Sentence

> ARVIS turns cognition into a **runtime-regulated dynamical system with enforceable stability constraints**

---

---

## 🔄 Canonical Cognitive Flow

ARVIS follows a strict separation between cognition, decision, and execution.

The full system can be represented as:

```text
                 ┌──────────────────────────────┐
                 │      Cognitive Pipeline      │
                 │ (deterministic reasoning)    │
                 └──────────────┬───────────────┘
                                │
                                ▼
                    ┌──────────────────────┐
                    │   Decision System    │
                    │ Gate → Confirmation │
                    │ → Execution         │
                    └────────────┬────────┘
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │    Action Decision   │
                    │ (tool / no tool)    │
                    └────────────┬────────┘
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │   Runtime Layer      │
                    │ ToolExecutor         │
                    │ Adapters             │
                    └────────────┬────────┘
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │   Tool Execution     │
                    │ (side effects)       │
                    └────────────┬────────┘
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │   Observability      │
                    │ ToolResults          │
                    │ DecisionTrace        │
                    │ CognitiveState       │
                    └────────────┬────────┘
                                 │
                                 ▼
                    ┌──────────────────────┐
                    │   IR Projection      │
                    │ CognitiveIR          │
                    │ (deterministic)      │
                    └──────────────────────┘
```

### Key Properties

- The pipeline is deterministic and produces decisions only
- The runtime executes side effects (tools, adapters)
- The decision layer never performs execution
- All execution is:
    - observable
    - recorded
    - replay-safe

### Critical Separation

Layer	Responsibility
Pipeline	cognition (deterministic)
Decision	admissibility & constraints
Runtime	execution (side effects)
IR	deterministic external representation

This separation is fundamental to ARVIS:

**→ decisions remain deterministic and replayable, even when execution is not**

---

## 🧪 Validation

ARVIS includes an extensive deterministic validation suite:

- unit tests (pipeline, IR, adapters)
- integration tests (end-to-end pipeline execution)
- replay determinism tests (IR → pipeline)
- normalization and hashing invariants
- stability and gate constraint validation

The system enforces:

- deterministic execution
- order-invariant IR normalization
- stable hashing
- replay consistency

---

## 🚀 Quickstart

```bash
git clone https://github.com/Julien-Lefauconnier/arvis.git
cd arvis
pip install -e .
```

# 🧠 Cognitive OS (Public Interface)

ARVIS exposes a **Cognitive Operating System interface** for external use.

This layer provides:

- a stable public API
- a unified result view
- abstraction over the internal pipeline

```python
from arvis.api import CognitiveOS

os = CognitiveOS()

result = os.run(
    user_id="test-user",
    cognitive_input={}
)

print(result.summary())
```

---

# 🔄 Intermediate Representation (IR)

ARVIS exposes a **canonical Intermediate Representation (IR)** of each cognitive execution.

The IR is not a simple export.

It is a **deterministic, normalized, validated, and hashed representation** of the cognitive process.

---

## IR Pipeline

The IR is constructed through a canonical pipeline:

```text
CognitivePipeline
    → CognitiveIRBuilder
    → CognitiveIRNormalizer
    → CognitiveIRValidator
    → CognitiveIRSerializer
    → CognitiveIRHasher
    → CognitiveIREnvelope
```
This guarantees:

- deterministic structure
- order-invariant normalization
- validation before exposure
- stable hashing
- replayability

### Properties

The IR is:

- deterministic
- serializable
- hashable
- replayable
- model-independent
- Structure (v1 — implementation-aligned)

The current IR exposes a canonical aggregation:

```python
ir = result.to_ir()
```

It includes:

- input (CognitiveInputIR)
- context (CognitiveContextIR)
- decision (CognitiveDecisionIR)
- state (CognitiveStateIR)
- gate (CognitiveGateIR)

Optional extensions (implementation-dependent):

- projection
- validity
- stability
- adaptive snapshot
- tools (runtime execution results)

### Key Guarantees

- identical input → identical IR
- normalization removes ordering ambiguity
- hash stability is guaranteed
- IR can be replayed deterministically

### Use Cases

- deterministic replay
- audit and compliance
- system interoperability
- LLM-safe structured prompting

---

## Reflexive System

ARVIS now includes an explicit reflexive architecture.

This layer provides:

- declarative capability snapshots
- structured introspection views
- reflexive timeline aggregation and explanation
- compliance-oriented explanation and attestation
- read-only reflexive snapshots for safe external exposure

The reflexive layer is observational only:

- no hidden inference
- no self-modification
- no authority escalation
- no raw cognitive leakage

---

## 📚 Full Mathematical Documentation

- M0 → M13: docs/math/
- Mapping: docs/architecture/MAPPING_ARVIS_SPECIFICATIONS_IMPLEMENTATION.md

---

## Final Statement

ARVIS does not optimize decisions.

It enforces:

→ the conditions under which decisions are allowed to exist