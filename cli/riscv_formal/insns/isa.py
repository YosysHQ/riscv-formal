from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, ClassVar, Optional

from yosys_mau.source_str import report, re as ssre

from .model import Instruction
from riscv_formal.named_set import NamedSet

def _empty_insn_gen(_) -> NamedSet[Instruction]:
    return NamedSet()

@dataclass
class Isa:
    str: str

    _isa_dict: dict[str, Optional[str]] | None = None
    _mods: set[str] | None = None
    _insns: NamedSet[Instruction] | None = None

    _compositions: ClassVar[dict[str, Iterable[str]]] = {}
    _generators: ClassVar[dict[str, Callable[[Iterable[str]], NamedSet[Instruction]]]] = {
        "rv": _empty_insn_gen,
    }
    _aliased_by: ClassVar[dict[Callable, set[str]]] = {
        _empty_insn_gen: set(),
    }

    @property
    def isa_dict(self) -> dict[str, Optional[str]]:
        if self._isa_dict is None:
            matched = ssre.match(
                r"rv(?P<width>\d+)(?P<base>[ie])(?P<ext>[a-v]*)(?P<multi>_?[SZX]\w+)?$", self.str, ssre.I
            )
            if matched is None:
                raise report.InputError(self.str, "Unable to parse isa string")
            self._isa_dict = matched.groupdict()
        return self._isa_dict

    @property
    def xlen(self) -> int:
        match self.isa_dict["width"]:
            case "64":
                return 64
            case "32":
                return 32
            case other:
                raise report.InputError(other, f"Unsupported xlen {other}")

    @property
    def mods(self) -> Iterable[str]:
        if self._mods is None:
            # Only multi can have a value of None, so these are safe to treat as str
            base: str = self.isa_dict["base"] # type: ignore
            width: str = self.isa_dict["width"] # type: ignore
            ext: str = self.isa_dict["ext"] # type: ignore
            self._mods = set((base.upper(), width))
            for mod in ext:
                self._mods.add(mod.upper())
            for mod in (self.isa_dict["multi"] or "").split("_"):
                if mod:
                    self._mods.add(mod.title())
            for mod in self._mods:
                for submod in self._compositions.get(mod, []):
                    self._mods.add(submod)
        return self._mods

    @property
    def insns(self) -> Iterable[Instruction]:
        assert self._insns is not None
        return self._insns

    @property
    def compressed(self) -> bool:
        return "c" in self.mods

    @classmethod
    def register_composition(cls, mod: str, composed_of: Iterable[str]) -> None:
        # e.g. B is composed of Zba + Zbb + Zbs
        cls._compositions[mod] = composed_of

    @classmethod
    def register_generator(cls,
        generator: Callable[[Iterable[str]], NamedSet[Instruction]],
        *mods: str,
    ) -> None:
        # Aliasing allows the same generator to be used for multiple extensions
        # (or sub extensions).  Aliases are tracked so that generators are only
        # called once across all aliases.
        # e.g. the bext generator returns all Zb* instructions
        # Generators are called with the list of isa_mods currently in use.  This
        # allows for conditionally generating instructions as needed.  Results are
        # then filtered by Instruction.included_in(isa_mods), allowing generators to
        # ignore the input list of isa_mods and return all available instructions.
        for mod in mods:
            cls._generators[mod] = generator
        cls._aliased_by[generator] = set(mods)

    @classmethod
    def register_non_insn_ext(cls, *args: str) -> None:
        # Helper for registering extensions with no instruction checks
        for mod in args:
            cls._generators[mod] = _empty_insn_gen
            cls._aliased_by[_empty_insn_gen].add(mod)

    def generate(self) -> None:
        self._insns = NamedSet()
        unknown_mods: set[str] = set()
        handled_mods: set[str] = set()

        for mod in self.mods:
            if mod.isnumeric():
                # skip xlen mods
                continue

            # skip already handled mods
            if mod in handled_mods: continue

            try:
                generator = self._generators[mod]
            except KeyError:
                unknown_mods.add(mod)
                continue

            for insn in generator(self.mods):
                # generators can over specify
                if not insn.included_in(self.mods):
                    continue

                # skip invalid xlen
                # TODO support optionally testing rv32 instructions in an rv64 core
                if not insn.valid_xlen(self.xlen):
                    continue

                self._insns.add(insn)

            # mark all aliases as handled
            handled_mods.update(self._aliased_by[generator])

        for mod in unknown_mods:
            raise report.InputError(mod, f"unsupported ISA mod/extension {mod!r}")
