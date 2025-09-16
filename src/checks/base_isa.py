import json
from textwrap import dedent
from typing import Optional

import click

from .instruction_checker import InstructionChecker
from ..insns import Instruction, builtins
from ..rvfi import (
    Observer,
    SpeculativeObserver,
    ZeroedObserver,
    SpeculativeEvaluation,
)

def dump_isa(
    name: str,
    insns: dict[str, Instruction],
    xlen: int,
    format: str,
    channel: Optional[int] = None,
    channelized: bool = True,
) -> str:
    rvfi: dict[str, Observer] = {o.name: o for o in [
        SpeculativeObserver("valid", "1"),
                   Observer("order", "64"),
                   Observer("insn", "`RISCV_FORMAL_ILEN"),
        SpeculativeObserver("trap", "1"),
                   Observer("halt", "1"),
                   Observer("intr", "1"),
                   Observer("mode", "2"),
                   Observer("ixl", "2"),
        SpeculativeObserver("rs1_addr", "5", "rvfi.rs1_addr"),
        SpeculativeObserver("rs2_addr", "5", "rvfi.rs2_addr"),
             ZeroedObserver("rs1_rdata", "`RISCV_FORMAL_XLEN", "spec_rs1_addr == 0"),
             ZeroedObserver("rs2_rdata", "`RISCV_FORMAL_XLEN", "spec_rs2_addr == 0"),
        SpeculativeObserver("rd_addr", "5"),
        SpeculativeObserver("rd_wdata", "`RISCV_FORMAL_XLEN"),
                   Observer("pc_rdata", "`RISCV_FORMAL_XLEN"),
        SpeculativeObserver("pc_wdata", "`RISCV_FORMAL_XLEN", "rvfi.pc_rdata + 4"),
        SpeculativeObserver("mem_addr", "`RISCV_FORMAL_XLEN"),
        SpeculativeObserver("mem_rmask", "`RISCV_FORMAL_XLEN/8"),
        SpeculativeObserver("mem_wmask", "`RISCV_FORMAL_XLEN/8"),
                   Observer("mem_rdata", "`RISCV_FORMAL_XLEN"),
        SpeculativeObserver("mem_wdata", "`RISCV_FORMAL_XLEN"),
    ]}

    defined_checks: list[SpeculativeEvaluation] = [
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

    isa_checker = InstructionChecker(
        name = name,
        instructions = insns,
        observers = rvfi,
        defined_checks = defined_checks,
        channel = channel,
        channelized = channelized if channelized is not None else channel is not None
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
    insns: dict[str, Instruction] = {}

    if fault:
        from ..rvfi import mem_fault, misa_fault
        misa_fault.register_weak_misa()

    for key, val in builtins().items():
        # skip incompatible xlen
        if xlen > val.xlen_max or xlen < val.xlen_min:
            continue
        # skip M extension for NERV
        if "M" in val.extension:
            continue

        insns[key] = val

    click.echo(dump_isa("insn_check", insns, xlen, format))

if __name__ == "__main__":
    base_isa()
