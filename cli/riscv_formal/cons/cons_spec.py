
from typing import (
    ClassVar,
    Iterable,
    Callable,
)

from yosys_mau import task_loop as tl

from .cons import Cons
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
        Cons(name= "reg", has_start = True),
    ])

"""
for grp in groups:
    for i in range(nret):
        check_cons(grp, "reg", chanidx=i, start=0, depth=1)
        check_cons(grp, "pc_fwd", chanidx=i, start=0, depth=1)
        check_cons(grp, "pc_bwd", chanidx=i, start=0, depth=1)
        check_cons(grp, "liveness", chanidx=i, start=0, trig=1, depth=2)
        check_cons(grp, "unique", chanidx=i, start=0, trig=1, depth=2)
        check_cons(grp, "causal", chanidx=i, start=0, depth=1)
        check_cons(grp, "causal_mem", chanidx=i, start=0, depth=1)
        check_cons(grp, "causal_io", chanidx=i, start=0, depth=1)
        check_cons(grp, "ill", chanidx=i, depth=0)
        check_cons(grp, "fault", chanidx=i, depth=0)

        check_cons(grp, "bus_imem", chanidx=i, start=0, depth=1, bus_mode=True)
        check_cons(grp, "bus_imem_fault", chanidx=i, start=0, depth=1, bus_mode=True)
        check_cons(grp, "bus_dmem", chanidx=i, start=0, depth=1, bus_mode=True)
        check_cons(grp, "bus_dmem_fault", chanidx=i, start=0, depth=1, bus_mode=True)
        check_cons(grp, "bus_dmem_io_read", chanidx=i, start=0, depth=1, bus_mode=True)
        check_cons(grp, "bus_dmem_io_read_fault", chanidx=i, start=0, depth=1, bus_mode=True)
        check_cons(grp, "bus_dmem_io_write", chanidx=i, start=0, depth=1, bus_mode=True)
        check_cons(grp, "bus_dmem_io_write_fault", chanidx=i, start=0, depth=1, bus_mode=True)
        check_cons(grp, "bus_dmem_io_order", chanidx=i, start=0, depth=1, bus_mode=True)

    check_cons(grp, "hang", start=0, depth=1)
    check_cons(grp, "cover", start=0, depth=1)

    for csr in sorted(csrs):
        for chanidx in range(nret):
            for csr_test in csr_tests.get(csr, [None]):
                check_cons(grp, csr, chanidx, start=0, depth=1, csr_mode=True, csr_test=csr_test)
"""

ConsSpec.register_generator(base_cons, "I")
