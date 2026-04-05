# M12 — Decision Lattice & Stability Algebra

## 1. Objective

This document formalizes the algebraic structure of decision-making in ARVIS.

It establishes that:

- The decision space forms a **meet-semilattice**,
- The Gate operator $G$ and the projection-control operator $\Pi_{\text{ctrl}}$ are **monotone** operators,
- The full decision system defines a **stability algebra** over a partially ordered set.

This provides a structural and compositional foundation for decision stability that goes beyond classical Lyapunov analysis.

## 2. Decision Space as an Ordered Set

We define the decision space:

$$
\mathcal{V} := \{\text{ALLOW}, \text{REQUIRE\_CONFIRMATION}, \text{ABSTAIN}\}
$$

equipped with the total preorder:

$$
\text{ABSTAIN} \succ \text{REQUIRE\_CONFIRMATION} \succ \text{ALLOW}
$$

We induce the partial order $\preceq$ defined by:

$$
v_1 \preceq v_2 \iff v_2 \succeq v_1
$$

which gives the chain:

$$
\text{ALLOW} \preceq \text{REQUIRE\_CONFIRMATION} \preceq \text{ABSTAIN}
$$

## 3. Meet-Semilattice Structure

### 3.1 Definition

We define the binary meet operator:

$$
\wedge : \mathcal{V} \times \mathcal{V} \to \mathcal{V}, \quad
v_1 \wedge v_2 := \min_{\succ}(v_1, v_2)
$$

Then $(\mathcal{V}, \wedge)$ forms a **meet-semilattice**.

Moreover, since $\mathcal{V}$ is finite and totally ordered, it forms a **complete lattice**, 
where both meet ($\wedge$) and join ($\vee$) exist for all subsets.

### 3.2 Properties

For all $v_1, v_2, v_3 \in \mathcal{V}$:

- **Idempotence**: $v \wedge v = v$
- **Commutativity**: $v_1 \wedge v_2 = v_2 \wedge v_1$
- **Associativity**: $v_1 \wedge (v_2 \wedge v_3) = (v_1 \wedge v_2) \wedge v_3$
- **Absorption of top element**: $v \wedge \text{ABSTAIN} = \text{ABSTAIN}$

Consequently:
- **ABSTAIN** is the **top element** ($\top$),
- **ALLOW** is the **bottom element** ($\bot$).

Thus:

$$
\forall v \in \mathcal{V}, \quad v \wedge \top = \top, \quad v \wedge \bot = v
$$

## 4. Decision Operators as Endomorphisms

### 4.1 Gate Operator

$$
G : \mathcal{S} \times \mathcal{P} \to \mathcal{V}
$$

where $\mathcal{S}$ denotes the system state space.

Here $\mathcal{P}$ is the projection certificate space (M3.3).

### 4.2 Projection-Control Operator

$$
\Pi_{\text{ctrl}} : \mathcal{S} \to \mathcal{V}
$$

### 4.3 Lifted Operators

We define the evaluation mappings:

$$
\mathcal{G}(s, P_t) := G(s, P_t), \quad \mathcal{P}(s) := \Pi_{\text{ctrl}}(s)
$$

## 5. Monotonicity

### 5.1 Order Preservation

An operator $F$ is **monotone with respect to an ordered input space** if:

$$
x_1 \preceq_{\mathcal{S}} x_2 \implies F(x_1) \preceq F(x_2)
$$

In ARVIS:
- $\mathcal{G}$ is monotone with respect to an order on $\mathcal{S}$ induced by increasing instability signals,
- $\mathcal{P}$ is monotone with respect to an order on $\mathcal{S}$ induced by increasing structural risk.

**Remark:**  
The ordering on $\mathcal{S}$ is **implicit and application-dependent** (e.g., increasing instability or risk).

### 5.2 Decision Monotonicity (Key Property)

For all states $s_t$:

$$
v_t^{\text{final}} = v_t^{\text{gate}} \wedge v_t^\pi
$$

implies:

$$
v_t^{\text{final}} \preceq v_t^{\text{gate}} \quad \text{and} \quad v_t^{\text{final}} \preceq v_t^\pi
$$

This follows from the definition of the meet operator.

## 6. Stability Algebra

We define the **ARVIS Stability Algebra** as:

$$
\mathcal{A} = (\mathcal{V}, \wedge, \mathcal{G}, \mathcal{P})
$$

composed of:
- The meet-semilattice $(\mathcal{V}, \wedge)$,
- Two monotone operators $G$ and $\Pi_{\text{ctrl}}$,
- The decision composition rule:

$$
v_t^{\text{final}} = \mathcal{G}(s_t, P_t) \wedge \mathcal{P}(s_t)
$$

This defines a **lattice-based decision fusion system**.

## 7. Closure and Safety Properties

### 7.1 Closure

For all inputs, $v_t^{\text{final}} \in \mathcal{V}$. The system is closed under composition.

### 7.2 Safety Monotonicity

Let $v^\star$ be any unsafe decision. If $v^\star \preceq v$, then:

$$
v^\star \wedge v = v^\star
$$

Thus, **unsafe decisions are absorbing** under the meet operation.

In particular:

$$
\text{ABSTAIN} \wedge v = \text{ABSTAIN}
$$

### 7.3 No Relaxation Theorem

For all states:

$$
v_t^{\text{final}} \preceq v_t^{\text{gate}}
$$

No operator in the system can produce a decision less restrictive than the one produced by the Gate.

This is a direct consequence of the meet-semilattice structure.

## 8. Dual Stability Interpretation

The algebra naturally decomposes decision-making into two orthogonal layers:

- **Energy-driven operator**: $G$ (Lyapunov-based)
- **Structure-driven operator**: $\Pi_{\text{ctrl}}$ (projection-based)

Their meet-composition $G \wedge \Pi_{\text{ctrl}}$ ensures that both families of constraints are enforced simultaneously, and neither can relax the other.

## 9. Compatibility with Closed-Loop Stability (M7–M11)

The stability algebra is consistent with previous results:
- Gate safety guarantees (M6) are preserved,
- Closed-loop negative feedback properties (M7) are respected,
- Empirical filtering behavior (M10) is structurally enforced.

It provides the **algebraic layer** underlying these properties.

## 10. Extension to Multi-Operator Systems

The semilattice structure naturally generalizes to any number of constraint layers:

$$
v_t^{\text{final}} = \bigwedge_{i=1}^n v_t^{(i)}
$$

where each $v_t^{(i)}$ encodes a distinct safety or validity constraint (Gate, Projection-control, Validity filters, etc.).

This generalization preserves:
- monotonicity,
- absorption of unsafe decisions,
- closure.

## 11. Limitations

The stability algebra:
- Does **not** by itself imply dynamical stability,
- Does **not** replace Lyapunov analysis,
- Is discrete and non-differentiable,
- Depends on the correctness of the underlying operators $G$ and $\Pi_{\text{ctrl}}$.

It should be interpreted as an **order-theoretic structure**, not a dynamical system.

## 12. Final Statement

The ARVIS decision system forms a **meet-semilattice-based stability algebra**, where:

- Decisions are strictly ordered by restrictiveness/safety,
- All operators are monotone,
- Composition is realized by the meet operation,
- Unsafe decisions are absorbing.

This algebraic structure guarantees that **no combination of decision layers can ever produce a less restrictive outcome** than any individual safety constraint.

It provides a rigorous compositional foundation for multi-layered safety in ARVIS, complementary to energy-based (Lyapunov) stability.

Formally, the decision process is a **monotone lattice fusion system**:

$$
v_t^{\text{final}} = \bigwedge_i v_t^{(i)}
$$

ensuring that safety constraints compose without contradiction or relaxation.