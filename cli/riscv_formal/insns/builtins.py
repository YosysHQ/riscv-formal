# Copyright (C) 2017  Claire Xenia Wolf <claire@yosyshq.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from .model import (
    Instruction_format,
    Instruction,
    MemoryInstruction,
)

from .ext_mapper import register_ext_generator, register_non_insn_ext
from riscv_formal.named_set import NamedSet

FORMAT_R = Instruction_format(
    "R-type", [
        ("funct7", 7),
        ("rs2", 5),
        ("rs1", 5),
        ("funct3", 3),
        ("rd", 5),
        ("opcode", 7),
    ],
)

FORMAT_I = Instruction_format(
    "I-type", [
        ("imm12", 12),
        ("rs1", 5),
        ("funct3", 3),
        ("rd", 5),
        ("opcode", 7),
    ],
    imm = "$signed(insn_imm12)",
)

FORMAT_I_SHIFT = Instruction_format(
    "I-type (shift variation)", [
        ("funct6", 6),
        ("shamt", 6),
        ("rs1", 5),
        ("funct3", 3),
        ("rd", 5),
        ("opcode", 7),
    ],
)

FORMAT_S = Instruction_format(
    "S-type", [
        ("imm11_5", 7),
        ("rs2", 5),
        ("rs1", 5),
        ("funct3", 3),
        ("imm4_0", 5),
        ("opcode", 7),
    ],
    imm = "$signed({insn_imm11_5, insn_imm4_0})",
)

FORMAT_B = Instruction_format(
    "B-type", [
        ("imm12", 1),
        ("imm10_5", 6),
        ("rs2", 5),
        ("rs1", 5),
        ("funct3", 3),
        ("imm4_1", 4),
        ("imm11", 1),
        ("opcode", 7),
    ],
    imm = "$signed({insn_imm12, insn_imm11, insn_imm10_5, insn_imm4_1, 1'b0})",
)

FORMAT_U = Instruction_format(
    "U-type", [
        ("imm20", 20),
        ("rd", 5),
        ("opcode", 7),
    ],
    imm = "$signed({insn_imm20, 12'b0})",
)

FORMAT_J = Instruction_format(
    "J-type", [
        ("imm20", 1),
        ("imm10_1", 10),
        ("imm11", 1),
        ("imm19_12", 8),
        ("rd", 5),
        ("opcode", 7),
    ],
    imm = "$signed({insn_imm20, insn_imm19_12, insn_imm11, insn_imm10_1, 1'b0})",
)


def insn_b(insn, funct3, expr, extension = "I"):
    return Instruction(
        name = insn,
        insn_parts = FORMAT_B,
        opcode = "1100011",
        extension = extension,
        op_values = {
            "funct3": funct3,
        },
        next_pc = f"{expr} ? rvfi_pc_rdata + insn_imm : rvfi_pc_rdata + 4",
        imm = True,
        read_pc = True,
    )

def insn_l(insn, funct3, numbytes, signext, extension = "I"):
    result_width = numbytes*8
    return MemoryInstruction(
        name = insn,
        insn_parts = FORMAT_I,
        opcode = "0000011",
        mem_addr = "rvfi_rs1_rdata + insn_imm",
        mem_bytes = numbytes,
        result = "mem_rdata",
        extension = extension,
        op_values = {
            "funct3": funct3,
        },
        imm = True,
        sign_extend_from = result_width if signext else None,
        zero_extend_from = result_width if not signext else None,
        xlen_min = max(32, result_width if signext else result_width*2),
    )

def insn_s(insn, funct3, numbytes, extension = "I"):
    result_width = numbytes*8
    return MemoryInstruction(
        name = insn,
        insn_parts = FORMAT_S,
        opcode = "0100011",
        mem_addr = "rvfi_rs1_rdata + insn_imm",
        mem_bytes = numbytes,
        mem_wdata = "rvfi_rs2_rdata",
        extension = extension,
        op_values = {
            "funct3": funct3,
        },
        imm = True,
        xlen_min = max(32, result_width),
    )

def insn_alu(insn, funct7, funct3, expr, shamt=False, wmode=False, uwmode=False, extension="I"):
    if wmode and uwmode:
        raise NotImplementedError("Got both uwmode and umode")

    return Instruction(
        name = insn,
        insn_parts = FORMAT_R,
        opcode = "0111011" if uwmode or wmode else "0110011",
        result = expr,
        extension = extension,
        shamt = shamt,
        sign_extend_from = 32 if wmode else None,
        xlen_min = 64 if wmode or uwmode else 32,
        op_values = {
            "funct7": funct7,
            "funct3": funct3,
        },
    )

def insn_imm(insn, funct3, expr, wmode=False, extension = "I"):
    return Instruction(
        name = insn,
        insn_parts = FORMAT_I,
        opcode = "0011011" if wmode else "0010011",
        result = expr,
        extension = extension,
        sign_extend_from = 32 if wmode else None,
        xlen_min = 64 if wmode else 32,
        op_values = {
            "funct3": funct3,
        },
        imm = True,
    )

def insn_shimm(insn, funct6, funct3, expr, wmode=False, uwmode=False, extension = "I"):
    if wmode and uwmode:
        raise NotImplementedError("Got both uwmode and umode")

    instr = Instruction(
        name = insn,
        insn_parts = FORMAT_I_SHIFT,
        opcode = "0011011" if wmode or uwmode else "0010011",
        result = expr,
        extension = extension,
        sign_extend_from = 32 if wmode else None,
        xlen_min = 64 if wmode or uwmode else 32,
        op_values = {
          "funct6": funct6,
          "funct3": funct3,
        },
    )

    if wmode:
        instr.check_valid.append("!insn_shamt[5]")
    elif not uwmode:
        instr.check_valid.append("!insn_shamt[5] || `RISCV_FORMAL_XLEN == 64")

    return instr

def builtins(_) -> NamedSet[Instruction]:
    return NamedSet([
        # Base Integer ISA (I)

        Instruction(
            name = "lui", insn_parts = FORMAT_U, opcode = "0110111", extension = "I",
            result = "insn_imm", imm = True,
        ),
        Instruction(
            name = "auipc", insn_parts = FORMAT_U, opcode = "0010111", extension = "I",
            result = "rvfi_pc_rdata + insn_imm", imm = True, read_pc = True,
        ),
        Instruction(
            name = "jal", insn_parts = FORMAT_J, opcode = "1101111", extension = "I",
            result = "rvfi_pc_rdata + 4", next_pc = "rvfi_pc_rdata + insn_imm", imm = True, read_pc = True,
        ),
        Instruction(
            name = "jalr", insn_parts = FORMAT_I, opcode = "1100111", extension = "I", op_values = { "funct3": "000" },
            result = "rvfi_pc_rdata + 4", next_pc = "(rvfi_rs1_rdata + insn_imm) & ~1", imm = True, read_pc = True,
        ),

        insn_b("beq",  "000", "rvfi_rs1_rdata == rvfi_rs2_rdata"),
        insn_b("bne",  "001", "rvfi_rs1_rdata != rvfi_rs2_rdata"),
        insn_b("blt",  "100", "$signed(rvfi_rs1_rdata) < $signed(rvfi_rs2_rdata)"),
        insn_b("bge",  "101", "$signed(rvfi_rs1_rdata) >= $signed(rvfi_rs2_rdata)"),
        insn_b("bltu", "110", "rvfi_rs1_rdata < rvfi_rs2_rdata"),
        insn_b("bgeu", "111", "rvfi_rs1_rdata >= rvfi_rs2_rdata"),

        insn_l("lb",  "000",  1, True),
        insn_l("lh",  "001",  2, True),
        insn_l("lw",  "010",  4, True),
        insn_l("lbu", "100",  1, False),
        insn_l("lhu", "101",  2, False),
        insn_l("lwu", "110",  4, False),
        insn_l("ld",  "011",  8, True),

        insn_s("sb",  "000", 1),
        insn_s("sh",  "001", 2),
        insn_s("sw",  "010", 4),
        insn_s("sd",  "011", 8),

        insn_alu("add",  "0000000", "000", "rvfi_rs1_rdata + rvfi_rs2_rdata"),
        insn_alu("sub",  "0100000", "000", "rvfi_rs1_rdata - rvfi_rs2_rdata"),
        insn_alu("sll",  "0000000", "001", "rvfi_rs1_rdata << shamt", shamt=True),
        insn_alu("slt",  "0000000", "010", "$signed(rvfi_rs1_rdata) < $signed(rvfi_rs2_rdata)"),
        insn_alu("sltu", "0000000", "011", "rvfi_rs1_rdata < rvfi_rs2_rdata"),
        insn_alu("xor",  "0000000", "100", "rvfi_rs1_rdata ^ rvfi_rs2_rdata"),
        insn_alu("srl",  "0000000", "101", "rvfi_rs1_rdata >> shamt", shamt=True),
        insn_alu("sra",  "0100000", "101", "$signed(rvfi_rs1_rdata) >>> shamt", shamt=True),
        insn_alu("or",   "0000000", "110", "rvfi_rs1_rdata | rvfi_rs2_rdata"),
        insn_alu("and",  "0000000", "111", "rvfi_rs1_rdata & rvfi_rs2_rdata"),

        insn_imm("addi",  "000", "rvfi_rs1_rdata + insn_imm"),
        insn_imm("slti",  "010", "$signed(rvfi_rs1_rdata) < $signed(insn_imm)"),
        insn_imm("sltiu", "011", "rvfi_rs1_rdata < insn_imm"),
        insn_imm("xori",  "100", "rvfi_rs1_rdata ^ insn_imm"),
        insn_imm("ori",   "110", "rvfi_rs1_rdata | insn_imm"),
        insn_imm("andi",  "111", "rvfi_rs1_rdata & insn_imm"),

        insn_shimm("slli", "000000", "001", "rvfi_rs1_rdata << insn_shamt"),
        insn_shimm("srli", "000000", "101", "rvfi_rs1_rdata >> insn_shamt"),
        insn_shimm("srai", "010000", "101", "$signed(rvfi_rs1_rdata) >>> insn_shamt"),

        insn_imm("addiw",  "000", "rvfi_rs1_rdata[31:0] + insn_imm[31:0]", wmode=True),

        insn_shimm("slliw", "000000", "001", "rvfi_rs1_rdata[31:0] << insn_shamt", wmode=True),
        insn_shimm("srliw", "000000", "101", "rvfi_rs1_rdata[31:0] >> insn_shamt", wmode=True),
        insn_shimm("sraiw", "010000", "101", "$signed(rvfi_rs1_rdata[31:0]) >>> insn_shamt", wmode=True),

        insn_alu("addw", "0000000", "000", "rvfi_rs1_rdata[31:0] + rvfi_rs2_rdata[31:0]", wmode=True),
        insn_alu("subw", "0100000", "000", "rvfi_rs1_rdata[31:0] - rvfi_rs2_rdata[31:0]", wmode=True),
        insn_alu("sllw", "0000000", "001", "rvfi_rs1_rdata[31:0] << shamt", shamt=True, wmode=True),
        insn_alu("srlw", "0000000", "101", "rvfi_rs1_rdata[31:0] >> shamt", shamt=True, wmode=True),
        insn_alu("sraw", "0100000", "101", "$signed(rvfi_rs1_rdata[31:0]) >>> shamt", shamt=True, wmode=True),
    ])

register_ext_generator(builtins, "I")
register_non_insn_ext("Zicsr", "Zicntr", "Zihpm")
