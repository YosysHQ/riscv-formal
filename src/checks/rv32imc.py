import click

from .base_isa import dump_isa
from ..insns import Instruction, builtins
from ..insns.mext import mext
from ..insns.cext import cext

@click.option('--format', type=click.Choice(['json', 'verilog']), default='json')
@click.command()
def rv32imc(format: str):
    xlen = 32
    insns: dict[str, Instruction] = {}
    all_insns: dict[str, Instruction] = builtins()
    all_insns.update(mext())
    all_insns.update(cext())
    for key, val in all_insns.items():
        if xlen > val.xlen_max or xlen < val.xlen_min:
            continue

        if val.extension not in ["I", "M", "Zca"]:
            continue

        insns[key] = val

    click.echo(dump_isa("insn_check", insns, xlen, format))

if __name__ == "__main__":
    rv32imc()
