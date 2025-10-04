import json
from textwrap import dedent
from typing import Optional

import click

from . import InstructionChecker, CompleteISAChecker
from ..insns import Instruction, builtins
from ..rvfi import (
    base_observers,
    SpeculativeEvaluation,
)
from ..named_set import NamedSet

def base_checks() -> list[SpeculativeEvaluation]:
    return [
        SpeculativeEvaluation(
            "if (rvfi.rs1_addr == 0) assert(rvfi.rs1_rdata == 0);",
            ignore_trap = True,
        ),
        SpeculativeEvaluation(
            "if (rvfi.rs2_addr == 0) assert(rvfi.rs2_rdata == 0);",
            ignore_trap = True,
        ),
        SpeculativeEvaluation(
            "assert(`rvformal_addr_eq(spec_pc_wdata, rvfi.pc_wdata));",
            speculates_about = ["pc_wdata"],
        ),
        SpeculativeEvaluation(
            "if (spec_mem_wmask || spec_mem_rmask) assert(`rvformal_addr_eq(spec_mem_addr, rvfi.mem_addr));",
            speculates_about = ["mem_addr"],
        ),
        SpeculativeEvaluation(
            dedent("""\
                for (i = 0; i < `RISCV_FORMAL_XLEN/8; i = i+1) begin
                    if (spec_mem_wmask[i]) begin
                        assert(rvfi.mem_wmask[i]);
                        assert(spec_mem_wdata[i*8 +: 8] == rvfi.mem_wdata[i*8 +: 8]);
                    end else if (rvfi.mem_wmask[i]) begin
                        assert(rvfi.mem_rmask[i]);
                        assert(rvfi.mem_rdata[i*8 +: 8] == rvfi.mem_wdata[i*8 +: 8]);
                    end
                    if (spec_mem_rmask[i]) begin
                        assert(rvfi.mem_rmask[i]);
                    end
                end"""
            ),
            speculates_about = ["mem_wmask", "mem_rmask", "mem_wdata"],
        ),
    ]

def dump_isa(
    name: str,
    insns: NamedSet[Instruction] | Instruction,
    xlen: int,
    format: str,
    channel: Optional[int] = None,
    channelized: bool = True,
) -> str:
    rvfi = base_observers()
    defined_checks = base_checks()

    # checks base_isa with a missing lb insn check
    # isa_checker = CompleteISAChecker(
    #     name = name,
    #     instructions = insns,
    #     observers = rvfi,
    #     channel = channel,
    #     channelized = channelized if channelized is not None else channel is not None,
    #     valid_opcodes = [
    #         "1110011", # SYSTEM
    #     ], 
    #     extra_valid_checks = [
    #         "rvfi.insn[14:12] == 3'b 000 && rvfi.insn[6:0] == 7'b 0000011", # lb
    #     ]
    # )

    if isinstance(insns, Instruction):
        insns = NamedSet([insns])

    isa_checker = InstructionChecker(
        name = name,
        instructions = insns,
        observers = rvfi,
        defined_checks = defined_checks,
        channel = channel,
        channelized = channelized if channelized is not None else channel is not None,
    )

    isa_checker.configure_io()

    if format == "json":
        return json.dumps(isa_checker)
    elif format == "verilog":
        return isa_checker.to_verilog(xlen=xlen)

@click.option('--fault', is_flag=True)
@click.option('--format', type=click.Choice(['json', 'verilog']), default='json')
@click.command()
def base_isa(fault: bool, format: str):
    xlen = 32
    insns: NamedSet[Instruction] = NamedSet()

    if fault:
        from ..rvfi import mem_fault, misa_fault
        misa_fault.register_weak_misa()

    for insn in builtins():
        # skip incompatible xlen
        if xlen > insn.xlen_max or xlen < insn.xlen_min:
            continue
        # skip M extension for NERV
        if "M" in insn.extension:
            continue

        insns.add(insn)

    click.echo(dump_isa("insn_check", insns, xlen, format))

if __name__ == "__main__":
    base_isa()
