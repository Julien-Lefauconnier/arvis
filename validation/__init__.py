# validation/__init__.py
"""Empirical validation campaigns (M10 and successors).

Measurement tooling, not runtime code: this package is tracked and
tested but deliberately excluded from the distributed wheel
(pyproject packages.find includes only ``arvis*``). Campaign
artifacts (corpora, seeds, observed metrics, reports) are versioned
here so a third party can regenerate and rerun them bit-for-bit, as
M10 section 9 requires.
"""
