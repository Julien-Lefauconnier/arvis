# ARVIS — M0: System Boundary & Mathematical Scope Definition

## Objective

This document defines the **exact mathematical boundary** of the ARVIS system.

It establishes:
- what parts of ARVIS are **formally modeled**
- what parts are **observable but not yet formalized**
- what parts are **heuristic / engineering layers**
- the **mapping between code objects and mathematical objects**

This is the **root document** ensuring that:
> No claim exceeds its formal scope.

---

## 1. System Overview

ARVIS is modeled as a **discrete-time hybrid dynamical system** with:

- fast state dynamics
- slow adaptation dynamics
- switching regimes
- bounded disturbances
- observable outputs

---

## 2. Mathematical Core (IN SCOPE)

The current formal system is defined by:

### State Variables

| Symbol | Description | Type |
|------|-------------|------|
| \( x_t \) | Fast state (risk, stability signals) | \( \mathbb{R}^n \) |
| \( z_t \) | Slow state (adaptation, memory) | \( \mathbb{R}^m \) |
| \( q_t \) | Switching mode | finite set \( \mathcal{Q} \) |
| \( w_t \) | Disturbance / perturbation | bounded |

---

### System Dynamics

\[
x_{t+1} = f_{q_t}(x_t, z_t, w_t)
\]

\[
z_{t+1} = z_t + \eta g_{q_t}(x_t, z_t, w_t)
\]

\[
q_{t+1} = \sigma(q_t, \xi_t)
\]

---

### Lyapunov Structure

\[
W_q(x, z) = V_q(x) + \lambda \|z - T_q(x)\|^2
\]

---

### Stability Condition (T1)

\[
\frac{\log J}{\tau_d} + \log(1 - \kappa_{\mathrm{eff}}) < 0
\]

with:

\[
\kappa_{\mathrm{eff}} = \alpha - \gamma_z \eta L_T
\]

---

### Important Scope Clarification

The system defined above represents an **abstract mathematical model**.

It is not the full cognitive system.

In particular:
- the projection Π from real inputs to (x, z, q, w) is external to this model
- stability guarantees apply only to the projected dynamics

No guarantee is made on the original input space.

---

## 3. Code → Math Mapping

### 3.1 Core Signals

| Code Object | Math Object | Role | Status |
|------------|------------|------|--------|
| RiskSignal | component of \( x_t \) | fast state | IN MODEL |
| Stability metrics | component of \( x_t \) | fast state | IN MODEL |
| SlowState | \( z_t \) | slow dynamics | IN MODEL |
| SwitchingRuntime | \( q_t \) proxy | switching logic | APPROXIMATION |
| Disturbance inputs | \( w_t \) | perturbations | PARTIAL |

---

### 3.2 Derived Components

| Code Object | Math Interpretation | Status |
|------------|--------------------|--------|
| target_map | \( T_q(x) \) | IN MODEL |
| composite_lyapunov | \( W_q(x,z) \) | IN MODEL |
| global_stability_observer | bound estimator | RUNTIME MONITOR (no formal guarantee) |
| switching_params | \( J, \tau_d, \kappa \) | IN MODEL |

---

### 3.3 Cognitive Layer

| Code Object | Math Status |
|------------|------------|
| symbolic_state | OUT OF MODEL |
| context reasoning | OUT OF MODEL |
| memory semantics | OUT OF MODEL |
| LLM outputs | OUT OF MODEL |

---

### 3.4 Decision Layer

| Code Object | Math Status |
|------------|------------|
| decision gates | HEURISTIC |
| action selection | HEURISTIC |
| policy enforcement | HEURISTIC |
| fallback logic | HEURISTIC |

---

## 4. Scope Classification

### 4.1 Mathematically Defined (Abstract Model)

- Fast state dynamics \( x_t \)
- Slow state \( z_t \)
- Composite Lyapunov \( W \)
- Stability condition T1
- Switching bounds (idealized)

These components are formally defined at the model level.

They are not formally verified (no machine-checked proof).

---

### 4.2 Partially Formalized

- Switching mechanism \( q_t \)
- Disturbances \( w_t \)
- Runtime stability monitoring
- Mapping from signals → state

---

### 4.3 Not Formalized (Yet)

- Cognitive reasoning
- Symbolic representations
- Multi-agent interactions
- Decision policies
- LLM uncertainty

---

## 5. Critical Gap (Primary Risk)

The main theoretical gap is the projection:

\[
\Pi : \mathcal{C} \rightarrow (x, z, q, w)
\]

This projection is:

- not formally defined
- not guaranteed to be injective
- potentially lossy
- not proven Lipschitz globally

This implies:

- distinct cognitive states may map to identical projected states
- Lyapunov stability may hold in the projected space while failing in the original space

Therefore:

> All stability guarantees are **conditional on the projection being well-behaved**.

This is currently the **main limitation of the system**.

---

## 6. Formal Guarantee Scope

Current guarantees apply ONLY to:

> The abstract hybrid system defined in Section 2.

They DO NOT apply to:

- full cognitive pipeline
- decision making
- symbolic reasoning
- external model outputs

These guarantees are theoretical results on the abstract system.

They are not runtime-certified and rely on the validity of assumptions.

---

## 7. Required Next Steps

To extend guarantees to the full system:

1. Formalize projection operator \( \Pi \)
2. Define bounded cognitive disturbance model
3. Integrate symbolic state into slow dynamics
4. Prove robustness (ISS) w.r.t perturbations
5. Align runtime signals with theoretical variables

---

## 8. Principle of Valid Claims

A claim is valid ONLY if:

1. It corresponds to a defined mathematical object
2. It is covered by a result
3. The code implements that object faithfully
4. The assumptions are satisfied in practice

---

## 9. Final Statement

ARVIS currently provides:

- a **valid stability core for a hybrid system**
- a **partial mapping to a cognitive pipeline**
- a **runtime monitoring layer consistent with theory**

It does NOT yet provide:

- full cognitive system guarantees
- formal verification of decision layers
- certified robustness to arbitrary inputs

---

## 10. Guiding Rule

> Expand the mathematical domain until it matches the real system — not the opposite.

---