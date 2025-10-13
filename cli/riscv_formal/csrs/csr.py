from dataclasses import dataclass, field
from textwrap import dedent, indent
from typing import Optional

from riscv_formal.generic_checker import GenericChecker
from riscv_formal.named_set import NamedSet
from riscv_formal.rvfi import Observer
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
    is_accessible: bool = True

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

    def make_observers(self) -> NamedSet[Observer]:
        if self.has_rvfi:
            return NamedSet([
                Observer(f"csr_{self.name}_{val}", self.width)
                    for val in ["rmask", "wmask", "rdata", "wdata"]
            ])
        else:
            return NamedSet()

    def _v_modname(self) -> str:
        return "rvfi_csr_check"

    @property
    def read_write(self) -> bool:
        assert self.privilege is not None
        return self.privilege[1:] == "RW"

    @property
    def min_priv(self) -> str:
        assert self.privilege is not None
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

    def _v_access_check(self, prefix: str = "csr") -> str:
        v_str = f"\nwire {prefix}_lo = {self._v_insn_csr_idx(hi=False)};\n"
        if self.indexh is not None:
            v_str += dedent(f"""\
                wire {prefix}_hi = {self._v_insn_csr_idx(hi=True)} && rvfi.ixl == 1;
                wire {prefix}_access = ({prefix}_hi || {prefix}_lo);
            """)
        else:
            v_str += f"wire {prefix}_access = {prefix}_lo;\n"
        v_str += f"wire {prefix}_insn_under_test = {prefix}_access && {self._v_insn_priv_check()};\n"
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
        """)

        if self.is_accessible:
            v_str += dedent(f"""\
                wire [1:0] csr_mode = rvfi.insn[13:12];
                wire [{xlen-1}:0] csr_rsval = rvfi.insn[14] ? rvfi.insn[19:15] : rvfi.rs1_rdata;

                wire [{xlen-1}:0] csr_insn_smask =
                    /* CSRRW, CSRRWI */ (rvfi.insn[13:12] == 1) ? csr_rsval :
                    /* CSRRS, CSRRSI */ (rvfi.insn[13:12] == 2) ? csr_rsval : 0;

                wire [{xlen-1}:0] csr_insn_cmask =
                    /* CSRRW, CSRRWI */ (rvfi.insn[13:12] == 1) ? ~csr_rsval :
                    /* CSRCS, CSRRCI */ (rvfi.insn[13:12] == 3) ? csr_rsval : 0;
            """)

        v_str += self._v_access_check()

        return v_str

    def _normalized_width(self, xlen: int) -> int:
        return 64 if (self.width == "64" and xlen == 32) else xlen

    def _v_rvfi_assign(self, val: str, xlen: int, prefix: str = "csr_insn") -> str:
        width = self._normalized_width(xlen)
        if self.name in WIDE_CSRS or self.width == "xlen" or xlen > 32:
            rhs = f"rvfi.csr_{self.name}_{val}"
        else:
            raise NotImplementedError()
        return f"wire [{width-1}:0] {prefix}_{val} = {rhs};\n"

    def _v_rvfi_map(self, xlen: int) -> str:
        v_str = "// rvfi mapping\n"
        for val in ["rmask", "wmask", "rdata", "wdata"]:
            v_str += self._v_rvfi_assign(val, xlen)
        return v_str

    def _v_ill_test(self) -> str:
        # TODO maybe legal accesses?
        return dedent(f"""\
            // no legal accesses
            always @* begin
                if (!reset && check) begin
                    assume (csr_insn_valid);
                    assume (csr_access);
                    assert (!csr_write_valid);
                    assert (!csr_read_valid);
                end
            end
        """)

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
        assert self.behavior is not None

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
        if self.has_rvfi:
            v_str += self._v_format_block(self._v_rvfi_map(xlen))
        if self.read_insn:
            v_str += self._v_format_block(self._v_insn_check(xlen))
        if self.rw_test:
            if not self.is_accessible:
                v_str += self._v_format_block(self._v_ill_test())
            elif self.has_rvfi:
                v_str += self._v_format_block(self._v_rw_test(xlen))
            else:
                raise NotImplementedError()
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


@dataclass(kw_only=True)
class HpmeventCsr(Csr):
    counter: MachineCsr

    event_counter_map: dict[str, str] = field(default_factory=dict)

    def _v_insn_check(self, xlen):
        v_str = super()._v_insn_check(xlen)
        v_str += self.counter._v_access_check("hpmcounter")
        return v_str

    def _v_rvfi_map(self, xlen: int) -> str:
        v_str = super()._v_rvfi_map(xlen)
        v_str += self.counter._v_rvfi_assign("rdata", xlen, "hpmcounter")
        return v_str

    def _v_hpm_check(self, xlen: int) -> str:
        event_width = self._normalized_width(xlen)
        counter_width = self.counter._normalized_width(xlen)
        valid_events: list[str] = []
        counter_checks: list[str] = []
        for cond, check in self.event_counter_map.items():
            counter_check = f"if ({cond}) begin\n"
            counter_check += self._v_format_block(check)
            counter_check += "end"
            counter_checks.append(counter_check)
            valid_events.append(cond)
        counter_checks_str = indent("\n".join(counter_checks), "                            ")
        valid_events_str = " || ".join(valid_events)
        return dedent(f"""\
            // HPM check
            `rvformal_rand_const_reg [63:0] insn_order;
            reg [{counter_width-1}:0] csr_hpmcounter_shadow;
            reg csr_hpmevent_written;
            reg [{event_width-1}:0] csr_hpmevent_shadow;

            always @(posedge clock) begin
                if (reset) begin
                    csr_hpmcounter_shadow = 0;
                    csr_hpmevent_written = 0;
                    csr_hpmevent_shadow = 0;
                end else begin
                    if (csr_hpmevent_written) begin
                        // one of the events under test was written
                        assume({valid_events_str});
                        // no further writes allowed
                        assume(!(csr_write_valid && (hpmcounter_insn_under_test || csr_insn_under_test)));
                        // check readback of counter
                        if (csr_read_valid && hpmcounter_insn_under_test) begin\n{counter_checks_str}
                        end
                    end
                    if (csr_write_valid && csr_insn_under_test) begin
                        assume(hpmcounter_rdata < 32'h F000_000);
                        csr_hpmcounter_shadow = hpmcounter_rdata;
                        csr_hpmevent_written = 1;
                        csr_hpmevent_shadow = csr_insn_wdata;
                    end
                end
            end
        """)

    def _v_body(self, xlen: int) -> str:
        v_str = super()._v_body(xlen)
        if self.event_counter_map:
            v_str += self._v_format_block(self._v_hpm_check(xlen))
        return v_str
