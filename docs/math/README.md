# The mathematical corpus, and where the implementation actually stands

This directory is the theoretical program of ARVIS (M0 to M15). It was
written ahead of the implementation, and the honest way to read it is
with the implementation frontier in hand: some of it is implemented and
measured on every governed run, some of it is implemented but only live
under specific conditions, and some of it is theory whose runtime
counterpart does not exist yet. This index states which is which, so
the corpus cannot imply more than the code delivers (campaign MATH-A,
LOT M5; the frontier moved substantially in that campaign).

## The implemented object: the contraction monitor (v0)

Since campaign MATH-A the default engine measures its own science
through `arvis/math/core/contraction_monitor_core.py`, a pure
transition `compute(bundle, prior) -> (snapshot, next_state)`:

- a four-axis Lyapunov state and its energy `V` (constructive
  candidate, `arvis/math/lyapunov/lyapunov.py`; A5 holds in class-K
  form, see M1);
- `delta_v` (the contraction signal) from the second threaded turn on
  (the host threads `scientific_state`, see
  `docs/architecture/RUNTIME_LIFECYCLE.md`);
- a certified PAC risk ceiling (windowed Hoeffding, or an
  anytime-valid confidence sequence) and a calibrated verdict on it;
- a hybrid (continuous + symbolic) drift score and an empirical
  regime estimator;
- the worst-axis refusal guard and the refusal-first gate ordering
  (`arvis/math/gate/`), with recovery bounded and capped.

This is deliberately a **monitor**: measured energy plus certified
risk plus replay. It is not a proven Lyapunov function for the full
cognitive dynamics.

## Document status

| Document | Content | Status vs implementation |
|---|---|---|
| M0 system boundary | projected system definition | conceptual frame; the projection of 0.1 is partial (certification-oriented) |
| M1 assumptions | A1-A15 | **normative for the corpus**; A5 restated in class-K form to match the implemented V (MATH-A M4); A12's kappa_eff is theoretical and distinct from the empirical contraction factor the runtime estimates |
| M1b formal system | formal definitions | theory |
| M1c result inventory | results catalogue | theory; read with this table |
| M2 proof skeleton | proof outlines | theory; quadratic-bound steps apply to the quadratic family only |
| M3.x state model / projection | state and Pi | partially implemented: the 0.1 projection is partial; sparse inputs get a minimal certificate |
| M4 adaptive stability | adaptation | partially: the runtime estimates the EMPIRICAL contraction factor with divergence accounting (`arvis/math/adaptive/adaptive_kappa_eff.py`); no eta-adaptation law is enforced |
| M5 adaptive integration | closed loop with adaptation | theory |
| M6 gate stability | gate consistency | implemented in spirit: refusal-first ordering, monotone strictness, bounded recovery are tested properties (`tests/math/gate/`, `tests/kernel/stages/`) |
| M7 closed-loop adaptive | closed-loop result | theory |
| M8 robust / ISS | practical stability, ISS | theory; `noise_robustness_ok` and `mode_stability_ok` are NOT evaluated by the projection certificate (see `VERSIONING.md`) |
| M9 synthesis / validity envelope | envelope | partially: `build_validity_envelope` implements the fail-closed envelope shape; global/switching enforcement is policy-driven |
| M10 empirical validation | validation program | partially: the PAC risk bound and the compliance/property suites are the implemented slice |
| M11 projection control operator | Pi control | theory |
| M12 decision lattice | verdict algebra | implemented: the strictness order and monotone composition are code (`arvis/math/lyapunov/verdict_order.py`) with Hypothesis properties |
| M13 limits and open problems | boundary | **read this second** (after M1); kept current with the frontier |
| M14 COS architecture | architecture essay | narrative |
| M15 comparative framework | comparison | narrative |

## What remains theory (the open frontier)

- the composite slow/symbolic coupling W and the small-gain condition
  as an ENFORCED runtime property (the small-gain check exists but its
  constants are declared assumptions, not measurements);
- switching/dwell-time enforcement tied to measured regime switches;
- ISS and noise-robustness certification (explicitly not certified,
  per `VERSIONING.md`);
- any guarantee over the full, unprojected cognitive dynamics.

Every claim in M2 through M9 is conditional on M1's assumptions and on
the projection; nothing in this directory certifies behavior of
arbitrary LLM output.
