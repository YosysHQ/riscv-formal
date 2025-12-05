from __future__ import annotations

from dataclasses import dataclass, field
import functools
from typing import (
    Callable,
    ClassVar,
    Iterable,
    Optional,
    Self,
    Type,
    overload,
)

from yosys_mau.source_str import report, re as ssre
import yosys_mau.task_loop as tl

from .csr import (
    Csr,
    MachineCsr,
    HpmeventCsr,
)
from .behavior import (
    Behavior,
    AnyValue,
    ConstValue,
    ZeroValue,
    UpcntValue,
    IncValue,
)
from riscv_formal.named_set import NamedSet, NamedClass
from riscv_formal.insns import Isa


@dataclass
class CsrConfig(NamedClass):
    # TODO fix masks
    tests: dict[str, Optional[str]]

    @classmethod
    def parse(cls, line: str, **kwds) -> Self:
        match line.split(maxsplit=1):
            case [name]:
                return cls(name, {}, **kwds)
            case [name, tests_str]:
                new = cls(name, {}, **kwds)

                for test_str in ssre.findall(r'((?:\S*?"[^"]*")+|\S+)', tests_str):
                    new.parse_and_add_test(test_str)
                return new
            case _:
                raise report.InputError(
                    line, "expected a csr name followed by an optional list of csr tests"
                )

    def parse_and_add_test(self, test_str):
        if "=" in test_str:
            test_name, test_arg = test_str.split("=", 1)
            test_arg = test_arg.strip('"')
        else:
            test_name = test_str
            test_arg = None
        self.add_test(test_name, test_arg)

    def add_test(self, test_name: str, test_param: str | None):
        if test_name in self.tests:
            previous_name = next(name for name in self.tests.keys() if name == test_name)
            raise report.InputError(
                test_name + previous_name,
                f"test {test_name!r} for CSR {self.name!r} is defined multiple times",
            )
        self.tests[test_name] = test_param
    

def csr(name: str, width: str, privilege: str, index: int, indexh: Optional[int] = None, behavior: Optional[Behavior] = None) -> Csr:
    return Csr(
        name = name,
        width = width,
        privilege = privilege,
        index = index,
        indexh = indexh,
        behavior = behavior,
        has_macro_define = True,
    )

def mcsr(name: str, width: str, privilege: str, index: int, indexh: Optional[int] = None, behavior: Optional[Behavior] = None) -> MachineCsr:
    return MachineCsr(
        name = name,
        width = width,
        privilege = privilege,
        index = index,
        indexh = indexh,
        behavior = behavior,
        has_macro_define = True,
    )

def mcsr_with_shadow(mname: str, width: str,  mprivilege: str, mindex: int, mindexh: Optional[int],
                     sname: str,              sprivilege: str, sindex: int, sindexh: Optional[int],
    ) -> tuple[MachineCsr, Csr]:
    machine_csr = mcsr(mname, width, mprivilege, mindex, mindexh)
    shadow_csr = machine_csr.shadow(sname, sprivilege, sindex, sindexh)
    return (machine_csr, shadow_csr)

def hpm_csr(ename: str, ewidth: str, eprivilege: str, eindex: int,
            cname: str, cwidth: str, cprivilege: str, cindex: int, cindexh: Optional[int],
            sname: str,              sprivilege: str, sindex: int, sindexh: Optional[int],
    ) -> tuple[HpmeventCsr, MachineCsr, Csr]:
    counter_csr = mcsr(cname, cwidth, cprivilege, cindex, cindexh)
    event_csr = HpmeventCsr(
        name = ename,
        width = ewidth,
        privilege = eprivilege,
        index = eindex,
        counter = counter_csr,
    )
    shadow_csr = counter_csr.shadow(sname, sprivilege, sindex, sindexh)
    return (event_csr, counter_csr, shadow_csr)

def base_csrs(isa_mods: Iterable[str]) -> NamedSet[Csr]:
    return NamedSet([
        mcsr("mvendorid",     "xlen", "MRO", 0xF11),
        mcsr("marchid",       "xlen", "MRO", 0xF12),
        mcsr("mimpid",        "xlen", "MRO", 0xF13),
        mcsr("mhartid",       "xlen", "MRO", 0xF14),
        mcsr("mconfigptr",    "xlen", "MRO", 0xF15),
        mcsr("mstatus",       "xlen", "MRW", 0x300),
        mcsr("mstatush",      "xlen", "MRW", 0x310),
        mcsr("misa",          "xlen", "MRW", 0x301),
        mcsr("mie",           "xlen", "MRW", 0x304),
        mcsr("mtvec",         "xlen", "MRW", 0x305),
        mcsr("mscratch",      "xlen", "MRW", 0x340),
        mcsr("mepc",          "xlen", "MRW", 0x341),
        mcsr("mcause",        "xlen", "MRW", 0x342),
        mcsr("mtval",         "xlen", "MRW", 0x343),
        mcsr("mip",           "xlen", "MRW", 0x344),
        # TODO optional CSRs
        # mcsr("mcountinhibit", "xlen", "MRW", 0x320),
    ])

def hext_csrs(isa_mods: Iterable[str]) -> NamedSet[Csr]:
    return NamedSet([
        mcsr("mtinst",        "xlen", "MRW", 0x34A),
        mcsr("mtval2",        "xlen", "MRW", 0x34B),
    ])

def sext_csrs(isa_mods: Iterable[str]) -> NamedSet[Csr]:
    return NamedSet([
        mcsr("medeleg",       "xlen", "MRW", 0x302),
        mcsr("mideleg",       "xlen", "MRW", 0x303),
    ])

def uext_csrs(isa_mods: Iterable[str]) -> NamedSet[Csr]:
    return NamedSet([
        mcsr("mcounteren",    "xlen", "MRW", 0x306),
        mcsr("menvcfg",       "xlen", "MRW", 0x30A),
        mcsr("menvcfgh",      "xlen", "MRW", 0x31A),
    ])

def fext_csrs(isa_mods: Iterable[str]) -> NamedSet[Csr]:
    return NamedSet([
        # Csr("fflags",         "xlen",  None,  None,  None),
        # Csr("frm",            "xlen",  None,  None,  None),
        # Csr("fcsr",           "xlen",  None,  None,  None),
    ])

def cntr_csrs(isa_mods: Iterable[str]) -> NamedSet[Csr]:
    return NamedSet([
        *mcsr_with_shadow(
            "mcycle",           "64", "MRW", 0xB00, 0xB80,
            "cycle",                  "URO", 0xC00, 0xC80,
        ),
        csr("time",             "64", "URO", 0xC01, 0xC81),
        *mcsr_with_shadow(
            "minstret",         "64", "MRW", 0xB02, 0xB82,
            "instret",                "URO", 0xC02, 0xC82,
        ),
    ])

def hpm_csrs(isa_mods: Iterable[str]) -> NamedSet[Csr]:
    max_idx = 32
    csr_list: list[Csr] = []
    for i in range(3, max_idx):
        csr_list.extend(hpm_csr(
            f"mhpmevent{i}", "xlen", "MRW", 0x320 + i,
            f"mhpmcounter{i}", "64", "MRW", 0xB00 + i, 0xB80 + i,
            f"hpmcounter{i}",        "URO", 0xC00 + i, 0xC80 + i,
        ))
    return NamedSet(csr_list)

def pmp_csrs(isa_mods: Iterable[str], entries: int = 64) -> NamedSet[Csr]:
    # TODO odd configs only exist for RV32
    return NamedSet([
        *(
            mcsr(f"pmpcfg{i}",    "xlen", "MRW", 0x3A0 + i)
            for i in range(entries >> 2)
        ),
        *(
            mcsr(f"pmpaddr{i}",   "xlen", "MRW", 0x3B0 + i)
            for i in range(entries)
        ),
    ])

def mask_bits(test: str, bits: "list[int]", mask_len: int, invert=False):
    mask = functools.reduce(lambda x, y: x | 1 << y, bits, 0)
    return f"{test}_mask={'~' if invert else ''}{mask_len}'b{mask:0{mask_len}b}"


@dataclass
class CsrSpec:
    str: Optional[str] = None
    available_csrs: NamedSet[Csr] = field(default_factory=NamedSet) # type: ignore
    csr_configs: NamedSet[CsrConfig] = field(init=False)
    custom_csrs: set[str] = field(init=False)

    _generators: ClassVar[dict[str, Callable[[Iterable[str]], NamedSet[Csr]]]] = {}
    _aliased_by: ClassVar[dict[Callable, set[str]]] = {}
    _behaviors: ClassVar[dict[str, Type[Behavior]]] = {}

    @property
    def csrs(self) -> Iterable[Csr]:
        for csr in self.available_csrs:
            if csr.name in self.csr_configs:
                yield csr

    @classmethod
    def register_generator(cls,
        generator: Callable[[Iterable[str]], NamedSet[Csr]],
        *mods: str,
    ):
        # Unlike insn generators, csr generators should not over specify
        for mod in mods:
            cls._generators[mod] = generator
        cls._aliased_by[generator] = set(mods)
        mods_str = ", ".join(mods)
        tl.log_debug(f"Registered csr callback for extensions: {mods_str}")

    @classmethod
    def register_behavior(cls, behavior: Type[Behavior]):
        cls._behaviors[behavior.NAME] = behavior

    @classmethod
    def get_behavior(cls, name: str) -> Type[Behavior]:
        return cls._behaviors[name]

    def __post_init__(self) -> None:
        self.csr_configs = NamedSet()
        self.custom_csrs = set()

    def generate(self, isa: Isa) -> None:
        self.available_csrs = NamedSet()
        handled_mods: set[str] = set()

        for mod in isa.mods:
            if mod in handled_mods: continue

            try:
                generator = self._generators[mod]
            except KeyError:
                # Not all extensions have CSRs
                continue

            self.available_csrs.update(generator(isa.mods))

            # mark all aliases as handled
            handled_mods.update(self._aliased_by[generator])

        def csr_line(name: str, test: Optional[str] = None):
            csr_config = CsrConfig(name, {test: None} if test else {})
            self.config_csr(csr_config)

        match self.str:
            case None:
                self.csr_configs = NamedSet()
            case "1.12":
                self.csr_configs = NamedSet()
                csr_line("mvendorid", "const")
                csr_line("marchid", "const")
                csr_line("mimpid", "const")
                csr_line("mhartid", "const")
                csr_line("mconfigptr", "const")
                # TODO test reserved bits in mstatus and misa
                # csr_line(
                #     "mstatus",
                #     mask_bits(
                #         "zero",
                #         [0, 2, 4, *range(23, 31)] + ([31, *range(38, 63)] if xlen == 64 else []),
                #         xlen,
                #     ),
                # )
                # csr_line(
                #     "misa",
                #     mask_bits(
                #         "zero",
                #         [6, 10, 11, 14, 17, 19, 22, 24, 25, *range(26, xlen - 2)],
                #         xlen,
                #     ),
                # )
                csr_line("mscratch", "any")
                # TODO test hpms
                # TODO test shadow registers

                # TODO test restricted CSR addresses
                restricted_csrs: dict[str, tuple[str | list[str], int, list[str]]] = {
                    "mcycle": ("Zicntr", 0xB00, ["inc"]),
                    "minstret": ("Zicntr", 0xB02, ["inc"]),
                    "medeleg": ("s", 0x302, []),
                    "mideleg": ("s", 0x303, []),
                    "mcounteren": ("u", 0x306, []),
                    # "mstatush": ("32", 0x310, [mask_bits("zero", [4, 5], xlen, invert=True)]),
                    "mtinst": ("h", 0x34A, []),
                    "mtval2": ("h", 0x34B, []),
                    "menvcfg": ("u", 0x30A, []),
                    "menvcfgh": (["u", "32"], 0x31A, []),
                }
                for name, (mods, addr, tests) in restricted_csrs.items():
                    if isinstance(mods, str):
                        mods = [mods]
                    is_enabled = True
                    for mod in mods:
                        if mod not in isa.mods:
                            is_enabled = False
                            break
                    if is_enabled:
                        csr_line(name, *tests)
                    else:
                        self.add_csr(addr, name)
                        self.mark_illegal(name)

                for csr in self.available_csrs:
                    if isinstance(csr, MachineCsr):
                        if csr.name not in self.csr_configs:
                            csr_line(csr.name)
            case spec:
                raise report.InputError(spec, f"unsupported CSR spec {spec!r}")

    @overload
    def add_csr(self, address: int, name: Optional[str] = None, /) -> None: ...
    @overload
    def add_csr(self, csr: Csr, /) -> None: ...
    def add_csr(self, csr_or_addr: int | Csr, name: Optional[str] = None):
        if isinstance(csr_or_addr, Csr):
            csr = csr_or_addr
        else:
            addr = csr_or_addr
            csr = Csr(
                # use the address as a fallback if there is no name
                name = name or f"{addr:3x}",
                # only xlen-width custom CSRs are supported
                width = "xlen",
                index = addr,
            )

        name = csr.name
        try:
            self.available_csrs.add(csr)
        except KeyError:
            raise report.InputError(name, f"CSR {name!r} already exists")
        else:
            self.custom_csrs.add(name)

    def config_csr(self, csr_config: CsrConfig, legal: bool = True) -> None:
        name = csr_config.name
        try:
            csr = self.available_csrs[name]
        except KeyError:
            raise report.InputError(name, f"unrecognised CSR {name!r}")

        # set CSR-under-test flags
        csr.has_rvfi = legal
        csr.is_accessible = legal
        csr.read_insn = True
        # TODO fix RW tests for wide CSRs
        csr.rw_test = csr.width == "xlen"

        # CSRs without a macro define need to be included in RISCV_FORMAL_CUSTOM_CSR_*
        if not csr.has_macro_define:
            self.custom_csrs.add(csr.name)

        # override any existing config
        self.csr_configs[name] = csr_config

    def mark_illegal(self, name_or_address: str | int):
        if isinstance(name_or_address, int):
            name = f"{name_or_address:3x}"
        else:
            name = name_or_address

        self.config_csr(CsrConfig(name, {}), legal=False)


builtins_map = {
    "Zicsr": base_csrs,
    "H": hext_csrs,
    "S": sext_csrs,
    "U": uext_csrs,
    "F": fext_csrs,
    "Zicntr": cntr_csrs,
    "Zihpm": hpm_csrs,
    # TODO pmp_csrs?
}

for mod, gen in builtins_map.items():
    CsrSpec.register_generator(gen, mod)

Isa.register_dependency("Zicntr", "Zicsr")
Isa.register_dependency("Zihpm", "Zicsr")

builtin_behaviors: list[Type[Behavior]] = [
    AnyValue,
    ConstValue,
    ZeroValue,
    UpcntValue,
    IncValue,
]

for behavior in builtin_behaviors:
    CsrSpec.register_behavior(behavior)
