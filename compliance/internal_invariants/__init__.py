"""Internal invariant suite (renamed from the former top-level layout).

These tests import internal modules (CognitivePipeline, contexts, test
fixtures) and are therefore white-box by construction: they pin kernel
invariants, not the installed package contract. The normative,
host-facing suite is ``compliance.blackbox``.
"""
