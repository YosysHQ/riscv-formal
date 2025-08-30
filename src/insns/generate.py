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

import json
from pathlib import Path
import click

from .model import Instruction, Instruction_format

FORMAT_R = Instruction_format(
    "R-type", [
        ("funct7", 7),
        ("rs2", 5),
        ("rs1", 5),
        ("funct3", 3),
        ("rd", 5),
        ("opcode", 7),
    ]
)

FORMAT_I = Instruction_format(
    "I-type", [
        ("imm12", 12),
        ("rs1", 5),
        ("funct3", 3),
        ("rd", 5),
        ("opcode", 7),
    ]
)

FORMAT_I_SHIFT = Instruction_format(
    "I-type (shift variation)", [
        ("funct6", 6),
        ("shamt", 6),
        ("rs1", 5),
        ("funct3", 3),
        ("rd", 5),
        ("opcode", 7),
    ]
)

FORMAT_S = Instruction_format(
    "S-type", [
        ("imm11_5", 7),
        ("rs2", 5),
        ("rs1", 5),
        ("funct3", 3),
        ("imm4_0", 5),
        ("opcode", 7),
    ]
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
    ]
)

FORMAT_U = Instruction_format(
    "U-type", [
        ("imm20", 20),
        ("rd", 5),
        ("opcode", 7),
    ]
)

FORMAT_J = Instruction_format(
    "J-type", [
        ("imm20", 1),
        ("imm10_1", 10),
        ("imm11", 1),
        ("imm19_12", 8),
        ("rd", 5),
        ("opcode", 7),
    ]
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
        raw_code = [
            "wire [`RISCV_FORMAL_XLEN-1:0] insn_imm = $signed({{insn_imm12, insn_imm11, insn_imm10_5, insn_imm4_1, 1'b0}});",
            f"wire cond = {expr};",
            f"wire [`RISCV_FORMAL_XLEN-1:0] next_pc = cond ? rvfi_pc_rdata + insn_imm : rvfi_pc_rdata + 4;",
        ],
        spec_map = {
            "pc_wdata": "next_pc",
            "trap": "next_pc[1:0] != 0"
        }
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
        raw_code = ["wire [`RISCV_FORMAL_XLEN - 1 : 0] insn_imm = $signed(insn_imm12);"]
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
        xlen_min = 64 if wmode else 32,
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

@click.command()
@click.option('-i', '--ilen', type=int, default=32)
@click.option('-x', '--xlen', type=int, default=32)
@click.option('--format', type=click.Choice(['json', 'verilog', 'auto']), default='auto')
@click.argument('out_file', type=click.Path(path_type=Path))
@click.argument('insn', type=str, default = "")
def generate(ilen: int, xlen: int, format: str, out_file: Path, insn: str):
    insns: dict[str, Instruction] = {}

    # Base Integer ISA (I)

    insns["beq"] =  insn_b("beq",  "000", "rvfi_rs1_rdata == rvfi_rs2_rdata")
    insns["bne"] =  insn_b("bne",  "001", "rvfi_rs1_rdata != rvfi_rs2_rdata")
    insns["blt"] =  insn_b("blt",  "100", "$signed(rvfi_rs1_rdata) < $signed(rvfi_rs2_rdata)")
    insns["bge"] =  insn_b("bge",  "101", "$signed(rvfi_rs1_rdata) >= $signed(rvfi_rs2_rdata)")
    insns["bltu"] = insn_b("bltu", "110", "rvfi_rs1_rdata < rvfi_rs2_rdata")
    insns["bgeu"] = insn_b("bgeu", "111", "rvfi_rs1_rdata >= rvfi_rs2_rdata")

    insns["add"] =  insn_alu("add",  "0000000", "000", "rvfi_rs1_rdata + rvfi_rs2_rdata")
    insns["sub"] =  insn_alu("sub",  "0100000", "000", "rvfi_rs1_rdata - rvfi_rs2_rdata")
    insns["sll"] =  insn_alu("sll",  "0000000", "001", "rvfi_rs1_rdata << shamt", shamt=True)
    insns["slt"] =  insn_alu("slt",  "0000000", "010", "$signed(rvfi_rs1_rdata) < $signed(rvfi_rs2_rdata)")
    insns["sltu"] = insn_alu("sltu", "0000000", "011", "rvfi_rs1_rdata < rvfi_rs2_rdata")
    insns["xor"] =  insn_alu("xor",  "0000000", "100", "rvfi_rs1_rdata ^ rvfi_rs2_rdata")
    insns["srl"] =  insn_alu("srl",  "0000000", "101", "rvfi_rs1_rdata >> shamt", shamt=True)
    insns["sra"] =  insn_alu("sra",  "0100000", "101", "$signed(rvfi_rs1_rdata) >>> shamt", shamt=True)
    insns["or"] =   insn_alu("or",   "0000000", "110", "rvfi_rs1_rdata | rvfi_rs2_rdata")
    insns["and"] =  insn_alu("and",  "0000000", "111", "rvfi_rs1_rdata & rvfi_rs2_rdata")

    insns["addi"] =  insn_imm("addi",  "000", "rvfi_rs1_rdata + insn_imm")
    insns["slti"] =  insn_imm("slti",  "010", "$signed(rvfi_rs1_rdata) < $signed(insn_imm)")
    insns["sltiu"] = insn_imm("sltiu", "011", "rvfi_rs1_rdata < insn_imm")
    insns["xori"] =  insn_imm("xori",  "100", "rvfi_rs1_rdata ^ insn_imm")
    insns["ori"] =   insn_imm("ori",   "110", "rvfi_rs1_rdata | insn_imm")
    insns["andi"] =  insn_imm("andi",  "111", "rvfi_rs1_rdata & insn_imm")

    insns["slli"] = insn_shimm("slli", "000000", "001", "rvfi_rs1_rdata << insn_shamt")
    insns["srli"] = insn_shimm("srli", "000000", "101", "rvfi_rs1_rdata >> insn_shamt")
    insns["srai"] = insn_shimm("srai", "010000", "101", "$signed(rvfi_rs1_rdata) >>> insn_shamt")

    insns["addiw"] = insn_imm("addiw",  "000", "rvfi_rs1_rdata[31:0] + insn_imm[31:0]", wmode=True)

    insns["slliw"] = insn_shimm("slliw", "000000", "001", "rvfi_rs1_rdata[31:0] << insn_shamt", wmode=True)
    insns["srliw"] = insn_shimm("srliw", "000000", "101", "rvfi_rs1_rdata[31:0] >> insn_shamt", wmode=True)
    insns["sraiw"] = insn_shimm("sraiw", "010000", "101", "$signed(rvfi_rs1_rdata[31:0]) >>> insn_shamt", wmode=True)

    insns["addw"] = insn_alu("addw", "0000000", "000", "rvfi_rs1_rdata[31:0] + rvfi_rs2_rdata[31:0]", wmode=True)
    insns["subw"] = insn_alu("subw", "0100000", "000", "rvfi_rs1_rdata[31:0] - rvfi_rs2_rdata[31:0]", wmode=True)
    insns["sllw"] = insn_alu("sllw", "0000000", "001", "rvfi_rs1_rdata[31:0] << shamt", shamt=True, wmode=True)
    insns["srlw"] = insn_alu("srlw", "0000000", "101", "rvfi_rs1_rdata[31:0] >> shamt", shamt=True, wmode=True)
    insns["sraw"] = insn_alu("sraw", "0100000", "101", "$signed(rvfi_rs1_rdata[31:0]) >>> shamt", shamt=True, wmode=True)

    # Multiply/Divide ISA (M)

    insns["mul"] =    insn_alu("mul",    "0000001", "000", "rvfi_rs1_rdata * rvfi_rs2_rdata", alt_add=0x2cdf52a55876063e, extension="M")
    insns["mulh"] =   insn_alu("mulh",   "0000001", "001", "({{`RISCV_FORMAL_XLEN{rvfi_rs1_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_rs1_rdata} *\n" +
            "\t\t{{`RISCV_FORMAL_XLEN{rvfi_rs2_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_add=0x15d01651f6583fb7, extension="M")
    insns["mulhsu"] = insn_alu("mulhsu", "0000001", "010", "({{`RISCV_FORMAL_XLEN{rvfi_rs1_rdata[`RISCV_FORMAL_XLEN-1]}}, rvfi_rs1_rdata} *\n" +
            "\t\t{`RISCV_FORMAL_XLEN'b0, rvfi_rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_sub=0xea3969edecfbe137, extension="M")
    insns["mulhu"] =  insn_alu("mulhu",  "0000001", "011", "({`RISCV_FORMAL_XLEN'b0, rvfi_rs1_rdata} * {`RISCV_FORMAL_XLEN'b0, rvfi_rs2_rdata}) >> `RISCV_FORMAL_XLEN", alt_add=0xd13db50d949ce5e8, extension="M")

    insns["div"] =    insn_alu("div",    "0000001", "100", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? {`RISCV_FORMAL_XLEN{1'b1}} :
                                                              rvfi_rs1_rdata == {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} && rvfi_rs2_rdata == {`RISCV_FORMAL_XLEN{1'b1}} ? {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} :
                                                              $signed(rvfi_rs1_rdata) / $signed(rvfi_rs2_rdata)""", alt_sub=0x29bbf66f7f8529ec, extension="M")
    insns["divu"] =   insn_alu("divu",   "0000001", "101", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? {`RISCV_FORMAL_XLEN{1'b1}} :
                                                              rvfi_rs1_rdata / rvfi_rs2_rdata""", alt_sub=0x8c629acb10e8fd70, extension="M")

    insns["rem"] =    insn_alu("rem",    "0000001", "110", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? rvfi_rs1_rdata :
                                                              rvfi_rs1_rdata == {1'b1, {`RISCV_FORMAL_XLEN-1{1'b0}}} && rvfi_rs2_rdata == {`RISCV_FORMAL_XLEN{1'b1}} ? {`RISCV_FORMAL_XLEN{1'b0}} :
                                                              $signed(rvfi_rs1_rdata) % $signed(rvfi_rs2_rdata)""", alt_sub=0xf5b7d8538da68fa5, extension="M")
    insns["remu"] =   insn_alu("remu",   "0000001", "111", """rvfi_rs2_rdata == `RISCV_FORMAL_XLEN'b0 ? rvfi_rs1_rdata :
                                                              rvfi_rs1_rdata % rvfi_rs2_rdata""", alt_sub=0xbc4402413138d0e1, extension="M")

    insns["mulw"] =   insn_alu("mulw",   "0000001", "000", "rvfi_rs1_rdata[31:0] * rvfi_rs2_rdata[31:0]", alt_add=0x2cdf52a55876063e, wmode=True, extension="M")

    insns["divw"] =   insn_alu("divw",   "0000001", "100", """rvfi_rs2_rdata[31:0] == 32'b0 ? {32{1'b1}} :
                                                               rvfi_rs1_rdata == {1'b1, {31{1'b0}}} && rvfi_rs2_rdata == {32{1'b1}} ? {1'b1, {31{1'b0}}} :
                                                               $signed(rvfi_rs1_rdata[31:0]) / $signed(rvfi_rs2_rdata[31:0])""", alt_sub=0x29bbf66f7f8529ec, wmode=True, extension="M")
    insns["divuw"] =  insn_alu("divuw",  "0000001", "101", """rvfi_rs2_rdata[31:0] == 32'b0 ? {32{1'b1}} :
                                                               rvfi_rs1_rdata[31:0] / rvfi_rs2_rdata[31:0]""", alt_sub=0x8c629acb10e8fd70, wmode=True, extension="M")

    insns["remw"] =   insn_alu("remw",   "0000001", "110", """rvfi_rs2_rdata == 32'b0 ? rvfi_rs1_rdata :
                                                               rvfi_rs1_rdata == {1'b1, {31{1'b0}}} && rvfi_rs2_rdata == {32{1'b1}} ? {32{1'b0}} :
                                                               $signed(rvfi_rs1_rdata[31:0]) % $signed(rvfi_rs2_rdata[31:0])""", alt_sub=0xf5b7d8538da68fa5, wmode=True, extension="M")
    insns["remuw"] =  insn_alu("remuw",  "0000001", "111", """rvfi_rs2_rdata == 32'b0 ? rvfi_rs1_rdata :
                                                               rvfi_rs1_rdata[31:0] % rvfi_rs2_rdata[31:0]""", alt_sub=0xbc4402413138d0e1, wmode=True, extension="M")

    # Bit Manipulation ISA (B)

    ## Zba: Address generation

    insns["sh1add"] = insn_alu("sh1add",  "0010000", "010", "rvfi_rs2_rdata + (rvfi_rs1_rdata << 1)", extension="Zba")
    insns["sh2add"] = insn_alu("sh2add",  "0010000", "100", "rvfi_rs2_rdata + (rvfi_rs1_rdata << 2)", extension="Zba")
    insns["sh3add"] = insn_alu("sh3add",  "0010000", "110", "rvfi_rs2_rdata + (rvfi_rs1_rdata << 3)", extension="Zba")

    insns["add_uw"] =    insn_alu("add_uw",      "0000100", "000", "rvfi_rs2_rdata + rvfi_rs1_rdata[31:0]",          uwmode=True, extension="Zba")
    insns["sh1add_uw"] = insn_alu("sh1add_uw",   "0010000", "010", "rvfi_rs2_rdata + (rvfi_rs1_rdata[31:0] << 1)",   uwmode=True, extension="Zba")
    insns["sh2add_uw"] = insn_alu("sh2add_uw",   "0010000", "100", "rvfi_rs2_rdata + (rvfi_rs1_rdata[31:0] << 2)",   uwmode=True, extension="Zba")
    insns["sh3add_uw"] = insn_alu("sh3add_uw",   "0010000", "110", "rvfi_rs2_rdata + (rvfi_rs1_rdata[31:0] << 3)",   uwmode=True, extension="Zba")
    insns["slli_uw"] =   insn_shimm("slli_uw",   "000010",  "001", "rvfi_rs1_rdata[31:0] << insn_shamt",             uwmode=True, extension="Zba")

    ## Zbb: Basic bit-manipulation

    insns["max"] =  insn_alu("max",     "0000101", "110", "($signed(rvfi_rs1_rdata) < $signed(rvfi_rs2_rdata)) ? rvfi_rs2_rdata : rvfi_rs1_rdata", extension="Zbb")
    insns["maxu"] = insn_alu("maxu",    "0000101", "111", "(rvfi_rs1_rdata < rvfi_rs2_rdata) ? rvfi_rs2_rdata : rvfi_rs1_rdata", extension="Zbb")
    insns["min"] =  insn_alu("min",     "0000101", "100", "($signed(rvfi_rs1_rdata) < $signed(rvfi_rs2_rdata)) ? rvfi_rs1_rdata : rvfi_rs2_rdata", extension="Zbb")
    insns["minu"] = insn_alu("minu",    "0000101", "101", "(rvfi_rs1_rdata < rvfi_rs2_rdata) ? rvfi_rs1_rdata : rvfi_rs2_rdata", extension="Zbb")

    insns["andn"] = insn_alu("andn",    "0100000", "111", "rvfi_rs1_rdata & ~rvfi_rs2_rdata",   extension="Zbb Zbkb")
    insns["orn"] =  insn_alu("orn",     "0100000", "110", "rvfi_rs1_rdata | ~rvfi_rs2_rdata",   extension="Zbb Zbkb")
    insns["xnor"] = insn_alu("xnor",    "0100000", "100", "~(rvfi_rs1_rdata ^ rvfi_rs2_rdata)", extension="Zbb Zbkb")
    insns["rol"] =  insn_alu("rol",     "0110000", "001", "(rvfi_rs1_rdata << shamt) | (rvfi_rs1_rdata >> (`RISCV_FORMAL_XLEN - shamt))", shamt=True, extension="Zbb Zbkb")
    insns["ror"] =  insn_alu("ror",     "0110000", "101", "(rvfi_rs1_rdata >> shamt) | (rvfi_rs1_rdata << (`RISCV_FORMAL_XLEN - shamt))", shamt=True, extension="Zbb Zbkb")
    insns["rori"] = insn_shimm("rori",  "011000", "101", "(rvfi_rs1_rdata >> insn_shamt) | (rvfi_rs1_rdata << (`RISCV_FORMAL_XLEN - insn_shamt))", extension="Zbb Zbkb")

    insns["rolw"] =  insn_alu("rolw",    "0110000", "001", "(rvfi_rs1_rdata[31:0] << shamt) | (rvfi_rs1_rdata[31:0] >> (32 - shamt))", shamt=True, wmode=True, extension="Zbb Zbkb")
    insns["rorw"] =  insn_alu("rorw",    "0110000", "101", "(rvfi_rs1_rdata[31:0] >> shamt) | (rvfi_rs1_rdata[31:0] << (32 - shamt))", shamt=True, wmode=True, extension="Zbb Zbkb")
    insns["roriw"] = insn_shimm("roriw", "011000", "101", "(rvfi_rs1_rdata[31:0] >> insn_shamt) | (rvfi_rs1_rdata[31:0] << (32 - insn_shamt))", wmode=True, extension="Zbb Zbkb")

    ## Zbs: Single-bit instructions

    insns["bclr"] =   insn_bit("bclr",    "010010", "001", "rvfi_rs1_rdata & ~(1 << index)", extension = "Zbs")
    insns["bclri"] =  insn_bit("bclri",   "010010", "001", "rvfi_rs1_rdata & ~(1 << index)", imode=True, extension = "Zbs")
    insns["bext"] =   insn_bit("bext",    "010010", "101", "(rvfi_rs1_rdata >> index) & 1",  extension = "Zbs")
    insns["bexti"] =  insn_bit("bexti",   "010010", "101", "(rvfi_rs1_rdata >> index) & 1",  imode=True, extension = "Zbs")
    insns["binv"] =   insn_bit("binv",    "011010", "001", "rvfi_rs1_rdata ^ (1 << index)",  extension = "Zbs")
    insns["binvi"] =  insn_bit("binvi",   "011010", "001", "rvfi_rs1_rdata ^ (1 << index)",  imode=True, extension = "Zbs")
    insns["bset"] =   insn_bit("bset",    "001010", "001", "rvfi_rs1_rdata | (1 << index)",  extension = "Zbs")
    insns["bseti"] =  insn_bit("bseti",   "001010", "001", "rvfi_rs1_rdata | (1 << index)",  imode=True, extension = "Zbs")

    if insn and insn not in insns:
        raise NotImplementedError(f"{insn} instruction")

    if insn:
        if format == "auto":
            if out_file.suffix == ".json":
                format = "json"
            elif out_file.suffix in [".v", ".sv"]:
                format = "verilog"
        
        instruction = insns[insn]
        if format == "json":
            data = instruction.to_json(skip_empty=True, indent=2)
        elif format == "verilog":
            data = instruction.to_verilog(xlen, ilen)
        else:
            raise NotImplementedError(f"{out_file.suffix!r} not supported")
    else:
        data = json.dumps(insns)
    with open(out_file, 'wt', encoding='utf-8') as f:
        click.echo(data, f)


if __name__ == "__main__":
    generate()
