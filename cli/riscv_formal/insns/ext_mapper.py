from typing import Callable, Iterable

from yosys_mau.source_str import report

from .model import Instruction
from riscv_formal.named_set import NamedSet

__ext_dict: dict[str, Callable[[Iterable[str]], NamedSet[Instruction]]] = {}
__ext_composition: dict[str, Iterable[str]] = {}
__aliased_by: dict[Callable, set[str]] = {}

def register_ext_composition(mod: str, composed_of: Iterable[str]) -> None:
    # e.g. B is composed of Zba + Zbb + Zbs
    __ext_composition[mod] = composed_of

def register_ext_generator(
    generator: Callable[[Iterable[str]], NamedSet[Instruction]],
    mods: str | Iterable[str],
) -> None:
    # Aliasing allows the same generator to be used for multiple extensions
    # (or sub extensions).  Aliases are tracked so that generators are only
    # called once across all aliases.
    # e.g. the bext generator returns all Zb* instructions
    # Generators are called with the list of isa_mods currently in use.  This
    # allows for conditionally generating instructions as needed.  Results are
    # then filtered by Instruction.included_in(isa_mods), allowing generators to
    # ignore the input list of isa_mods and return all available instructions.
    if isinstance(mods, str):
        mods = (mods,)
    for mod in mods:
        __ext_dict[mod] = generator
    __aliased_by[generator] = set(mods)

def map_ext(isa_mods: Iterable[str], xlen: int = 32) -> NamedSet[Instruction]:
    insns: NamedSet[Instruction] = NamedSet()
    unknown_mods: set[str] = set()
    handled_mods: set[str] = set()

    for mod in isa_mods:
        if mod.isnumeric():
            # skip xlen mods
            continue

        # get composition
        for submod in __ext_composition.get(mod, (mod,)):
            # skip already handled mods
            if submod in handled_mods: continue

            try:
                generator = __ext_dict[submod]
            except KeyError:
                unknown_mods.add(mod)
                continue

            for insn in generator(isa_mods):
                # generators can over specify
                if not insn.included_in(isa_mods):
                    continue

                # skip invalid xlen
                # TODO support optionally testing rv32 instructions in an rv64 core
                if not insn.valid_xlen(xlen):
                    continue

                insns.add(insn)

            # mark all aliases as handled
            handled_mods.update(__aliased_by[generator])

    for mod in unknown_mods:
        raise report.InputError(mod, f"unsupported ISA mod/extension {mod!r}")

    return insns
