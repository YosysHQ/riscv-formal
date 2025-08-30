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


def insn_alu(mnemonic, funct7, funct3, expr, alt_add=None, alt_sub=None, shamt=False, wmode=False, uwmode=False, extension="I"):
    if wmode and uwmode:
        raise NotImplementedError("Got both uwmode and umode")
    elif uwmode or wmode:
        opcode = "0111011"
    else:
        opcode = "0110011"

    insn = Instruction(
        name=mnemonic,
        insn_parts=FORMAT_R.insn_parts,
        opcode=opcode,
        result=expr,
        extension=extension,
        alt_add=alt_add,
        alt_sub=alt_sub,
        shamt=shamt,
        sign_extend_from = 32 if wmode else None,
        xlen_min = 64 if wmode or uwmode else 32,
        op_values = {
            "funct7": funct7,
            "funct3": funct3,
        },
    )

    return insn

@click.command()
@click.option('-i', '--ilen', type=int, default=32)
@click.option('-x', '--xlen', type=int, default=32)
@click.option('--format', type=click.Choice(['json', 'verilog', 'auto']), default='auto')
@click.argument('out_file', type=click.Path(path_type=Path))
@click.argument('insn', type=str, default = "")
def generate(ilen: int, xlen: int, format: str, out_file: Path, insn: str):
    insns: dict[str, Instruction] = {}

    insns["add"] = insn_alu("add",  "0000000", "000", "rvfi_rs1_rdata + rvfi_rs2_rdata")
    insns["sub"] = insn_alu("sub",  "0100000", "000", "rvfi_rs1_rdata - rvfi_rs2_rdata")
    insns["sll"] = insn_alu("sll",  "0000000", "001", "rvfi_rs1_rdata << shamt", shamt=True)
    insns["slt"] = insn_alu("slt",  "0000000", "010", "$signed(rvfi_rs1_rdata) < $signed(rvfi_rs2_rdata)")
    insns["sltu"] = insn_alu("sltu", "0000000", "011", "rvfi_rs1_rdata < rvfi_rs2_rdata")
    insns["xor"] = insn_alu("xor",  "0000000", "100", "rvfi_rs1_rdata ^ rvfi_rs2_rdata")
    insns["srl"] = insn_alu("srl",  "0000000", "101", "rvfi_rs1_rdata >> shamt", shamt=True)
    insns["sra"] = insn_alu("sra",  "0100000", "101", "$signed(rvfi_rs1_rdata) >>> shamt", shamt=True)
    insns["or"] = insn_alu("or",   "0000000", "110", "rvfi_rs1_rdata | rvfi_rs2_rdata")
    insns["and"] = insn_alu("and",  "0000000", "111", "rvfi_rs1_rdata & rvfi_rs2_rdata")

    insns["addw"] = insn_alu("addw", "0000000", "000", "rvfi_rs1_rdata[31:0] + rvfi_rs2_rdata[31:0]", wmode=True)
    insns["subw"] = insn_alu("subw", "0100000", "000", "rvfi_rs1_rdata[31:0] - rvfi_rs2_rdata[31:0]", wmode=True)
    insns["sllw"] = insn_alu("sllw", "0000000", "001", "rvfi_rs1_rdata[31:0] << shamt", shamt=True, wmode=True)
    insns["srlw"] = insn_alu("srlw", "0000000", "101", "rvfi_rs1_rdata[31:0] >> shamt", shamt=True, wmode=True)
    insns["sraw"] = insn_alu("sraw", "0100000", "101", "$signed(rvfi_rs1_rdata[31:0]) >>> shamt", shamt=True, wmode=True)

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
