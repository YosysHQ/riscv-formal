from __future__ import annotations

from dataclasses import dataclass, field
import functools
from typing import Optional

from yosys_mau.source_str import report

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
from riscv_formal.named_set import NamedSet
from riscv_formal.insns import Isa


@dataclass
class CsrConfig:
    include_behavior: bool = False
    include_shadows: bool = True
    

def csr(name: str, width: str, privilege: str, index: int, indexh: Optional[int] = None, behavior: Optional[Behavior] = None) -> Csr:
    return Csr(
        name = name,
        width = width,
        privilege = privilege,
        index = index,
        indexh = indexh,
        behavior = behavior,
    )

def mcsr(name: str, width: str, privilege: str, index: int, indexh: Optional[int] = None, behavior: Optional[Behavior] = None) -> MachineCsr:
    return MachineCsr(
        name = name,
        width = width,
        privilege = privilege,
        index = index,
        indexh = indexh,
        behavior = behavior,
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

def base_csrs() -> NamedSet[Csr]:
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

def hext_csrs() -> NamedSet[Csr]:
    return NamedSet([
        mcsr("mtinst",        "xlen", "MRW", 0x34A),
        mcsr("mtval2",        "xlen", "MRW", 0x34B),
    ])

def sext_csrs() -> NamedSet[Csr]:
    return NamedSet([
        mcsr("medeleg",       "xlen", "MRW", 0x302),
        mcsr("mideleg",       "xlen", "MRW", 0x303),
    ])

def uext_csrs() -> NamedSet[Csr]:
    return NamedSet([
        mcsr("mcounteren",    "xlen", "MRW", 0x306),
        mcsr("menvcfg",       "xlen", "MRW", 0x30A),
        mcsr("menvcfgh",      "xlen", "MRW", 0x31A),
    ])

def fext_csrs() -> NamedSet[Csr]:
    return NamedSet([
        # Csr("fflags",         "xlen",  None,  None,  None),
        # Csr("frm",            "xlen",  None,  None,  None),
        # Csr("fcsr",           "xlen",  None,  None,  None),
    ])

def cntr_csrs() -> NamedSet[Csr]:
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

def hpm_csrs() -> NamedSet[Csr]:
    max_idx = 32
    csr_list: list[Csr] = []
    for i in range(3, max_idx):
        csr_list.extend(hpm_csr(
            f"mhpmevent{i}", "xlen", "MRW", 0x320 + i,
            f"mhpmcounter{i}", "64", "MRW", 0xB00 + i, 0xB80 + i,
            f"hpmcounter{i}",        "URO", 0xC00 + i, 0xC80 + i,
        ))
    return NamedSet(csr_list)

def pmp_csrs(_: CsrConfig, entries: int = 64) -> NamedSet[Csr]:
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
    csrs: NamedSet[Csr] | None = None
    csrs_to_define: set[str] = field(default_factory=set)

    def generate(self, isa: Isa) -> None:
        match self.str:
            case None:
                self.csrs = NamedSet()
                return
            case "1.12":
                csr_ext_map = {
                    "I": base_csrs,
                    "H": hext_csrs,
                    "S": sext_csrs,
                    "U": uext_csrs,
                    "F": fext_csrs,
                    "Zicntr": cntr_csrs,
                    "Zihpm": hpm_csrs,
                    # TODO pmp_csrs?
                }

                # get CSRs
                self.csrs = NamedSet()
                for csr_ext, csr_generator in csr_ext_map.items():
                    if csr_ext in isa.mods:
                        self.csrs.update(csr_generator())

                csr_beh_map = {
                    "mvendorid": ConstValue(),
                    "marchid": ConstValue(),
                    "mimpid": ConstValue(),
                    "mhartid": ConstValue(),
                    "mconfigptr": ConstValue(),
                    # TODO test reserved bits in mstatus and misa
                    # "mstatus": mask_bits(
                    #     "zero",
                    #     [0, 2, 4, *range(23, 31)] + ([31, *range(38, 63)] if xlen == 64 else []),
                    #     xlen,
                    # ),
                    # "misa": mask_bits(
                    #     "zero",
                    #     [6, 10, 11, 14, 17, 19, 22, 24, 25, *range(26, xlen - 2)],
                    #     xlen,
                    # ),
                    "mscratch": AnyValue(),
                    "mcycle": IncValue(),
                    "minstret": IncValue(),
                    # TODO test hpms
                    # TODO test shadow registers
                }

                # provide CSR behaviors
                for csr in self.csrs:
                    csr.behavior = csr_beh_map.get(csr.name, None)
                    csr.has_rvfi = True
                    csr.read_insn = True
                    csr.rw_test = True
                    self.csrs_to_define.add(csr.name)
                
                # TODO test restricted CSR addresses
                # restricted_csrs = {
                #     "medeleg": ("s", "302", []),
                #     "mideleg": ("s", "303", []),
                #     "mcounteren": ("u", "306", []),
                #     "mstatush": ("32", "310", [mask_bits("zero", [4, 5], xlen, invert=True)]),
                #     "mtinst": ("h", "34A", []),
                #     "mtval2": ("h", "34B", []),
                #     "menvcfg": ("u", "30A", []),
                #     "menvcfgh": ("u", "31A", []),  # u-mode only *and* 32bit only
                # }
                # for name, data in restricted_csrs.items():
                #     if data[0] in config.options.isa.mods:
                #         csr_line(name, *data[2])
                #     else:
                #         illegal_csr_line(data[1], "m", "rw")
            case spec:
                raise report.InputError(spec, f"unsupported CSR spec {spec!r}")

    def add_csr(self, value: Csr) -> None:
        if self.csrs is None:
            raise NotImplementedError()
        self.csrs.add(value)
