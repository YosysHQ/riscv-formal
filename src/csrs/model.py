from dataclasses import dataclass, field
from textwrap import dedent, indent
from typing import Optional

from ..checks.generic_checker import GenericChecker
from ..named_set import NamedSet
from ..rvfi import SpeculativeObserver

@dataclass(kw_only=True)
class Csr(GenericChecker):
    width: str
    privilege: Optional[str] = None
    index: Optional[int] = None
    indexh: Optional[int] = None

    has_rvfi: bool = False
    read_insn: bool = True

    def _v_insn_under_test(self) -> str:
        v_str = f"(csr_insn_addr == 12'h {self.index:X})"
        try:
            priv = self.privilege[0]
        except IndexError:
            # no privilege
            pass
        else:
            priv_mode = {
                "M": 3,
                "S": 1,
                "U": 0,
            }[priv]
            v_str += f" && (rvfi.mode >= {priv_mode})"
        return v_str

    def _v_insn_check(self, xlen: int) -> str:
        v_str = dedent(f"""\
            // insn mapping
            wire csr_insn_valid = rvfi.valid && (rvfi.insn[6:0] == 7'b 1110011) && (rvfi.insn[13:12] != 0) && ((rvfi.insn >> 16 >> 16) == 0);
            wire [11:0] csr_insn_addr = rvfi.insn[31:20];

            wire csr_write = !rvfi.insn[13] || rvfi.insn[19:15];
            wire csr_read = rvfi.insn[11:7] != 0;
            wire csr_write_valid = csr_write && csr_insn_valid && !rvfi.trap;
            wire csr_read_valid = csr_read && csr_insn_valid && !rvfi.trap;

            wire [1:0] csr_mode = rvfi.insn[13:12];
            wire [{xlen-1}:0] csr_rsval = rvfi.insn[14] ? rvfi.insn[19:15] : rvfi.rs1_rdata;
            wire csr_insn_under_test = (""")

        v_str += self._v_insn_under_test() + ");\n"

        return v_str

    def _v_rvfi_map(self, xlen: int) -> str:
        v_str = "// rvfi mapping\n"
        for val in ["rmask", "wmask", "rdata", "wdata"]:
            v_str += f"wire [{xlen-1}:0] csr_insn_{val} = rvfi.csr_{self.name}_{val};\n"
        return v_str

    def _v_signal_map(self, xlen: int) -> str:
        v_str = dedent("""\
            // setup for csrs
            localparam [11:0] csr_none = 12'hFFF;
            """)

        if self.has_rvfi:
            v_str += "\n" + self._v_rvfi_map(xlen)

        if self.read_insn:
            v_str += "\n" + self._v_insn_check(xlen)

        return v_str

    def _behavioral_regs(self) -> NamedSet[SpeculativeObserver]:
        regs = NamedSet([
            SpeculativeObserver("rsval_shadow", "`RISCV_FORMAL_XLEN"),
            SpeculativeObserver("csr_written", "1"),
            SpeculativeObserver("csr_mode_shadow", "2"),
        ])
        if self.has_rvfi:
            regs.add(SpeculativeObserver("wdata_shadow", "`RISCV_FORMAL_XLEN"))
        return regs

    def _v_process(self) -> str:
        v_str = "// setup for testing\n"

        resets: list[str] = []
        for reg in self._behavioral_regs():
            reset = f"{reg.name} = {reg.spec_value};"
            v_str += f"reg {reg.bitrange()} {reset}\n"
            resets.append(reset)
        reset_str = "\n                    ".join(resets)

        if self.has_rvfi:
            assign_str = dedent("""
                rsval_shadow = csr_rsval;
                wdata_shadow = csr_insn_wdata;
                csr_written = 1;
                csr_mode_shadow = csr_mode;""")
            check_str = dedent("""
                case (csr_mode_shadow)
                    2'b 00 /* None */,
                    2'b 01 /* RW   */: begin
                        assert(rsval_shadow == csr_insn_rdata || csr_insn_rdata == wdata_shadow);
                        assert(rsval_shadow == wdata_shadow);
                    end
                    // Currently not testing set/clear from rsval
                    2'b 10 /* RS   */,
                    2'b 11 /* RC   */: begin assert(csr_insn_rdata == wdata_shadow); end
                endcase""")
        else:
            assign_str = dedent("""
                    rsval_shadow = csr_rsval;
                    csr_written = 1;
                    csr_mode_shadow = csr_mode;""")
            check_str = dedent("""
                assume(csr_mode_shadow <= 2'b 01);
                assume(rvfi.rd_addr != 0);
                case (csr_mode_shadow)
                    2'b 00 /* None */,
                    2'b 01 /* RW   */: begin
                        assert(rsval_shadow == rvfi.rd_wdata);
                    end
                    // Currently not testing set/clear from rsval
                    2'b 10 /* RS   */,
                    2'b 11 /* RC   */: begin assert(0); end
                endcase""")

        assign_str = indent(assign_str, "                            ")
        check_str = indent(check_str, "                            ")

        v_str += dedent(f"""
            // test
            always @(posedge clock) begin
                if (reset) begin
                    {reset_str}
                end else begin
                    if (check) begin
                        assume(csr_written);
                        if (csr_written && csr_read_valid && csr_insn_under_test) begin{check_str}
                        end
                    end else begin
                        if (csr_write_valid && csr_insn_under_test) begin{assign_str}
                        end
                    end
                end
            end
            """)
        return v_str

    def _v_body(self, xlen: int) -> str:
        v_str = self._v_format_block(self._v_rvfi_channel())
        v_str += self._v_format_block(self._v_signal_map(xlen))
        v_str += self._v_format_block(self._v_process())
        return v_str

@dataclass(kw_only=True)
class ShadowCsr(Csr):
    source: str


@dataclass(kw_only=True)
class MachineCsr(Csr):
    shadows: NamedSet[ShadowCsr] = field(default_factory=NamedSet)

    def shadow(self, name: str, privilege: str,
               index: int, indexh: Optional[int] = None,
               **kwargs
        ) -> ShadowCsr:
        shadow = ShadowCsr(
            name = name,
            width = self.width,
            privilege = privilege,
            index = index,
            indexh = indexh,
            source = self.name,
            **kwargs
        )
        self.shadows.add(shadow)
        return shadow


def csr(name: str, width: str, privilege: str, index: int, indexh: Optional[int] = None) -> Csr:
    return Csr(
        name = name,
        width = width,
        privilege = privilege,
        index = index,
        indexh = indexh,
    )

def mcsr(name: str, width: str, privilege: str, index: int, indexh: Optional[int] = None) -> MachineCsr:
    return MachineCsr(
        name = name,
        width = width,
        privilege = privilege,
        index = index,
        indexh = indexh,
    )

def mcsr_with_shadow(mname: str, width: str,  mprivilege: str, mindex: int, mindexh: Optional[int],
                     sname: str,              sprivilege: str, sindex: int, sindexh: Optional[int],
    ) -> tuple[MachineCsr, Csr]:
    machinecsr = mcsr(mname, width, mprivilege, mindex, mindexh)
    shadow = machinecsr.shadow(sname, sprivilege, sindex, sindexh)
    return (machinecsr, shadow)

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
        mcsr("medeleg",       "xlen", "MRW", 0x302),
        mcsr("mideleg",       "xlen", "MRW", 0x303),
        mcsr("mie",           "xlen", "MRW", 0x304),
        mcsr("mtvec",         "xlen", "MRW", 0x305),
        mcsr("mcounteren",    "xlen", "MRW", 0x306),
        mcsr("mscratch",      "xlen", "MRW", 0x340),
        mcsr("mepc",          "xlen", "MRW", 0x341),
        mcsr("mcause",        "xlen", "MRW", 0x342),
        mcsr("mtval",         "xlen", "MRW", 0x343),
        mcsr("mip",           "xlen", "MRW", 0x344),
        mcsr("mtinst",        "xlen", "MRW", 0x34A),
        mcsr("mtval2",        "xlen", "MRW", 0x34B),
        mcsr("mcountinhibit", "xlen", "MRW", 0x320),
        mcsr("menvcfg",       "xlen", "MRW", 0x30A),
        mcsr("menvcfgh",      "xlen", "MRW", 0x31A),
        *mcsr_with_shadow(
             "mcycle",          "64", "MRW", 0xB00, 0xB80,
             "cycle",                 "URO", 0xC00, 0xC80,
        ),
        csr("time",             "64", "URO", 0xC01, 0xC81),
        *mcsr_with_shadow(
             "minstret",        "64", "MRW", 0xB02, 0xB82,
             "instret",               "URO", 0xC02, 0xC82,
        ),
    ])

def hpm_csrs(max_idx: int = 32) -> NamedSet[Csr]:
    return NamedSet([
        *(
            Csr(f"mhpmevent{i}", "xlen", 0x320 + i,  None,  None)
            for i in range(3, max_idx)
        ),
        *(
            Csr(f"mhpmcounter{i}", "64", 0xB00 + i, None, 0xC00 + i,
                                         0xB80 + i, None, 0xC80 + i)
            for i in range(3, max_idx)
        ),
    ])

def pmp_csrs(entries: int = 64) -> NamedSet[Csr]:
    return NamedSet([
        *(
            MachineCsr(f"pmpcfg{i}",    "xlen", "MRW", 0x3A0 + i)
            for i in range(entries >> 2)
        ),
        *(
            MachineCsr(f"pmpaddr{i}",   "xlen", "MRW", 0x3B0 + i)
            for i in range(entries)
        ),
    ])

def fext_csrs() -> NamedSet[Csr]:
    return NamedSet([
        Csr("fflags",            "xlen",  None,  None,  None),
        Csr("frm",               "xlen",  None,  None,  None),
        Csr("fcsr",              "xlen",  None,  None,  None),
    ])
