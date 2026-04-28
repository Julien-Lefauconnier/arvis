# arvis/memory/memory_long_record.py

from dataclasses import dataclass

from arvis.memory.memory_long_entry import MemoryLongEntry


@dataclass(frozen=True)
class MemoryLongRecord:
    entry: MemoryLongEntry
    payload_ciphertext: bytes
    nonce: bytes
