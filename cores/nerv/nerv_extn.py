from dataclasses import dataclass
from typing import Iterable

from riscv_formal.csrs import Csr, CsrSpec, MachineCsr
from riscv_formal.insns import Isa, Instruction, CsrInstruction
from riscv_formal.named_set import NamedSet

def dummy_csrs(isa_mods: Iterable[str]) -> NamedSet[Csr]:
    return NamedSet([
        MachineCsr(
            name = "dummy",
            width = "xlen",
            privilege = "MRW",
            index = 0xBC0,
        ),
        MachineCsr(
            name = "dummy_ro",
            width = "xlen",
            privilege = "MRO",
            index = 0xFC0,
        )
    ])

def dummy_test(
    name: str,
    funct3: str,
    result: str,
    csrs_accessed: list[str],
    spec_map: dict[str, str] = {}
) -> CsrInstruction:
    return CsrInstruction(
        name = name,
        insn_parts = [
            ("imm17", 17),
            ("funct3", 3),
            ("rd", 5),
            ("opcode", 7),
        ],
        opcode = "0001011", # custom-0 opcode space
        extension = "Xnerv",
        result = result,
        imm = "$signed({insn_imm17, 4'b0})",
        csrs_accessed = csrs_accessed,
        op_values = {
            "funct3": funct3,
        },
        spec_map = spec_map,
    )

def dummy_insns(isa_mods: Iterable[str]) -> NamedSet[Instruction]:
    return NamedSet([
        dummy_test(
            "dummy_test", "000",
            "rvfi_csr_dummy_rdata + insn_imm",
            ["dummy"],
        ),
    ])

CsrSpec.register_generator(dummy_csrs, "Xnerv")
Isa.register_dependency("Xnerv", "Zicsr")
Isa.register_generator(dummy_insns, "Xnerv")
