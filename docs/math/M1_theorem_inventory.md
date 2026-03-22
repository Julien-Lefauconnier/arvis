# ARVIS — M1: Theorem Inventory

## Objective

This document defines the **complete structure of theoretical results** for ARVIS.

It organizes:

- all theorems
- their dependencies
- proof hierarchy
- scope of each result

This is the **blueprint of the formal proof**.

---

## 1. Structure Overview

The proof is decomposed into:

1. Fast subsystem stability
2. Slow-fast coupling control
3. Switching behavior
4. Global stability under switching
5. Robustness to disturbances (ISS)
6. (Future) adaptive extension

---

## 2. Dependency Graph

Theorems depend on each other as follows:

T1 → T2 → T3 → T4 → T5

where:

- T1: Fast stability
- T2: Slow tracking
- T3: Composite decrease
- T4: Switching stability
- T5: Global exponential stability

---

## 3. Theorem Definitions

---

### Theorem T1 — Fast Subsystem Stability

**Statement**

For each mode \( q \), under assumptions A1–A6:

\[
V_q(x_{t+1}) - V_q(x_t)
\leq -\alpha \|x_t\|^2 + \gamma_w \|w_t\|^2
\]

**Interpretation**

- Fast dynamics are **dissipative**
- Stability holds in absence of large disturbances

---

### Theorem T2 — Slow Tracking Bound

**Statement**

Under A7–A9:

\[
\|z_t - T_q(x_t)\| \leq C \eta
\]

for some constant \( C > 0 \)

**Interpretation**

- Slow state tracks target manifold
- Error proportional to time-scale parameter

---

### Theorem T3 — Composite Lyapunov Decrease

**Statement**

Under A1–A9:

\[
W_q(x_{t+1}, z_{t+1}) - W_q(x_t, z_t)
\leq -\kappa_{\mathrm{eff}} W_q(x_t, z_t) + \gamma \|w_t\|^2
\]

with:

\[
\kappa_{\mathrm{eff}} = \alpha - \gamma_z \eta L_T
\]

---

### Theorem T4 — Stability Under Switching

**Statement**

Under A10–A11:

\[
W_{q_{t+1}}(x_t, z_t) \leq J \cdot W_{q_t}(x_t, z_t)
\]

and switching frequency bounded by dwell-time constraint.

---

### Theorem T5 — Global Exponential Stability

**Statement**

Under all assumptions A1–A12:

If:

\[
\frac{\log J}{\tau_d} + \log(1 - \kappa_{\mathrm{eff}}) < 0
\]

then:

\[
W(t) \leq C \cdot e^{-\beta t} W(0)
\]

for some \( C > 0, \beta > 0 \)

---

### Theorem T6 — Input-to-State Stability (ISS)

**Statement**

Under A1–A13:

\[
W(t) \leq C e^{-\beta t} W(0) + \gamma \sup_{k \leq t} \|w_k\|^2
\]

---

### Theorem T7 — Observed Stability Consistency

**Statement**

Under A14:

\[
|\hat{W}(t) - W(t)| \leq \epsilon
\]

---

### Theorem T8 — Projection Consistency (CRITICAL)

**Statement**

Under A15:

\[
\|\Pi(c_1) - \Pi(c_2)\| \leq L_\Pi \|c_1 - c_2\|
\]

---

## 4. Proof Strategy

Each theorem will be proven using:

- Lyapunov methods
- singular perturbation arguments
- switching system theory
- ISS framework

---

## 5. Key Risks

The weakest links are:

1. Projection operator \( \Pi \)
2. Disturbance modeling
3. Switching approximation
4. Observability error

---

## 6. Minimal Valid Core

The minimal provable core is:

T1 + T3 + T4 + T5

Everything else extends it.

---

## 7. Extension Plan

Next additions:

- Adaptive dwell-time theorem
- Contraction-based stability
- Robust switching adaptation

---

## 8. Next Step

→ `M3_cognitive_state_model.md`

Where we formalize:
- cognitive variables
- projection operator
- mapping guarantees