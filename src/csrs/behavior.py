from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from textwrap import dedent
from typing import Optional

from ..named_set import NamedSet
from ..rvfi import SpeculativeObserver

@dataclass
class BehavioralReg(SpeculativeObserver):
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
            BehavioralReg("csr_written", "1", "1"),
            BehavioralReg("csr_mode_shadow", "2", "csr_mode"),
        ])
        if csr_has_rvfi:
            regs.add(BehavioralReg("wdata_shadow", csr_width, "csr_insn_wdata"))
        return regs

    @property
    def check_assumptions(self) -> list[str]:
        return ["csr_written"]

    @property
    def check_condition(self) -> str:
        return "csr_read_valid && csr_insn_under_test"

    def check(self, csr_has_rvfi: bool) -> str:
        if csr_has_rvfi:
            return dedent("""\
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
            return dedent("""\
                assume(csr_mode_shadow <= 2'b 01);
                case (csr_mode_shadow)
                    2'b 00 /* None */,
                    2'b 01 /* RW   */: begin
                        assert(rsval_shadow == rvfi.rd_wdata);
                    end
                    // Currently not testing set/clear from rsval
                    2'b 10 /* RS   */,
                    2'b 11 /* RC   */: begin assert(0); end
                endcase""")

    @property
    def assign_condition(self) -> str:
        return "csr_write_valid && csr_insn_under_test"

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
        ])
        if csr_has_rvfi:
            # try to shadow CSR interface
            regs.add(BehavioralReg("rdata_shadow", csr_width, "csr_insn_rdata"))
        else:
            # fallback to shadowing the writeback
            regs.add(BehavioralReg("rvfi_wdata_shadow", csr_width, "rvfi.rd_wdata"))
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
        return regs

    @property
    def global_assumptions(self) -> list[str]:
        return ["!(csr_write_valid && csr_insn_under_test)"]

    @property
    def check_assumptions(self) -> list[str]:
        return ["csr_read_lo"]

    @property
    def check_condition(self) -> str:
        return "csr_read_valid && csr_insn_under_test"

    def check(self, csr_has_rvfi: bool) -> str:
        if csr_has_rvfi:
            return dedent("""\
                assert(csr_insn_rdata > rdata_shadow);""")
        else:
            return dedent("""\
                // currently only tests low half when not using rvfi signal
                assume(csr_lo);
                assert(rvfi.rd_wdata > rdata_shadow[31:0]);""")

    @property
    def assign_assumptions(self) -> list[str]:
        return ["rdata_shadow < 32'h F000_0000"]

    @property
    def assign_condition(self) -> str:
        return "csr_read_valid && csr_insn_under_test"
