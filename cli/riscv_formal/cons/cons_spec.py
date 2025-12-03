
from typing import (
    ClassVar,
    Iterable,
    Callable,
)

from yosys_mau import task_loop as tl

from .cons import Cons, BusCons
from riscv_formal.named_set import NamedSet
from riscv_formal.insns import Isa


class ConsSpec:
    _cons: NamedSet[Cons] | None = None

    _generators: ClassVar[dict[str, Callable[[Iterable[str]], NamedSet[Cons]]]] = {}
    _aliased_by: ClassVar[dict[Callable, set[str]]] = {}

    @classmethod
    def register_generator(cls,
        generator: Callable[[Iterable[str]], NamedSet[Cons]],
        *mods: str,
    ) -> None:
        for mod in mods:
            cls._generators[mod] = generator
        cls._aliased_by[generator] = set(mods)
        mods_str = ", ".join(mods)
        tl.log_debug(f"Registered cons callback for extensions: {mods_str}")

    def generate(self, isa: Isa) -> None:
        self._cons = NamedSet()
        handled_mods: set[str] = set()

        for mod in isa.mods:
            if mod in handled_mods: continue

            try:
                generator = self._generators[mod]
            except KeyError:
                # Not all extensions have consistency checks
                continue

            self._cons.update(generator(isa.mods))

            # mark all aliases as handled
            handled_mods.update(self._aliased_by[generator])

    @property
    def cons(self) -> Iterable[Cons]:
        assert self._cons is not None
        return self._cons

def base_cons(_) -> NamedSet[Cons]:
    return NamedSet([
        # depth only
        Cons(name="ill"),
        Cons(name="fault"),

        # start + depth
        Cons(name="reg", has_start=True),
        Cons(name="pc_fwd", has_start=True),
        Cons(name="pc_bwd", has_start=True),
        Cons(name="causal", has_start=True),
        Cons(name="causal_mem", has_start=True),
        Cons(name="causal_io", has_start=True),

        # start + trig + depth
        Cons(name="liveness", has_start=True, has_trig=True),
        Cons(name="unique", has_start=True, has_trig=True),

        # non-channelized checks
        Cons(name="cover", has_start=True, can_channelize=False),
        Cons(name="hang", has_start=True, can_channelize=False),

        # bus checks
        BusCons(name="bus_imem"),
        BusCons(name="bus_imem_fault"),
        BusCons(name="bus_dmem"),
        BusCons(name="bus_dmem_fault"),
        BusCons(name="bus_dmem_io_read"),
        BusCons(name="bus_dmem_io_read_fault"),
        BusCons(name="bus_dmem_io_write"),
        BusCons(name="bus_dmem_io_write_fault"),
        BusCons(name="bus_dmem_io_order"),
    ])

"""
for grp in groups:
    for csr in sorted(csrs):
        for chanidx in range(nret):
            for csr_test in csr_tests.get(csr, [None]):
                check_cons(grp, csr, chanidx, start=0, depth=1, csr_mode=True, csr_test=csr_test)
"""

ConsSpec.register_generator(base_cons, "I")
