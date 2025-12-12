from dataclasses import dataclass, asdict
from typing import Collection, Iterable, Iterator, Any, TypeVar, overload
import json

import json_fix

class KeyMismatchError(Exception):
    """Mapping key does not match value.name.

    :param name: value.name
    :param key: Mapping key
    """
    name: str
    key: str
    def __init__(self, name: str, key: str, *args):
        self.name = name
        self.key = key
        super().__init__(*args)

    def __str__(self) -> str:
        return f"value.name of rhs ({self.name!r}) must match key of lhs ({self.key!r})"

class KeyExistsError(KeyError):
    """Mapping key already exists in collection."""
    pass

def skip_empty_factory(mapping: list[tuple[str, Any]]) -> dict:
    """Dictionary factory which skips empty values.

    :meta private:
    """
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
    """A dataclass which supports json conversion and has a name property.

    :param name: The name of the object, used as the key during lookup
    """
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

#: Type for collections of :class:`NamedClass` or a subclass of it.
NC = TypeVar('NC', bound=NamedClass)

@dataclass
class ValuedClass(NamedClass):
    """A :class:`NamedClass` with a value, mostly used for testing.

    :param val:
    """
    val: Any

class NamedSet(Collection[NC]):
    """A collection of values that can be accessed by name."""
    _store: dict[str, NC]

    def __init__(self, iterable: Iterable[NC] = ()) -> None:
        """
        :param iterable: Collection of values to initialize set with,
            defaults to an empty set
        """
        self._store = {o.name: o for o in iterable}

    def __contains__(self, item: object) -> bool:
        return item in self._store

    def __iter__(self) -> Iterator[NC]:
        return iter(self._store.values())

    def __len__(self) -> int:
        return len(self._store)

    def __getitem__(self, name: str) -> NC:
        return self._store[name]

    def __setitem__(self, name: str, value: NC) -> None:
        if value.name == name:
            self._store[name] = value
        else:
            raise KeyMismatchError(value.name, name)

    def __delitem__(self, name: str) -> None:
        del self._store[name]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({list(self)!r})"

    def __json__(self) -> list:
        return list(self)

    def add(self, value: NC) -> None:
        """Add value to collection.

        :param value: Value to add
        :raises KeyExistsError: value.name already exists in collection, and
            content does not match
        """
        try:
            is_equal = self[value.name] == value
        except KeyError:
            self[value.name] = value
        else:
            if not is_equal:
                raise KeyExistsError(value.name)

    def names(self) -> Iterator[str]:
        """Get an iterator for all names in collection."""
        return iter(self._store.keys())

    def update(self, other: "Iterable[NC]") -> None:
        """Update values in collection.

        :param other: Collection to update values from.
        """
        for val in other:
            self[val.name] = val

    @overload
    def get(self, name: str, /) -> NC | None: ...
    @overload
    def get(self, name: str, default: NC, /) -> NC: ...
    @overload
    def get(self, name: str, default: None = None, /) -> NC | None: ...
    def get(self, name: str, default: NC | None = None) -> NC | None:
        """Try return the named value if one exists, or default if not.

        :param name: The name to search for
        :param default: The value to return if none found, defaults to None
        :return: value or default
        """
        return self._store.get(name, default)

    @overload
    def pop(self, name: str, /) -> NC: ...
    @overload
    def pop(self, name: str, default: NC, /) -> NC: ...
    @overload
    def pop(self, name: str, default: None, /) -> NC | None: ...
    def pop(self, name: str, *args: NC | None) -> NC | None:
        """Remove the named value, and return it if it exists.

        :raises KeyError: Named value does not exist and no default provided.
        :return: value or default
        """
        return self._store.pop(name, *args)
