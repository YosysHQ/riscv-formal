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
        ("imm3", 3),
        ("crsd", 3),
        ("imm5", 5),
        ("opcode", 2),
    ],
    imm = "$signed({insn_imm3[2], insn_imm5[4:3], insn_imm5[0], insn_imm3[1:0], insn_imm5[2:1], 1'b0})"
)

FORMAT_CB7 = Instruction_format(
    "CB-type", [
        ("funct3", 3),
        ("imm1", 1),
        ("funct2", 2),
        ("crsd", 3),
        ("imm5", 5),
        ("opcode", 2),
    ],
    imm = "$signed({insn_imm1, insn_imm5})"
)

FORMAT_CJ = Instruction_format(
    "CJ-type", [
        ("funct3", 3),
        ("imm11", 11),
        ("opcode", 2),
    ],
    imm = "$signed({insn_imm11[10], insn_imm11[6], insn_imm11[8:7], insn_imm11[4], insn_imm11[5], insn_imm11[0], insn_imm11[9], insn_imm11[3:1], 1'b0})"
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
    _next_pc_check: str = "next_pc[0] != 0"

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
        if self.rd_reg:
            self._used_regs.append("rd")

    def _v_insn_map(self, xlen):
        v_str = super()._v_insn_map(xlen) + '\n'
        if self.rd_reg:
            v_str += f"wire [4:0] insn_rd = 5'd{self.rd_reg};\n"
        if self.rs1_reg:
            v_str += f"wire [4:0] insn_rs1 = 5'd{self.rs1_reg};\n"
        if "rsd" in self.inst_args:
            if self.read_rsd:
                v_str += "wire [4:0] insn_rs1 = insn_rsd;\n"
            if self.result is not None and self.rd_reg is None:
                v_str += "wire [4:0] insn_rd = insn_rsd;\n"
        if "crsd" in self.inst_args:
            if self.read_rsd:
                v_str += "wire [4:0] insn_rs1 = {2'b01, insn_crsd};\n"
            if self.result is not None and self.rd_reg is None:
                v_str += "wire [4:0] insn_rd = {2'b01, insn_crsd};\n"
        if "crd" in self.inst_args:
            v_str += "wire [4:0] insn_rd = {2'b01, insn_crd};\n"
        if "crs1" in self.inst_args:
            v_str += "wire [4:0] insn_rs1 = {2'b01, insn_crs1};\n"
        if "crs2" in self.inst_args:
            v_str += "wire [4:0] insn_rs2 = {2'b01, insn_crs2};\n"
        return v_str[:-1]


def insn_c_l(insn, funct3, numbytes, is_float = False, extension = "Zca"):
    result_width = numbytes*8
    if numbytes == 4:
        imm = "{insn_imm2[0], insn_imm3, insn_imm2[1], 2'b00}"
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

def insn_c_s(insn, funct3, numbytes, is_float = False, extension = "Zca"):
    result_width = numbytes*8
    if numbytes == 4:
        imm = "{insn_imm2[0], insn_imm3, insn_imm2[1], 2'b00}"
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
        rs1_reg = 2,
        xlen_min = max(32, result_width) if not is_float else 32,
        xlen_max = max(32, result_width) if is_float else 128,
    )

def insn_c_lsp(insn, funct3, numbytes, is_float = False, extension = "Zca"):
    result_width = numbytes*8
    if numbytes == 4:
        imm = "{insn_imm5[1:0], insn_imm1, insn_imm5[4:2], 2'b00}"
    elif numbytes == 8:
        imm = "{insn_imm5[2:0], insn_imm1, insn_imm5[4:3], 3'b000}"
    elif numbytes == 16:
        imm = "{insn_imm5[3:0], insn_imm1, insn_imm5[4], 4'b000}"
    else:
        raise NotImplementedError(numbytes)
    instr = C_Instruction(
        name = insn,
        insn_parts = FORMAT_CI,
        opcode = "10",
        extension = extension,
        op_values = {
            "funct3": funct3,
        },
        mem_addr = "rvfi_rs1_rdata + insn_imm",
        mem_bytes = numbytes,
        result = "mem_rdata",
        imm = imm,
        rs1_reg = 2,
        sign_extend_from = result_width if not is_float else None,
        xlen_min = max(32, result_width) if not is_float else 32,
        xlen_max = max(32, result_width) if is_float else 128,
    )

    if not is_float:
        instr.check_valid.append("insn_rd != 0")

    return instr

def insn_c_ssp(insn, funct3, numbytes, is_float = False, extension = "Zca"):
    result_width = numbytes*8
    if numbytes == 4:
        imm = "{insn_imm6[1:0], insn_imm6[5:2], 2'b00}"
    elif numbytes == 8:
        imm = "{insn_imm6[2:0], insn_imm6[5:3], 3'b000}"
    elif numbytes == 16:
        imm = "{insn_imm6[3:0], insn_imm6[5:4], 4'b000}"
    else:
        raise NotImplementedError(numbytes)
    return C_Instruction(
        name = insn,
        insn_parts = FORMAT_CSS,
        opcode = "10",
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

def insn_c_j(insn, funct3, link = False, extension = "Zca"):
    return C_Instruction(
        name = insn,
        insn_parts = FORMAT_CJ,
        opcode = "01",
        extension = extension,
        op_values = {
            "funct3": funct3,
        },
        next_pc = "rvfi_pc_rdata + insn_imm",
        rd_reg = 1 if link else None,
        result = "rvfi_pc_rdata + 2" if link else None,
        imm = True,
        read_pc = True,
        xlen_max = 32 if link else 128,
    )

def insn_c_jr(insn, funct4, link = False, extension = "Zca"):
    return C_Instruction(
        name = insn,
        insn_parts = FORMAT_CR,
        opcode = "10",
        extension = extension,
        op_values = {
            "funct4": funct4,
        },
        next_pc = "rvfi_rs1_rdata & ~1",
        read_rsd = True,
        rd_reg = 1 if link else None,
        result = "rvfi_pc_rdata + 2" if link else None,
        read_pc = True,
        check_valid = ["insn_rs1 != 0", "insn_rs2 == 0"]
    )

def insn_c_b(insn, funct3, expr, extension = "Zca"):
    return C_Instruction(
        name = insn,
        insn_parts = FORMAT_CB,
        opcode = "01",
        extension = extension,
        op_values = {
            "funct3": funct3,
        },
        next_pc = f"{expr} ? rvfi_pc_rdata + insn_imm : rvfi_pc_rdata + 2",
        imm = True,
        read_pc = True,
        read_rsd = True,
    )

def insn_c_li(insn, funct3, umode, extension = "Zca"):
    instr = C_Instruction(
        name = insn,
        insn_parts = FORMAT_CI,
        opcode = "01",
        extension = extension,
        op_values = {
            "funct3": funct3,
        },
        result = "insn_imm",
        imm = "$signed({insn_imm1, insn_imm5, 12'b0})" if umode else True,
        check_valid = [ "insn_rsd != 0" ],
    )

    if umode:
        instr.check_valid.append("insn_rsd != 2")
        instr.check_valid.append("insn_imm != 0")

    return instr

def insn_c_addi(insn, sp_mult = None, wmode = False, extension = "Zca"):
    instr = C_Instruction(
        name = insn,
        insn_parts = FORMAT_CIW if sp_mult == 4 else FORMAT_CI,
        opcode = "00" if sp_mult == 4 else "01",
        extension = extension,
        op_values = {
            "funct3": "011" if sp_mult == 16 else "001" if wmode else "000",
        },
        result = "rvfi_rs1_rdata + insn_imm",
        imm = "$signed({insn_imm1, insn_imm5[2:1], insn_imm5[3], insn_imm5[0], insn_imm5[4], 4'b0})" if sp_mult == 16 else True,
        read_rsd = True if not sp_mult else None,
        rd_reg = 2 if sp_mult == 16 else None,
        rs1_reg = 2 if sp_mult == 4 else None,
        xlen_min = 64 if wmode else 32,
        sign_extend_from = 32 if wmode else None,
    )

    if sp_mult or not wmode:
        instr.check_valid.append("insn_imm != 0")
    if sp_mult == 16:
        instr.check_valid.append("insn_rs1 == insn_rd")

    return instr

def insn_c_shimm(insn, funct2, expr, extension = "Zca"):
    instr = C_Instruction(
        name = insn,
        insn_parts = FORMAT_CB7 if funct2 else FORMAT_CI,
        opcode = "01" if funct2 else "10",
        extension = extension,
        op_values = {
            "funct3": "100" if funct2 else "000",
        },
        result = expr,
        read_rsd = True,
        raw_code = [ "wire [5:0] insn_shamt = {insn_imm1, insn_imm5};" ],
        check_valid = [
            "!insn_shamt[5] || `RISCV_FORMAL_XLEN == 64",
        ],
    )

    if funct2:
        instr.op_values["funct2"] = funct2
    else:
        instr.check_valid.append("insn_rsd != 0")

    return instr

def insn_c_andi(insn, extension = "Zca"):
    return C_Instruction(
        name = insn,
        insn_parts = FORMAT_CB7,
        opcode = "01",
        extension = extension,
        op_values = {
            "funct3": "100",
            "funct2": "10",
        },
        result = "rvfi_rs1_rdata & insn_imm",
        imm = True,
        read_rsd = True,
    )

def insn_c_mvadd(insn, funct4, add, extension = "Zca"):
    return C_Instruction(
        name = insn,
        insn_parts = FORMAT_CR,
        opcode = "10",
        extension = extension,
        op_values = {
            "funct4": funct4,
        },
        result = "rvfi_rs1_rdata + rvfi_rs2_rdata" if add else "rvfi_rs2_rdata",
        read_rsd = add is not None,
        check_valid = [
            "insn_rsd != 0",
            "insn_rs2 != 0",
        ]
    )

def insn_c_alu(insn, funct6, funct2, expr, wmode = False, extension = "Zca"):
    return C_Instruction(
        name = insn,
        insn_parts = FORMAT_CA,
        opcode = "01",
        extension = extension,
        op_values = {
            "funct6": funct6,
            "funct2": funct2,
        },
        result = expr,
        read_rsd = True,
        sign_extend_from = 32 if wmode else None,
        xlen_min = 64 if wmode else 32,
    )

def cext():
    return {i.name: i for i in [
        # Load and Store Instructions

        ## Stack-Pointer-Based

        insn_c_lsp("c_lwsp",  "010",  4),
        insn_c_lsp("c_ldsp",  "011",  8),
        insn_c_lsp("c_lqsp",  "001", 16),
        insn_c_lsp("c_flwsp", "011",  4, True, "Zcf"),
        insn_c_lsp("c_fldsp", "001",  8, True, "Zcd"),

        insn_c_ssp("c_swsp",  "110",  4),
        insn_c_ssp("c_sdsp",  "111",  8),
        insn_c_ssp("c_sqsp",  "101", 16),
        insn_c_ssp("c_fswsp", "111",  4, True, "Zcf"),
        insn_c_ssp("c_fsdsp", "101",  8, True, "Zcd"),

        ## Register-Based

        insn_c_l("c_lw",  "010",  4),
        insn_c_l("c_ld",  "011",  8),
        insn_c_l("c_lq",  "001", 16),
        insn_c_l("c_flw", "011",  4, True, "Zcf"),
        insn_c_l("c_fld", "001",  8, True, "Zcd"),

        insn_c_s("c_sw",  "110",  4),
        insn_c_s("c_sd",  "111",  8),
        insn_c_s("c_sq",  "101", 16),
        insn_c_s("c_fsw", "111",  4, True, "Zcf"),
        insn_c_s("c_fsd", "101",  8, True, "Zcd"),

        # Control Transfer Instructions

        insn_c_j("c_j",   "101", False),
        insn_c_j("c_jal", "001", True),
        insn_c_jr("c_jr",   "1000", False),
        insn_c_jr("c_jalr", "1001", True),

        insn_c_b("c_beqz", "110", "rvfi_rs1_rdata == 0"),
        insn_c_b("c_bnez", "111", "rvfi_rs1_rdata != 0"),

        # Integer Computational Instructions

        ## Integer Constant-Generation

        insn_c_li("c_li", "010", False),
        insn_c_li("c_lui", "011", True),

        ## Integer Register-Immediate

        insn_c_addi("c_addi"),
        insn_c_addi("c_addiw", wmode=True),
        insn_c_addi("c_addi16sp", sp_mult=16),
        insn_c_addi("c_addi4spn", sp_mult=4),

        insn_c_shimm("c_slli", None, "rvfi_rs1_rdata << insn_shamt"),
        insn_c_shimm("c_srli", "00", "rvfi_rs1_rdata >> insn_shamt"),
        insn_c_shimm("c_srai", "01", "$signed(rvfi_rs1_rdata) >>> insn_shamt"),

        insn_c_andi("c_andi"),

        ## Integer Register-Register

        insn_c_mvadd("c_mv",  "1000", False),
        insn_c_mvadd("c_add", "1001", True),

        insn_c_alu("c_and", "100011", "11", "rvfi_rs1_rdata & rvfi_rs2_rdata"),
        insn_c_alu("c_or",  "100011", "10", "rvfi_rs1_rdata | rvfi_rs2_rdata"),
        insn_c_alu("c_xor", "100011", "01", "rvfi_rs1_rdata ^ rvfi_rs2_rdata"),
        insn_c_alu("c_sub", "100011", "00", "rvfi_rs1_rdata - rvfi_rs2_rdata"),

        insn_c_alu("c_addw", "100111", "01", "rvfi_rs1_rdata[31:0] + rvfi_rs2_rdata[31:0]", wmode=True),
        insn_c_alu("c_subw", "100111", "00", "rvfi_rs1_rdata[31:0] - rvfi_rs2_rdata[31:0]", wmode=True),
    ]}
