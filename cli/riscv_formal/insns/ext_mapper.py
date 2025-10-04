from typing import Callable

from yosys_mau import task_loop as tl

from .model import Instruction
from riscv_formal.named_set import NamedSet
from .builtins import builtins

# TODO registering non base extensions (incl. custom)
ext_dict: dict[str, Callable[[], NamedSet[Instruction]]] = {}

def register_ext(mod: str, generator: Callable[[], NamedSet[Instruction]]) -> None:
    ext_dict[mod] = generator

def map_ext(mods: list[str], xlen: int = 32) -> NamedSet[Instruction]:
    insns: NamedSet[Instruction] = NamedSet()

    for insn in builtins():
        # TODO extension aliasing (e.g. B -> Zba Zbb Zbs)
        if insn.extension not in mods:
            continue

        # skip incompatible instructions
        if not insn.valid_xlen(xlen):
            continue

        insns.add(insn)

    return insns
