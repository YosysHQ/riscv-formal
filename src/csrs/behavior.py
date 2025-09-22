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
        return "csr_written && csr_read_valid && csr_insn_under_test"

    def check(self, csr_has_rvfi: bool) -> str:
        if csr_has_rvfi:
            return dedent("""
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
            return dedent("""
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

    @property
    def assign_condition(self) -> str:
        return "csr_write_valid && csr_insn_under_test"

class UpcntValue(Behavior):
    def regs(self, csr_width: str, csr_has_rvfi: bool) -> NamedSet[BehavioralReg]:
        regs = NamedSet([
            BehavioralReg("csr_read_shadowed", "1", "1"),
        ])
        if csr_has_rvfi:
            regs.add(BehavioralReg("rdata_shadow", csr_width, "csr_insn_rdata"))
        else:
            regs.add(BehavioralReg("rdata_shadow", csr_width, "rvfi.rd_wdata"))
        return regs

    @property
    def global_assumptions(self) -> list[str]:
        return ["!(csr_write_valid && csr_insn_under_test)"]

    @property
    def check_assumptions(self) -> list[str]:
        return ["csr_read_shadowed"]

    @property
    def check_condition(self) -> str:
        return "csr_read_valid && csr_insn_under_test"

    def check(self, csr_has_rvfi: bool) -> str:
        if csr_has_rvfi:
            return dedent("""
                assert(csr_insn_rdata > rdata_shadow);""")
        else:
            return dedent("""
                assume(0);""")

    @property
    def assign_assumptions(self) -> list[str]:
        return ["rdata_shadow < 32'h F000_0000"]

    @property
    def assign_condition(self) -> str:
        return "csr_read_valid && csr_insn_under_test"
