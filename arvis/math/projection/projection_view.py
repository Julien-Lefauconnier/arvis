# arvis/math/projection/projection_view.py

from __future__ import annotations

from collections.abc import ItemsView, Iterator, KeysView, Mapping, ValuesView
from dataclasses import dataclass
from typing import TypeVar, overload

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class ProjectionView(Mapping[str, float]):
    _values: dict[str, float]

    def items(self) -> ItemsView[str, float]:
        return self._values.items()

    def keys(self) -> KeysView[str]:
        return self._values.keys()

    def values(self) -> ValuesView[float]:
        return self._values.values()

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __getitem__(self, key: str) -> float:
        return self._values[key]

    @overload
    def get(self, key: str) -> float | None: ...

    @overload
    def get(self, key: str, default: float) -> float: ...

    @overload
    def get(self, key: str, default: T) -> float | T: ...

    def get(
        self,
        key: str,
        default: object = None,
    ) -> float | object:
        return self._values.get(key, default)

    def to_dict(self) -> dict[str, float]:
        return dict(self._values)

    @classmethod
    def from_mapping(
        cls,
        mapping: Mapping[str, float] | None,
    ) -> ProjectionView:
        if mapping is None:
            return cls(_values={})

        out: dict[str, float] = {}

        for k, v in mapping.items():
            if isinstance(v, (int, float)):
                out[str(k)] = float(v)

        return cls(_values=out)
