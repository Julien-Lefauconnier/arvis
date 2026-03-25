# ARVIS

**A runtime-monitored and validated cognitive dynamical system**

> Not a model. Not an agent.  
> A **closed-loop system that enforces decision stability under uncertainty**.

---

## 🧠 What ARVIS is

ARVIS is a **discrete-time hybrid dynamical system** operating on cognitive signals.

At each timestep:

$$ o_t \xrightarrow{\Pi} (x_t, z_t, q_t, w_t) \xrightarrow{W_t} \hat{\kappa}_t \xrightarrow{G} C \rightarrow (x_{t+1}, z_{t+1}) $$

Where:

- $\Pi$ : projection from cognition to state
- $W$ : composite Lyapunov function
- $\hat{\kappa}$ : adaptive contraction estimate
- $G$ : decision gate
- $C$ : control modulation

This defines a **closed-loop cognitive system with feedback**.

→ Formal definition:
- [M0 — System Boundary](docs/math/M0_system_boundary.md)
- [M1 — Formal System Definition](docs/math/M1_formal_system_definition.md)

---

## 📐 Mathematical Scope

ARVIS is defined within a **validated operational domain**.

All guarantees apply only if:

$$ \forall t, \quad o_t \in O_{\text{valid}} $$

This requires:
- bounded projection $\Pi$
- Lipschitz continuity of state transitions
- bounded disturbances
- valid switching dynamics

Outside this domain:
→ **no stability guarantee is claimed**

→ Formalization:
- [M1 — Assumptions](docs/math/M1_assumptions.md)
- [M3 — Projection Validated Domain](docs/math/M3_projection_validated_domain.md)

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

$` G : (x, z, W, \hat{\kappa}, H) \mapsto \{\text{ALLOW}, \text{REQUIRE CONFIRMATION}, \text{ABSTAIN}\} `$

The Gate enforces:

- Lyapunov decrease constraints
- adaptive instability detection
- switching constraints
- trajectory consistency

A decision violating constraints → **is rejected (ABSTAIN)**

→ Formalization:
- [M6 — Gate Condition](docs/math/M6_gate_stabilty_result_and_decision_consistency.md)

---

## 🔁 Closed-Loop Stability

ARVIS is a feedback system:

1. state is projected ($\Pi$)
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

## 🧠 What ARVIS guarantees

- dynamically stable (within domain)
- bounded under perturbations
- rejected when instability is detected
- reproducible & traceable

---

## 🚫 What ARVIS does NOT guarantee

- correctness of decisions
- optimality
- global stability outside validated domain

ARVIS guarantees **stability constraints**, not decision quality.

---

## 🧩 System Architecture

### State (Bundle)
### Modeling (Core)
### Control & Gate
### Timeline (append-only, hash-chained)

→ [M12 — Cognitive Operating System](docs/math/M12_cognitive_operating_system_(COS)_architecture.md)

---

## ⚡ In One Sentence

> ARVIS turns cognition into a **runtime-regulated dynamical system with enforceable stability constraints**

---

## 🧪 Validation

- 600+ tests (unit, integration, adversarial)
- 95%+ coverage
- invariant validation (Lyapunov, switching, ISS)

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

ARVIS provides a structured **Intermediate Representation (IR)** of cognition.

The IR is:

- deterministic
- serializable
- model-agnostic
- replayable

```python
ir = result.to_ir()
```

The IR exposes:

- decision state
- cognitive state
- gate outcome

It enables:

- LLM integration
- replay / simulation
- external system interoperability

---

## 📚 Full Mathematical Documentation

- M0 → M13: docs/math/
- Mapping: docs/architecture/MAPPING_ARVIS_SPECIFICATIONS_IMPLEMENTATION.md

---

## Final Statement

ARVIS does not optimize decisions.

It enforces:

→ the conditions under which decisions are allowed to exist