# ARVIS

**A runtime-monitored and validated cognitive dynamical system**

> Not a model. Not an agent.  
> A **closed-loop system that enforces decision stability under uncertainty**.

---

## 🧠 What ARVIS is

ARVIS is a **discrete-time hybrid dynamical system** operating on cognitive signals.

At each timestep:

o_t → Π → (x_t, z_t, q_t, w_t) → W_t → κ̂_t → G → C → (x_{t+1}, z_{t+1})

Where:

- Π : projection from cognition to state  
- W : composite Lyapunov function  
- κ̂ : adaptive contraction estimate  
- G : decision gate  
- C : control modulation  

This defines a **closed-loop cognitive system with feedback**.

→ Formal definition:  
- [M0 — System Boundary](docs/math/M0_system_boundary.md)  
- [M1 — Formal System Definition](docs/math/M1_formal_system_definition.md)

---

## 📐 Mathematical Scope

ARVIS is defined within a **validated operational domain**.

All guarantees apply only if:

∀ t, o_t ∈ O_valid

This requires:

- bounded projection Π  
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

log(J) / τ_d + log(1 - k_eff) < 0

Where:

- J : switching gain  
- τ_d : dwell time  
- k_eff : effective contraction factor  

This condition defines the admissible trajectories of the reference switching system.

→ Specification:  
- [Theoretical Stability Core (reference model)](./ARVIS_STABILITY_CORE_SPECIFICATIONS.md)  
- [M6 — Gate Stability Result](docs/math/M6_gate_stabilty_result_and_decision_consistency.md)

The stability core defines a theoretical baseline system.

The full ARVIS implementation extends this core with projection, gating, control and runtime validation layers that are not covered by the same guarantees.

---

## ⚙️ Decision Mechanism

Decisions are not generated.

They are **validated through a constrained operator**:

G : (x, z, W, κ̂, H) → {ALLOW, REQUIRE_CONFIRMATION, ABSTAIN}

The Gate enforces:

- Lyapunov decrease constraints  
- adaptive instability detection  
- switching constraints  
- trajectory consistency  

A decision violating constraints:

→ **is rejected (ABSTAIN)**

→ Formalization:  
- [M6 — Gate Condition](docs/math/M6_gate_stabilty_result_and_decision_consistency.md)

---

## 🔁 Closed-Loop Stability

ARVIS is a feedback system:

1. state is projected (Π)  
2. stability is measured (W)  
3. contraction is estimated (κ̂)  
4. decisions are filtered (G)  
5. control adjusts system dynamics (C)  

This produces a regulation loop:

instability ↑ → control ↓ → stabilization

→ Formalization:  
- [M7 — Closed-loop Adaptive Stability](docs/math/M7_closedloop_Adaptive_stability_result.md)

---

## 📊 Stability Guarantees (Conditional)

Under assumptions A1–A15 (not fully verifiable at runtime):

- bounded trajectories  
- exponential decay up to a perturbation tube  
- robustness to disturbances (ISS-type behavior)  
- runtime instability detection  
- enforced decision rejection when unstable  

Formally:

W(t) ≤ C e^{-β t} W(0) + Γ(||w||) + r

→ Formalization:  
- [M8 — Robust Practical Stability (ISS)](docs/math/M8_Robust_Practical_stability_and_ISS_interpretation.md)

---

## 🧭 Validity Envelope

At runtime, ARVIS enforces a **validity envelope**:

V_t = ValidityEnvelope

It aggregates runtime indicators related to:

- projection validity  
- switching safety  
- stability bounds  
- adaptive consistency  

If violated:

→ the decision is **downgraded or rejected**

→ Formalization:  
- [M9 — System Synthesis & Validity Envelope](docs/math/M9_system_synthesis_validity_envelop_and_global.md)

---

## 📡 Runtime validation

ARVIS combines:

- theoretical guarantees (M6–M9)  
- runtime observers  
- adaptive stability estimation  
- empirical validation mechanisms  

→ Result:

decisions are **evaluated and constrained at runtime under observable conditions**, not assumed safe

→ Formalization:  
- [M10 — Runtime Validation](docs/math/M10_empirical_stability_validation_and_runtime_validation.md)

---

## 🧠 What ARVIS guarantees

ARVIS guarantees that decisions are:

- dynamically stable (within domain)  
- bounded under perturbations  
- rejected when instability is detected  
- reproducible (deterministic pipeline)  
- traceable (hash-chained timeline)

---

## 🚫 What ARVIS does NOT guarantee

ARVIS does NOT guarantee:

- correctness of decisions  
- optimality  
- global stability outside validated domain  

ARVIS guarantees **stability constraints**, not decision quality.

---

## 🧩 System Architecture

ARVIS can be functionally decomposed into:

### State (Bundle)
Deterministic cognitive snapshot

### Modeling (Core)
Scientific evaluation (risk, drift, stability)

### Control & Gate
Constraint enforcement and decision filtering

### Timeline
Append-only, hash-chained memory

→ Architecture:  
- [M12 — Cognitive Operating System](docs/math/M12_cognitive_operating_system_(COS)_architecture.md)

---

## ⚡ In One Sentence

> ARVIS turns cognition into a **runtime-regulated dynamical system with enforceable stability constraints**

---

## 🧪 Validation

- 600+ tests (unit, integration, adversarial)  
- 95%+ coverage  
- invariant validation (Lyapunov, switching, ISS)  
- adversarial pipeline testing  

This is a **empirically validated cognitive system implementation**, not a heuristic pipeline.

---

## 🚀 Quickstart

```bash
git clone https://github.com/Julien-Lefauconnier/arvis.git
cd arvis
pip install -e .
```

```python
from arvis.api import CognitiveOS

os = CognitiveOS()

result = os.run(
    user_id="test-user",
    cognitive_input="Should I approve this transaction?"
)

print(result.decision)
print(result.stability.score)
```

---

## 📚 Full Mathematical Documentation

- M0 → M13: docs/math/
- Mapping: docs/architecture/MAPPING_ARVIS_SPECIFICATIONS_IMPLEMENTATION.md

---

## Final Statement

ARVIS does not optimize decisions.

It enforces:

→ the conditions under which decisions are allowed to exist