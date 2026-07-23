# Contributing to ARVIS

ARVIS is a deterministic kernel that other systems trust with their effects. The
bar is therefore higher than the size of a change suggests: a two-line patch on
the effect path deserves the same scrutiny as a feature.

This document tells you how to run what CI runs, what a change is expected to
carry, and where the line sits between the kernel and the layer built on it.

## Setup

Python 3.11 or later.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

Development dependencies are pinned exactly, on purpose: a lint or type result
that shifts with the tooling is not a result.

## The gate

One command runs everything CI runs:

```bash
bash scripts/run_quality_gate.sh
```

It runs, in order: `ruff format --check`, `ruff check`, `mypy arvis --strict`,
Bandit at medium and high, the test suite with its coverage floor, and the
examples smoke run. `bash scripts/run_quality_gate.sh security` runs Bandit
alone.

A pull request is expected to arrive with the gate green. If something in the
gate is wrong, say so in the pull request rather than working around it.

## What a change carries

**One increment per commit.** A commit does one thing and leaves the gate green.
A branch that needs four steps is four commits, not one large diff.

**A test that would have failed before.** Not a test that exercises the new
code, a test that fails without the fix. For anything on the effect path,
prefer an adversarial test: state the attack, then close it.

**English everywhere.** Code, comments, docstrings, commit messages, and test
names. The package is checked for this.

**No unreachable module.** A module nothing imports fails
`tests/contracts/test_module_reachability_ratchet.py`. Wire it or do not add it;
the wheel is not a place to park work in progress.

**No em dashes**, in code or documentation.

## Where the boundary is

ARVIS carries the generic mechanism. The layer built on top carries the meaning.

Concretely, a contribution belongs elsewhere if it needs to know what a domain
means: a vocabulary for finance or law, a template that turns structure into
finished wording, a renderer that presents a timeline to a human, a heuristic
that reads intent from natural language. The kernel constrains, records and
introspects; it does not interpret or present.

If a change makes the kernel aware of a business domain, it is in the wrong
repository, however useful it is.

## The effect path

Changes under `arvis/kernel_core/syscalls/`, `arvis/tools/` and
`arvis/kernel_core/canonicalization.py` govern real effects. Their invariants
are documented in `docs/architecture/EFFECT_PATH.md` and pinned by
`tests/adversarial/`.

Before touching them, know that: an effect payload is frozen at authorization; a
capability is single-use and bound to a sealed identity context; a result is
cryptographically bound to its intent; a value with no injective canonical
encoding is refused rather than collapsed. A change that relaxes any of these is
not a refactor, and the pull request should say so in its first line.

Anything that alters canonical bytes changes a format version and invalidates
old hashes explicitly. See [VERSIONING.md](VERSIONING.md).

## Ratchets

Several tests exist to stop drift rather than to check behaviour: the module
reachability ratchet, the context facade ratchet, the broad-except guard, and
the public API surface check. They fail when a change makes the codebase looser.

Do not update the frozen list to make one pass. Either the change belongs
outside the ratchet, or relaxing it is the deliberate point of the pull request
and is argued as such.

## Pull requests

State what breaks without the change, and how you know. Link the issue if there
is one. If the change touches the effect path, canonicalization or the public
API, say it in the first line: it changes who reviews it.

Documentation counts as part of the change. A behaviour that contradicts
`README.md`, `VERSIONING.md` or a specification in `docs/standard/` is a defect
even when the code is correct.

## Reporting problems

Security issues go to the address in [SECURITY.md](SECURITY.md), never to a
public issue.

A runtime that claims more than [VERSIONING.md](VERSIONING.md) allows is a
defect worth reporting, and a security-adjacent one.

Everything else: <https://github.com/Julien-Lefauconnier/arvis/issues>.
