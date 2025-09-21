import json
import click

from . import CsrChecker
from ..csrs import Csr, base_csrs
from ..named_set import NamedSet

def dump_csr(name: str, csrs: NamedSet[Csr], xlen: int, format: str) -> str:
    csr_checker = CsrChecker(
        name = name,
        csrs = csrs,
    )

    if format == "json":
        return json.dumps(csr_checker)
    elif format == "verilog":
        return csr_checker.to_verilog()

@click.option('-x', '--xlen', type=int, default=32)
@click.option('--format', type=click.Choice(['json', 'verilog']), default='json')
@click.command()
def base_csr(xlen: int, format: str):
    csrs: NamedSet[Csr] = NamedSet()
    for csr in base_csrs():
        if csr.name not in ["cycle", "mcycle"]:
            continue

        csrs.add(csr)

    click.echo(dump_csr("csr_check", csrs, xlen, format))

if __name__ == "__main__":
    base_csr()
