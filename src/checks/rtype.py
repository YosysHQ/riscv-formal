import json
import click

from .instruction_checker import InstructionChecker
from ..insns import Instruction, builtins
from ..rvfi import Observer, SpeculativeObserver, ZeroedObserver

@click.option('--format', type=click.Choice(['json', 'verilog']), default='json')
@click.command()
def rtype(format: str):
    rtype_mnemonics = ["add", "sub", "slt", "sltu", "xor", "or", "and"]
    rtype_insns: dict[str, Instruction] = {}
    for key, val in builtins().items():
        if key in rtype_mnemonics:
            rtype_insns[key] = val

    rvfi: dict[str, Observer] = {o.name: o for o in [
        SpeculativeObserver("valid", "1"),
                   Observer("order", "64"),
                   Observer("insn", "`RISCV_FORMAL_ILEN"),
        SpeculativeObserver("trap", "1"),
                   Observer("halt", "1"),
                   Observer("intr", "1"),
                   Observer("mode", "2"),
                   Observer("ixl", "2"),
        SpeculativeObserver("rs1_addr", "5"),
        SpeculativeObserver("rs2_addr", "5"),
             ZeroedObserver("rs1_rdata", "`RISCV_FORMAL_XLEN", "spec_rs1_addr == 0"),
             ZeroedObserver("rs2_rdata", "`RISCV_FORMAL_XLEN", "spec_rs2_addr == 0"),
        SpeculativeObserver("rd_addr", "5"),
        SpeculativeObserver("rd_wdata", "`RISCV_FORMAL_XLEN"),
                   Observer("pc_rdata", "`RISCV_FORMAL_XLEN"),
        SpeculativeObserver("pc_wdata", "`RISCV_FORMAL_XLEN", "rvfi_pc_rdata + 4"),
        SpeculativeObserver("mem_addr", "`RISCV_FORMAL_XLEN"),
        SpeculativeObserver("mem_rmask", "`RISCV_FORMAL_XLEN/8"),
        SpeculativeObserver("mem_wmask", "`RISCV_FORMAL_XLEN/8"),
                   Observer("mem_rdata", "`RISCV_FORMAL_XLEN"),
        SpeculativeObserver("mem_wdata", "`RISCV_FORMAL_XLEN"),
    ]}

    rtype_checker = InstructionChecker(
        name = "rtype_insns",
        instructions = rtype_insns,
        observers = rvfi,
    )
    if format == "json":
        data = json.dumps(rtype_checker)
    elif format == "verilog":
        data = rtype_checker.to_verilog(xlen=32)
    click.echo(data)

if __name__ == "__main__":
    rtype()
