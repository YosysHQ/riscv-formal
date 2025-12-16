from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, ClassVar, Optional

from yosys_mau.source_str import report, re as ssre
import yosys_mau.task_loop as tl

from riscv_formal.generic_checker import GenericChecker
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
    _dependencies: ClassVar[dict[str, Iterable[str]]] = {}
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
            self._mods = set()
            def add_mods(*mods: str):
                assert self._mods is not None
                for mod in mods:
                    # prevent infinite recursion by only adding if we haven't already
                    if mod not in self._mods:
                        self._mods.add(mod.title())
                        for submod in self._compositions.get(mod, []):
                            add_mods(submod)

            # Only multi can have a value of None, so these are safe to treat as str
            base: str = self.isa_dict["base"] # type: ignore
            width: str = self.isa_dict["width"] # type: ignore
            ext: str = self.isa_dict["ext"] # type: ignore
            add_mods(base.upper(), width, *ext)
            multi = self.isa_dict["multi"]
            if multi is not None:
                add_mods(*multi.split("_"))
        return self._mods

    @property
    def insns(self) -> Iterable[Instruction]:
        assert self._insns is not None
        return self._insns

    @property
    def compressed(self) -> bool:
        return "c" in self.mods

    @classmethod
    def register_composition(cls, mod: str, *composed_of: str) -> None:
        """e.g. mod "B" is composed of "Zba", "Zbb", "Zbs"

        :param mod: ISA extension
        :param composed_of: One or more extensions
        """
        cls._compositions[mod] = composed_of

    @classmethod
    def register_dependency(cls, mod: str, *depends_on: str) -> None:
        """e.g. mod "Zicntr" depends on "Zicsr"

        :param mod: ISA extension
        :param depends_on: One or more extensions
        """
        cls._dependencies[mod] = depends_on

    @classmethod
    def register_generator(cls,
        generator: Callable[[Iterable[str]], NamedSet[Instruction]],
        *mods: str,
    ) -> None:
        """e.g. the ``bext`` generator returns "Zba", "Zbb", "Zbc", ...
        
        The same generator can be used for multiple extensions (or sub
        extensions).  Generators are only called once across all aliases, taking
        the list of ``isa_mods`` (extensions) currently in use and returning all
        available :class:`Instruction` checks for that set of mods/extensions.
        Results are then filtered by ``Instruction.included_in(isa_mods)``,
        allowing generators to optionally ignore the input list of
        mods/extensions and always return all instructions provided.

        :param generator: Generator function (factory method?)
        :param mods: All extensions which should trigger this generator
        """
        for mod in mods:
            cls._generators[mod] = generator
        cls._aliased_by[generator] = set(mods)
        mods_str = ", ".join(mods)
        tl.log_debug(f"Registered instruction callback for extensions: {mods_str}")

    @classmethod
    def register_non_insn_ext(cls, *mods: str) -> None:
        """Helper for registering extensions with no instruction checks.

        If the current configuration includes any unsupported extensions an
        error will be raised; this method allows registering extensions as
        supported even if they don't have any instructions to check.

        :param mods: One or more extensions
        """
        for mod in mods:
            cls._generators[mod] = _empty_insn_gen
            cls._aliased_by[_empty_insn_gen].add(mod)

    def generate(self) -> None:
        self._insns = NamedSet()
        handled_mods: set[str] = set()

        for mod in self.mods:
            if mod.isnumeric():
                # skip xlen mods
                GenericChecker.xlen = int(mod)
                continue

            # check for dependencies
            for submod in self._dependencies.get(mod, []):
                if submod not in self.mods:
                    raise report.InputError(mod, f"ISA mod/extension {mod!r} depends on {submod}")

            # skip already handled mods
            if mod in handled_mods: continue

            try:
                generator = self._generators[mod]
            except KeyError:
                raise report.InputError(mod, f"unsupported ISA mod/extension {mod!r}")

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
