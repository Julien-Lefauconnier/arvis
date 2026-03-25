# ARVIS — M1: Assumptions

## Objective

This document defines all assumptions required for the **mathematical analysis of the ARVIS abstract system**.  
These assumptions apply only to the **projected dynamical system** defined in M0.  
They do not necessarily hold for the full cognitive pipeline.

---

## 1. General Principle

All guarantees in ARVIS are **conditional**:

> They hold only if the assumptions below are satisfied.  
> No runtime certification of these assumptions is claimed.

---

## 2. Structural Assumptions

### A1 — Measurability

For all modes $`q \in \mathcal{Q}`$:

- $`f_q(x, z, w)`$ is measurable
- $`g_q(x, z, w)`$ is measurable

---

### A2 — Local Regularity

Functions $`f_q`$, $`g_q`$ are locally Lipschitz:

$$
\|f_q(x_1, z_1, w_1) - f_q(x_2, z_2, w_2)\|
\leq L_x \|x_1 - x_2\| + L_z \|z_1 - z_2\| + L_w \|w_1 - w_2\|
$$

---

## 3. Boundedness Assumptions

### A3 — Bounded Disturbances

$$
\|w_t\| \leq W_{\max}
$$

### A4 — Bounded Initial Conditions

$$
\|x_0\| \leq X_{\max}, \quad \|z_0\| \leq Z_{\max}
$$

---

## 4. Lyapunov Assumptions

### A5 — Positive Definiteness

$$
c_1 \|x\|^2 \leq V_q(x) \leq c_2 \|x\|^2
$$

### A6 — Decrease Condition

There exist \( \alpha > 0 \), \( \gamma_w > 0 \) such that:

$$
V_q(x_{t+1}) - V_q(x_t) \leq -\alpha \|x_t\|^2 + \gamma_w \|w_t\|^2
$$

### A7 — Target Map Regularity

$$
\|T_q(x_1) - T_q(x_2)\| \leq L_T \|x_1 - x_2\|
$$

### A8 — Slow-Fast Coupling

$$
\|g_q(x, z, w)\| \leq \gamma_z \big( \|x\| + \|z\| + \|w\| \big)
$$

---

## 5. Time-Scale Separation

### A9 — Small Adaptation Rate

$$
0 < \eta \leq \eta_{\max}
$$

with \( \eta_{\max} \) sufficiently small for stability analysis.

---

## 6. Switching Assumptions

### A10 — Average Dwell-Time

$$
N_\sigma(t_0, t) \leq N_0 + \frac{t - t_0}{\tau_d}
$$

### A11 — Mode Compatibility

$$
W_{q'}(x, z) \leq J \cdot W_q(x, z)
$$

---

## 7. Effective Contraction Condition

### A12 — Contraction Condition

$$
\kappa_{\mathrm{eff}} = \alpha - \gamma_z \eta L_T
$$

The system is contractive only if:

$$
\kappa_{\mathrm{eff}} > 0
$$

This condition is **not guaranteed a priori** and must be estimated or enforced.

---

## 8. Disturbance Compatibility

### A13 — Bounded Influence

$$
\|f_q(x, z, w) - f_q(x, z, 0)\| \leq \gamma \|w\|
$$

---

## 9. Interface Assumptions (Critical)

### A14 — State Observability (Approximate)

The system produces observable quantities \( \hat{x}_t \) such that:

$$
\|\hat{x}_t - x_t\| \leq \epsilon
$$

This is an **approximation**, not a guaranteed observer.

### A15 — Projection Assumption (Weak Form)

There exists a projection:

$$
\Pi : \mathcal{C} \rightarrow (x, z, q, w)
$$

such that:
- outputs are bounded
- projection is locally regular in nominal conditions

However:
- Π is not assumed injective
- Π is not guaranteed globally Lipschitz
- Π may lose information

> **All guarantees apply only to the projected system.**

---

## 10. Hidden Engineering Assumptions

The implementation implicitly assumes:
- normalized signals
- finite-dimensional representations
- bounded numerical errors
- stable measurement pipeline

These are **not** formally proven.

---

## 11. Assumption Violations

If any assumption is violated:
- theoretical guarantees do not hold
- stability claims become invalid
- runtime behavior may diverge from model

---

## 12. Summary

All ARVIS guarantees are:
- conditional
- model-level (projected system)
- dependent on A1–A15

---

## 13. Key Limitation

The main limitation is:

> the lack of formal characterization of the projection \( \Pi \)

---

## 14. Next Step

→ [M1_result_inventory.md](M1_result_inventory.md)