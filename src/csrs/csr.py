from dataclasses import dataclass, field
from textwrap import dedent, indent
from typing import Optional

from ..checks.generic_checker import GenericChecker
from ..named_set import NamedSet
from .behavior import Behavior

WIDE_CSRS = [
    "mcycle",
    "minstret",
    *( f"mhpmcounter{i}" for i in range(3, 32) ),
]

@dataclass(kw_only=True)
class Csr(GenericChecker):
    width: str
    privilege: Optional[str] = None
    index: Optional[int] = None
    indexh: Optional[int] = None

    has_rvfi: bool = False
    read_insn: bool = True
    rw_test: bool = False

    behavior: Optional[Behavior] = None

    @property
    def min_priv_level(self) -> int:
        return {
            "M": 3,
            "H": 2,
            "S": 1,
            "U": 0,
        }[self.min_priv]

    def __post_init__(self):
        super().__post_init__()

        # auto assign privilege
        for idx in [self.index, self.indexh]:
            if idx is None: continue
            bindex = f"{idx:012b}"
            read_bin = bindex[0:2] # csr[11:10]
            priv_bin = bindex[2:4] # csr[ 9: 8]
            priv_level = ["U", "S", "H", "M"][int(priv_bin, 2)]
            read_write = "RO" if read_bin == "11" else "RW"
            auto_priv = priv_level + read_write
            if self.privilege is None:
                self.privilege = auto_priv

        # check privilege
        try:
            valid_priv = (
                self.privilege[0] in ["U", "S", "H", "M"] and
                self.privilege[1:] in ["RO", "RW"])
        except IndexError:
            valid_priv = False
        if not valid_priv:
            raise NotImplementedError()

    def _v_modname(self) -> str:
        return "rvfi_csr_check"

    @property
    def read_write(self) -> bool:
        return self.privilege[1:] == "RW"

    @property
    def min_priv(self) -> str:
        return self.privilege[0]

    def _v_insn_priv_check(self) -> Optional[str]:
        return f"rvfi.mode >= {self.min_priv_level}"

    def _v_insn_csr_idx(self, hi: bool) -> str:
        idx = self.indexh if hi else self.index
        try:
            return f"csr_insn_addr == 12'h {idx:X}"
        except TypeError:
            #indexh is None
            return "0"

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

            wire [{xlen-1}:0] csr_insn_smask =
                /* CSRRW, CSRRWI */ (rvfi.insn[13:12] == 1) ? csr_rsval :
                /* CSRRS, CSRRSI */ (rvfi.insn[13:12] == 2) ? csr_rsval : 0;

            wire [{xlen-1}:0] csr_insn_cmask =
                /* CSRRW, CSRRWI */ (rvfi.insn[13:12] == 1) ? ~csr_rsval :
                /* CSRCS, CSRRCI */ (rvfi.insn[13:12] == 3) ? csr_rsval : 0;

            wire csr_lo = {self._v_insn_csr_idx(hi=False)};
        """)

        if self.indexh is not None:
            v_str += dedent(f"""\
                wire csr_hi = {self._v_insn_csr_idx(hi=True)} && rvfi.ixl == 1;
                wire csr_access = (csr_hi || csr_lo);
            """)
        else:
            v_str += f"wire csr_access = csr_lo;\n"
        v_str += f"wire csr_insn_under_test = csr_access && {self._v_insn_priv_check()};\n"

        return v_str

    def _v_rvfi_map(self, xlen: int) -> str:
        v_str = "// rvfi mapping\n"
        for val in ["rmask", "wmask", "rdata", "wdata"]:
            width = 64 if (self.width == "64" and xlen == 32) else xlen
            if self.name in WIDE_CSRS or self.width == "xlen" or xlen > 32:
                rhs = f"rvfi.csr_{self.name}_{val}"
            else:
                raise NotImplementedError()
            v_str += f"wire [{width-1}:0] csr_insn_{val} = {rhs};\n"
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

    def _v_rw_test(self, xlen: int) -> str:
        csr_illacc = f"rvfi.mode < {self.min_priv_level}"
        if not self.read_write:
            csr_illacc += " || csr_write"
        v_str = dedent(f"""\
            // read/write testing
            wire csr_illacc = csr_insn_valid && ({csr_illacc});
            wire [{xlen-1}:0] effective_csr_insn_wmask = csr_insn_rmask | csr_insn_wmask;
            wire [{xlen-1}:0] effective_csr_insn_wdata = (csr_insn_wdata & csr_insn_wmask) | (csr_insn_rdata & ~csr_insn_wmask);

            // CSR accesses are (currently) only valid in non-C instructions and never jump
            wire [{xlen-1}:0] spec_pc_wdata = rvfi.pc_rdata + 4;

            always @* begin
                if (!reset && check) begin
                    // checked instruction is a well formed access to CSR under test
                    assume (csr_insn_valid);
                    assume (csr_insn_addr != csr_none);
                    assume (csr_access);

                    if (!`rvformal_addr_valid(rvfi.pc_rdata) || csr_illacc) begin
                        // an illegal csr access must trap
                        assert (rvfi.trap);
                        assert (rvfi.rd_addr == 0);
                        assert (rvfi.rd_wdata == 0);
                    end else begin
                        assert (!rvfi.trap);

                        // check rd/rs access
                        assert (rvfi.rd_addr == rvfi.insn[11:7]);
                        if (rvfi.insn[14] == 0) assert (rvfi.rs1_addr == rvfi.insn[19:15]);

                        // check pc
                        assert (`rvformal_addr_eq(rvfi.pc_wdata, spec_pc_wdata));

                        // bits that should have been read were
                        if (rvfi.rd_addr == 0) begin
                            assert (rvfi.rd_wdata == 0);
                        end else begin
                            assert (csr_insn_rmask == {{{xlen}{{1'b1}}}});
                            assert (csr_insn_rdata == rvfi.rd_wdata);
                        end

                        // bits that should have been written were
                        assert (((csr_insn_smask | csr_insn_cmask) & ~effective_csr_insn_wmask) == 0);
                        assert ((csr_insn_smask & ~effective_csr_insn_wdata) == 0);
                        assert ((csr_insn_cmask & effective_csr_insn_wdata) == 0);
                    end

                    // csr accesses are never considered memory writes on RVFI
                    assert (rvfi.mem_wmask == 0);
                end
            end
            """)
        
        return v_str

    def _v_process(self, xlen: int) -> str:
        v_str = "// setup for testing\n"

        reg_width = "64" if (self.width == "64" and xlen == 32) else "xlen"

        resets: list[str] = []
        assigns: list[str] = []
        for reg in self.behavior.regs(reg_width, self.has_rvfi):
            reset = f"{reg.name} = {reg.default_value};"
            v_str += f"reg {reg.bitrange()} {reset}\n"
            resets.append(reset)
            if not self.has_rvfi and reg_width == "64" and reg.spec_value == "rvfi.rd_wdata":
                assigns.append(f"if (csr_hi) {reg.name}[63:32] = {reg.spec_value};")
                assigns.append(f"if (csr_lo) {reg.name}[31: 0] = {reg.spec_value};")
            elif reg.spec_value is not None:
                assigns.append(f"{reg.name} = {reg.spec_value};")
        reset_str = "\n                    ".join(resets)
        assign_str = "\n                            ".join(assigns)

        global_assumes_str = ""
        for assumption in self.behavior.global_assumptions:
            global_assumes_str += f"\n                    assume({assumption});"

        check_assumes_str = ""
        for assumption in self.behavior.check_assumptions:
            check_assumes_str += f"\n                        assume({assumption});"

        assign_assumes_str = ""
        for assumption in self.behavior.assign_assumptions:
            assign_assumes_str += f"\n                            assume({assumption});"

        check_str = indent(self.behavior.check(self.has_rvfi), "                            ")

        global_code = self.behavior.global_code(self.has_rvfi)
        if global_code:
            global_assumes_str += "\n" + indent(global_code, "                    ")

        assign_code = self.behavior.assign(self.has_rvfi)
        if assign_code:
            assign_assumes_str += "\n" + indent(assign_code, "                            ")

        v_str += dedent(f"""
            // test behaviour
            always @(posedge clock) begin
                if (reset) begin
                    {reset_str}
                end else begin{global_assumes_str}
                    if (check) begin{check_assumes_str}
                        if ({self.behavior.check_condition}) begin\n{check_str}
                        end
                    end else begin
                        if ({self.behavior.assign_condition}) begin{assign_assumes_str}
                            {assign_str}
                        end
                    end
                end
            end
            """)
        return v_str

    def _v_body(self, xlen: int) -> str:
        v_str = self._v_format_block(self._v_rvfi_channel())
        v_str += self._v_format_block(self._v_signal_map(xlen))
        if self.rw_test:
            if not self.has_rvfi:
                raise NotImplementedError()
            v_str += self._v_format_block(self._v_rw_test(xlen))
        if self.behavior:
            v_str += self._v_format_block(self._v_process(xlen))
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
        mcsr("mie",           "xlen", "MRW", 0x304),
        mcsr("mtvec",         "xlen", "MRW", 0x305),
        mcsr("mscratch",      "xlen", "MRW", 0x340),
        mcsr("mepc",          "xlen", "MRW", 0x341),
        mcsr("mcause",        "xlen", "MRW", 0x342),
        mcsr("mtval",         "xlen", "MRW", 0x343),
        mcsr("mip",           "xlen", "MRW", 0x344),
        mcsr("mcountinhibit", "xlen", "MRW", 0x320),
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

def hpm_csrs(max_idx: int = 32) -> NamedSet[Csr]:
    csr_list: list[Csr] = []
    for i in range(3, max_idx):
        csr_list.append(mcsr(f"mhpmevent{i}", "xlen", "MRW", 0x320 + i))
        csr_list.extend(mcsr_with_shadow(
            f"mhpmcounter{i}", "64", "MRW", 0xB00 + i, 0xB80 + i,
            f"hpmcounter{i}",        "URO", 0xC00 + i, 0xC80 + i)
        )
    return NamedSet(csr_list)

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
