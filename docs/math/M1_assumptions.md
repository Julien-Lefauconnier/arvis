# ARVIS — M1: Assumptions

## Objective

This document defines all **explicit assumptions** required for:

- stability analysis
- Lyapunov decrease
- switching behavior
- robustness to disturbances

These assumptions define the **validity domain** of all theoretical guarantees.

No result in ARVIS is valid outside this domain.

---

## 1. General Principle

All assumptions must be:

- explicit
- minimal
- testable (when possible)
- associated with code-level interpretation

---

## 2. Regularity Assumptions

### A1 — Measurability

For all \( q \in \mathcal{Q} \):

- \( f_q(x, z, w) \) is measurable
- \( g_q(x, z, w) \) is measurable

---

### A2 — Local Lipschitz Continuity

For all \( q \), there exist constants:

- \( L_x > 0 \)
- \( L_z > 0 \)
- \( L_w > 0 \)

such that:

\[
\|f_q(x_1, z_1, w_1) - f_q(x_2, z_2, w_2)\|
\leq L_x \|x_1 - x_2\| + L_z \|z_1 - z_2\| + L_w \|w_1 - w_2\|
\]

Same for \( g_q \)

---

## 3. Boundedness Assumptions

### A3 — Bounded Disturbances

\[
\|w_t\| \leq W_{\max}
\]

---

### A4 — Bounded Initial Conditions

\[
\|x_0\| \leq X_{\max}, \quad \|z_0\| \leq Z_{\max}
\]

---

## 4. Lyapunov Assumptions

### A5 — Positive Definiteness

\[
c_1 \|x\|^2 \leq V_q(x) \leq c_2 \|x\|^2
\]

---

### A6 — Decrease Condition

There exists \( \alpha > 0 \) such that:

\[
V_q(x_{t+1}) - V_q(x_t) \leq -\alpha \|x_t\|^2 + \gamma_w \|w_t\|^2
\]

---

### A7 — Target Map Regularity

\[
\|T_q(x_1) - T_q(x_2)\| \leq L_T \|x_1 - x_2\|
\]

---

### A8 — Slow-Fast Coupling

There exists \( \gamma_z > 0 \) such that:

\[
\|g_q(x, z, w)\| \leq \gamma_z ( \|x\| + \|z\| + \|w\| )
\]

---

## 5. Time-Scale Separation

### A9 — Small Parameter

\[
0 < \eta \leq \eta_{\max}
\]

with:

\[
\eta_{\max} \text{ sufficiently small}
\]

---

## 6. Switching Assumptions

### A10 — Average Dwell-Time

\[
N_\sigma(t_0, t) \leq N_0 + \frac{t - t_0}{\tau_d}
\]

---

### A11 — Mode Compatibility

For all \( q, q' \):

\[
W_{q'}(x, z) \leq J \cdot W_q(x, z)
\]

---

## 7. Effective Contraction

### A12 — Positive Effective Decay

\[
\kappa_{\mathrm{eff}} = \alpha - \gamma_z \eta L_T > 0
\]

---

## 8. Disturbance Compatibility

### A13 — Bounded Influence

There exists \( \gamma > 0 \):

\[
\|f_q(x, z, w) - f_q(x, z, 0)\| \leq \gamma \|w\|
\]

---

## 9. Observability Assumptions

### A14 — Observable State Mapping

The system provides a mapping:

\[
\hat{x}_t = \mathcal{O}(y_t)
\]

such that:

\[
\|\hat{x}_t - x_t\| \leq \epsilon
\]

---

## 10. Projection Assumptions (CRITICAL)

### A15 — Cognitive Projection Consistency

There exists a projection:

\[
\Pi : \mathcal{C} \to (x, z, q, w)
\]

such that:

- bounded output
- locally Lipschitz
- stable under perturbations

---

## 11. Hidden Assumptions (Explicitly Exposed)

This system implicitly assumes:

- normalization of signals
- no adversarial unbounded input
- finite-dimensional representation of cognition
- stability of measurement process

---

## 12. Assumption Violations

If any assumption is violated:

- no stability guarantee holds
- runtime monitoring may become unreliable
- system behavior is undefined mathematically

---

## 13. Summary

The ARVIS guarantees are valid ONLY if:

- A1–A15 hold simultaneously
- parameters satisfy T1 condition
- system remains within bounded domain

---

## 14. Next Step

→ `M1_theorem_inventory.md`

Defines:
- all theorems
- proof structure
- dependencies