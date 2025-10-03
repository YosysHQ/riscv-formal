from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from textwrap import dedent
from typing import Optional

from ..named_set import NamedSet
from ..rvfi import SpeculativeObserver

@dataclass
class BehavioralReg(SpeculativeObserver):
    spec_value: Optional[str] = "0"
    default_value: str = "0"

class Behavior(metaclass=ABCMeta):
    @abstractmethod
    def regs(self, csr_width: str, csr_has_rvfi: bool) -> NamedSet[BehavioralReg]: pass

    @property
    def global_assumptions(self) -> list[str]:
        return []

    def global_code(self, csr_has_rvfi: bool) -> Optional[str]:
        return None

    @property
    def check_assumptions(self) -> list[str]:
        return []

    @property
    @abstractmethod
    def check_condition(self) -> str: pass

    @abstractmethod
    def check(self, csr_has_rvfi: bool) -> str: pass

    @property
    def assign_assumptions(self) -> list[str]:
        return []

    @property
    @abstractmethod
    def assign_condition(self) -> str: pass

    def assign(self, csr_has_rvfi: bool) -> Optional[str]:
        return None

    def _repr_args(self) -> str:
        return ""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._repr_args()})"

    def __json__(self) -> str:
        return repr(self)

class AnyValue(Behavior):
    def regs(self, csr_width: str, csr_has_rvfi: bool) -> NamedSet[BehavioralReg]:
        regs = NamedSet([
            BehavioralReg("rsval_shadow", csr_width, "csr_rsval"),
            BehavioralReg("csr_write_shadow", "1", "1"),
            BehavioralReg("csr_mode_shadow", "2", "csr_mode"),
            BehavioralReg("csr_mask_shadow", csr_width, None),
            # try to shadow CSR interface, with fallback to the writeback
            BehavioralReg("rdata_shadow", csr_width, "csr_insn_rdata" if csr_has_rvfi else "rvfi.rd_wdata"),
        ])
        return regs

    @property
    def check_assumptions(self) -> list[str]:
        return ["csr_write_shadow"]

    @property
    def check_condition(self) -> str:
        return "csr_read_valid && csr_insn_under_test"

    def check(self, csr_has_rvfi: bool) -> str:
        lhs = "csr_insn_rdata" if csr_has_rvfi else "rvfi.rd_wdata"
        check = dedent(f"""\
            case (csr_mode_shadow)
                2'b 00 /* None (ignored) */,
                2'b 01 /* RW */: assert({lhs} == rsval_shadow);
                2'b 10 /* RS */: assert(({lhs} & csr_mask_shadow) == csr_mask_shadow);
                2'b 11 /* RC */: assert(({lhs} & csr_mask_shadow) == '0);
            endcase
            // only mask bits are changed from prior read
            assert(({lhs} & ~csr_mask_shadow) == (rdata_shadow & ~csr_mask_shadow));""")
        return check

    @property
    def assign_condition(self) -> str:
        return "csr_write_valid && csr_insn_under_test"

    def assign(self, csr_has_rvfi: bool) -> Optional[str]:
        assign = "" if csr_has_rvfi else "assume(csr_read_valid);\n"
        assign += dedent("""\
            csr_mask_shadow = 
                /* RS */ csr_mode == 2'b 10 ? csr_insn_smask :
                /* RC */ csr_mode == 2'b 11 ? csr_insn_cmask : '1;""")
        return assign

class ConstValue(Behavior):
    def __init__(self, const_value: Optional[str | int] = None):
        if isinstance(const_value, int):
            self.const_value = f"'h {const_value:X}"
        else:
            self.const_value = const_value

    def _repr_args(self):
        return self.const_value

    def regs(self, csr_width: str, csr_has_rvfi: bool) -> NamedSet[BehavioralReg]:
        regs = NamedSet([
            BehavioralReg("csr_read_shadow", "1", "1"),
            BehavioralReg("csr_mode_shadow", "2", "csr_mode"),
            # try to shadow CSR interface, with fallback to the writeback
            BehavioralReg("rdata_shadow", csr_width, "csr_insn_rdata" if csr_has_rvfi else "rvfi.rd_wdata"),
        ])
        return regs

    @property
    def check_condition(self) -> str:
        return "csr_read_valid && csr_insn_under_test"

    def check(self, csr_has_rvfi: bool) -> str:
        check = ""
        if self.const_value is None:
            # fallback to compare against read value if we don't know the const
            check += "assume(csr_read_shadow);\n"
            rhs = "rdata_shadow" if csr_has_rvfi else "rvfi_wdata_shadow"
        else:
            rhs = self.const_value

        lhs = "csr_insn_rdata" if csr_has_rvfi else "rvfi.rd_wdata"
        check += f"assert({lhs} == {rhs});"
        return check

    @property
    def assign_condition(self) -> str:
        return "csr_read_valid && csr_insn_under_test"

class ZeroValue(ConstValue):
    def __init__(self):
        super().__init__(0)

    def _repr_args(self):
        return ""

class UpcntValue(Behavior):
    def __init__(self):
        self.comparison = ">"
    
    def regs(self, csr_width: str, csr_has_rvfi: bool) -> NamedSet[BehavioralReg]:
        if csr_has_rvfi:
            regs = NamedSet([
                BehavioralReg("csr_read_lo", "1", "1"),
                BehavioralReg("rdata_shadow", csr_width, "csr_insn_rdata"),
            ])
        else:
            regs = NamedSet([
                BehavioralReg("csr_read_hi", "1", "csr_hi"),
                BehavioralReg("csr_read_lo", "1", "csr_lo"),
                BehavioralReg("rdata_shadow", csr_width, "rvfi.rd_wdata"),
            ])
        regs.add(BehavioralReg("csr_written", "1", None))
        regs.add(BehavioralReg("wdata_shadow", csr_width, None))
        return regs

    @property
    def global_assumptions(self) -> list[str]:
        return []

    def global_code(self, csr_has_rvfi: bool) -> str:
        # no writes without read that could decrease the value manually
        return "if (csr_write_valid) assume(csr_read_valid);"

    @property
    def check_assumptions(self) -> list[str]:
        return ["csr_read_lo"]

    @property
    def check_condition(self) -> str:
        return "csr_read_valid && csr_insn_under_test"

    def check(self, csr_has_rvfi: bool) -> str:
        check = ""
        if csr_has_rvfi:
            lhs = "csr_insn_rdata"
            bitrange = ""
        else:
            lhs = "rvfi.rd_wdata"
            bitrange = "[31:0]"
            # currently only tests low half when not using rvfi signal
            check += "assume(csr_lo);\n"
        check += dedent(f"""\
                if (csr_written) begin
                    assume(wdata_shadow < 32'h F000_000);
                    assert({lhs} {self.comparison} wdata_shadow{bitrange});
                end else begin
                    assume(rdata_shadow < 32'h F000_000);
                    assert({lhs} {self.comparison} rdata_shadow{bitrange});
                end""")
        return check

    @property
    def assign_condition(self) -> str:
        return "csr_read_valid && csr_insn_under_test"

    def assign(self, csr_has_rvfi: bool) -> str:
        if not csr_has_rvfi:
            # incomplete wdata calculation without RVFI
            raise NotImplementedError()
        rhs = "csr_insn_wdata" if csr_has_rvfi else "csr_rsval"
        return dedent(f"""\
            if (csr_write_valid) begin
                wdata_shadow = {rhs};
                csr_written = 1;
            end else
                csr_written = 0;""")

class IncValue(UpcntValue):
    def __init__(self):
        self.comparison = ">="
