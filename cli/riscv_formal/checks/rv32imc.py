import click

from .base_isa import dump_isa
from ..insns import Instruction, builtins
from ..insns.mext import mext
from ..insns.cext import cext
from ..named_set import NamedSet

@click.option('--format', type=click.Choice(['json', 'verilog']), default='json')
@click.command()
def rv32imc(format: str):
    xlen = 32
    insns: NamedSet[Instruction] = NamedSet
    all_insns: NamedSet[Instruction] = builtins()
    all_insns.update(mext())
    all_insns.update(cext())
    for insn in all_insns:
        if xlen > insn.xlen_max or xlen < insn.xlen_min:
            continue

        if insn.extension not in ["I", "M", "Zca"]:
            continue

        insns.add(insn)

    click.echo(dump_isa("insn_check", insns, xlen, format))

if __name__ == "__main__":
    rv32imc()
