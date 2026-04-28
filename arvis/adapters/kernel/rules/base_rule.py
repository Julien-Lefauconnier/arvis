# arvis/adapters/kernel/rules/base_rule.py

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any


class CanonicalRule(ABC):
    """
    Base contract for IR -> canonical signal rules.
    """

    @abstractmethod
    def applies(self, ir: Any) -> bool:
        raise NotImplementedError

    @abstractmethod
    def emit_codes(self, ir: Any) -> Iterable[str]:
        raise NotImplementedError
