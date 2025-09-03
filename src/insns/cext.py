from dataclasses import dataclass
from typing import Optional

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
    imm = "$signed({insn_imm1, insn_imm5})"
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
    imm = "{insn_imm8[5:2], insn_imm8[7:6], insn_imm8[0], insn_imm8[1], 2'b00}"
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

    read_rsd: Optional[bool] = None
    rd_reg: Optional[int] = None
    rs1_reg: Optional[int] = None

    _default_pc_increment: str = "rvfi_pc_rdata + 2"

    def _config_used_regs(self):
        super()._config_used_regs()
        for inst_arg in self.inst_args:
            if inst_arg.startswith('c'):
                inst_arg = inst_arg[1:]
            if inst_arg == "rsd":
                if self.read_rsd:
                    self._used_regs.append("rs1")
                if self.result is not None:
                    self._used_regs.append("rd")
            elif inst_arg in self._maybe_sources + self._maybe_dests:
                self._used_regs.append(inst_arg)
        if self.rs1_reg:
            self._used_regs.append("rs1")

    def _v_insn_map(self, xlen):
        v_str = super()._v_insn_map(xlen) + '\n'
        if self.rd_reg:
            v_str += f"wire [4:0] insn_rd = 5'd{self.rd_reg};\n"
        if self.rs1_reg:
            v_str += f"wire [4:0] insn_rs1 = 5'd{self.rs1_reg};\n"
        if "rsd" in self.inst_args:
            if self.read_rsd:
                v_str += f"wire [4:0] insn_rs1 = insn_rsd;\n"
            if self.result is not None and self.rd_reg is None:
                v_str += f"wire [4:0] insn_rd = insn_rsd;\n"
        if "crd" in self.inst_args:
            v_str += "wire [4:0] insn_rd = {2'b01, insn_crd};\n"
        if "crs1" in self.inst_args:
            v_str += "wire [4:0] insn_rs1 = {2'b01, insn_crs1};\n"
        if "crs2" in self.inst_args:
            v_str += "wire [4:0] insn_rs2 = {2'b01, insn_crs2};\n"
        return v_str[:-1]


def insn_c_l(insn, funct3, numbytes, is_float = False, extension = "C"):
    result_width = numbytes*8
    if numbytes == 4:
        imm = "{insn_imm2[0], insn_imm3, insn_imm2[1], 2'b 00}"
    elif numbytes == 8:
        imm = "{insn_imm2, insn_imm3, 3'b000}"
    elif numbytes == 16:
        imm = "{insn_imm3[0], insn_imm2, insn_imm3[2:1], 4'b000}"
    else:
        raise NotImplementedError(numbytes)
    return C_Instruction(
        name = insn,
        insn_parts = FORMAT_CL,
        opcode = "00",
        extension = extension,
        op_values = {
            "funct3": funct3,
        },
        mem_addr = "rvfi_rs1_rdata + insn_imm",
        mem_bytes = numbytes,
        result = "mem_rdata",
        imm = imm,
        sign_extend_from = result_width if not is_float else None,
        xlen_min = max(32, result_width) if not is_float else 32,
        xlen_max = max(32, result_width) if is_float else 128,
    )


def insn_c_s(insn, funct3, numbytes, is_float = False, extension = "C"):
    result_width = numbytes*8
    if numbytes == 4:
        imm = "{insn_imm2[0], insn_imm3, insn_imm2[1], 2'b 00}"
    elif numbytes == 8:
        imm = "{insn_imm2, insn_imm3, 3'b000}"
    elif numbytes == 16:
        imm = "{insn_imm3[0], insn_imm2, insn_imm3[2:1], 4'b000}"
    else:
        raise NotImplementedError(numbytes)
    return C_Instruction(
        name = insn,
        insn_parts = FORMAT_CS,
        opcode = "00",
        extension = extension,
        op_values = {
            "funct3": funct3,
        },
        mem_addr = "rvfi_rs1_rdata + insn_imm",
        mem_bytes = numbytes,
        mem_wdata = "rvfi_rs2_rdata",
        imm = imm,
        xlen_min = max(32, result_width) if not is_float else 32,
        xlen_max = max(32, result_width) if is_float else 128,
    )

def insn_c_addi(insn = "c_addi", sp = None, wmode = False, extension = "C"):
    instr = C_Instruction(
        name = insn,
        insn_parts = FORMAT_CIW if sp == 4 else FORMAT_CI,
        opcode = "00" if sp == 4 else "01",
        extension = extension,
        op_values = {
            "funct3": "011" if sp == 16 else "001" if wmode else "000",
        },
        result = "rvfi_rs1_rdata + insn_imm",
        imm = "$signed({insn_imm1, insn_imm5[2:1], insn_imm5[3], insn_imm5[0], insn_imm5[4], 4'b0})" if sp == 16 else True,
        read_rsd = True if not sp else None,
        rd_reg = 2 if sp == 16 else None,
        rs1_reg = 2 if sp == 4 else None,
        xlen_min = 64 if wmode else 32,
        sign_extend_from = 32 if wmode else None,
    )

    if sp:
        instr.check_valid.append("insn_imm != 0")
    if sp == 16:
        instr.check_valid.append("insn_rs1 == insn_rd")

    return instr

def cext():
    return {i.name: i for i in [
        C_Instruction(
            name = "c_li", insn_parts = FORMAT_CI, opcode = "01", extension = "C", op_values = { "funct3": "010" },
            result = "insn_imm", imm = True,
        ),
        C_Instruction(
            name = "c_lui", insn_parts = FORMAT_CI, opcode = "01", extension = "C", op_values = { "funct3": "011" },
            result = "insn_imm", imm = "$signed({insn_imm1, insn_imm5, 12'b0})", check_valid = ["insn_rsd != 5'd2"]
        ),

        insn_c_l("c_lw",  "010",  4),
        insn_c_l("c_ld",  "011",  8),
        insn_c_l("c_lq",  "001", 16),
        insn_c_l("c_flw", "011",  4, True, "C and F"),
        insn_c_l("c_fld", "001",  8, True, "C and D"),

        insn_c_s("c_sw",  "110",  4),
        insn_c_s("c_sd",  "111",  8),
        insn_c_s("c_sq",  "101", 16),
        insn_c_s("c_fsw", "111",  4, True, "C and F"),
        insn_c_s("c_fsd", "101",  8, True, "C and D"),

        insn_c_addi(),
        insn_c_addi("c_addiw", wmode=True),
        insn_c_addi("c_addi4spn", sp=4),
        insn_c_addi("c_addi16sp", sp=16),
    ]}
