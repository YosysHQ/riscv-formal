from dataclasses import dataclass
from typing import Optional

from ..named_set import NamedClass

@dataclass
class Observer(NamedClass):
    name: str
    width: str

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
    spec_value: Optional[str] = "0"

@dataclass
class ZeroedObserver(Observer):
    zero_condition: str = "0"

