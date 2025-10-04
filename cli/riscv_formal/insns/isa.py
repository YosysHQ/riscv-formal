from __future__ import annotations

from dataclasses import dataclass

from .model import Instruction
from riscv_formal.named_set import NamedSet

@dataclass
class Isa:
    str: str
    xlen: int
    mods: list[str]
    insns: NamedSet[Instruction]

    @property
    def compressed(self) -> bool:
        return "c" in self.mods
