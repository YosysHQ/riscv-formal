import click

from .base_isa import dump_isa
from ..insns import Instruction, builtins
from ..named_set import NamedSet

@click.option('--format', type=click.Choice(['json', 'verilog']), default='json')
@click.command()
def rtype(format: str):
    rtype_mnemonics = ["add", "sub", "slt", "sltu", "xor", "or", "and"]
    rtype_insns: NamedSet[Instruction] = NamedSet()
    for insn in builtins():
        if insn.name in rtype_mnemonics:
            rtype_insns.add(insn)

    click.echo(dump_isa("insn_check", rtype_insns, 32, format))

if __name__ == "__main__":
    rtype()
