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

from textwrap import dedent
from typing import Optional

from .model import (
    Instruction_format,
    Instruction,
    MemoryInstruction,
)

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

def insn_alu(insn, funct7, funct3, expr, alt_add=None, alt_sub=None, shamt=False, wmode=False, uwmode=False, extension="I"):
    if wmode and uwmode:
        raise NotImplementedError("Got both uwmode and umode")

    return Instruction(
        name = insn,
        insn_parts = FORMAT_R,
        opcode = "0111011" if uwmode or wmode else "0110011",
        result = expr,
        extension = extension,
        alt_add = alt_add,
        alt_sub = alt_sub,
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

def insn_count(insn, funct5, trailing=False, pop=False, wmode=False, extension = "B"):
    if pop and trailing:
        raise NotImplementedError("Got both pop and trailing")
    elif pop: # count all ones
        result_body = """
                    result = result + rvfi_rs1_rdata[i];"""
    elif trailing: # count trailing zeros
        result_body = """
                    found = found | rvfi_rs1_rdata[i];
                    result = result + !(rvfi_rs1_rdata[i] | found);"""
    else: # count leading zeros
        result_body = """
                    if (rvfi_rs1_rdata[i] == 1'b1)
                        result = 0;
                    else
                        result = result + 1;"""

    return Instruction(
        name = insn,
        insn_parts = FORMAT_I,
        opcode = "0011011" if wmode else "0010011",
        extension = extension, 
        xlen_min = 64 if wmode else 32,
        op_values = {
            "imm12": "0110000_" + funct5,
            "funct3": "001",
        },
        raw_code = dedent(f"""\
            integer i;
            reg [%RESULT_WIDTH%-1:0] result;
            reg found;

            always @(rvfi_rs1_rdata)
            begin
                result = 0;
                found = 0;
                for (i=0; i<%RESULT_WIDTH%; i=i+1)
                begin{result_body}
                end
            end""").splitlines()
    )

def insn_ext(insn, funct5, signed=False, bmode=False, extension = "B"):
    extend_from = 8 if bmode else 16
    return Instruction(
        name = insn,
        insn_parts = FORMAT_I,
        opcode = "0010011" if signed else "{3'b 011, `RISCV_FORMAL_XLEN != 32, 3'b 011}",
        result = "rvfi_rs1_rdata",
        extension = extension,
        sign_extend_from = extend_from if signed else None,
        zero_extend_from = extend_from if not signed else None,
        op_values = {
            "imm12": ("0110000_" if signed else "0000100_") + funct5,
            "funct3": "001" if  signed else "100",
        },
    )

def insn_bit(insn, funct6, funct3, expr, imode=False, extension = "B"):
    index = "insn_shamt" if imode else "rvfi_rs2_rdata"

    instr = Instruction(
        name = insn,
        insn_parts = FORMAT_I_SHIFT if imode else FORMAT_R,
        opcode = "0010011" if imode else "0110011",
        result = expr,
        extension = extension,
        op_values = {"funct3": funct3},
        xlen_max = 64 if imode else 128,
        raw_code = [
            f"wire [`RISCV_FORMAL_XLEN-1:0] index = {index} & (`RISCV_FORMAL_XLEN - 1);"
        ],
    )

    if imode:
        instr.op_values["funct6"] = funct6
        instr.check_valid.append("!insn_shamt[5] || `RISCV_FORMAL_XLEN == 64")
    else:
        instr.op_values["funct7"] = funct6 + "0"

    return instr

def insn_bytes(insn, funct12, funct3, expr, bitwise=False, extension = "B"):
    if bitwise:
        loop_int = "integer i, j"
        inner_loop = f"""
                    for (j=0; j<8; j=j+1)
                    begin
                        result[i*8+j] = {expr};
                    end"""
    else:
        loop_int = "integer i"
        inner_loop = f"""
                    result[i*8+:8] = {expr};"""
    return Instruction(
        name = insn,
        insn_parts = FORMAT_I,
        opcode = "0010011",
        extension = extension,
        op_values = {
            "imm12": funct12,
            "funct3": funct3,
        },
        raw_code = dedent(f"""\
            reg [%RESULT_WIDTH%-1:0] result;
            {loop_int};
            localparam integer nbytes = %RESULT_WIDTH% / 8;
            always @(rvfi_rs1_rdata)
            begin
                result = 0;
                for (i=0; i<nbytes; i=i+1)
                begin{inner_loop}
                end
            end""").splitlines()
    )

def insn_pack(insn="pack", funct3="100", result_width: Optional[int] = None, signed=False, extension = "B"):
    if result_width:
        xlen_min = max(32, result_width if not signed else result_width*2)
    else:
        xlen_min = 32
    return Instruction(
        name = insn,
        insn_parts = FORMAT_R,
        opcode = "0111011" if signed else "0110011",
        extension = extension,
        raw_code = ["localparam INPUT_WIDTH = %RESULT_WIDTH%/2;"],
        result = f"{{rvfi_rs2_rdata[0+:INPUT_WIDTH], rvfi_rs1_rdata[0+:INPUT_WIDTH]}}",
        sign_extend_from = result_width if signed else None,
        zero_extend_from = result_width if not signed else None,
        op_values = {
            "funct7": "0000100",
            "funct3": funct3,
        },
        xlen_min = xlen_min,
    )

def insn_zip(insn, funct3, unzip=False, extension = "B"):
    if unzip:
        inner_loop = """
                    result[i] = rvfi_rs1_rdata[2*i];
                    result[i + %RESULT_WIDTH%/2] = rvfi_rs1_rdata[2*i + 1];"""
    else:
        inner_loop = """
                    result[2*i] = rvfi_rs1_rdata[i];
                    result[2*i + 1] = rvfi_rs1_rdata[i + %RESULT_WIDTH%/2];"""
    return Instruction(
        name = insn,
        insn_parts = FORMAT_I,
        opcode = "0010011",
        extension = extension,
        op_values = {
            "imm12": "0000100_01111",
            "funct3": funct3,
        },
        xlen_max = 32,
        raw_code = dedent(f"""\
            reg [%RESULT_WIDTH%-1:0] result;
            integer i;

            always @(rvfi_rs1_rdata)
            begin
                result = 0;
                for (i=0; i<(%RESULT_WIDTH%/2); i=i+1)
                begin{inner_loop}
                end
            end
            """).splitlines()
    )

def insn_clmul(insn, funct3, expr, index1=False, extension = "B"):
    if index1:
        i_first = "1"
        i_last = "%RESULT_WIDTH%+1"
    else:
        i_first = "0"
        i_last = "%RESULT_WIDTH%"
    return Instruction(
        name = insn,
        insn_parts = FORMAT_R,
        opcode = "0110011",
        extension = extension,
        op_values = {
            "funct7": "0000101",
            "funct3": funct3,
        },
        raw_code = dedent(f"""\
            reg [%RESULT_WIDTH%-1:0] result;
            integer i;

            always @(rvfi_rs1_rdata, rvfi_rs2_rdata)
            begin
                result = 0;
                for (i={i_first}; i<{i_last}; i=i+1)
                begin
                    if ((rvfi_rs2_rdata >> i) & 1)
                        result = result ^ ({expr});
                    else
                        result = result;
                end
            end""").splitlines()
    )

def insn_xperm(insn, funct3, width, extension = "Zbkx"):
    return Instruction(
        name = insn,
        insn_parts = FORMAT_R,
        opcode = "0110011",
        extension = extension,
        op_values = {
            "funct7": "0010100",
            "funct3": funct3,
        },
        raw_code = dedent(f"""\
            reg [%RESULT_WIDTH%-1:0] result;
            integer i;

            always @(rvfi_rs1_rdata, rvfi_rs2_rdata)
            begin
                result = 0;
                for (i=0; i<%RESULT_WIDTH%; i=i+{width})
                begin
                    result[i+:{width}] = (rvfi_rs1_rdata >> rvfi_rs2_rdata[i+:{width}]) & {{{width}{{1'b1}}}};
                end
            end""").splitlines()
    )

def builtins():
    return {i.name: i for i in [
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

        # Multiply/Divide ISA (M)

        insn_alu("mul",    "0000001", "000", "rvfi_rs1_rdata * rvfi_rs2_rdata", alt_add=0x2cdf52a55876063e, extension="M"),
        insn_alu("mulh",   "0000001", "001", "({{`RISCV_FORMAL_XLEN{rvfi_rs1_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_rs1_rdata} *\n" +
                "\t\t{{`RISCV_FORMAL_XLEN{rvfi_rs2_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_add=0x15d01651f6583fb7, extension="M"),
        insn_alu("mulhsu", "0000001", "010", "({{`RISCV_FORMAL_XLEN{rvfi_rs1_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_rs1_rdata} *\n" +
                "\t\t{`RISCV_FORMAL_XLEN'b0, rvfi_rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_sub=0xea3969edecfbe137, extension="M"),
        insn_alu("mulhu",  "0000001", "011", "({`RISCV_FORMAL_XLEN'b0, rvfi_rs1_rdata} * {`RISCV_FORMAL_XLEN'b0, rvfi_rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_add=0xd13db50d949ce5e8, extension="M"),

        insn_alu("div",    "0000001", "100", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? {`RISCV_FORMAL_XLEN{1'b1}} :
                                                rvfi_rs1_rdata == {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} && rvfi_rs2_rdata == {`RISCV_FORMAL_XLEN{1'b1}} ? {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} :
                                                $signed(rvfi_rs1_rdata) / $signed(rvfi_rs2_rdata)""", alt_sub=0x29bbf66f7f8529ec, extension="M"),
        insn_alu("divu",   "0000001", "101", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? {`RISCV_FORMAL_XLEN{1'b1}} :
                                                rvfi_rs1_rdata / rvfi_rs2_rdata""", alt_sub=0x8c629acb10e8fd70, extension="M"),

        insn_alu("rem",    "0000001", "110", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? rvfi_rs1_rdata :
                                                rvfi_rs1_rdata == {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} && rvfi_rs2_rdata == {`RISCV_FORMAL_XLEN{1'b1}} ? {`RISCV_FORMAL_XLEN{1'b0}} :
                                                $signed(rvfi_rs1_rdata) % $signed(rvfi_rs2_rdata)""", alt_sub=0xf5b7d8538da68fa5, extension="M"),
        insn_alu("remu",   "0000001", "111", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? rvfi_rs1_rdata :
                                                rvfi_rs1_rdata % rvfi_rs2_rdata""", alt_sub=0xbc4402413138d0e1, extension="M"),

        insn_alu("mulw",   "0000001", "000", "rvfi_rs1_rdata[31:0] * rvfi_rs2_rdata[31:0]", alt_add=0x2cdf52a55876063e, wmode=True, extension="M"),

        insn_alu("divw",   "0000001", "100", """rvfi_rs2_rdata[31:0] == 32'b0 ? {32{1'b1}} :
                                                rvfi_rs1_rdata == {1'b1, {31{1'b0}}} && rvfi_rs2_rdata == {32{1'b1}} ? {1'b1, {31{1'b0}}} :
                                                $signed(rvfi_rs1_rdata[31:0]) / $signed(rvfi_rs2_rdata[31:0])""", alt_sub=0x29bbf66f7f8529ec, wmode=True, extension="M"),
        insn_alu("divuw",  "0000001", "101", """rvfi_rs2_rdata[31:0] == 32'b0 ? {32{1'b1}} :
                                                rvfi_rs1_rdata[31:0] / rvfi_rs2_rdata[31:0]""", alt_sub=0x8c629acb10e8fd70, wmode=True, extension="M"),

        insn_alu("remw",   "0000001", "110", """rvfi_rs2_rdata == 32'b0 ? rvfi_rs1_rdata :
                                                rvfi_rs1_rdata == {1'b1, {31{1'b0}}} && rvfi_rs2_rdata == {32{1'b1}} ? {32{1'b0}} :
                                                $signed(rvfi_rs1_rdata[31:0]) % $signed(rvfi_rs2_rdata[31:0])""", alt_sub=0xf5b7d8538da68fa5, wmode=True, extension="M"),
        insn_alu("remuw",  "0000001", "111", """rvfi_rs2_rdata == 32'b0 ? rvfi_rs1_rdata :
                                                rvfi_rs1_rdata[31:0] % rvfi_rs2_rdata[31:0]""", alt_sub=0xbc4402413138d0e1, wmode=True, extension="M"),

        # Bit Manipulation ISA (B)

        ## Zba: Address generation

        insn_alu("sh1add",  "0010000", "010", "rvfi_rs2_rdata + (rvfi_rs1_rdata << 1)", extension="Zba"),
        insn_alu("sh2add",  "0010000", "100", "rvfi_rs2_rdata + (rvfi_rs1_rdata << 2)", extension="Zba"),
        insn_alu("sh3add",  "0010000", "110", "rvfi_rs2_rdata + (rvfi_rs1_rdata << 3)", extension="Zba"),

        insn_alu("add_uw",      "0000100", "000", "rvfi_rs2_rdata + rvfi_rs1_rdata[31:0]",          uwmode=True, extension="Zba"),
        insn_alu("sh1add_uw",   "0010000", "010", "rvfi_rs2_rdata + (rvfi_rs1_rdata[31:0] << 1)",   uwmode=True, extension="Zba"),
        insn_alu("sh2add_uw",   "0010000", "100", "rvfi_rs2_rdata + (rvfi_rs1_rdata[31:0] << 2)",   uwmode=True, extension="Zba"),
        insn_alu("sh3add_uw",   "0010000", "110", "rvfi_rs2_rdata + (rvfi_rs1_rdata[31:0] << 3)",   uwmode=True, extension="Zba"),
        insn_shimm("slli_uw",   "000010",  "001", "rvfi_rs1_rdata[31:0] << insn_shamt",             uwmode=True, extension="Zba"),

        ## Zbb: Basic bit-manipulation

        insn_count("clz",   "00000", extension="Zbb"),
        insn_count("ctz",   "00001", trailing=True, extension="Zbb"),
        insn_count("cpop",  "00010", pop=True, extension="Zbb"),
        insn_alu("max",     "0000101", "110", "($signed(rvfi_rs1_rdata) < $signed(rvfi_rs2_rdata)) ? rvfi_rs2_rdata : rvfi_rs1_rdata", extension="Zbb"),
        insn_alu("maxu",    "0000101", "111", "(rvfi_rs1_rdata < rvfi_rs2_rdata) ? rvfi_rs2_rdata : rvfi_rs1_rdata", extension="Zbb"),
        insn_alu("min",     "0000101", "100", "($signed(rvfi_rs1_rdata) < $signed(rvfi_rs2_rdata)) ? rvfi_rs1_rdata : rvfi_rs2_rdata", extension="Zbb"),
        insn_alu("minu",    "0000101", "101", "(rvfi_rs1_rdata < rvfi_rs2_rdata) ? rvfi_rs1_rdata : rvfi_rs2_rdata", extension="Zbb"),
        insn_ext("sext_b",  "00100", signed=True, bmode=True, extension="Zbb"),
        insn_ext("sext_h",  "00101", signed=True, extension="Zbb"),
        insn_ext("zext_h",  "00000", extension="Zbb"),
        insn_bytes("orc_b", "12'b 0010100_00111", "101", "{8{|rvfi_rs1_rdata[i*8+:8]}}", extension="Zbb"),

        insn_alu("andn",    "0100000", "111", "rvfi_rs1_rdata & ~rvfi_rs2_rdata",   extension="Zbb Zbkb"),
        insn_alu("orn",     "0100000", "110", "rvfi_rs1_rdata | ~rvfi_rs2_rdata",   extension="Zbb Zbkb"),
        insn_alu("xnor",    "0100000", "100", "~(rvfi_rs1_rdata ^ rvfi_rs2_rdata)", extension="Zbb Zbkb"),
        insn_alu("rol",     "0110000", "001", "(rvfi_rs1_rdata << shamt) | (rvfi_rs1_rdata >> (`RISCV_FORMAL_XLEN - shamt))", shamt=True, extension="Zbb Zbkb"),
        insn_alu("ror",     "0110000", "101", "(rvfi_rs1_rdata >> shamt) | (rvfi_rs1_rdata << (`RISCV_FORMAL_XLEN - shamt))", shamt=True, extension="Zbb Zbkb"),
        insn_shimm("rori",  "011000", "101", "(rvfi_rs1_rdata >> insn_shamt) | (rvfi_rs1_rdata << (`RISCV_FORMAL_XLEN - insn_shamt))", extension="Zbb Zbkb"),
        insn_bytes("rev8",  "{6'b 011010, `RISCV_FORMAL_XLEN == 64, 5'b 11000}", "101", "rvfi_rs1_rdata[((nbytes-i)*8)-1-:8]", extension="Zbb Zbkb"),

        insn_pack(extension = "Zbkb"),
        insn_pack("packh", "111", result_width=16, extension = "Zbkb"),
        insn_bytes("brev8", "12'b 0110100_00111", "101", "rvfi_rs1_rdata[(i+1)*8-(j+1)]", bitwise=True, extension="Zbkb"),
        insn_zip("zip",   "001", extension = "Zbkb"),
        insn_zip("unzip", "101", unzip=True, extension = "Zbkb"),

        insn_count("clzw",  "00000", wmode=True, extension = "Zbb"),
        insn_count("ctzw",  "00001", trailing=True, wmode=True, extension = "Zbb"),
        insn_count("cpopw", "00010", pop=True, wmode=True, extension = "Zbb"),

        insn_alu("rolw",    "0110000", "001", "(rvfi_rs1_rdata[31:0] << shamt) | (rvfi_rs1_rdata[31:0] >> (32 - shamt))", shamt=True, wmode=True, extension="Zbb Zbkb"),
        insn_alu("rorw",    "0110000", "101", "(rvfi_rs1_rdata[31:0] >> shamt) | (rvfi_rs1_rdata[31:0] << (32 - shamt))", shamt=True, wmode=True, extension="Zbb Zbkb"),
        insn_shimm("roriw", "011000", "101", "(rvfi_rs1_rdata[31:0] >> insn_shamt) | (rvfi_rs1_rdata[31:0] << (32 - insn_shamt))", wmode=True, extension="Zbb Zbkb"),

        insn_pack("packw", "100", result_width=32, signed=True, extension = "Zbkb"),

        ## Zbc: Carry-less multiplication

        insn_clmul("clmul",  "001", "rvfi_rs1_rdata << i", extension="Zbc Zbkc"),
        insn_clmul("clmulh", "011", "rvfi_rs1_rdata >> (`RISCV_FORMAL_XLEN - i)", index1=True, extension="Zbc Zbkc"),

        insn_clmul("clmulr", "010", "rvfi_rs1_rdata >> (`RISCV_FORMAL_XLEN - i - 1)", extension="Zbc"),

        ## Zbs: Single-bit instructions

        insn_bit("bclr",    "010010", "001", "rvfi_rs1_rdata & ~(1 << index)", extension = "Zbs"),
        insn_bit("bclri",   "010010", "001", "rvfi_rs1_rdata & ~(1 << index)", imode=True, extension = "Zbs"),
        insn_bit("bext",    "010010", "101", "(rvfi_rs1_rdata >> index) & 1",  extension = "Zbs"),
        insn_bit("bexti",   "010010", "101", "(rvfi_rs1_rdata >> index) & 1",  imode=True, extension = "Zbs"),
        insn_bit("binv",    "011010", "001", "rvfi_rs1_rdata ^ (1 << index)",  extension = "Zbs"),
        insn_bit("binvi",   "011010", "001", "rvfi_rs1_rdata ^ (1 << index)",  imode=True, extension = "Zbs"),
        insn_bit("bset",    "001010", "001", "rvfi_rs1_rdata | (1 << index)",  extension = "Zbs"),
        insn_bit("bseti",   "001010", "001", "rvfi_rs1_rdata | (1 << index)",  imode=True, extension = "Zbs"),

        ## Zbkx: Crossbar permutations

        insn_xperm("xperm4", "010", 4),
        insn_xperm("xperm8", "100", 8),

    ]}
