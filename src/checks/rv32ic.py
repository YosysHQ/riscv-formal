import click

from .base_isa import dump_isa
from ..insns import Instruction, builtins
from ..insns.cext import cext

@click.option('--format', type=click.Choice(['json', 'verilog']), default='json')
@click.command()
def rtype(format: str):
    xlen = 32
    rv32ic: dict[str, Instruction] = {}
    all_insns: dict[str, Instruction] = builtins()
    all_insns.update(cext())
    for key, val in all_insns.items():
        if xlen > val.xlen_max or xlen < val.xlen_min:
            continue
        if val.extension not in ["I", "Zca"]:
            continue

        rv32ic[key] = val

    dump_isa("insn_check", rv32ic, xlen, format)

if __name__ == "__main__":
    rtype()
