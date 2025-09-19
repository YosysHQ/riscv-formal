from dataclasses import dataclass
from typing import Collection, Iterable, Iterator, Any, TypeVar


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


@dataclass
class NamedClass:
    name: str


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
