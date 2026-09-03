# Decision records

The code comments cite decision identifiers: `F-***` invariants,
`DM-**` campaign decisions, `P0-*` audit findings, and a few
audit-numbered items (`A14-BETA-*`, `A15-BETA-*`, `D-a`, `DS3`). They
used to resolve only in the author's private project notes; an outside
reader could not tell a load-bearing invariant from a historical
remark. These pages make every cited identifier resolvable inside the
repository, and a contract test
(`tests/docs/test_decision_ids_resolve.py`) fails the gate when a
comment cites an identifier these pages do not define.

- [INVARIANTS.md](INVARIANTS.md): the `F-***` doctrine invariants.
  These are load-bearing: code keeps them true and tests pin them.
- [DECISIONS.md](DECISIONS.md): the `DM-**` campaign decisions, in
  campaign order. Each says what was decided, why, and where it is
  enforced.
- [AUDITS.md](AUDITS.md): audit finding identifiers (`P0-*`,
  `A14-BETA-*`, `A15-BETA-*`) and structural decisions (`D-a`, `DS3`)
  cited by comments.

## The campaigns, in one line each

The repository was remediated through focused campaigns, each closed
with a full quality gate, mutation replay and clean-clone
verification. Chronologically: a cleanup arc (dead code, measured
math, structure, observability, first release); MATH-B and MATH-C
(the M10 empirical validation harness and its two registered
corpora); FIX (audit defects, honest projection margins); KERNEL
(canonicalization injectivity, audit bijection, ZIP guard: the
0.1.0b6 security fixes); CI (gate/workflow parity); ALLOW and PROJ
(certificate and projection semantics); SEUIL (registered
weak-stability threshold); GATE-SEM (the verdict semantics: adaptive
fail-closed, kernel shortcut bounded, honest trace); INTEGRITY (one
canonical encoder, real API fingerprint, honest risk view);
RELEASE-b6; HONEST-DOCS (prose held by the gate); SURFACE (two public
surfaces, one engine posture, typed vocabulary); HARDEN (effect-path
decisions, ambient configuration, monotone Pi margin, sensor
degradation floor, policy tables, supply chain); FINITION (doc drift
ratcheted, front page, morgue). `CHANGELOG.md` carries the shipped
view of the same history.
