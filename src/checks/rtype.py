import click

from .base_isa import dump_isa
from ..insns import Instruction, builtins

@click.option('--format', type=click.Choice(['json', 'verilog']), default='json')
@click.command()
def rtype(format: str):
    rtype_mnemonics = ["add", "sub", "slt", "sltu", "xor", "or", "and"]
    rtype_insns: dict[str, Instruction] = {}
    for key, val in builtins().items():
        if key in rtype_mnemonics:
            rtype_insns[key] = val

    dump_isa("insn_check", rtype_insns, 32, format)

if __name__ == "__main__":
    rtype()
