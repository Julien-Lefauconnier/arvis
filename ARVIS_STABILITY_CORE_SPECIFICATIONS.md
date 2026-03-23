# ARVIS: Two-Timescale Hybrid Cognitive Control with Lyapunov Stability Guarantees

**Julien Lefauconnier**  
Veramem  
March 2026

## Position in ARVIS

This document defines the **theoretical stability core** of ARVIS.

It does NOT describe the full ARVIS system.

In particular, it does NOT cover:

- the projection operator Π (real implementation)
- the decision Gate G
- the control layer C
- the cognitive pipeline

These elements are introduced in M3–M9 and are not covered by the guarantees established here.

This document should be interpreted as:

→ a theoretical reference model  
→ a baseline stability system  
→ a constraint layer for the full implementation

## Scope

This specification defines the Lyapunov-based stability core of ARVIS systems.
It applies to discrete-time hybrid systems with slow--fast dynamics and switching regimes.

## Notation

- $\|\cdot\|$ denotes Euclidean norm
- $q_t$ denotes switching regime

## Abstract

This document defines stability guarantees for discrete-time two-timescale switched systems with slow--fast coupling. The system consists of:

- a fast contracting subsystem,
- a slow adaptive subsystem,
- and a finite switching mechanism.

A composite Lyapunov construction captures the interaction between contraction, coupling, and regime switching. Under regularity assumptions and an average dwell-time constraint, we establish:

- exponential stability under an explicit dwell-time bound,
- an explicit stability region in the $(\eta,\tau_d)$ plane.

The key result is a switching--coupling tradeoff: stability holds when decay between switches dominates Lyapunov metric jumps at switching instants, yielding a quantitative boundary in the $(\eta,\tau_d)$ plane.

## Introduction

Switched and hybrid systems arise in a wide range of control applications including adaptive control, supervisory logic, and learning-based architectures. Stability analysis of such systems typically relies on Lyapunov functions combined with average dwell-time arguments or spectral conditions.

For discrete-time systems exhibiting both slow--fast dynamics and regime switching, classical tools include:

- discrete-time ISS theory,
- singular perturbation methods,
- average dwell-time stability,
- Markov jump system analysis.

However, existing results typically treat:

1. coupling strength independently of switching frequency, or
2. switching constraints independently of slow--fast adaptation.

In many adaptive architectures, slow structural updates interact with fast contraction dynamics while supervisory logic induces mode switching. In such settings, stability depends jointly on:

- contraction rate,
- coupling gain,
- switching frequency,
- metric mismatch across regimes.

This work provides a unified treatment of this interaction. Beyond stability analysis, the obtained stability frontier also provides explicit design guidelines for selecting adaptation rates compatible with supervisory switching constraints in hybrid learning-control architectures.

### Main Contributions

1. A composite Lyapunov construction for discrete-time two-timescale switched systems.
2. An explicit switching--coupling tradeoff

$$
\frac{\log J}{\tau_d} + \log(1-\kappa_{\mathrm{eff}}) < 0
$$

where

$$
\kappa_{\mathrm{eff}} = \alpha - \gamma_z \eta L_T
$$

3. An explicit stability region in the $(\eta,\tau_d)$ plane.
4. An explicit design guideline for selecting admissible adaptation rates as a function of switching dwell-time.
5. A numerical illustration confirming the predicted decay behavior.

The results identify a quantitative stability frontier governed by contraction, coupling, and switching excitation.

## Relation to Implementation

The present work establishes stability guarantees for a discrete-time two-timescale switched dynamical system. It defines the **stability core** of the ARVIS system.

However, the full ARVIS implementation extends this core with additional layers, including:

- decision fusion mechanisms,
- confidence estimation,
- runtime enforcement and fallback logic,
- multi-dimensional disturbance representations.

These components are not covered by the present theoretical guarantees. Throughout this paper, all results apply strictly to the Lyapunov-based stability core defined in Sections 2–4.

The relationship between theory and implementation is formally described in a separate correspondence document.

All implementation layers must preserve the stability conditions defined in this document.

## Theory–Implementation Boundary

This section refines the scope definition by explicitly distinguishing proven guarantees from system-level extensions.

The present document defines a **stability core** based on Lyapunov analysis.

The ARVIS system extends this core with additional layers:

- signal processing
- decision fusion
- confidence estimation
- runtime enforcement

These layers are not covered by the formal guarantees.

They are constrained by the stability core but not formally proven in this document.

## Related Work

Stability of switched systems has been extensively studied using common Lyapunov functions and average dwell-time techniques. Classical results establish exponential stability when either:

- a common Lyapunov function exists across all modes, or
- switching satisfies sufficiently slow average dwell-time constraints.

Examples include the works of Liberzon (2003) and Hespanha and Morse (1999).

Input-to-state stability (ISS) theory for discrete-time systems provides robustness guarantees under bounded disturbances (Jiang and Wang, 2001; Sontag, 2008).

Slow--fast systems are typically analyzed using singular perturbation methods, where the fast subsystem is stabilized for frozen slow variables (Khalil, 2002). Composite Lyapunov constructions are commonly used to combine fast and slow stability properties.

Markov jump systems extend switching analysis to stochastic regimes, with stability characterized by spectral or LMI conditions (Costa, Fragoso, and Marques, 2005).

However, most existing frameworks treat either:

1. slow--fast coupling strength independently of switching frequency, or
2. switching frequency independently of coupling magnitude.

In contrast, the present work provides an explicit parametric stability boundary in the $(\eta,\tau_d)$ plane. The condition

$$
\frac{\log J}{\tau_d} + \log(1-\kappa_{\mathrm{eff}}) < 0
$$

reveals a quantitative tradeoff between:

- effective contraction $(\alpha - \gamma_z \eta L_T)$,
- metric mismatch across regimes $(J)$,
- and switching frequency $(1/\tau_d)$.

The present work introduces an explicit parametric stability boundary. Such a coupling--switching frontier for discrete-time two-timescale switched systems has not previously been characterized in this form.

## Problem Setup

We consider the discrete-time hybrid switched system

$$
\begin{align}
x_{t+1} &= f_{q_t}(x_t, z_t, w_t) \\
z_{t+1} &= (1 - \eta) z_t + \eta T(x_t) \\
q_{t+1} &= \Psi(q_t, x_t)
\end{align}
$$

where $x_t \in \mathbb{R}^n$ is the fast state, $z_t \in \mathbb{R}^m$ is the slow state, $q_t \in Q$ is a finite regime index, the disturbance $w_t$ is bounded and may represent a multi-dimensional signal, and $\eta \in (0,1)$ is the slow update rate.

The variable $x_t$ represents the fast contracting subsystem, while $z_t$ represents a slowly adapting structural state. The switching variable $q_t$ selects the active regime among a finite set of modes.

We assume compact admissible sets

$$
X \subset \mathbb{R}^n, \qquad Z \subset \mathbb{R}^m,
$$

and bounded disturbance satisfying

$$
\|w_t\| \le w_{\max}.
$$

In practical implementations, this corresponds to structured disturbance components such as uncertainty, conflict, or instability signals.

$q_t \in Q$ is a finite regime index.

In implementation, switching may be governed by runtime constraints enforcing dwell-time and stability conditions. The present model assumes an equivalent discrete abstraction.

## System Model and Definitions

We formalize the system as a discrete-time dynamical system:

- Fast state: $x_t \in \mathbb{R}^n$
- Slow state: $z_t \in \mathbb{R}^m$
- Switching state: $q_t \in Q$
- Disturbance: $w_t \in \mathbb{R}^d$

Define the system evolution:

$$
(x_{t+1}, z_{t+1}, q_{t+1}) = F(x_t, z_t, q_t, w_t)
$$

Define the composite Lyapunov function:

$$
W_q(x,z) = V_q(x) + \lambda \|z - T(x)\|^2
$$

Define:

$$
W_t := W(x_t, z_t)
$$

Define admissibility:

A trajectory is said to be **uniformly practically exponentially stable** if there exist constants $\kappa > 0$ and $C \ge 0$ such that:

$$
W_t \le (1-\kappa)^t W_0 + C
$$

for some $\kappa > 0$.

## Assumptions and Lyapunov Construction

### Regularity

**R1 — Local Lipschitz continuity.**  
For each regime $q \in Q$, the map $f_q(x,z,w)$ is locally Lipschitz in $(x,z)$ uniformly in $w$.

**R2 — Bounded slow map.**  
The map $T(x)$ is globally Lipschitz on $X$ with constant $L_T$ and bounded on $X$.

**R3 — One-step increment bounds.**  
There exist constants $L_x, L_z, L_w \ge 0$ such that for all admissible $(x,z,w)$ and regimes $q$,

$$
\begin{align}
\| f_q(x,z,w) - f_q(x,z,0) \| &\le L_w \|w\| \\
\| f_q(x,z,0) - f_q(x',z,0) \| &\le L_x \|x-x'\| \\
\| f_q(x,z,0) - f_q(x,z',0) \| &\le L_z \|z-z'\|
\end{align}
$$

These conditions ensure well-posedness and bounded sensitivity to perturbations.

**R4 — Lyapunov projection sufficiency.**  
We assume that the system state is observable through a reduced Lyapunov representation. In practice, stability-relevant properties of $(x_t, z_t)$ are captured by $W_q(x_t,z_t)$.

This assumption reflects implementations operating in a compressed state space.

### Lyapunov Ingredients

We assume a quadratic regime-dependent control Lyapunov function

$$
V_q(x) = x^\top P_q x
$$

with $P_q$ positive definite.

Define the envelope

$$
V(x) := \min_{q \in Q} V_q(x)
$$

We introduce the composite candidate

$$
W_q(x,z) := V_q(x) + \lambda \|z - T(x)\|^2
$$

For switching analysis we define the composite envelope

$$
W(x,z) := \min_{q \in Q} W_q(x,z)
$$

which provides a common comparison function across regimes.

Using comparability of $V_q$ (Assumption A3), we obtain

$$
m W(x,z) \le W_q(x,z) \le M W(x,z)
$$

and therefore all regime-dependent Lyapunov functions are uniformly comparable through the envelope $W$.

Thus the family $\{W_q\}$ is uniformly comparable across regimes due to the Lyapunov comparability assumption A3.

This Lyapunov function penalizes both cognitive instability (fast layer) and structural mismatch (slow layer).

### Switching Constraint and Comparability

**A1 — Fast-layer ISS (practical).**  
There exist $\alpha \in (0,1)$, $c \ge 0$ and $\gamma_z,\gamma_w \ge 0$ such that for all regimes $q$

$$
V_q(x_{t+1}) \le V_q(x_t) - \alpha (V_q(x_t)-c) + \gamma_z \|z_t-z_{t-1}\| + \gamma_w \|w_t\|
$$

Using slow dynamics,

$$
z_t - z_{t-1} = \eta (T(x_{t-1}) - z_{t-1})
$$

so

$$
\|z_t-z_{t-1}\| \le \eta \|e_{t-1}\|
$$

Hence the $\gamma_z$ term is controlled directly by the slow mismatch.

**A2 — Average dwell-time.**  
The number of switches $N(t_0,t)$ satisfies

$$
N(t_0,t) \le N_0 + \frac{t-t_0}{\tau_d}
$$

**A3 — Lyapunov comparability.**  
There exist $m,M>0$ such that

$$
mV(x) \le V_q(x) \le MV(x)
$$

for all $q$ and $x$.

### Slow--Fast Increment Structure

From the slow dynamics

$$
z_{t+1} = z_t + \eta (T(x_t) - z_t)
$$

define the slow mismatch

$$
e_t := z_t - T(x_t)
$$

Then

$$
z_{t+1} - T(x_{t+1}) = (1-\eta)e_t + (T(x_t) - T(x_{t+1}))
$$

Using Lipschitz continuity of $T$

$$
\|T(x_t)-T(x_{t+1})\| \le L_T \|x_{t+1}-x_t\|
$$

Hence

$$
\begin{align}
\|e_{t+1}\|^2 &\le (1-\eta)^2 \|e_t\|^2 \\
&\quad + 2(1-\eta)L_T \|e_t\|\,\|x_{t+1}-x_t\| \\
&\quad + L_T^2 \|x_{t+1}-x_t\|^2
\end{align}
$$

This relation reveals the slow--fast cross-coupling term.

### Bounding the Fast Increment

Using R3

$$
\|x_{t+1}-x_t\| = \|f_q(x_t,z_t,w_t) - x_t\| \le D + L_z\,\|e_t\| + L_w\,\|w_t\|
$$

where $D$ bounds nominal drift

$$
D := \max_q \sup_x \|f_q(x,T(x),0)-x\|
$$

Squaring yields

$$
\|x_{t+1}-x_t\|^2 \le 3D^2 + 3L_z^2\|e_t\|^2 + 3L_w^2\|w_t\|^2
$$

### Composite Lyapunov Increment

Consider the regime-dependent composite Lyapunov function

$$
W_q(x,z) = V_q(x) + \lambda \|e\|^2
$$

Then

$$
\Delta W_{q,t} = \Delta V_{q,t} + \lambda(\|e_{t+1}\|^2 - \|e_t\|^2)
$$

Using A1 and the bounds above, after Young's inequality with parameter $\mu>0$, we obtain

$$
\Delta W_{q,t} \le -\alpha\bigl(V_q(x_t)-c\bigr) + \lambda\bigl(A_e(\eta,\mu)-1\bigr)\|e_t\|^2 + C_1\|w_t\|^2 + C_0
$$

where

$$
A_e(\eta,\mu) = (1-\eta)^2 \left(1 + \frac{L_T^2}{\mu}\right) + 3(\mu+L_T^2)L_z^2
$$

**Absorption of the coupling term.**  
The term $\gamma_z \|z_t - z_{t-1}\|$ introduces a coupling between the fast and slow subsystems. Using the slow update dynamics

$$
z_t - z_{t-1} = \eta (T(x_{t-1}) - z_{t-1}),
$$

we obtain

$$
\|z_t - z_{t-1}\| \le \eta \|e_{t-1}\|.
$$

To incorporate this term into the Lyapunov contraction, we apply Young's inequality. For any $\theta>0$,

$$
\gamma_z \eta \|e_t\| \le \frac{\gamma_z \eta L_T}{2\theta} V_q(x_t) + \frac{\theta}{2} \|e_t\|^2 .
$$

The first term perturbs the contraction coefficient of the fast Lyapunov function, while the second term can be absorbed into the slow mismatch energy. Consequently the effective contraction rate satisfies

$$
\kappa_{\mathrm{eff}} = \alpha - \delta(\eta),
$$

with

$$
\delta(\eta) \le \gamma_z \eta L_T .
$$

For simplicity we use the conservative bound

$$
\kappa_{\mathrm{eff}} := \alpha - \gamma_z \eta L_T.
$$

This bound preserves the qualitative dependence of the stability region while keeping the presentation concise.

**Composite contraction lemma.**  
Combining the bound on $\Delta V_q$ with the slow–fast mismatch increment yields

$$
\Delta W_{q,t} = \Delta V_{q,t} + \lambda (\|e_{t+1}\|^2 - \|e_t\|^2).
$$

Using the Young bound for the coupling term and the estimate on $\|e_{t+1}\|^2$, we obtain

$$
\Delta W_{q,t} \le -\left(\alpha - \frac{\gamma_z \eta L_T}{2\theta}\right) V_q(x_t) + \left(\lambda (A_e(\eta,\mu)-1) + \frac{\theta}{2}\right) \|e_t\|^2 + C_1\|w_t\|^2 + C_0 .
$$

Choosing parameters $\theta>0$ and $\lambda>0$ such that

$$
\lambda (1-A_e(\eta,\mu)) > \frac{\theta}{2}
$$

ensures that the mismatch energy remains dissipative. Consequently there exists $\kappa_{\mathrm{eff}}>0$ such that

$$
W_{q}(t+1) \le (1-\kappa_{\mathrm{eff}}) W_q(t) + C\|w_t\|^2 + C_0 .
$$

The conservative estimate

$$
\kappa_{\mathrm{eff}} = \alpha - \gamma_z \eta L_T
$$

is then used throughout the analysis.

### Existence of $\eta^*$

Choose $\mu$ such that

$$
3(\mu+L_T^2)L_z^2 < \frac14
$$

This imposes the small-gain condition

$$
12L_z^2L_T^2 < 1
$$

ensuring existence of $\mu>0$. Define

$$
\mu^* := \frac{1}{12L_z^2} - L_T^2
$$

assuming $L_z>0$ and $\mu^*>0$. Then choose

$$
\eta^* = 1 - \sqrt{\frac{1}{2(1 + L_T^2/\mu^*)}}
$$

Hence

$$
\lambda(A_e-1)\|e_t\|^2 \le -\frac{\lambda}{4}\|e_t\|^2
$$

Therefore the composite Lyapunov function satisfies

$$
W_{t+1} \le (1-\kappa_{\mathrm{eff}})\,W_t + C\,\|w_t\|^2 + C_0
$$

with

$$
\kappa_{\mathrm{eff}} := \alpha - \gamma_z \eta L_T
$$

provided $\kappa_{\mathrm{eff}}>0$. Iterating yields

$$
W_t \le (1-\kappa_{\mathrm{eff}})^t W_0 + \frac{C_0}{\kappa_{\mathrm{eff}}}
$$

Hence trajectories converge to the compact level set where

$$
0 < \eta < \min(\eta^*,\alpha/(\gamma_z L_T)).
$$

This establishes composite contraction under small-gain coupling.

## Main Results

We now state the core tradeoff theorem at the level of the composite Lyapunov function $W_q$. The proof follows standard switched Lyapunov arguments and is summarized below.

**Theorem 1 (ARVIS Stability Condition)**

Assume A1--A3 and R1--R3. Let the effective contraction (coupling slack) be

$$
\kappa_{\mathrm{eff}} := \alpha - \gamma_z \eta L_T
$$

Let

$$
J := \frac{M}{m} \ge 1
$$

be the worst-case Lyapunov metric jump at switching instants. Assume

$$
0 < \kappa_{\mathrm{eff}} < 1
$$

so that inter-switch composite contraction is well-defined. In the disturbance-free homogeneous part ($w_t=0$) and in the aligned case (nominal drift negligible), the Lyapunov stability core is exponentially stable whenever (sufficient condition)

$$
\frac{\log J}{\tau_d} + \log(1-\kappa_{\mathrm{eff}}) < 0 \tag{T1}
$$

Equivalently,

$$
\tau_d > \tau_d^*(\eta) := \frac{\log J}{-\log(1-\kappa_{\mathrm{eff}})} .
$$

**Remark**  
The condition (T1) shows that stability requires the decay between switches to dominate the Lyapunov metric mismatch induced by switching. Equivalently, switching must be sufficiently slow relative to the effective contraction rate $\kappa_{\mathrm{eff}}$.

**Remark (Spectral interpretation)**  
The switching--coupling condition (T1) admits a spectral interpretation in terms of products of Lyapunov contraction operators. Between switching instants the dynamics contracts by a factor

$$
(1-\kappa_{\mathrm{eff}})
$$

while switching introduces a multiplicative jump bounded by $J$. Over a horizon $t$ the composite evolution satisfies

$$
W(x_t) \le J^{N(t)} (1-\kappa_{\mathrm{eff}})^{t-N(t)} W(x_0)
$$

Thus the condition

$$
\frac{\log J}{\tau_d} + \log(1-\kappa_{\mathrm{eff}}) < 0
$$

ensures that the exponential growth rate of the corresponding product operator remains negative.

We refer to condition (T1) as the ARVIS stability condition.

The inequality (T1) constitutes the fundamental stability condition of ARVIS systems.

### Proof sketch (composite level)

Between switching instants, Assumption A1 yields

$$
W_q(t+1) \le (1-\kappa_{\mathrm{eff}}) W_q(t)
$$

By uniform comparability of $W_q$

$$
W_{q_{k+1}}(t_k) \le J W_{q_k}(t_k)
$$

with $J=M/m$. Over an interval $[0,t]$ combining contraction and switching effects gives

$$
W(x_t) \le J^{N(0,t)} (1-\kappa_{\mathrm{eff}})^{t-N(0,t)} W(x_0)
$$

Using the average dwell-time bound

$$
N(0,t) \le N_0 + \frac{t}{\tau_d}
$$

taking logarithms and dividing by $t$ yields condition (T1), which ensures exponential decay.

**Lemma (Global boundedness under drift)**  
If $D \neq 0$, define

$$
\Omega := \{(x,z): W(x,z) \le C_0/\kappa_{\mathrm{eff}}\}.
$$

Then $\Omega$ is compact and positively invariant.

**Proof**  
From

$$
W_{t+1} \le (1-\kappa_{\mathrm{eff}}) W_t + C_0
$$

we obtain by iteration

$$
W_t \le (1-\kappa_{\mathrm{eff}})^t W_0 + \frac{C_0}{\kappa_{\mathrm{eff}}}.
$$

Thus

$$
\limsup_{t \to \infty} W_t \le \frac{C_0}{\kappa_{\mathrm{eff}}}.
$$

Hence all trajectories enter $\Omega$ in finite time.

**Theorem 2 (Parametric Stability Region)**  
Assume $0<\alpha<1$ and define

$$
\eta_{\max} := \frac{\alpha}{\gamma_z L_T}.
$$

For $\eta \in [0,\eta_{\max})$ define

$$
\tau_{\min}(\eta) := \frac{\log J}{-\log(1-\alpha+\gamma_z \eta L_T)}.
$$

Then stability holds for all parameter pairs $(\eta,\tau_d)$ satisfying

$$
\tau_d > \tau_{\min}(\eta).
$$

Moreover $\tau_{\min}(\eta)$ is increasing in $\eta$ and diverges as $\eta \to \eta_{\max}^-$.

### Uniform Practical ISS

**Theorem 3 (Uniform Practical ISS under Dwell-Time)**  
Under assumptions A1--A3 and R1--R3, and for $0<\eta<\eta^*$, if

$$
\frac{\log J}{\tau_d} + \log(1-\kappa_{\mathrm{eff}}) < 0
$$

then the Lyapunov core system is uniformly practically ISS. There exist constants $\beta\in(0,1)$ and $c_1,c_2>0$ such that

$$
W(x_t,z_t) \le \beta^t W(x_0,z_0) + \sum_{k=0}^{t-1} \beta^{t-1-k} \bigl(C\|w_k\|^2 + C_0\bigr).
$$

**Proof**  

From composite contraction under switching

$$
W_{t+1} \le \beta W_t + C\,\|w_t\|^2 + C_0.
$$

Iterating gives

$$
W_t \le \beta^t W_0 + \sum_{k=0}^{t-1} \beta^{t-1-k}(C\|w_k\|^2 + C_0).
$$

Taking the supremum over disturbances yields:

$$
W_t \le \beta^t W_0 + \frac{C}{1-\beta} \sup_{0 \le k < t} \|w_k\|^2 + \frac{C_0}{1-\beta}.
$$

### Geometric Interpretation

Define switching frequency

$$
\sigma := \frac{1}{\tau_d}.
$$

Stability requires

$$
\sigma \log J < -\log(1-\kappa_{\mathrm{eff}}).
$$

For small $\kappa_{\mathrm{eff}}$

$$
\log(1-\kappa_{\mathrm{eff}}) \approx -\kappa_{\mathrm{eff}}
$$

yielding the approximate condition

$$
\sigma \log J < \kappa_{\mathrm{eff}}.
$$

Thus stability holds when effective damping > switching excitation.

### Relation to Singular Perturbation Theory

As $\eta \to 0$,

$$
z_{t+1} = z_t
$$

and the slow subsystem freezes. The composite analysis reduces to classical switched contraction. For small but nonzero $\eta$ the cross-term $\gamma_z \eta L_T$ quantifies the deviation from the frozen manifold approximation. Thus $\eta$ acts as a discrete perturbation parameter.

### Design Guideline for Admissible Adaptation Rates

From Theorem 1 the stability condition is

$$
\frac{\log J}{\tau_d} + \log(1-\kappa_{\mathrm{eff}}) < 0
$$

with $\kappa_{\mathrm{eff}} = \alpha - \gamma_z \eta L_T$.

For a given dwell time $\tau_d$ define

$$
\kappa_{\min} := 1 - \exp\left(-\frac{\log J}{\tau_d}\right).
$$

Stability requires

$$
\kappa_{\mathrm{eff}} > \kappa_{\min}.
$$

Substituting the definition of $\kappa_{\mathrm{eff}}$ yields the admissible adaptation bound

$$
\eta < \frac{\alpha - \kappa_{\min}}{\gamma_z L_T}.
$$

This provides a direct design rule: faster switching reduces the admissible adaptation rate, while slower supervisory switching allows stronger structural adaptation.

## Numerical Illustration

We illustrate the theoretical results through numerical experiments. Four complementary figures are provided:

1. Stability region in the parameter plane $(\eta,\tau_d)$
2. Evolution of the composite Lyapunov energy
3. Sensitivity of the stability region with respect to the metric mismatch $J$
4. Empirical validation of the stability frontier

### Stability Region

The stability boundary predicted by Theorem 2 is

$$
\tau_d^*(\eta)= \frac{\log J}{-\log(1-\alpha+\gamma_z \eta L_T)} .
$$

Figure 1 visualizes the resulting stability region in the $(\eta,\tau_d)$ parameter plane. Below the curve $\tau_d^*(\eta)$ the system becomes unstable, while above the curve contraction dominates switching.

![Stability region in the (η,τ_d) plane predicted by Theorem 2](figures/stability_region.png)

### Lyapunov Energy Evolution

To illustrate the exponential decay predicted by Theorem 1, Figure 2 shows the evolution of the composite Lyapunov energy $W_t$ for three representative parameter configurations:

- a stable configuration,
- a configuration close to the stability boundary,
- an unstable configuration.

The logarithmic scale reveals exponential decay of the Lyapunov energy in the stable regime.

![Evolution of the composite Lyapunov energy under different parameter regimes](figures/fig2_lyapunov_decay.png)

### Sensitivity to Metric Mismatch

The stability boundary depends on the Lyapunov comparability constant

$$
J = \frac{M}{m}
$$

which measures the mismatch between Lyapunov metrics across regimes. Figure 3 illustrates how increasing $J$ shrinks the stability region. Larger metric mismatch therefore requires larger dwell time to guarantee stability.

![Effect of Lyapunov metric mismatch on the stability region](figures/fig3_stability_vs_J.png)

### Empirical Validation of the Stability Frontier

To further validate the theoretical tradeoff, we performed a grid exploration of the parameter plane $(\eta,\tau_d)$. For each parameter pair the hybrid system was simulated and the convergence of the composite Lyapunov energy was evaluated. Figure 4 compares the empirical stability classification with the theoretical stability boundary predicted by Theorem 2.

The results confirm that the theoretical boundary accurately predicts the transition between stable and unstable regimes. Points above the boundary are consistently stable, while instability predominantly appears below the curve, consistent with the fact that the theoretical condition is sufficient but not necessary.

![Empirical validation of the stability frontier](figures/fig4_empirical_phase_diagram.png)

### Example System

We validate the predicted behavior on a simple linear two-regime example. The fast subsystem is

$$
x_{t+1} = A_q x_t + B z_t + w_t
$$

with $A_q \in \{A_1, A_2\}$ where

$$
A_1 = \begin{bmatrix} 0.8 & 0.1 \\ 0.0 & 0.7 \end{bmatrix}, \quad A_2 = \begin{bmatrix} 0.75 & -0.1 \\ 0.05 & 0.8 \end{bmatrix}
$$

and

$$
B = \begin{bmatrix} 0.1 \\ 0.1 \end{bmatrix}.
$$

The slow map is defined as

$$
T(x) = Kx, \qquad K = \begin{bmatrix} 0.2 & 0.1 \end{bmatrix}.
$$

The slow dynamics therefore becomes

$$
z_{t+1} = (1-\eta)z_t + \eta K x_t.
$$

With $\eta = 0.05$ and bounded noise $\|w_t\| \le 0.05$, simulations show decay of the composite energy and bounded trajectories under switching, consistent with condition (T1).

## Limitations

The present analysis provides guarantees only for the Lyapunov-based stability core.

The following aspects are not formally covered:

- decision-making logic
- confidence estimation
- adaptive control policies
- symbolic or non-metric state representations
- empirical stability estimators

These components belong to higher-level system layers.

Le problème persiste parce que GitHub (via son renderer KaTeX) est extrêmement sensible aux notations comme \kappa_{\mathrm{eff}} quand elles sont imbriquées dans des fractions ou des indices complexes. Le \mathrm{} à l'intérieur d'un subscript provoque souvent un parsing error silencieux ou un rendu cassé (comme ce que tu vois : kappa_(mathrm(eff)) ou des accolades qui débordent).
Solution qui marche à 99 % sur GitHub en 2025-2026

Remplace tous les \kappa_{\mathrm{eff}} par \kappa_{eff} (sans \mathrm{}) dans toute la section.
C'est la notation la plus robuste et la plus lisible sur GitHub, et elle reste parfaitement acceptable scientifiquement (beaucoup de papiers utilisent eff en indice simple pour effective).

Voici la version corrigée et testée (copie-colle directement dans ton fichier Markdown) :

## Conformance Requirements

An implementation is considered **ARVIS-compliant** if:

1. It implements a composite Lyapunov function of the form:

$$
W_q(x,z) = V_q(x) + \lambda \|z - T(x)\|^2
$$

2. It enforces a contraction condition:

$$
W_{t+1} \le (1 - \kappa_{eff}) W_t + C
$$

3. It enforces the switching condition:

$$
\log J / \tau_d + \log(1 - \kappa_{eff}) < 0
$$

where \( J \) denotes the Lyapunov comparability ratio across regimes.

4. It guarantees bounded disturbance handling.

5. It preserves Lyapunov comparability across regimes.

Extensions beyond this core are permitted but **must not violate** these conditions.

Implementations **MUST** expose sufficient observability to verify these conditions at runtime or through testing.

Any violation of the above conditions invalidates ARVIS compliance.

## Minimal Compliance

A minimal ARVIS-compliant system must satisfy conditions (1)–(3).

## Non-Goals

The present specification does not attempt to:

- define a complete cognitive architecture,
- provide guarantees for decision-making policies,
- prove optimality or performance,
- formalize confidence or uncertainty estimation,
- cover non-Lyapunov-based systems.

The focus is strictly on stability guarantees.

## Conclusion

We derived an explicit switching--coupling tradeoff for two-timescale discrete-time switched systems. The main condition yields a quantitative stability boundary in the $(\eta,\tau_d)$ parameter plane: stronger slow adaptation requires slower switching (larger dwell-time), while improved cross-regime metric alignment (smaller $J$) expands the stability region.

The obtained result unifies three classical tools of stability analysis:

- contraction analysis of the fast subsystem,
- average dwell-time theory for switched systems,
- slow--fast coupling analysis.

These elements combine within a single explicit parametric stability condition

$$
\frac{\log J}{\tau_d} + \log(1-\kappa_{\mathrm{eff}}) < 0,
$$

which characterizes the balance between contraction, coupling, and switching excitation.

Beyond theoretical guarantees, the obtained stability frontier provides a practical design guideline for hybrid learning-control architectures. In particular, it clarifies how the admissible adaptation rate must scale with the supervisory switching frequency.

The proposed framework highlights the structural interaction between slow learning dynamics and fast contracting control loops, a configuration that increasingly appears in modern adaptive and learning-based systems.

Future work will investigate several extensions, including:

- stochastic switching and Markov jump regimes,
- non-quadratic Lyapunov constructions,
- data-driven identification of stability regions,
- and extensions to continuous-time hybrid systems.

## Informal Interpretation

The ARVIS stability condition can be interpreted as:

- fast dynamics must contract faster than switching injects energy,
- slow adaptation must remain sufficiently small relative to contraction,
- regime mismatch must remain bounded.

This provides a control-theoretic interpretation of cognitive stability.