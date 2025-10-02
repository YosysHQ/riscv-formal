from dataclasses import dataclass, asdict
from typing import Collection, Iterable, Iterator, Any, TypeVar
import json

import json_fix

class KeyMismatchError(Exception):
    rhs: str
    lhs: str
    def __init__(self, rhs, lhs, *args):
        self.rhs = rhs
        self.lhs = lhs
        super().__init__(*args)

    def __str__(self) -> str:
        return f"rhs ({self.rhs!r}) must match lhs ({self.lhs!r})"

class KeyExistsError(KeyError):
    pass

def skip_empty_factory(mapping: list[tuple[str, Any]]) -> dict:
    """dictionary factory which skips empty values"""
    result = {}
    for key, val in mapping:
        if isinstance(val, bool):
            result[key] = val
        elif val:
            # skip falsy non-boolean values
            result[key] = val
    return result


@dataclass
class NamedClass:
    name: str

    @classmethod
    def from_json(cls, s: str):
        mapping = json.loads(s)
        return cls(**mapping)

    def __json__(self, skip_empty: bool = True) -> dict:
        if skip_empty:
            return asdict(self, dict_factory=skip_empty_factory)
        else:
            return asdict(self)

    def to_json(self, skip_empty: bool = True, indent: int | str | None = None) -> str:
        return json.dumps(self.__json__(skip_empty), indent=indent)


T = TypeVar('T', bound=NamedClass)

@dataclass
class ValuedClass(NamedClass):
    val: Any


class NamedSet(Collection[T]):
    _store: dict[str, T]

    def __init__(self, iterable: Iterable[T] = ()) -> None:
        self._store = {o.name: o for o in iterable}

    def __contains__(self, item: object) -> bool:
        return item in self._store

    def __iter__(self) -> Iterator[T]:
        return iter(self._store.values())

    def __len__(self) -> int:
        return len(self._store)

    def __getitem__(self, key: str) -> T:
        return self._store[key]

    def __setitem__(self, key: str, value: T) -> None:
        if value.name == key:
            self._store[key] = value
        else:
            raise KeyMismatchError(value.name, key)

    def __delitem__(self, key: str) -> None:
        del self._store[key]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({list(self)!r})"

    def __json__(self) -> list:
        return list(self)

    def add(self, value: T) -> None:
        try:
            is_equal = self[value.name] == value
        except KeyError:
            self[value.name] = value
        else:
            if not is_equal:
                raise KeyExistsError(value.name)

    def names(self) -> Iterator[str]:
        return iter(self._store.keys())

    def update(self, other: "NamedSet[T]") -> None:
        for val in other:
            self[val.name] = val
