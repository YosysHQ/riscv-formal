import json
import click

from .instruction_checker import InstructionChecker
from ..insns import Instruction, builtins
from ..rvfi import Observer, SpeculativeObserver, ZeroedObserver

def dump_isa(name: str, insns: dict[str, Instruction], xlen: int, format: str):
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

    isa_checker = InstructionChecker(
        name = name,
        instructions = insns,
        observers = rvfi,
    )

    isa_checker.configure_io()

    if format == "json":
        data = json.dumps(isa_checker)
    elif format == "verilog":
        data = isa_checker.to_verilog(xlen=xlen)
    click.echo(data)

@click.option('--format', type=click.Choice(['json', 'verilog']), default='json')
@click.command()
def base_isa(format: str):
    xlen = 32
    insns: dict[str, Instruction] = {}

    for key, val in builtins().items():
        # skip incompatible xlen
        if xlen > val.xlen_max or xlen < val.xlen_min:
            continue
        # skip M extension for NERV
        if "M" in val.extension:
            continue
        # skip memory related instructions because they're incomplete
        if val.mem_addr:
            continue

        insns[key] = val

    dump_isa("insn_check", insns, xlen, format)

if __name__ == "__main__":
    base_isa()
