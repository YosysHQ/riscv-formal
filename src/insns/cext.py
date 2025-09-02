from dataclasses import dataclass

from .model import Instruction, Instruction_format

FORMAT_CR = Instruction_format(
    "CR-type", [
        ("funct4", 4),
        ("rsd", 5),
        ("rs2", 5),
        ("opcode", 2),
    ],
)

FORMAT_CI = Instruction_format(
    "CI-type", [
        ("funct3", 3),
        ("imm1", 1),
        ("rsd", 5),
        ("imm5", 5),
        ("opcode", 2),
    ],
    imm = "$signed({imm1, imm5})"
)

FORMAT_CSS = Instruction_format(
    "CSS-type", [
        ("funct3", 3),
        ("imm6", 6),
        ("rs2", 5),
        ("opcode", 2),
    ],
)

FORMAT_CIW = Instruction_format(
    "CIW-type", [
        ("funct3", 3),
        ("imm8", 8),
        ("crd", 3),
        ("opcode", 2),
    ],
)

FORMAT_CL = Instruction_format(
    "CL-type", [
        ("funct3", 3),
        ("imm3", 3),
        ("crs1", 3),
        ("imm2", 2),
        ("crd", 3),
        ("opcode", 2),
    ],
)

FORMAT_CS = Instruction_format(
    "CS-type", [
        ("funct3", 3),
        ("imm3", 3),
        ("crs1", 3),
        ("imm2", 2),
        ("crs2", 3),
        ("opcode", 2),
    ],
)

FORMAT_CA = Instruction_format(
    "CA-type", [
        ("funct6", 6),
        ("crsd", 3),
        ("funct2", 2),
        ("crs2", 3),
        ("opcode", 2),
    ],
)

FORMAT_CB = Instruction_format(
    "CB-type", [
        ("funct3", 3),
        ("offset4", 4),
        ("crsd", 3),
        ("offset5", 5),
        ("opcode", 2),
    ],
)

FORMAT_CJ = Instruction_format(
    "CJ-type", [
        ("funct3", 3),
        ("target", 11),
        ("opcode", 2),
    ],
)

# Inject instruction padding checks
def assign_padding(self: Instruction) -> str:
    assignment = "wire [`RISCV_FORMAL_ILEN-1:0] insn_padding = "
    if self.ilen == 16:
        assignment += "rvfi_insn >> 16;"
    elif self.ilen == 32:
        assignment += "rvfi_insn >> 16 >> 16;"
    else:
        raise NotImplementedError(self.ilen)
    return assignment

Instruction.register_assign("padding", assign_padding)
Instruction.register_check("!insn_padding")

@dataclass(kw_only=True)
class C_Instruction(Instruction):
    ilen: int = 16
    opcode_width: int = 2

    _default_pc_increment: str = "rvfi_pc_rdata + 2"


def cext():
    return {i.name: i for i in [
        C_Instruction(
            name = "c_li", insn_parts = FORMAT_CI, opcode = "01", extension = "C",
            result = "insn_imm", imm = True,
        ),
    ]}
