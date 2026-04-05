# ARVIS — M2: Stability Proof Skeleton (Implementation-Aligned)

## Objective

This document provides a **structured, step-by-step proof skeleton** that links:

- the ARVIS mathematical stability core (M1),
- the implemented projection operator Π (M3),
- the empirically validated domain O_valid (M3 Phase A).

It is **not** a complete formal proof (no machine-checked verification, no full induction over infinite trajectories).  
It is an **implementation-aligned proof outline** designed to guide future formalization (Coq, Lean, SMT, or detailed pen-and-paper derivation).

The skeleton follows standard techniques from switched hybrid systems literature (Liberzon 2003, Hespanha 2004, Branicky 1998, Lin & Antsaklis).

### Execution Semantics

All transitions $(t \to t+1)$ are treated as **atomic state updates** in the mathematical model.

In the implemented system, such a transition may be computed through multiple runtime steps (e.g., staged pipeline execution or scheduler ticks).

However, the proof considers only the **fully completed transition**, and all intermediate execution states are excluded from the model.

---

## 1. System Definition (Recap from M1)

We consider the projected discrete-time switched system:

$$
\begin{aligned}
x_{t+1} &= f_{q_t}(x_t, z_t, u_t, w_t) \\
z_{t+1} &= z_t + \eta \, g_{q_t}(x_t, z_t, u_t, w_t)
\end{aligned}
$$

with switching signal:

$$
q_t = \Pi_q(o_t), \quad (x_t, z_t, q_t, w_t) = \Pi(o_t)
$$

Initial condition: $(x_0, z_0, q_0) = \Pi(o_0)$.

All dynamics are defined **only on the projected state** and hold exclusively when $o_t \in \mathcal{O}_{\text{valid}} \ \forall t$.

---

## 2. Projection Domain Assumption (Empirically Validated – M3 Phase A)

There exists a non-empty subset $\mathcal{O}_{\text{valid}} \subset \mathcal{O}$ such that for every trajectory satisfying $o_t \in \mathcal{O}_{\text{valid}} \ \forall t$:

1. $\Pi(o_t)$ is bounded: $\|(x_t, z_t, w_t)\| \leq M < \infty$
2. $\Pi$ is locally Lipschitz on $\mathcal{O}_{\text{valid}}$ (with constant $L_\Pi$ estimated empirically)
3. $\Pi$ is noise-robust (small input perturbations yield small output changes)
4. Switching signal $q_t = \Pi_q(o_t)$ is stable away from mode boundaries
5. The composite Lyapunov candidate $W(x,z)$ is well-defined and positive definite on the image of $\Pi$

These properties are **empirically validated** on a deterministic fixture corpus (see M3_projection_validated_domain.md).  
**No global properties** (global Lipschitz, injectivity, full domain coverage) are claimed.

---

## 3. Lyapunov Function Candidate (Composite – Standard Form)

We define the mode-dependent composite Lyapunov function:

$$
W_q(x,z) = V_q(x) + \lambda \|z - T_q(x)\|^2
$$

where:
- $V_q : \mathbb{R}^n \to \mathbb{R}_{\geq 0}$ is a positive definite, radially unbounded Lyapunov function for the fast subsystem in mode $q$ (assumed to exist under A3–A6)
- $T_q : \mathbb{R}^n \to \mathbb{R}^m$ is a continuously differentiable target map (slow state equilibrium manifold for mode $q$)
- $\lambda > 0$ is a sufficiently large coupling gain (to be chosen)

Assumption (from M1): there exist class-$\mathcal{K}_\infty$ functions $\underline{\alpha}, \overline{\alpha}$ such that

$$
\underline{\alpha}(\|x\|) \leq V_q(x) \leq \overline{\alpha}(\|x\|) \quad \forall q
$$

---

## 4. One-Step Decrease – Fast Dynamics (Core Contraction Step)

This section analyzes the decrease of the Lyapunov function over a **single logical transition** $(t \to t+1)$, 
assumed to correspond to a fully evaluated system update.

**Under** the fast subsystem contraction assumption (A7–A9, local exponential decrease rate $\alpha > 0$):

$$
V_{q}(f_q(x, z, u, w)) - V_q(x) \leq -\alpha V_q(x) + \gamma_w \|w\|^2 + \gamma_u \|u\|^2
$$

(with $\gamma_w, \gamma_u$ class-$\mathcal{K}$ gains)

**Then**, choosing $\lambda$ large enough to dominate cross-terms (singular perturbation argument), the composite decrease satisfies (for small enough $\eta$):

$$
W_{q}(x_{t+1}, z_{t+1}) - W_q(x_t, z_t) \leq -\kappa_{\text{eff}} \, W_q(x_t, z_t) + \Gamma(\|w_t\| + \|u_t\|)
$$

where

$$
\kappa_{\text{eff}} = \alpha - \gamma_z \eta L_T - \delta(\eta, \lambda)
$$

(with $\delta \to 0$ as $\eta \to 0$ and $L_T = \sup \| \partial T_q / \partial x \|$ Lipschitz constant of target map).

This is the **local contraction step** in each mode (fast timescale dominance).

---

## 5. Switching Extension – Average Dwell-Time Condition

The dwell-time condition is evaluated over **logical time steps** $t$, each corresponding to a completed system transition.

**Under** the jump condition at switching instants (A10–A11):

$$
W_{q'}(x, z) \leq J \, W_q(x, z) \quad \text{with jump gain } J \geq 1
$$

and assuming the average dwell-time $\tau_d$ (average time between switches) satisfies the small-gain condition:

$$
\frac{\log J}{\tau_d} + \log(1 - \kappa_{\text{eff}}) < 0
\quad \Leftrightarrow \quad \kappa_{\text{eff}} > 1 - e^{-\frac{\log J}{\tau_d}}
$$

**Then** the system achieves **global exponential stability on the projected trajectories** staying in $\mathcal{O}_{\text{valid}}$:

$$
W(t) \leq C \, e^{-\beta t} \, W(0) \quad \text{with } \beta > 0, \, C > 0 \text{ depending on } J, \kappa_{\text{eff}}, \tau_d
$$

This is a **conditional result**: it holds only if the switching signal induced by $\Pi_q(o_t)$ satisfies the dwell-time bound on the validated domain.

---

## 6. Domain Restriction & Scope

The above result holds **exclusively** for trajectories satisfying:

$$
o_t \in \mathcal{O}_{\text{valid}} \quad \forall t \geq 0
$$

and under **all** assumptions A1–A15 (M1_assumptions.md).  
Outside $\mathcal{O}_{\text{valid}}$ or upon violation of any A_i: **no stability result is claimed**.

---

## 7. Interpretation & Implementation Alignment

This skeleton establishes:
- consistency between the mathematical model (M1) and the implemented projection + pipeline
- structural feasibility of exponential stability under dwell-time + contraction
- empirical grounding via Phase A validation of projection properties (M3)

It bridges control-theoretic guarantees to the cognitive pipeline without overclaiming.

In particular, the runtime scheduler is responsible for ensuring that each transition is executed to completion 
before being considered in the logical time evolution used in this proof.

---

## 8. Key Limitations (Repeated for Emphasis)

- $\Pi$ is **not** globally Lipschitz nor injective → potential lossy collisions in projection
- $\mathcal{O}_{\text{valid}}$ is **empirically defined**, not exhaustively characterized
- Dwell-time is **not** formally enforced at runtime (only indirectly via gate)
- No formal bound on residual set when $w_t \neq 0$ or $u_t$ active (see M8 for ISS extension)
- No machine-checked proof (Coq/Lean/SMT pending)

---

## 9. Next Steps Toward Formal Proof

1. Derive explicit constants for $\lambda$, $\kappa_{\text{eff}}$, $\beta$ in the one-step decrease
2. Quantify empirical dwell-time statistics on fixture corpus
3. Prove boundedness of adaptive estimator error $\widehat{\kappa}_t - \kappa_t$ (M4–M5)
4. Extend to practical stability with perturbations (move to M8 skeleton)
5. Formal verification of minimal core (T1 + T3 + T4 + T5) in proof assistant

---

## Final Statement

ARVIS admits a **locally valid exponential stability skeleton** on the empirically validated projection domain $\mathcal{O}_{\text{valid}}$, under average dwell-time and effective contraction conditions.  

This outline is **implementation-aligned**, **mathematically structured**, and **explicitly conditional** — providing a credible bridge between hybrid systems theory and the ARVIS cognitive runtime.