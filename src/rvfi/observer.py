from dataclasses import dataclass, asdict
import json

import json_fix

from ..named_set import NamedClass

@dataclass
class Observer(NamedClass):
    name: str
    width: str

    @classmethod
    def from_json(cls, s: str):
        mapping = json.loads(s)
        return cls(**mapping)

    def __json__(self) -> dict:
        return asdict(self)

    def bitrange(self) -> str:
        if self.width == "1":
            return ""
        elif self.width == "xlen":
            return "[`RISCV_FORMAL_XLEN-1:0]"
        try:
            return f"[{int(self.width)-1}:0]"
        except ValueError:
            return f"[{self.width}-1:0]"

@dataclass
class SpeculativeObserver(Observer):
    spec_value: str = "0"

@dataclass
class ZeroedObserver(Observer):
    zero_condition: str = "0"

