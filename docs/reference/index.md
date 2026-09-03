# The two public surfaces

Everything an integrator may rely on lives on exactly two surfaces,
pinned by contract tests and versioned by
[VERSIONING.md](../../VERSIONING.md): the root package `arvis` (the
eleven symbols below) and the `arvis.host_api` modules. Every other
import path is internal and may change in any release. The reference
on these pages is generated from the docstrings the gate requires on
one hundred percent of this surface
(`tests/contracts/test_public_docstrings.py`).

Start with [`arvis`](arvis.md) for the engine and the result view;
reach for [`arvis.host_api`](host_api.md) when your integration
needs the runtime, tool-policy or service types by name.
