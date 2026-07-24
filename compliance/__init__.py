"""ARVIS compliance suites.

Two suites with different natures:

- ``internal_invariants``: exercises kernel invariants by building
  pipeline contexts directly (imports internal modules and test
  fixtures). Valuable, but not normative for a host: it does not prove
  anything about the installed package surface.
- ``blackbox``: the normative suite. It uses only the public surface
  (``arvis.__all__`` and ``arvis.host_api``), carries versioned
  scenarios, and is meant to run against the installed wheel in a
  pristine environment (``scripts/run_blackbox_against_wheel.sh``).
"""
