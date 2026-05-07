# ARVIS — M1: Formal System Definition

## Objective

This document provides a **fully explicit mathematical definition** of the ARVIS core system.  
It defines:
- the exact state space
- the system dynamics
- the switching structure
- the disturbance model
- the output structure

This definition is **the reference model** for all subsequent proofs.

---

## 1. Notation

- $`t \in \mathbb{N}`$: discrete time
- $`\|\cdot\|`$: Euclidean norm unless specified
- $`\mathcal{Q}`$: finite set of modes

### Time Semantics

Each time index $t$ corresponds to a **logical system transition**.

A transition $(t \to t+1)$ is defined as a **fully completed system update**, regardless of the internal execution mechanism.

---

## 2. State Space

We define the global state:

$$
s_t = (x_t, z_t, q_t)
$$

with:

### 2.1 Fast State

$$
x_t \in \mathbb{R}^n
$$

Represents:
- risk signals
- stability indicators
- instantaneous cognitive metrics

### 2.2 Slow State

$$
z_t \in \mathbb{R}^m
$$

Represents:
- memory accumulation
- long-term adaptation
- contextual integration

### 2.3 Switching State

$$
q_t \in \mathcal{Q}
$$

- finite set of modes
- each mode corresponds to a regime of operation

---

## 3. Disturbance Model

We define:

$$
w_t \in \mathcal{W}
$$

where:
- $`\mathcal{W} \subset \mathbb{R}^d`$ is bounded
- $`\|w_t\| \leq W_{\max}`$

Disturbances represent:
- input noise
- model uncertainty
- cognitive perturbations (approximate)

---

## 4. System Dynamics

The following equations define the **abstract state transition** between two consecutive logical time steps.

Each transition $(t \to t+1)$ is assumed to be **atomic** at the model level, even if its computation is
performed incrementally in an implementation.

### 4.1 Fast Dynamics

$$
x_{t+1} = f_{q_t}(x_t, z_t, w_t)
$$

where:

$$
f_q : \mathbb{R}^n \times \mathbb{R}^m \times \mathcal{W} \to \mathbb{R}^n
$$

### 4.2 Slow Dynamics

$$
z_{t+1} = z_t + \eta \, g_{q_t}(x_t, z_t, w_t)
$$

where:
- $`\eta > 0`$ is a small parameter (time-scale separation)
- $`g_q : \mathbb{R}^n \times \mathbb{R}^m \times \mathcal{W} \to \mathbb{R}^m`$

### 4.3 Switching Dynamics

$$
q_{t+1} = \sigma(q_t, \xi_t)
$$

where:
- $`\sigma : \mathcal{Q} \times \Xi \to \mathcal{Q}`$
- $`\xi_t`$ : switching trigger signal

---

## 5. Switching Constraints

### 5.1 Average Dwell-Time

There exist constants:
- $`\tau_d > 0`$
- $`N_0 \geq 0`$

such that for any interval:

$$
N_\sigma(t_0, t) \leq N_0 + \frac{t - t_0}{\tau_d}
$$

### 5.2 Jump Condition

There exists $`J \geq 1`$ such that:

$$
W_{q'}(x, z) \leq J \cdot W_q(x, z)
$$

for all admissible mode transitions $`q \to q'`$

---

## 6. Target Map

For each mode $`q`$, define:

$$
T_q : \mathbb{R}^n \to \mathbb{R}^m
$$

Interpretation:
- desired slow state given fast state

---

## 7. Lyapunov Functions

### 7.1 Fast Lyapunov

For each $`q`$:

$$
V_q : \mathbb{R}^n \to \mathbb{R}_{\geq 0}
$$

### 7.2 Composite Lyapunov

$$
W_q(x, z) = V_q(x) + \lambda \|z - T_q(x)\|^2
$$

with $`\lambda > 0`$

---

## 8. Output Structure

We define observable output:

$$
y_t = h(x_t, z_t)
$$

where:

$$
h : \mathbb{R}^n \times \mathbb{R}^m \to \mathbb{R}^p
$$

This represents:
- runtime signals
- monitoring outputs

---

## 9. Initial Conditions

$$
x_0 \in \mathbb{R}^n, \quad z_0 \in \mathbb{R}^m, \quad q_0 \in \mathcal{Q}
$$

---

## 10. Well-Posedness Requirements

The system is well-defined if:
1. $`f_q`$, $`g_q`$ are measurable
2. solutions exist for all $`t`$
3. trajectories remain bounded under assumptions

Additionally, it is assumed that each transition $(t \to t+1)$ corresponds to a **fully evaluated system update**, 
ensuring consistency between the mathematical model and any staged or incremental execution.

---

## 11. Separation of Time Scales

We assume:

$$
0 < \eta \ll 1
$$

ensuring:
- fast dynamics dominate locally
- slow dynamics evolve gradually

---

## 12. Summary

The ARVIS core system is:
- a **discrete-time switched nonlinear system**
- with **two time scales**
- subject to **bounded disturbances**
- governed by a **mode-dependent Lyapunov function**

---

## 13. Next Step

The next document defines:
- regularity assumptions
- contraction properties
- bounds on disturbances
- Lipschitz conditions

→ see [`M1_assumptions.md`](M1_assumptions.md)