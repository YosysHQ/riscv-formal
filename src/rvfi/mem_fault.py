from textwrap import dedent

from ..checks.instruction_checker import InstructionChecker
from .observer import Observer

def mem_fault_handler(observers: dict[str, Observer]) -> str:
    return dedent("""\
        assert (rvfi.trap);
        assert (rvfi.rd_addr == 0);
        assert (rvfi.rd_wdata == 0);
        assert (rvfi.mem_wmask == 0);
        assert (rvfi.mem_rmask == 0);
        assert (spec_mem_wmask || spec_mem_rmask);
        assert (`rvformal_addr_eq(spec_mem_addr, rvfi.mem_addr));

        assert (rvfi.mem_fault_wmask == spec_mem_wmask);
        assert ((rvfi.mem_fault_rmask & spec_mem_rmask) == spec_mem_rmask);""")

InstructionChecker.register_hw_trap("rvfi.mem_fault", mem_fault_handler)
