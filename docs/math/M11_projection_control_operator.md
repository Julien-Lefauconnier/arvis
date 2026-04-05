# M11 — Projection-Control Operator (Π_ctrl) and Decision-Theoretic Structure

## 1. Objective

This document introduces and formalizes the **projection-control operator**:

$$
\Pi_{\text{ctrl}}
$$

which acts as a structural safety operator in the ARVIS decision system.

It establishes:

- The formal decision space and ordering
- The definition of $\Pi_{\text{ctrl}}$
- Its interaction with the Gate operator $G$
- Its monotonicity and non-relaxation properties
- Its role in ensuring structural stability constraints **independent** of Lyapunov energy

This document completes the decision-theoretic layer of ARVIS.

## 2. Decision Space

We define the decision space as:

$$
V := \{\text{ALLOW}, \text{REQUIRE\_CONFIRMATION}, \text{ABSTAIN}\}
$$

equipped with a total preorder $\succ$ defined by:

$$
\text{ABSTAIN} \succ \text{REQUIRE\_CONFIRMATION} \succ \text{ALLOW}
$$

### 2.1 Interpretation

- **ALLOW** → unconstrained execution  
- **REQUIRE_CONFIRMATION** → constrained / delayed execution  
- **ABSTAIN** → execution forbidden

### 2.2 Induced Meet Operator

We define the decision fusion operator:

$$
\min_{\succ} : V \times V \to V
$$

as the **meet operator induced by the preorder $\succ$**, i.e. the most restrictive decision.

This defines $(V, \min_{\succ})$ as a **totally ordered meet-semilattice**.

## 3. Definition of the Projection-Control Operator

$$
\Pi_{\text{ctrl}} : \mathcal{X} \times \mathcal{Z} \times \mathcal{H} \to V
$$

where:
- $(x_t, z_t) \in \mathcal{X} \times \mathcal{Z}$ is the projected system state,
- $H_t \in \mathcal{H}$ is the contextual / historical signal.

We denote:

$$
v_t^\pi := \Pi_{\text{ctrl}}(x_t, z_t, H_t)
$$

### 3.1 Operational Role

$\Pi_{\text{ctrl}}$ evaluates **structural safety constraints** such as:

- Projection boundary proximity
- Domain validity margins
- Structural inconsistencies
- Projection-induced instability signals

**Important**: It is independent of Lyapunov energy variation.

It operates on **projection-derived signals**, not directly on the raw observation space.

## 4. Final Decision Composition

The ARVIS final decision is defined as:

$$
v_t^{\text{final}} = \min_{\succ}(v_t^{\text{gate}}, v_t^\pi)
$$

where:

$$
v_t^{\text{gate}} = G(W_t, \Delta W_t, \widehat{\kappa}_t, H_t, P_t)
$$

$$
v_t^\pi = \Pi_{\text{ctrl}}(x_t, z_t, H_t)
$$

where $P_t$ is the projection certificate (M3.3), indirectly influencing both operators.

## 5. Fundamental Properties of $\Pi_{\text{ctrl}}$

### 5.1 Monotonicity (Non-Relaxation)

For all admissible inputs:

$$
v_t^{\text{final}} = \min_{\succ}(v_t^{\text{gate}}, v_t^\pi) \preceq v_t^{\text{gate}}
$$

**Interpretation**: $\Pi_{\text{ctrl}}$ can only **restrict** a decision, never relax it.

This property follows directly from the definition of $\min_{\succ}$.

### 5.2 Absorption Property

$$
v_t^\pi = \text{ABSTAIN} \implies v_t^{\text{final}} = \text{ABSTAIN}
$$

**Interpretation**: Structural violations are **non-bypassable**.

This expresses that ABSTAIN is a **top element** of $(V, \succ)$.

### 5.3 Idempotence

$$
\min_{\succ}(v, v) = v
$$

Thus, if $v_t^{\text{final}}$ already incorporates $\Pi_{\text{ctrl}}$:

$$
\min_{\succ}(v_t^{\text{final}}, v_t^\pi) = v_t^{\text{final}}
$$

### 5.4 Commutativity

$$
\min_{\succ}(v_1, v_2) = \min_{\succ}(v_2, v_1)
$$

### 5.5 Associativity

$$
\min_{\succ}(v_1, \min_{\succ}(v_2, v_3)) = \min_{\succ}(\min_{\succ}(v_1, v_2), v_3)
$$

Thus, $(V, \min_{\succ})$ forms a **commutative idempotent semigroup**.

## 6. Structural Stability Layer

### 6.1 Dual Stability Decomposition

ARVIS stability is decomposed into two independent layers:

- **Energy stability** (Lyapunov-based) — controlled by $W_t$, $\Delta W_t$, $\widehat{\kappa}_t$
- **Structural stability** (projection-based) — enforced by $\Pi_{\text{ctrl}}$

### 6.2 Independence

$\Pi_{\text{ctrl}}$ does **not** depend on $\Delta W_t$ or $\widehat{\kappa}_t$.  
It captures **geometric and structural constraints** and complements the energy-based filtering.

More precisely:

$$
\Pi_{\text{ctrl}} \text{ does not directly depend on } W_t \text{ or } \widehat{\kappa}_t
$$

but may depend on signals derived from projection and validity diagnostics.

## 7. Compatibility with Gate Operator

### 7.1 No Relaxation Guarantee

$$
v_t^{\text{final}} \preceq v_t^{\text{gate}}
$$

### 7.2 Safety Preservation

If the Gate operator enforces constraints (C1–C7, M6), then:

$$
v_t^{\text{final}} = \min_{\succ}(v_t^{\text{gate}}, v_t^\pi)
$$

preserves all safety guarantees provided by the Gate.

This follows from monotonicity:

$$
v_t^{\text{final}} \preceq v_t^{\text{gate}}
$$


### 7.3 Strengthening Property

$\Pi_{\text{ctrl}}$ can only:
- preserve the Gate decision, or
- strengthen it toward more restrictive outcomes.

## 8. Non-Expansivity in Decision Space

We define the discrete metric on $V$:

$$
d(v_1, v_2) = 
\begin{cases}
0 & \text{if } v_1 = v_2 \\
1 & \text{otherwise}
\end{cases}
$$

Then:

$$
d(v_t^{\text{final}}, v_t^{\text{gate}}) \leq 1
$$

and more importantly:

$$
v_t \preceq v_t^{\text{gate}}
$$

which guarantees that the decision never expands toward less restrictive outcomes.

Note: the order-theoretic property is stronger than the metric bound.

## 9. Relation to Validity Envelope

$\Pi_{\text{ctrl}}$ consumes signals derived from the **Validity Envelope** $\mathcal{V}_t$, including:

- Projection availability
- Switching safety
- Kappa safety
- Exponential bound checks

It acts as the **structural interpreter** of $\mathcal{V}_t$.

This dependence is **indirect**, via runtime signals rather than direct functional dependence on $\mathcal{V}_t$.

## 10. Empirical Observability (Link to M10)

The operator $\Pi_{\text{ctrl}}$ is empirically characterized by:

$$
P(v_t^\pi), \quad P(v_t^\pi \prec v_t^{\text{gate}}), \quad P(v_t^{\text{final}} \prec v_t^{\text{gate}})
$$

as introduced in M10. This provides a measurable notion of structural filtering intensity.

## 11. Limitations

$\Pi_{\text{ctrl}}$ **does not**:

- Guarantee stability on its own
- Replace Lyapunov-based reasoning
- Define a continuous control law
- Provide formal invariance guarantees

It is a **discrete structural filter**.

It should not be interpreted as a continuous operator or a dynamical system.

## 12. Final Statement

The projection-control operator $\Pi_{\text{ctrl}}$ introduces a **structural stability layer** in ARVIS that is:

- Independent of energy dynamics
- Strictly monotone under the decision ordering
- Non-relaxing and absorbing
- Fully compatible with Gate filtering
- Empirically measurable

Together with the Gate operator, it forms a **dual-layer stability enforcement mechanism**:

- Energy-based filtering (Lyapunov)
- Structural filtering (projection-control)

This completes the formalization of the ARVIS decision system.

Formally, ARVIS decision-making can be viewed as a **lattice-based fusion system** combining:

$$
v_t^{\text{final}} = v_t^{\text{gate}} \wedge v_t^\pi
$$

where $\wedge := \min_{\succ}$.