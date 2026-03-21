\title{ARVIS: Two-Timescale Hybrid Cognitive Control with Lyapunov Stability Guarantees}

\author{
Julien Lefauconnier \\
Veramem
}

\date{2026}

\maketitle


\begin{abstract}

This paper studies stability of discrete-time two-timescale switched systems
with slow--fast coupling. The system consists of:

\begin{itemize}
\item a fast contracting subsystem,
\item a slow adaptive subsystem,
\item and a finite switching mechanism.
\end{itemize}

A composite Lyapunov construction captures the interaction between contraction,
coupling, and regime switching. Under regularity assumptions and an average
dwell-time constraint, we establish:

\begin{itemize}
\item exponential stability under an explicit dwell-time bound,
\item an explicit stability region in the $(\eta,\tau_d)$ plane.
\end{itemize}

The key result is a switching--coupling tradeoff: stability holds when decay
between switches dominates Lyapunov metric jumps at switching instants,
yielding a quantitative boundary in the $(\eta,\tau_d)$ plane.

\end{abstract}

------------------------------------------------------------------------

\section{Introduction}

Switched and hybrid systems arise in a wide range of control
applications including adaptive control, supervisory logic,
and learning-based architectures. Stability analysis of such
systems typically relies on Lyapunov functions combined with
average dwell-time arguments or spectral conditions.

For discrete-time systems exhibiting both slow--fast dynamics
and regime switching, classical tools include:

\begin{itemize}
\item discrete-time ISS theory,
\item singular perturbation methods,
\item average dwell-time stability,
\item Markov jump system analysis.
\end{itemize}

However, existing results typically treat

\begin{enumerate}
\item coupling strength independently of switching frequency, or
\item switching constraints independently of slow--fast adaptation.
\end{enumerate}

In many adaptive architectures, slow structural updates interact
with fast contraction dynamics while supervisory logic induces
mode switching. In such settings, stability depends jointly on

\begin{itemize}
\item contraction rate,
\item coupling gain,
\item switching frequency,
\item metric mismatch across regimes.
\end{itemize}

This paper provides a unified treatment of this interaction.

Beyond stability analysis, the obtained stability frontier
also provides explicit design guidelines for selecting
adaptation rates compatible with supervisory switching
constraints in hybrid learning-control architectures.

The main contributions are:

\begin{enumerate}

\item A composite Lyapunov construction for discrete-time
two-timescale switched systems.

\item An explicit switching--coupling tradeoff

\begin{equation}
\frac{\log J}{\tau_d} + \log(1-\kappa_{\mathrm{eff}}) < 0
\end{equation}

where

\begin{equation}
\kappa_{\mathrm{eff}} = \alpha - \gamma_z \eta L_T
\end{equation}

\item An explicit stability region in the $(\eta,\tau_d)$ plane.

\item An explicit design guideline for selecting admissible
adaptation rates as a function of switching dwell-time.

\item A numerical illustration confirming the predicted
decay behavior.

\end{enumerate}

The results identify a quantitative stability frontier governed
by contraction, coupling, and switching excitation.

------------------------------------------------------------------------

\subsection{Related Work}

Stability of switched systems has been extensively studied using
common Lyapunov functions and average dwell-time techniques.
Classical results establish exponential stability when either

\begin{itemize}
\item a common Lyapunov function exists across all modes, or
\item switching satisfies sufficiently slow average dwell-time
constraints.
\end{itemize}

Examples include the works of Liberzon (2003) and
Hespanha and Morse (1999).

Input-to-state stability (ISS) theory for discrete-time systems
provides robustness guarantees under bounded disturbances
(Jiang and Wang, 2001; Sontag, 2008).

Slow--fast systems are typically analyzed using singular
perturbation methods, where the fast subsystem is stabilized
for frozen slow variables (Khalil, 2002). Composite Lyapunov
constructions are commonly used to combine fast and slow
stability properties.

Markov jump systems extend switching analysis to stochastic
regimes, with stability characterized by spectral or LMI
conditions (Costa, Fragoso, and Marques, 2005).

However, most existing frameworks treat either

\begin{enumerate}
\item slow--fast coupling strength independently of switching frequency, or
\item switching frequency independently of coupling magnitude.
\end{enumerate}

In contrast, the present work provides an explicit parametric
stability boundary in the $(\eta,\tau_d)$ plane. The condition

\begin{equation}
\frac{\log J}{\tau_d} + \log(1-\kappa_{\mathrm{eff}}) < 0
\end{equation}

reveals a quantitative tradeoff between

\begin{itemize}
\item effective contraction $(\alpha - \gamma_z \eta L_T)$,
\item metric mismatch across regimes $(J)$,
\item and switching frequency $(1/\tau_d)$.
\end{itemize}

To the best of our knowledge, such an explicit coupling--switching
frontier for discrete-time two-timescale switched systems has
not previously been characterized in this form.

------------------------------------------------------------------------

\section{Problem Setup}

We consider the discrete-time hybrid switched system

\begin{align}
x_{t+1} &= f_{q_t}(x_t, z_t, w_t) \\
z_{t+1} &= (1 - \eta) z_t + \eta T(x_t) \\
q_{t+1} &= \Psi(q_t, x_t)
\end{align}

where $x_t \in \mathbb{R}^n$ is the fast state,
$z_t \in \mathbb{R}^m$ is the slow state,
$q_t \in Q$ is a finite regime index,
$w_t$ is a bounded disturbance,
and $\eta \in (0,1)$ is the slow update rate.

The variable $x_t$ represents the fast contracting subsystem,
while $z_t$ represents a slowly adapting structural state.
The switching variable $q_t$ selects the active regime
among a finite set of modes.

We assume compact admissible sets

\[
X \subset \mathbb{R}^n,
\qquad
Z \subset \mathbb{R}^m,
\]

and bounded disturbance satisfying

\begin{equation}
\|w_t\| \le w_{\max}.
\end{equation}

------------------------------------------------------------------------

\section{Assumptions and Lyapunov Construction}

\subsection{Regularity}

\paragraph{R1 --- Local Lipschitz continuity.}
For each regime $q \in Q$, the map $f_q(x,z,w)$ is locally Lipschitz
in $(x,z)$ uniformly in $w$.

\paragraph{R2 --- Bounded slow map.}
The map $T(x)$ is globally Lipschitz on $X$ with constant $L_T$
and bounded on $X$.

\paragraph{R3 --- One-step increment bounds.}
There exist constants $L_x, L_z, L_w \ge 0$ such that for all
admissible $(x,z,w)$ and regimes $q$,

\begin{equation}
\| f_q(x,z,w) - f_q(x,z,0) \| \le L_w \|w\|
\end{equation}

\begin{equation}
\| f_q(x,z,0) - f_q(x',z,0) \| \le L_x \|x-x'\|
\end{equation}

\begin{equation}
\| f_q(x,z,0) - f_q(x,z',0) \| \le L_z \|z-z'\|
\end{equation}

These conditions ensure well-posedness and bounded sensitivity
to perturbations.

---

\subsection{Lyapunov Ingredients}

We assume a quadratic regime-dependent control Lyapunov function

\begin{equation}
V_q(x) = x^\top P_q x
\end{equation}

with $P_q$ positive definite.

Define the envelope

\begin{equation}
V(x) := \min_{q \in Q} V_q(x)
\end{equation}

We introduce the composite candidate

\begin{equation}
W_q(x,z) := V_q(x) + \lambda \|z - T(x)\|^2
\end{equation}

For switching analysis we define the composite envelope

\begin{equation}
W(x,z) := \min_{q \in Q} W_q(x,z)
\end{equation}

which provides a common comparison function across regimes.

Using comparability of $V_q$ (Assumption A3), we obtain

\begin{equation}
m W(x,z) \le W_q(x,z) \le M W(x,z)
\end{equation}

and therefore all regime-dependent Lyapunov functions are
uniformly comparable through the envelope $W$.

Thus the family $\{W_q\}$ is uniformly comparable across regimes
due to the Lyapunov comparability assumption A3.

This function penalizes both cognitive instability
(fast layer) and structural mismatch (slow layer).

---

\subsection{Switching Constraint and Comparability}

\paragraph{A1 --- Fast-layer ISS (practical).}

There exist $\alpha \in (0,1)$, $c \ge 0$ and $\gamma_z,\gamma_w \ge 0$
such that for all regimes $q$

\begin{equation}
V_q(x_{t+1})
\le
V_q(x_t) - \alpha (V_q(x_t)-c)
+ \gamma_z \|z_t-z_{t-1}\|
+ \gamma_w \|w_t\|
\end{equation}

Using slow dynamics,

\begin{equation}
z_t - z_{t-1} = \eta (T(x_{t-1}) - z_{t-1})
\end{equation}

so

\begin{equation}
\|z_t-z_{t-1}\| \le \eta \|e_{t-1}\|
\end{equation}

Hence the $\gamma_z$ term is controlled directly
by the slow mismatch.

\paragraph{A2 --- Average dwell-time.}

The number of switches $N(t_0,t)$ satisfies

\begin{equation}
N(t_0,t) \le N_0 + \frac{t-t_0}{\tau_d}
\end{equation}

\paragraph{A3 --- Lyapunov comparability.}

There exist $m,M>0$ such that

\begin{equation}
mV(x) \le V_q(x) \le MV(x)
\end{equation}

for all $q$ and $x$.

---

\subsection{Slow--Fast Increment Structure}

From the slow dynamics

\begin{equation}
z_{t+1} = z_t + \eta (T(x_t) - z_t)
\end{equation}

define the slow mismatch

\begin{equation}
e_t := z_t - T(x_t)
\end{equation}

Then

 \begin{equation}
 z_{t+1} - T(x_{t+1}) =
 (1-\eta)e_t + (T(x_t) - T(x_{t+1}))
 \end{equation}

Using Lipschitz continuity of $T$

\begin{equation}
\|T(x_t)-T(x_{t+1})\|
\le
L_T \|x_{t+1}-x_t\|
\end{equation}

Hence

\begin{align}
\|e_{t+1}\|^2
&\le (1-\eta)^2 \|e_t\|^2 \\
&\quad + 2(1-\eta)L_T \|e_t\|\,\|x_{t+1}-x_t\| \\
&\quad + L_T^2 \|x_{t+1}-x_t\|^2
\end{align}

This relation reveals the slow--fast cross-coupling term.

---

\subsection{Bounding the Fast Increment}

Using R3

\begin{equation}
\|x_{t+1}-x_t\|=
\|f_q(x_t,z_t,w_t) - x_t\|
\le
D + L_z\,\|e_t\| + L_w\,\|w_t\|
\end{equation}

where $D$ bounds nominal drift

\begin{equation}
D := \max_q \sup_x \|f_q(x,T(x),0)-x\|
\end{equation}

Squaring yields

\begin{equation}
\|x_{t+1}-x_t\|^2
\le
3D^2 + 3L_z^2\|e_t\|^2 + 3L_w^2\|w_t\|^2
\end{equation}

---

\subsection{Composite Lyapunov Increment}

Consider the regime-dependent composite Lyapunov function

\begin{equation}
W_q(x,z) = V_q(x) + \lambda \|e\|^2
\end{equation}

Then

 \begin{equation}
 \Delta W_{q,t}=
 \Delta V_{q,t} + \lambda(\|e_{t+1}\|^2 - \|e_t\|^2)
 \end{equation}

Using A1 and the bounds above,
after Young's inequality with parameter $\mu>0$,
we obtain

\begin{equation}
\Delta W_{q,t}
\le
-\alpha\bigl(V_q(x_t)-c\bigr)
+
\lambda\bigl(A_e(\eta,\mu)-1\bigr)\|e_t\|^2
+
C_1\|w_t\|^2
+
C_0
\end{equation}

where

\begin{equation}
A_e(\eta,\mu)=
(1-\eta)^2
\left(1 + \frac{L_T^2}{\mu}\right)
 +
3(\mu+L_T^2)L_z^2
\end{equation}

\paragraph{Absorption of the coupling term.}

The term $\gamma_z \|z_t - z_{t-1}\|$ introduces a coupling
between the fast and slow subsystems. Using the slow update
dynamics

\[
z_t - z_{t-1} = \eta (T(x_{t-1}) - z_{t-1}),
\]

we obtain

\[
\|z_t - z_{t-1}\| \le \eta \|e_{t-1}\|.
\]

To incorporate this term into the Lyapunov contraction,
we apply Young's inequality. For any $\theta>0$,

\[
\gamma_z \eta \|e_t\|
\le
\frac{\gamma_z \eta L_T}{2\theta} V_q(x_t)
+
\frac{\theta}{2} \|e_t\|^2 .
\]

The first term perturbs the contraction coefficient
of the fast Lyapunov function, while the second term
can be absorbed into the slow mismatch energy.

Consequently the effective contraction rate satisfies

\[
\kappa_{\mathrm{eff}}=
\alpha - \delta(\eta),
\]

with

\[
\delta(\eta) \le \gamma_z \eta L_T .
\]

For simplicity we use the conservative bound

\[
\kappa_{\mathrm{eff}} := \alpha - \gamma_z \eta L_T.
\]

This bound preserves the qualitative dependence of the
stability region while keeping the presentation concise.

\paragraph{Composite contraction lemma.}

Combining the bound on $\Delta V_q$ with the slow–fast
mismatch increment yields

\[
\Delta W_{q,t}=
\Delta V_{q,t}
+
\lambda (\|e_{t+1}\|^2 - \|e_t\|^2).
\]

Using the Young bound for the coupling term
and the estimate on $\|e_{t+1}\|^2$, we obtain

\[
\Delta W_{q,t}
\le-
\left(\alpha - \frac{\gamma_z \eta L_T}{2\theta}\right)
V_q(x_t)
+
\left(
\lambda (A_e(\eta,\mu)-1) + \frac{\theta}{2}
\right)
\|e_t\|^2
+
C_1\|w_t\|^2
+
C_0 .
\]

Choosing parameters $\theta>0$ and $\lambda>0$ such that

\[
\lambda (1-A_e(\eta,\mu)) > \frac{\theta}{2}
\]

ensures that the mismatch energy remains dissipative.

Consequently there exists $\kappa_{\mathrm{eff}}>0$ such that

\[
W_{q}(t+1)
\le
(1-\kappa_{\mathrm{eff}}) W_q(t)
+
C\|w_t\|^2
+
C_0 .
\]

The conservative estimate

\[
\kappa_{\mathrm{eff}} =
\alpha - \gamma_z \eta L_T
\]

is then used throughout the analysis.

---

\subsection{Existence of $\eta^*$}

Choose $\mu$ such that

\begin{equation}
3(\mu+L_T^2)L_z^2 < \frac14
\end{equation}

This imposes the small-gain condition

\begin{equation}
12L_z^2L_T^2 < 1
\end{equation}

ensuring existence of $\mu>0$.

Define

\begin{equation}
\mu^* := \frac{1}{12L_z^2} - L_T^2
\end{equation}

assuming $L_z>0$ and $\mu^*>0$.

Then choose

\begin{equation}
\eta^* =
1 -
\sqrt{\frac{1}{2(1 + L_T^2/\mu^*)}}
\end{equation}

Hence

\begin{equation}
\lambda(A_e-1)\|e_t\|^2
\le
-\frac{\lambda}{4}\|e_t\|^2
\end{equation}

Therefore the composite Lyapunov function satisfies

\begin{equation}
W_{t+1}
\le
(1-\kappa_{\mathrm{eff}})\,W_t
+
C\,\|w_t\|^2
+
C_0
\end{equation}

with

\begin{equation}
\kappa_{\mathrm{eff}} := \alpha - \gamma_z \eta L_T
\end{equation}

provided $\kappa_{\mathrm{eff}}>0$.

Iterating yields

\begin{equation}
W_t
\le
(1-\kappa_{\mathrm{eff}})^t W_0
+
\frac{C_0}{\kappa_{\mathrm{eff}}}
\end{equation}

Hence trajectories converge to the compact level set where

\begin{equation}
0 < \eta < \min(\eta^*,\alpha/(\gamma_z L_T)).
\end{equation}

This establishes composite contraction under small-gain coupling.

------------------------------------------------------------------------

\section{Main Results}

We now state the core tradeoff theorem at the level of the composite
Lyapunov function $W_q$. The proof follows standard switched Lyapunov
arguments and is summarized below.

\begin{theorem}[Switching--Coupling Tradeoff]
Assume A1--A3 and R1--R3. Let the effective contraction
(coupling slack) be

\begin{equation}
\kappa_{\mathrm{eff}} := \alpha - \gamma_z \eta L_T
\end{equation}

Let

\[
J := \frac{M}{m} \ge 1
\]

be the worst-case Lyapunov metric jump at switching instants.

Assume

\begin{equation}
0 < \kappa_{\mathrm{eff}} < 1
\end{equation}

so that inter-switch composite contraction is well-defined.

In the disturbance-free homogeneous part ($w_t=0$)
and in the aligned case (nominal drift negligible),
exponential stability holds whenever

\begin{equation}
\frac{\log J}{\tau_d} + \log(1-\kappa_{\mathrm{eff}}) < 0
\tag{T1}
\end{equation}

Equivalently,

\begin{equation}
\tau_d > \tau_d^*(\eta)
:= \frac{\log J}{-\log(1-\kappa_{\mathrm{eff}})} .
\end{equation}

\end{theorem}

---

\begin{remark}
The condition (T1) shows that stability requires the decay
between switches to dominate the Lyapunov metric mismatch
induced by switching. Equivalently, switching must be sufficiently
slow relative to the effective contraction rate
$\kappa_{\mathrm{eff}}$.
\end{remark}

---

\begin{remark}[Spectral interpretation]

The switching--coupling condition (T1) admits a spectral
interpretation in terms of products of Lyapunov contraction
operators.

Between switching instants the dynamics contracts by a factor

\[
(1-\kappa_{\mathrm{eff}})
\]

while switching introduces a multiplicative jump bounded by $J$.

Over a horizon $t$ the composite evolution satisfies

\begin{equation}
W(x_t)
\le
J^{N(t)}
(1-\kappa_{\mathrm{eff}})^{t-N(t)}
W(x_0)
\end{equation}

Thus the condition

\begin{equation}
\frac{\log J}{\tau_d}
+
\log(1-\kappa_{\mathrm{eff}})
<
0
\end{equation}

ensures that the exponential growth rate of the corresponding
product operator remains negative.

\end{remark}

---

\subsection*{Proof sketch (composite level)}

Between switching instants, Assumption A1 yields

\begin{equation}
W_q(t+1)
\le
(1-\kappa_{\mathrm{eff}}) W_q(t)
\end{equation}

By uniform comparability of $W_q$

\begin{equation}
W_{q_{k+1}}(t_k)
\le
J W_{q_k}(t_k)
\end{equation}

with $J=M/m$.

Over an interval $[0,t]$ combining contraction
and switching effects gives

\begin{equation}
W(x_t)
\le
J^{N(0,t)}
(1-\kappa_{\mathrm{eff}})^{t-N(0,t)}
W(x_0)
\end{equation}

Using the average dwell-time bound

\begin{equation}
N(0,t) \le N_0 + \frac{t}{\tau_d}
\end{equation}

taking logarithms and dividing by $t$ yields condition (T1),
which ensures exponential decay.

---

\begin{lemma}[Global boundedness under drift]

If $D \neq 0$, define

\begin{equation}
\Omega
:=
\{(x,z): W(x,z) \le C_0/\kappa_{\mathrm{eff}}\}.
\end{equation}

Then $\Omega$ is compact and positively invariant.

\end{lemma}

\begin{proof}

From

\begin{equation}
W_{t+1}
\le
(1-\kappa_{\mathrm{eff}}) W_t
+
C_0
\end{equation}

we obtain by iteration

\begin{equation}
W_t
\le
(1-\kappa_{\mathrm{eff}})^t W_0
+
\frac{C_0}{\kappa_{\mathrm{eff}}}.
\end{equation}

Thus

\begin{equation}
\limsup_{t \to \infty} W_t
\le
\frac{C_0}{\kappa_{\mathrm{eff}}}.
\end{equation}

Hence all trajectories enter $\Omega$ in finite time.

\end{proof}

---

\begin{theorem}[Parametric Stability Region]

Assume $0<\alpha<1$ and define

\begin{equation}
\eta_{\max} := \frac{\alpha}{\gamma_z L_T}.
\end{equation}

For $\eta \in [0,\eta_{\max})$ define

\begin{equation}
\tau_{\min}(\eta)
:=
\frac{\log J}{-\log(1-\alpha+\gamma_z \eta L_T)}.
\end{equation}

Then stability holds for all parameter pairs $(\eta,\tau_d)$
satisfying

\begin{equation}
\tau_d > \tau_{\min}(\eta).
\end{equation}

Moreover $\tau_{\min}(\eta)$ is increasing in $\eta$
and diverges as $\eta \to \eta_{\max}^-$.

\end{theorem}

---

\subsection{Uniform Practical ISS}

\begin{theorem}[Uniform Practical ISS under Dwell-Time]

Under assumptions A1--A3 and R1--R3,
and for $0<\eta<\eta^*$,
if

\begin{equation}
\frac{\log J}{\tau_d} + \log(1-\kappa_{\mathrm{eff}}) < 0
\end{equation}

then the switched hybrid system is uniformly practically ISS.

There exist constants $\beta\in(0,1)$ and $c_1,c_2>0$ such that

\begin{equation}
W(x_t,z_t)
\le
\beta^t W(x_0,z_0)
+
\sum_{k=0}^{t-1}
\beta^{t-1-k}
\bigl(C\|w_k\|^2 + C_0\bigr).
\end{equation}

\end{theorem}

\begin{proof}

From composite contraction under switching

\begin{equation}
W_{t+1}
\le
\beta W_t + C\,\|w_t\|^2 + C_0.
\end{equation}

Iterating gives

\begin{equation}
W_t
\le
\beta^t W_0
+
\sum_{k=0}^{t-1}
\beta^{t-1-k}(C\|w_k\|^2 + C_0).
\end{equation}

Taking the supremum over disturbances yields

\begin{equation}
W_t
\le
\beta^t W_0
+
\frac{C}{1-\beta}
\sup_{0\le k<t}\|w_k\|^2
+
\frac{C_0}{1-\beta}.
\end{equation}

\end{proof}

---

\subsection{Geometric Interpretation}

Define switching frequency

\begin{equation}
\sigma := \frac{1}{\tau_d}.
\end{equation}

Stability requires

\begin{equation}
\sigma \log J
<
-\log(1-\kappa_{\mathrm{eff}}).
\end{equation}

For small $\kappa_{\mathrm{eff}}$

\begin{equation}
\log(1-\kappa_{\mathrm{eff}})
\approx
-\kappa_{\mathrm{eff}}
\end{equation}

yielding the approximate condition

\begin{equation}
\sigma \log J < \kappa_{\mathrm{eff}}.
\end{equation}

Thus stability holds when

\[
\text{effective damping} >
\text{switching excitation}.
\]

---

\subsection{Relation to Singular Perturbation Theory}

As $\eta \to 0$,

\[
z_{t+1} = z_t
\]

and the slow subsystem freezes.

The composite analysis reduces to classical switched contraction.

For small but nonzero $\eta$ the cross-term
$\gamma_z \eta L_T$
quantifies the deviation from the frozen manifold approximation.

Thus $\eta$ acts as a discrete perturbation parameter.

---

\subsection{Design Guideline for Admissible Adaptation Rates}

From Theorem 1 the stability condition is

\[
\frac{\log J}{\tau_d}
+
\log(1-\kappa_{\mathrm{eff}})
<
0
\]

with

\[
\kappa_{\mathrm{eff}} = \alpha - \gamma_z \eta L_T.
\]

For a given dwell time $\tau_d$ define

\begin{equation}
\kappa_{\min}
:=
1 -
\exp\left(-\frac{\log J}{\tau_d}\right).
\end{equation}

Stability requires

\[
\kappa_{\mathrm{eff}} > \kappa_{\min}.
\]

Substituting the definition of $\kappa_{\mathrm{eff}}$
yields the admissible adaptation bound

\begin{equation}
\eta
<
\frac{\alpha - \kappa_{\min}}
{\gamma_z L_T}.
\end{equation}

This provides a direct design rule:
faster switching reduces the admissible adaptation rate,
while slower supervisory switching allows stronger
structural adaptation.

------------------------------------------------------------------------

\section{Numerical Illustration}

We illustrate the theoretical results through numerical experiments.
Four complementary figures are provided:

\begin{enumerate}
\item Stability region in the parameter plane $(\eta,\tau_d)$
\item Evolution of the composite Lyapunov energy
\item Sensitivity of the stability region with respect to the metric mismatch $J$
\item Empirical validation of the stability frontier
\end{enumerate}

---

\subsection{Stability Region}

The stability boundary predicted by Theorem 2 is

\begin{equation}
\tau_d^*(\eta)=
\frac{\log J}
{-\log(1-\alpha+\gamma_z \eta L_T)} .
\end{equation}

Figure~\ref{fig:stability_region} visualizes the resulting
stability region in the $(\eta,\tau_d)$ parameter plane.

Below the curve $\tau_d^*(\eta)$ the system becomes unstable,
while above the curve contraction dominates switching.

\begin{figure}[t]
\centering
\includegraphics[width=0.7\linewidth]{figures/stability_region.png}
\caption{Stability region in the $(\eta,\tau_d)$ plane predicted by Theorem 2.}
\label{fig:stability_region}
\end{figure}

---

\subsection{Lyapunov Energy Evolution}

To illustrate the exponential decay predicted by Theorem 1,
Figure~\ref{fig:lyapunov_decay} shows the evolution of the
composite Lyapunov energy $W_t$ for three representative
parameter configurations:

\begin{itemize}
\item a stable configuration,
\item a configuration close to the stability boundary,
\item an unstable configuration.
\end{itemize}

The logarithmic scale reveals exponential decay
of the Lyapunov energy in the stable regime.

\begin{figure}[t]
\centering
\includegraphics[width=0.7\linewidth]{figures/fig2_lyapunov_decay.png}
\caption{Evolution of the composite Lyapunov energy under different parameter regimes.}
\label{fig:lyapunov_decay}
\end{figure}

---

\subsection{Sensitivity to Metric Mismatch}

The stability boundary depends on the Lyapunov
comparability constant

\begin{equation}
J = \frac{M}{m}
\end{equation}

which measures the mismatch between Lyapunov metrics
across regimes.

Figure~\ref{fig:metric_mismatch}
illustrates how increasing $J$ shrinks the stability region.
Larger metric mismatch therefore requires larger dwell time
to guarantee stability.

\begin{figure}[t]
\centering
\includegraphics[width=0.7\linewidth]{figures/fig3_stability_vs_J.png}
\caption{Effect of Lyapunov metric mismatch on the stability region.}
\label{fig:metric_mismatch}
\end{figure}

---

\subsection{Empirical Validation of the Stability Frontier}

To further validate the theoretical tradeoff,
we performed a grid exploration of the parameter plane $(\eta,\tau_d)$.

For each parameter pair the hybrid system was simulated
and the convergence of the composite Lyapunov energy was evaluated.

Figure~\ref{fig:empirical_stability} compares the empirical
stability classification with the theoretical stability boundary
predicted by Theorem 2.

The results confirm that the theoretical boundary accurately
predicts the transition between stable and unstable regimes.
Points above the boundary are consistently stable,
while instability predominantly appears below the curve,
consistent with the fact that the theoretical condition
is sufficient but not necessary.

\begin{figure}[t]
\centering
\includegraphics[width=0.7\linewidth]{figures/fig4_empirical_phase_diagram.png}
\caption{Empirical validation of the stability frontier.}
\label{fig:empirical_stability}
\end{figure}

---

\subsection{Example System}

We validate the predicted behavior on a simple linear
two-regime example.

The fast subsystem is

\begin{equation}
x_{t+1} = A_q x_t + B z_t + w_t
\end{equation}

with $A_q \in \{A_1, A_2\}$ where

\begin{equation}
A_1 =
\begin{bmatrix}
0.8 & 0.1 \\
0.0 & 0.7
\end{bmatrix}
\end{equation}

\begin{equation}
A_2 =
\begin{bmatrix}
0.75 & -0.1 \\
0.05 & 0.8
\end{bmatrix}
\end{equation}

and

\begin{equation}
B =
\begin{bmatrix}
0.1 \\
0.1
\end{bmatrix}.
\end{equation}

The slow map is defined as

\begin{equation}
T(x) = Kx,
\qquad
K =
\begin{bmatrix}
0.2 & 0.1
\end{bmatrix}.
\end{equation}

The slow dynamics therefore becomes

\begin{equation}
z_{t+1} = (1-\eta)z_t + \eta K x_t.
\end{equation}

With $\eta = 0.05$ and bounded noise
$\|w_t\| \le 0.05$,
simulations show decay of the composite energy
and bounded trajectories under switching,
consistent with condition (T1).

------------------------------------------------------------------------

\section{Conclusion}

We derived an explicit switching--coupling tradeoff for
two-timescale discrete-time switched systems.

The main condition yields a quantitative stability boundary
in the $(\eta,\tau_d)$ parameter plane: stronger slow
adaptation requires slower switching (larger dwell-time),
while improved cross-regime metric alignment
(smaller $J$) expands the stability region.

The obtained result unifies three classical tools of
stability analysis:

\begin{itemize}
\item contraction analysis of the fast subsystem,
\item average dwell-time theory for switched systems,
\item slow--fast coupling analysis.
\end{itemize}

These elements combine within a single explicit
parametric stability condition

\begin{equation}
\frac{\log J}{\tau_d} + \log(1-\kappa_{\mathrm{eff}}) < 0,
\end{equation}

which characterizes the balance between contraction,
coupling, and switching excitation.

Beyond theoretical guarantees, the obtained stability frontier
provides a practical design guideline for hybrid
learning-control architectures. In particular, it clarifies
how the admissible adaptation rate must scale with the
supervisory switching frequency.

The proposed framework highlights the structural interaction
between slow learning dynamics and fast contracting control
loops, a configuration that increasingly appears in modern
adaptive and learning-based systems.

Future work will investigate several extensions, including:

\begin{itemize}
\item stochastic switching and Markov jump regimes,
\item non-quadratic Lyapunov constructions,
\item data-driven identification of stability regions,
\item and extensions to continuous-time hybrid systems.
\end{itemize}