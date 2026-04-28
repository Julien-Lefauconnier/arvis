# arvis/cognition/coherence/coherence_limits.py

"""
Coherence limits (declarative constants).

These limits are used by observers/policies to detect instability.
They do not enforce behavior.
"""

# Default maximum changes allowed in the active coherence window
DEFAULT_MAX_CHANGES: int = 20

# Cap the per-step delta, to avoid "one giant jump" consuming the whole budget
DEFAULT_STEP_CAP: int = 10

# Optional sliding window size (number of cycles) if you later implement windowing
# For now, ChangeBudget is simple and does not encode window semantics.
DEFAULT_WINDOW_SIZE: int = 10
