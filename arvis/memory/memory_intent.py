# arvis/memory/memory_intent.py

from enum import Enum

class MemoryIntent(Enum):
    NONE = "none"
    CANDIDATE = "candidate"
    CONFIRMED = "confirmed"
