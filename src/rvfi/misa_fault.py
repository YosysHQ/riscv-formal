from textwrap import dedent
from typing import Optional

from ..checks import InstructionChecker
from ..insns import Instruction
from . import (
    Observer,
    SpeculativeObserver,
    SpeculativeEvaluation,
)

MISA_MAP = {
    "A": 1 <<  0, # Atomic
    "B": 1 <<  1, # Bit manipulation
    "C": 1 <<  2, # Compressed
    "D": 1 <<  3, # Double-precision float
    "E": 1 <<  4, # RV32E/64E base ISA
    "F": 1 <<  5, # Single-precision float
    "G": 1 <<  6, # -reserved-
    "H": 1 <<  7, # -reserved-
    "I": 1 <<  8, # RV32I/64I/128I base ISA
    "J": 1 <<  9, # -reserved-
    "K": 1 << 10, # -reserved-
    "L": 1 << 11, # -reserved-
    "M": 1 << 12, # Integer Muliply/Divide
    "N": 1 << 13, # User-level interrupts
    "O": 1 << 14, # -reserved-
    "P": 1 << 15, # Packed-SIMD
    "Q": 1 << 16, # Quad-precision float
    "R": 1 << 17, # -reserved-
    "S": 1 << 18, # Supervisor mode
    "T": 1 << 19, # -reserved-
    "U": 1 << 20, # User mode
    "V": 1 << 21, # Vector
    "W": 1 << 22, # -reserved-
    "X": 1 << 23, # Non-std extensions
    "Y": 1 << 24, # -reserved-
    "Z": 1 << 25, # -reserved-
}

for b_ext in ["Zba", "Zbb", "Zbs"]:
    MISA_MAP[b_ext] = MISA_MAP["B"]

MISA_MAP["Zca"] = MISA_MAP["C"]
MISA_MAP["Zcf"] = MISA_MAP["C"] | MISA_MAP["F"]

def misa_rmask_speculator(insn: Instruction) -> Optional[str]:
    ext = insn.extension
    try:
        misa_bit = MISA_MAP[ext.capitalize()]
    except (KeyError, AttributeError):
        return None
    else:
        return f"'b{misa_bit:026b}"

def weak_misa_fault_handler(observers: dict[str, Observer]) -> str:
    return dedent("""\
        // core *may* trap
        assert (rvfi.rd_addr == 0);
        assert (rvfi.rd_wdata == 0);
        assert (rvfi.mem_wdata == 0);""")

def strong_misa_fault_handler(observers: dict[str, Observer]) -> str:
    return dedent("""\
        // core *must* trap
        assert (rvfi.trap);
        assert (rvfi.rd_addr == 0);
        assert (rvfi.rd_wdata == 0);
        assert (rvfi.mem_wdata == 0);""")

InstructionChecker.register_check(
    SpeculativeEvaluation(
        "assert (checked_misa);",
        speculates_about = ["csr_misa_rmask"],
        ignore_trap = True,
    ))
InstructionChecker.register_verilog(dedent("""\
    wire checked_misa = ((spec_csr_misa_rmask & rvfi.csr_misa_rmask) == spec_csr_misa_rmask);
    wire misa_may_trap = checked_misa && ((rvfi.csr_misa_rdata & spec_csr_misa_rmask) == 0);"""))
InstructionChecker.register_speculator(
    SpeculativeObserver("csr_misa_rmask", "26"),
    misa_rmask_speculator)

def register_weak_misa():
    InstructionChecker.register_hw_trap("misa_may_trap && rvfi.trap", weak_misa_fault_handler)

def register_strong_misa():
    InstructionChecker.register_hw_trap("misa_may_trap", strong_misa_fault_handler)
